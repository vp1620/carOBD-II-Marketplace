# Car OBD-II Marketplace

Read OBD-2 fault data from a vehicle, diagnose issues with an AI agent (backed by owner's-manual + community knowledge), and connect car owners with parts/mechanics through a marketplace.

**Wedge customer:** the budget-conscious driver enthusiast — *"the least I need to spend to track my car safely."* The B2C enthusiast product leads; the mechanic/marketplace B2B side is a second segment.

> **Build order:** get a simple functioning full-stack website working first, then layer everything else on top. See [Roadmap](#roadmap) and [Future Concepts](#future-concepts).

---

---

## Where things live

This file is the overview. Depth lives next to the thing it describes.

| | |
|---|---|
| **[`docs/features/`](docs/features/)** | how each feature works, why, and what bites — start at its README |
| **[`backlog/`](backlog/)** | roadmap, one file per phase, each with exit criteria |
| **[`docs/market/`](docs/market/)** | who wants this — go-to-market, validation questions, competitors, and what real people actually said |
| **`DECISIONS.md`** | why the code looks the way it does — question, first answer, concern, decision |
| **`CLAUDE.md`** | working agreements for this repo |

## Repository Structure

```
carOBD-II-Marketplace/
├── backend-OBD-reader/
│   ├── obd_reader/            # the reader package (decode ELM327 → records)
│   │   ├── pids.py            # PID registry + decode formulas
│   │   ├── decoder.py         # raw hex → value / fault codes
│   │   ├── models.py          # Reading record (the downstream data shape)
│   │   ├── reader.py          # SerialReader (real adapter) + FixtureReader (offline)
│   │   └── server.py          # FastAPI app: polls the reader, pushes readings over /ws
│   ├── main.py                # entry point — starts the server on :8000
│   └── tests/
│       └── test_decoder.py    # golden-file test: replays a capture through the real reader
├── frontend-web/              # Live dashboard — vanilla JS, no build step
├── test_files/
│   ├── sample_obd_raw_stream.txt # recorded ELM327 capture (test input)
│   └── sample_obd_output.json    # golden reader output (expected result)
├── DEVELOPMENT_PLAN.md        # full living plan
└── README.md
```

---

## Quick Start — Record Parsing

The adapter sends raw ASCII hex (e.g. `41 0C 1A F8`); the reader decodes it into JSON records (a `Reading` per value). The test replays a recorded capture (`test_files/sample_obd_raw_stream.txt`) through the **real** reader and checks the output against a known-correct "golden" file (`test_files/sample_obd_output.json`). A *golden-file* test = run the code, then diff its output against a committed expected file; any drift fails the test.

```bash
cd backend-OBD-reader

# Run the golden-file + edge-case tests (no pytest install needed)
python3 tests/test_decoder.py     # -> 6/6 passed

# Or with pytest for the same tests
pytest tests/test_decoder.py -q
```

---

## Running the live feed

```bash
pip install -r requirements.txt
python3 backend-OBD-reader/main.py        # fixture mode — no car needed, serves :8000
```

With a real adapter, point it at the serial port:

```bash
OBD_PORT=/dev/tty.OBDII python3 backend-OBD-reader/main.py
```

It binds `0.0.0.0`, so a phone on the same network can reach the dashboard. Connect a
client and print five live messages:

```bash
python3 - <<'EOF'
import asyncio, json, websockets
async def main():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        for _ in range(5):
            print(json.loads(await ws.recv()))
asyncio.run(main())
EOF
```

---

---

## How it works, in five lines

```
car ──OBD-II──► ELM327 adapter ──serial──► SerialReader ──► decoder ──► Reading
                                                                          │
              browser ◄──WebSocket── FastAPI ◄── faults.describe() ◄──────┘
```

1. **`reader.py`** asks the adapter for one PID at a time and reads back a line of hex.
2. **`decoder.py`** turns that hex into a number, using the formula in **`pids.py`**.
3. **`faults.py`** turns a fault code into meaning: description, severity, and where on the car.
4. **`server.py`** fans each reading out to every connected browser.
5. **`app.js`** draws it.

**The protocol details, the framing, and the gotchas are in
[`docs/features/obd-reader.md`](docs/features/obd-reader.md).** It is worth reading before
changing anything in `reader.py` — the ELM327's `>`-prompt framing and its habit of echoing
commands are not obvious from the code.

No car needed: with no adapter attached the reader replays a recording, and
`OBD_FIXTURE` selects which. See [`simulated_codes/`](simulated_codes/).

## Tech Stack

**Backend:** Python now — **the ELM327 protocol and the OBD-II decoders are written from the spec, not wrapped from a library.** `pyserial` for the port, FastAPI for the WebSocket; everything above the byte stream is ours: AT-command init, `>`-prompt framing, Mode 01 PID formulas (SAE J1979) and Mode 03 DTC bit-unpacking (SAE J2012).

Why that was worth doing rather than importing `python-obd`: the decode path had to be injectable so a recorded byte capture could drive the **real** reader in tests (`FakeSerial`), and it had to stay reachable when the transport changes — a BLE adapter (#31) plugs in behind the same two-method contract. A library that owns its own serial connection can do neither. `python-obd` is used, deliberately, as an **independent oracle** in `backend-OBD-reader/tools/compare_decoders.py` — never imported by `obd_reader/`.

→ Go later (`go.bug.st/serial`, goroutines, `gorilla/websocket`). Migration is gradual and gated: GO-0 checks the Python against an external reference *before* porting, GO-4 shadow-runs Go beside Python on identical bytes, and the fallback switch ships with an expiry date.

**Frontend:** **Vanilla JS today — no build step, no framework, no bundler.** A deliberate Phase 1 choice: the page is ~200 lines and the dependency it needs is a WebSocket, which the browser already has. Adding React would mean a toolchain to run a dashboard that fits on one screen.

The condition that would change it: state living in more than one place at once. Today `renderFaults()` is a pure function of the last message; when active faults have to be held, diffed and animated independently (#27), a component model starts paying for itself.

→ React Native later for mobile, which is the one path that genuinely needs it — iOS forbids Bluetooth Classic SPP, so a native app is the only way to reach a BLE adapter from a phone (#31, MOB-2).

**Storage (polyglot, one Postgres instance where possible):**

| Data | Storage | Why |
|---|---|---|
| Raw OBD readings (live) | PostgreSQL **JSONB** | Flexible schema, PIDs vary by car |
| Fault events / DTC history | **TimescaleDB** (Postgres extension) | Time-series: onset, trends, recurrence |
| Vehicles / users / marketplace | PostgreSQL (relational) | Structured, needs joins |
| Owner's manual + Reddit embeddings | **Qdrant** | Vector / semantic search |
| Raw scraped Reddit data | **MongoDB** | Flexible schema |
| Agent session state | **Redis** | Fast, TTL |
| Posted questions + reply tracking | **MongoDB** | Lifecycle tracking |

DynamoDB considered but deferred (upfront access-pattern design, AWS lock-in, early ops complexity). Migration trigger: Postgres write throughput becoming a bottleneck.

**Language split at a glance:**
- **Python** — Phase 1 + the entire agentic/AI layer (best ecosystem for RAG, embeddings, scraping)
- **Go** — performance-critical serial-read + WebSocket-serve backend, once Phase 1 is proven
- **Kotlin/Java** — only the Android Auto surface
- **JS/TypeScript** — vanilla for the Phase 1 dashboard; React Native for mobile when MOB-2 lands

---

---

## Testing

```bash
pytest backend-OBD-reader/tests -q
```

Three kinds, doing three different jobs:

| Kind | Answers | Why it exists |
|---|---|---|
| **Golden-file** | does the reader still do what it used to? | replays a byte capture through the **real** `SerialReader` via an injected `FakeSerial` — not a parallel parser |
| **Spec conformance** | does it do the **right** thing? | re-implements SAE J1979 independently. Deliberately does *not* import `pids.py`: an oracle that imports the code under test proves nothing |
| **Contract** | do the two sides still agree? | every zone the backend emits has an icon in the frontend — the gap that once shipped as an `emission`/`emissions` typo and survived review *and* the whole suite |

**Details, and how to run each one: [`docs/features/testing.md`](docs/features/testing.md).**

## Working with Claude Code (Skills & Commands)

This repo is built with the help of **Claude Code** (Anthropic's AI coding tool in
the terminal). A few conventions are automated as **skills** so the whole team gets
the same result. If you're new, read this before making changes.

**What a skill is.** A skill is a reusable, named instruction set that Claude runs
when you invoke it. You call one by typing a slash command, e.g. `/new-pr`. Think of
it as a saved "recipe" for a repeatable task, so nobody has to re-explain the steps
or the house style each time.

**Where skills live.**
- **Project skills** — `.claude/skills/<name>/SKILL.md`, committed to this repo, so
  everyone who clones it shares them. (This is where `/new-pr` lives.)
- **Personal skills** — `~/.claude/skills/<name>/SKILL.md`, only on your machine.

**Skills in this repo:**

| Command | What it does |
|---|---|
| `/new-pr` | Turns the current branch into a pull request. Folds the *durable* high-level info + important commands into `README.md`, then opens the PR with `gh` — the file-by-file review guide (a **Key terms** glossary, a review-order table, a **Data flow** diagram) goes in the PR description, not a checked-in file. Reads the real branch diff so it never invents changes. (Replaces the retired per-PR `docs/prs/*.md` files.) |
| `/log-decisions` | End-of-day curation of the decision journal. Reads the local prompt cache (`.claude/decision-cache.jsonl`) plus the last 24h of git history, drafts the genuinely significant decisions into `DECISIONS.pending.md` for you to review, then rotates the cache. Drafts only — it never edits `DECISIONS.md` or commits. |

**Important commands to know:**

| Command | What it does |
|---|---|
| `/<skill-name>` | Runs a skill (e.g. `/new-pr`). Type `/` to see what's available. |
| `/help` | Lists the built-in commands and how to use them. |
| `/clear` | Wipes the current conversation context — start fresh without closing the app. |
| `/config` | Opens settings (model, theme, etc.). |
| `! <command>` | Runs a normal shell command *inside* the session, e.g. `! python3 backend-OBD-reader/tests/test_decoder.py`. The output goes straight into the chat. |

**Gotcha — skills load at startup.** After you **add or edit** a skill file, Claude
Code won't see the change until you **restart it** (or reload). If a new `/command`
doesn't appear, that's why.

**How to test a skill safely.** Run it on a branch and *review its output before
committing* — for a doc-generating skill like `/new-pr`, read the README changes and
the PR body it produced before you rely on them. Don't let a skill commit for you
unless you've checked what it produced.

---

---

## Roadmap

Phase 1 is committed; everything after it is directional. Each phase has **exit criteria** —
observable by someone who is not the author — rather than a feature checklist.

**[`backlog/`](backlog/)** · [Phase 1](backlog/phase-1.md) · [Phase 2](backlog/phase-2.md) · [Later](backlog/later.md)

Phase 2 exists because [Wekfest](docs/market/findings/2026-09-06-wekfest-chicago.md)
produced evidence for it. Ideas without evidence stay in `later.md` — enthusiasm is not
evidence, including our own.

## Guiding Principles

1. **Functioning simple website first** — resist agents/3D/mobile until the core streams data to a browser.
2. **Design the data model for multi-tenancy and roles now**, even if not built yet.
3. **Keep the Python simulator** — useful for testing even after the Go migration.
4. **One Postgres instance** where possible; add Qdrant/Mongo/Redis only when a feature needs them.
5. **Gherkin `.feature` files survive the language migration** — invest in them.
