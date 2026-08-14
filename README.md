# Car OBD-II Marketplace

Read OBD-2 fault data from a vehicle, diagnose issues with an AI agent (backed by owner's-manual + community knowledge), and connect car owners with parts/mechanics through a marketplace.

**Wedge customer:** the budget-conscious driver enthusiast — *"the least I need to spend to track my car safely."* The B2C enthusiast product leads; the mechanic/marketplace B2B side is a second segment.

> **Build order:** get a simple functioning full-stack website working first, then layer everything else on top. See [Roadmap](#roadmap) and [Future Concepts](#future-concepts).

---

## Repository Structure

```
carOBD-II-Marketplace/
├── backend-OBD-reader/
│   └── obd-2-parsing.py       # python-obd: auto-connect + query PIDs
├── frontend-web/              # React dashboard (to build)
├── testing/
│   ├── sample_obd_output.json # example reader output (raw hex + decoded transactions)
│   └── test_record_parsing.py # pytest: raw ELM327 → transaction-record parsing
├── DEVELOPMENT_PLAN.md        # full living plan
└── README.md
```

---

## Quick Start — Record Parsing

The adapter sends raw ASCII hex (e.g. `41 0C 1A F8`); the reader decodes it into JSON transaction records. `testing/sample_obd_output.json` shows both sides (the `raw` hex and the decoded `value`), and `testing/test_record_parsing.py` verifies the decode step.

```bash
# Run the parser against the sample fixture (no pytest needed)
python3 testing/test_record_parsing.py

# Or with pytest for the full test matrix
pytest testing/test_record_parsing.py -q
```

---

## Hardware & Protocol

- **Adapter:** Bluetooth ELM327 (serial-over-Bluetooth / RFCOMM SPP)
- **Baud:** 9600–38400
- **Init sequence:** `ATZ` → `ATE0` → `ATL0` → `ATSP0`
- **Read a PID:** e.g. `010C` (RPM) → response `41 0C 1A F8`
- Responses terminate with the `>` prompt, not a newline

**Common PIDs:**

| PID | Name | Formula |
|---|---|---|
| `010C` | Engine RPM | `(A*256+B)/4` |
| `010D` | Vehicle speed | `A` km/h |
| `0105` | Coolant temp | `A-40` °C |
| `0111` | Throttle position | `A*100/255` % |
| `012F` | Fuel level | `A*100/255` % |
| `0104` | Engine load | `A*100/255` % |
| `0110` | MAF air flow | `(A*256+B)/100` g/s |
| `0114` | O2 sensor voltage | `A/200` V |
| `0142` | Battery/module voltage | `(A*256+B)/1000` V |
| `010F` | Intake air temp | `A-40` °C |

---

## Tech Stack

**Backend:** Python now (`python-obd`, WebSocket server) → Go later (`go.bug.st/serial`, goroutines, `gorilla/websocket`). Migration is gradual — Go tests against the Python simulator's TCP server; replicate each PID decoder and verify parity before cutover.

**Frontend:** React now (website) → React Native later (shares components; connects to Bluetooth OBD directly from phone). Use React from day one so mobile can reuse components.

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
- **JS/TypeScript** — React web, React Native mobile, Three.js 3D

---

## Testing

- **Unit:** `pytest` (Python) → `go test` (Go)
- **Microservice contract / BDD:** `pytest-bdd` + Gherkin `.feature` files → `godog` (Go)
- Gherkin `.feature` files are language-agnostic — reusable across the Python→Go migration; only step definitions get rewritten.

```
testing/
├── sample_obd_output.json     # example reader output (fixture)
├── test_record_parsing.py     # pytest — raw hex → transaction record (DONE)
└── integration/
    ├── features/              # one .feature per microservice
    └── steps/
```

---

## Working with Claude Code (Skills & Commands)

This repo is built with the help of **Claude Code** (Anthropic's AI coding tool in
the terminal). A few conventions are automated as **skills** so the whole team gets
the same result. If you're new, read this before making changes.

**What a skill is.** A skill is a reusable, named instruction set that Claude runs
when you invoke it. You call one by typing a slash command, e.g. `/pr-doc`. Think of
it as a saved "recipe" for a repeatable task, so nobody has to re-explain the steps
or the house style each time.

**Where skills live.**
- **Project skills** — `.claude/skills/<name>/SKILL.md`, committed to this repo, so
  everyone who clones it shares them. (This is where `/pr-doc` lives.)
- **Personal skills** — `~/.claude/skills/<name>/SKILL.md`, only on your machine.

**Skills in this repo:**

| Command | What it does |
|---|---|
| `/pr-doc` | Generates or updates the PR documentation file (`docs/prs/PRn.md`) for the current branch, in our house style — a plain-language **Key terms** glossary, a review-order table of the changed files, and a **Data flow** diagram. Reads the real branch diff so it never invents changes. Use it instead of hand-writing PR docs. |

**Important commands to know:**

| Command | What it does |
|---|---|
| `/<skill-name>` | Runs a skill (e.g. `/pr-doc`). Type `/` to see what's available. |
| `/help` | Lists the built-in commands and how to use them. |
| `/clear` | Wipes the current conversation context — start fresh without closing the app. |
| `/config` | Opens settings (model, theme, etc.). |
| `! <command>` | Runs a normal shell command *inside* the session, e.g. `! python3 backend-OBD-reader/tests/test_decoder.py`. The output goes straight into the chat. |

**Gotcha — skills load at startup.** After you **add or edit** a skill file, Claude
Code won't see the change until you **restart it** (or reload). If a new `/command`
doesn't appear, that's why.

**How to test a skill safely.** Run it on a branch and *review its output before
committing* — for a doc-generating skill like `/pr-doc`, generate the file, read the
diff, and only then commit. Don't let a skill commit for you unless you've checked
what it produced.

---

## Agentic Diagnosis

Multi-agent system triggered when a DTC arrives.

- **Agent 1 — Diagnostic RAG:** searches owner's-manual + Reddit embeddings (Qdrant). Returns a diagnosis if confident; escalates if not.
- **Agent 2 — Social Posting:** called as a tool by Agent 1 (`escalate_to_reddit`). Posts to Reddit; tracks the post so replies feed back into the knowledge base.

**Escalation & fallback:**

```
Agent can't answer
   → Post to Reddit (PRAW), MongoDB status: pending_reddit
   → Background job polls replies every 6 hours
       ├── Reply → embed into Qdrant → answer customer → resolved_reddit
       └── No reply after 72h → post to app blog → notify mechanics
                → mechanic answers → embed into Qdrant → resolved_blog
```

The personal-blog fallback owns the knowledge (feeds Qdrant), avoids Reddit API cost/limits, uses verified mechanics, and doubles as a mechanic-acquisition channel. The reply-ingestion loop makes the knowledge base self-improving.

**Libraries:** `PRAW`, `pypdf`, `sentence-transformers`, `qdrant-client`, `anthropic`, `redis-py`, `pymongo`, `Celery` + Redis.
**Target subreddits:** `r/MechanicAdvice`, `r/AskAMechanic`.

---

## Marketplace

- Region-aware catalog: the fault's body zone (from the DTC) routes the user to the relevant parts/services.
- Parts sourced via API calls / scraping from reputable third-party vendors.
- **First integrations:** **SubiMods** and **JDM Muscle** (start by scraping / calling these), expanding to more vendors over time.
- Ties into the CRM/mechanic side: shops list services, owners get directed from a diagnosis straight to the parts or service they need.

---

## Roadmap

```
Phase 1: Simple full-stack website  ← BUILD FIRST
  - Backend streams OBD-2 readings (Python)
  - WebSocket push to browser
  - React dashboard of live readings
  - DTC detection + basic diagnosis
  - Test infrastructure

Then:
  → PWA (installable, offline-capable)
    → Mobile app (React Native, Bluetooth OBD direct)
      → CRM (shop/mechanic management, service history)
        → B2B marketplace (owners ↔ mechanics ↔ parts vendors)
```

**Recommendation flow:** fault → agent diagnoses + generates recommendation → mechanic reviews (approve/modify/override — quality gate for liability) → customer accepts → books service / orders part. A `source` field (`agent` | `mechanic`) on each recommendation later reveals which performs better.

**Role-differentiated UI:** customers see their car + plain-language diagnoses; mechanics see a fleet of customer vehicles + raw DTCs + full agent reasoning. Plan multi-tenancy into auth from day one — a shop owns many customer vehicles; retrofitting this is painful.

**In-car (future):** Android Auto (CarPlay blocks diagnostic apps). Show a 3D car model with the problem area highlighted, mapped from DTC prefix (`P01/P02`→engine, `P03`→ignition, `P04`→exhaust, `P07/P08`→transmission, `C0`→chassis, `B0`→body, `U0`→network). Render 3D on the phone, push a flat image to the head unit. Recurring same-zone faults over time → a fault heat map on the car body.

---

## Future Concepts

Recorded, not Phase 1. Each depends on earlier phases (website → fleet data → mobile app) existing first.

### Budget-conscious enthusiast positioning
Two fused value props: **minimum hardware spend** (~$10 ELM327 + app, not a $500 scan tool) and **minimum repair spend** (honest triage — what matters, what can wait, real cost). The agent should be a "don't get ripped off" engine: its output must include **cost estimates + urgency**, not just a diagnosis. Recommendations lead from the app (this crowd distrusts shop upsells). B2C enthusiast wedge first builds trust + a data moat, then opens the B2B marketplace.

### Predictive maintenance / Remaining Useful Life (RUL)
Estimate part life for predictive measures. **This is a data problem, not a simulation problem** — learn degradation from fleet telemetry. Gazebo (robot dynamics, not fatigue) and FEA (needs per-vehicle CAD + material specs) are the wrong tools. TimescaleDB fault history is the training data. Progression: (1) accumulate history, (2) simple threshold/trend rules with zero ML, (3) RUL models (survival analysis / gradient-boosted) once failure data exists. Later: physics-informed ML to need less data. **Do now:** ensure the schema captures timestamped per-PID, per-vehicle granularity.

### Handling-visualization gimmick
Predicted part health → degraded physics parameters → dynamics sim → "how your car handles now vs. healthy." Plays to a simulator's real strength (dynamics). **The reusable asset is the mapping layer** (part health → physics params), which is simulator-agnostic. Don't default to Gazebo for a web gimmick; prefer CARLA (accuracy + looks) or a game-engine / Three.js browser physics model (lightweight, stays in-stack). Sequenced after predictive maintenance.

### Track Mode — "chances of doing another lap safely"
Signature enthusiast feature. Monitor **changes in dynamics** during a track session and advise whether another lap is safe.
- **Within-session degradation** (rate of change within minutes), not long-term RUL.
- **Sensor fusion, phone is the star:** handling/dynamics (G-forces, cornering, braking profiles, lap times) come from the **phone IMU + GPS**, NOT OBD-2 — OBD-2 measures none of those. OBD-2 contributes engine thermal (coolant `0105`, oil `015C` if supported, intake).
- **Sample-rate reality:** cheap Bluetooth ELM327 polls slowly vs. 50–1000 Hz pro loggers; fine because temps change slowly and the IMU samples fast + free. Disclose it won't match a dedicated logger.
- **Output = limiting factor + time-to-limit, not a naked percentage** (false precision + liability). E.g. "Oil temp trending to critical in ~2 laps — cool-down lap recommended."
- **Liability framing (bake in):** advisory trend info, not a safety guarantee. Observational language, never "safe to continue." The driver decides.
- **Schema note:** anticipate a session-scoped, high-frequency "track session" capture mode, distinct from slow ambient polling. Reuses the handling-sim data and the predictive-maintenance time-series.

---

## Guiding Principles

1. **Functioning simple website first** — resist agents/3D/mobile until the core streams data to a browser.
2. **Design the data model for multi-tenancy and roles now**, even if not built yet.
3. **Keep the Python simulator** — useful for testing even after the Go migration.
4. **One Postgres instance** where possible; add Qdrant/Mongo/Redis only when a feature needs them.
5. **Gherkin `.feature` files survive the language migration** — invest in them.
