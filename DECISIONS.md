# Decision Log

A running journal of design decisions — lightweight [ADRs](https://adr.github.io/)
(Architecture Decision Records). This project is built with AI assistance (Claude Code);
this log records where I **read the generated code, questioned it, and changed direction**,
so the reasoning behind the codebase is visible and reviewable — not just the final diff.

**Entry template**

```
## YYYY-MM-DD — <short title>

**Status:** done | deferred | planned

- **Question I raised —** …
- **Initially generated —** …
- **My concern —** …
- **Decision —** …
- **Files / follow-up —** …
```

---

## 2026-08-14 — Tests should be file-driven (golden-file), not hard-coded

**Status:** done

- **Question I raised —** Don't hard-code decode inputs in the test; read inputs from a file and diff the output against an expected file.
- **Initially generated —** A test with decode inputs and expected values written inline as assertions.
- **My concern —** Inline cases are hard to grow and can't be reused. I want to reuse the "raw capture → records" transformation to write Gherkin/BDD tests later.
- **Decision —** Adopt a golden-file test: read `sample_obd_raw_stream.txt`, produce output, diff against `sample_obd_output.json`.
- **Files / follow-up —** `backend-OBD-reader/tests/test_decoder.py`, `test_files/`.

---

## 2026-08-16 — The test must exercise the REAL code path, not a parallel copy

**Status:** done

- **Question I raised —** "stream.py is not the right way of testing since it's not using the functions the live path would use."
- **Initially generated —** The golden test decoded the capture through a separate `stream.py` module (`decode_stream`) — a second implementation of the parse/extract logic that only the test used. The code a real adapter drives was never exercised.
- **My concern —** A test that runs a parallel parser can pass while the real path is broken; the two silently drift. There were actually *three* copies of the decode logic.
- **Decision —** Inject a `FakeSerial` transport into the **real** `SerialReader` so the test drives the live path (framing → decode → `Reading`). Delete the duplicates (`stream.py`, `testing/test_record_parsing.py`, `obd-2-parsing.py`).
- **Files / follow-up —** `obd_reader/reader.py` (injectable `transport`), `tests/test_decoder.py`. The refactor also surfaced that `poll_once()` only read Mode 01 PIDs, so `decode_dtcs` had no live caller — added `poll_dtcs()` to fix that.

---

## 2026-08-16 — A `/new-pid` helper skill: deferred, with a correctness guardrail

**Status:** deferred

- **Question I raised —** Would a skill that adds a PID make the test suite more robust over time?
- **Initially generated —** A skill that scaffolds a new PID across the registry, fixture, and golden file, then runs the tests.
- **My concern —** It only helps if it doesn't cheat. If the skill fills the expected golden value by running the decoder, it enshrines a wrong formula as "golden" (bigger coverage, zero correctness).
- **Decision —** Not building it yet. When we do, the expected value must be supplied by me / the OBD-II spec and asserted against the decoder — never scraped from the decoder's own output.
- **Files / follow-up —** None yet (idea parked).

---

## 2026-08-16 — Domain modeling: Vehicle vs. Reading (is-a vs. has-a)

**Status:** planned

- **Question I raised —** Should there be a `Vehicle` superclass with `Sensor` and `ErrorRead` subclasses to keep things organized?
- **Initially generated —** (my proposal) inheritance — `Sensor` / `ErrorRead` extend `Vehicle`.
- **My concern —** A sensor reading is not a *kind of* vehicle, so inheritance is wrong here. A Vehicle **has** readings (composition). If anything subclasses, it's the readings themselves.
- **Decision —** `Vehicle` is a thin entity (identity + metadata) that *has* readings via a repository — not a fat aggregate holding every reading in memory. Split `Reading` into `SensorReading` / `FaultReading` (removes the `type ==` branching).
- **Files / follow-up —** Lands with persistence; the `Reading` split is the cheap first step.

---

## 2026-08-16 — `Problem` as a first-class derived entity (the marketplace's contract)

**Status:** planned

- **Question I raised —** I want a per-car list of *problems* that the marketplace reads to recommend parts + fixes, derived from a summary of all the readings.
- **Initially generated —** Readings (and fault codes) stored in a DB; consumers query them directly.
- **My concern —** A raw fault-code list isn't what the marketplace needs, and it shouldn't understand PIDs/hex. Problems are derived, deduplicated, and stateful (open → fixed), and can come from sensor trends with no DTC at all.
- **Decision —** Introduce `Problem` — distinct from `FaultReading` — as the derived, stateful entity the marketplace/agent/resale report consume. It's the decoupling boundary between the telemetry and commerce sides.
- **Files / follow-up —** Spine for the DIAG / MKT / AGENT / PRED / MAINT epics.

---

## 2026-08-24 — DTC catalog: data file now, DB only for the tier that actually grows

**Status:** done (file split) / planned (DIAG-3 manufacturer tier)

- **Question I raised —** For PR 2, is it better to keep the fault codes in a separate constants file, or even a DB that grows as new codes are found for specific types of vehicles?
- **Initially generated —** PR 2 shipped the code meanings as dictionary literals inside `faults.py` — `DTC_DESCRIPTIONS` plus two hard-coded sets (`_CRITICAL_CODES`, `_WARNING_CODES`) — mixed in with the lookup logic.
- **My concern —** The list is going to grow, and some codes are specific to a make of car, so hard-coded dictionaries in a logic module won't hold up. If it grows continuously, a database may be the right home rather than a file.
- **Decision —** Split the catalog out of `faults.py` into `data/dtc_generic.json`, but do **not** introduce a DB yet. Reviewing the codes showed they are really two datasets with different change rates: **generic** codes (`P0xxx`, `P2xxx`, `C0`, `B0`, `U0`) are fixed by a published standard and identical on every car, while **manufacturer-specific** codes (`P1xxx`, `C1/C2`, `B1/B2`, `U1/U2`) differ per make and are the only tier that grows. Everything currently in the repo is the generic tier. A DB for it would buy nothing and cost something real: `describe()` is a pure function today, and putting the catalog behind Postgres would mean the decoder needs a running database to decode — breaking the "test suite runs with no hardware or services" property (OBD-4) and the hermetic golden-file test. Reference data also belongs in the repo where a wrong description surfaces as a reviewable diff rather than a silent row edit. JSON rather than a `constants.py` specifically so the planned Go port (GO-1) can read the same catalog, which a Python dict could not provide. The DB becomes correct at the manufacturer tier, which needs two things that don't exist yet: vehicle records (STORE-3) to know the make, and a genuine runtime write path (AGENT-2/4, EVAL-3).
- **Files / follow-up —** `backend-OBD-reader/obd_reader/data/dtc_generic.json` (new), `backend-OBD-reader/obd_reader/faults.py` (rules only; catalog now read through a single `_load_catalog()` so the source can change in one place), tests unchanged and passing (11/11). Manufacturer tier tracked as **DIAG-3** in BACKLOG.md, with the guardrail that community/scraped sources may supply `description` only — `severity` stays a human judgement.

---

## 2026-08-24 — P04xx is not all exhaust: split emissions from exhaust zones

**Status:** done

- **Question I raised —** (not mine) Raised during review of the fault-detection code, not by me.
- **Initially generated —** `zone_for()` mapped the whole `P04xx` family to the `exhaust` zone.
- **My concern —** Confirmed the problem once it was pointed out: `P04xx` is "auxiliary emission controls", which also covers EGR (`P040x`), secondary air (`P041x`) and EVAP (`P044x`/`P045x`). An EVAP fault — often just a loose fuel cap — was being reported as an exhaust problem.
- **Decision —** Split the range on its third digit and add an `emissions` zone; catalyst (`P042x`/`P043x`) and exhaust pressure (`P047x`) stay `exhaust`. This matters beyond a label because zone routes the parts catalog (MKT-1) and the 3D affected-area view, so a wrong zone recommends the wrong parts. Lookup uses a slice, not an index, so a truncated code like `"P04"` still resolves rather than raising.
- **Files / follow-up —** `obd_reader/faults.py`, `tests/test_faults.py`, README zone mapping. Shipped as PR #6, stacked on PR #2 because `faults.py` does not exist on `main`.

---

## 2026-08-24 — Per-make control is capability data + release gates, not per-make toggles

**Status:** planned

- **Question I raised —** When onboarding each make, should there be toggles so we control which features are available and contain bugs that disrupt certain features?
- **Initially generated —** (my proposal) a per-make toggle per feature, one file per make.
- **My concern —** A bug affecting one make shouldn't disrupt the whole app, and new makes shouldn't silently enable half-working features.
- **Decision —** Separate the two things the proposal conflated. **Capability** ("what can this car do?") is permanent per-vehicle data, discovered from the ECU itself via the supported-PID bitmasks (`0100`/`0120`/`0140`) and stored on the vehicle record — not a hand-maintained per-make table, which would be wrong for trims and model years anyway. **Release gating** ("do we trust this yet?") is a real feature flag, but keyed feature-major with make as an *optional* narrowing, since most features fail make-independently; per-make-per-feature flags would be an N×M matrix that cannot be tested. Catalog trust becomes a `status: experimental | verified` field reusing the PRED-6 "general guidance — not yet personalized" hedge, rather than a separate mechanism.
- **Files / follow-up —** Not built. `features.yaml` schema + env-override precedence + a flag-expiry test to be storied in BACKLOG.md.

---

## 2026-08-24 — Rejected a graph/GraphQL context layer for token optimization

**Status:** deferred

- **Question I raised —** Should I implement a graph-based context layer (seen described as "GraphQL Claude context for less token usage") as a skill that runs at all times?
- **Initially generated —** Two conflated ideas: GraphQL as an MCP tool interface, and knowledge-graph memory servers.
- **My concern —** Token burn across long sessions.
- **Decision —** Don't build it. A skill that "runs at all times" is self-defeating — skills load on demand, so an always-on one *adds* tokens every turn. Claude Code already ships Tool Search, which defers tool definitions natively. And the repo already has the useful 80%: stable story IDs, terse index docs pointing at detail, load-on-demand. Automated traversal is the expensive, low-payoff remainder. Revisit if `DECISIONS.md` reaches ~50 entries and needs semantic retrieval; until then, build retrieval where it's the actual product feature (AGENT-1/2, Qdrant).
- **Files / follow-up —** None. Measure with `/context` before optimizing anything here.

---

## 2026-08-24 — Decision curator: two triggers, and the PR becomes the ratify step

**Status:** done (scripts) / planned (wiring)

- **Question I raised —** The curator should run on whichever comes first — 00:30 CT or the conversation closing (`/clear` or terminal exit) — and should open a PR for review, not a numbered roadmap PR.
- **Initially generated —** `/log-decisions` as originally written: drafts to `DECISIONS.pending.md`, and **never** commits, pushes, or writes `DECISIONS.md`.
- **My concern —** The draft file relies on me noticing it. Investigation confirmed the risk was real: the prompt cache sat empty from 2026-08-16 to 2026-08-24 and the skill had never once run, because project hooks only load when Claude Code is launched from the repo directory.
- **Decision —** Amend the skill's contract: the curator writes entries to `DECISIONS.md` on a throwaway branch and opens a PR, and **the PR review is the ratification step**. This keeps the "human ratifies" principle — arguably strengthens it, since a PR is versioned and can't be silently forgotten — while removing the reliance on spotting a local file. Supporting choices: the shell does all git/PR mechanics and the model runs with no tools and returns only text, so an unattended run can't touch the repo unreviewed; work happens in a detached git worktree so a background run never disturbs an in-progress branch; entries are dated by *session* date, not run date, because the 00:30 run is already the next calendar day; a hard gate on conversation evidence means commits alone never produce a PR; and one PR per day, appended to, so unreviewed decision PRs can't pile into a queue.
- **Files / follow-up —** `.claude/hooks/run-curator.sh`, `curator-trigger.sh`, `.claude/hooks/README.md`. Still to wire: `SessionEnd` in `settings.json`, the `SKILL.md` rewrite, the cron entry. The GitHub API calls were deliberately removed and left as TODOs to implement by hand.

---

## 2026-08-24 — Guardrails: branch protection and a written policy, not hard blocks

**Status:** done (protection deleted for a learning exercise — reapply)

- **Question I raised —** Should there be hard guardrails preventing conversations or edits while a decision PR is unmerged, and requiring the decision PR to merge before any other PR is touched — breakable only for emergencies?
- **Initially generated —** (my proposal) enforce both as hard blocks.
- **My concern —** The decision log rots if nothing forces it to be kept current.
- **Decision —** Don't hard-block. Review surfaced three problems: no hook can distinguish a bug fix from a feature, so the emergency exception collapses to self-declaration and trains me to bypass it; as a solo dev I am both author and approver, so a gate I can always open is a ritual; and it inverts the dependency, gating work on the documentation of that work. Landed instead on **GitHub branch protection** on `main` (PR required, 0 approvals — GitHub forbids self-approval, so requiring 1 would be a permanent lockout) with `enforce_admins: false` as an *auditable* emergency override, plus a **written working agreement in `CLAUDE.md`** that Claude honours and I can waive by saying so. Also noted: the log's decay traced to the hooks never firing, not to a lack of discipline — a plumbing bug, not a process one.
- **Files / follow-up —** `CLAUDE.md`. Protection was applied, then deliberately deleted so I can reapply it myself as a GitHub API exercise; `CLAUDE.md` currently claims `main` is protected and will be accurate again once I do.

---

## 2026-08-24 — Defer the DTC catalog to first use instead of import

**Status:** planned

- **Question I raised —** Isn't it bad to keep reloading all the codes? Shouldn't it only load info for codes that match what's being read?
- **Initially generated —** `_CATALOG = _load_catalog()` at module level, so the file is read as a side effect of importing `faults`.
- **My concern —** Loading the whole catalog when only a few codes are ever read looks wasteful.
- **Decision —** Keep loading the whole catalog; don't go per-code. It already loads once (module-level, and Python caches modules), and per-code loading would put disk I/O on a hot path called per fault — ~900KB for the full generic set is negligible against a ~50–80MB server baseline. The real defect is different: reading a file as an *import side effect* makes the module untestable, since the first import pins the real catalog for the whole run. Fix is `@cache` on the loader — same single read, but deferred to first use and resettable via `cache_clear()`. Only the loader gets cached, never `describe()`, which returns a mutable dict that callers could corrupt for everyone. The one regression — a broken catalog would surface at first lookup instead of at startup — is cancelled by calling the loader once explicitly in the server's `lifespan`, which is better than the current implicit behaviour. Per-make catalogs (DIAG-3) *do* load on demand, keyed by make.
- **Files / follow-up —** Deferred as a follow-up after PR #2 merges — `obd_reader/faults.py` (2 call sites), plus a warmup line in `server.py`. Add a BACKLOG story on `feat/fault-detection` after merge, not now, since BACKLOG.md differs across branches.

---

## 2026-08-29 — Android Auto ships as its own repo, but it is a client, not a microservice

**Status:** planned

- **Question I raised —** Android Auto should be a separate repo so the project ends up as a microservices setup; adding it to the backend would complicate the code too much.
- **Initially generated —** Nothing built; it sits under Future Concepts.
- **My concern —** Bolting a Kotlin surface onto the Python backend would tangle two ecosystems in one codebase.
- **Decision —** Separate repo, yes — but the reasoning is ecosystem, not architecture. An Android Auto app runs *on the phone* ("render 3D on the phone, push a flat image to the head unit"); it consumes the API like the React dashboard does and serves nothing. Calling it a microservice would invite service infrastructure it has no use for. The real reason to split is different language, toolchain and release cadence (Kotlin/Gradle/Play Store vs Python/uv). What actually makes a later split cheap is the **API contract**, not the repo boundary — and that pressure is live now, since `/ws` already has to serve the web dashboard and eventually React Native. If a genuine microservice is wanted, the agent layer is the better candidate: its heavy deps are already isolated behind a `pyproject` extra. Not creating the repo yet — nothing to put in it, and an empty repo is a second thing to keep in sync.
- **Files / follow-up —** None. Revisit when Phase 1 is done.

---

## 2026-08-30 — Golden fault cases: selective assertions, hand-written, never generated

**Status:** done

- **Question I raised —** Why not use the golden-file test method again for fault detection?
- **Initially generated —** Seven inline assertions spread across two test functions in `test_faults.py`.
- **My concern —** The decoder's golden-file approach worked well and should be reused where it fits.
- **Decision —** Adopt it, but **only for the derived fields** (`zone`, `severity`, `deferrable`). `description` and `severity` are read verbatim from the catalog, so restating them would copy `dtc_generic.json` into a second file and mean editing two files per code. Unlike the decoder's full-replica comparison, each case asserts **only the fields it names** — so a case stays about one claim. Structured as **one file per scenario** (my call; better than a single table because the story lives next to the codes that prove it, and adding a case is a new file rather than a merge-conflict-prone table edit). The non-negotiable rule: cases are **hand-written from the OBD-II ranges and never generated by running `describe()`** — generated before the P04xx fix, a file would have contained `P0442 → exhaust`, freezing the EVAP-as-exhaust bug as "expected" and making the correct fix look like a regression. Same guardrail as the deferred `/new-pid` skill.
- **Files / follow-up —** `tests/faults/test_golden.py`, `tests/faults/cases/` (PR #9, #15). `test_case_files_are_well_formed` is load-bearing, not boilerplate: it catches an entry that names no expected fields, which the golden test would otherwise pass green.

---

## 2026-08-30 — Tests split by what a failure tells you, and grouped per feature

**Status:** done

- **Question I raised —** Should `test_faults.py` be separate from `test_faults_golden.py`? And should there be a folder per feature holding a golden test, an assertion test, and that feature's JSON?
- **Initially generated —** Flat `tests/` directory, fixtures three levels away under `test_files/`, and the same mappings asserted in two places with partial overlap — nine codes in both files, four only inline.
- **My concern —** Neither file was authoritative, so adding a case meant guessing where it belonged.
- **Decision —** One folder per feature, cases co-located, and the two test kinds split by **what a red run tells you**: `test_golden.py` means "a mapping is wrong", `test_contract.py` means "a guarantee broke". Not everything becomes golden — a guarantee like "must not raise" cannot be expressed as a value comparison, and written as a case it would silently pass the moment the function returned a constant. One carve-out: `test_files/sample_obd_output.json` **cannot move**, because `reader.py`'s `FixtureReader` loads it at runtime, making it production input as well as test data.
- **Files / follow-up —** PR #15. Coverage rose despite the test count falling 15 → 13: 20 codes and 36 assertions, up from 23. Added two guarantees no golden case could catch — that `describe()` returns all five keys, and that the catalog is actually being read at all.

---

## 2026-08-30 — Zone mappings become data; both catalogs load lazily

**Status:** done

- **Question I raised —** We agreed not to keep JSON data inside `faults.py` but to load it in — the zone tables should be a bank somewhere reasonable too.
- **Initially generated —** The catalog was extracted in PR #2, but `_LETTER_ZONE` and `_P04_SUBZONE` stayed as dict literals and the family mapping stayed an if-chain.
- **My concern —** Same argument as the catalog: these are data sitting inside a logic module.
- **Decision —** Move them to `data/dtc_zones.json` — not `pids.py`, which is the Mode 01 *sensor* registry and a different domain. **Mappings become data, rules stay code**: `zone_for()` keeps the lookup order, the `code[3:4]` slice that survives a truncated code, and the fallbacks. The deciding argument was that I am about to research these against the OBD-II ranges, and as data a revision is a reviewable diff against a source. Took the deferred `@cache` change at the same time, so importing `faults` no longer touches the filesystem — verified as 0 cache misses at import and 1 across 51 lookups. Only the loaders are cached, never `describe()`, which returns a mutable dict that shared callers could corrupt.
- **Files / follow-up —** PR #14. Trade-off recorded in the docstring: a broken catalog now fails at first lookup rather than at import, so whatever starts the reader should call it once at startup. Nothing does yet.

---

## 2026-08-30 — Two tracking surfaces, and what an issue is actually for

**Status:** done

- **Question I raised —** I want active layering of priority segmented chronologically, and the skill should understand the problem, check what already exists on GitHub, and file a story or comment saying what the issue fixes and how.
- **Initially generated —** `BACKLOG.md` as a flat file of 52 stories with no notion of what is next, and nothing linking a PR to the work it does.
- **My concern —** I proposed container issues per feature, then noticed the flaw myself — such an issue never closes.
- **Decision —** Two surfaces, deliberately not mirrored: `BACKLOG.md` is the **roadmap** (everything, with rationale), GitHub Issues are **only what is queued now**, joined by story ID. The 52 stories are explicitly **not** 52 issues — most are later-phase and would bury the few that matter. No container issues: the epic already exists as a `BACKLOG.md` heading and the story-ID prefix already carries attribution, so a container would restate it and then drift. Chronological layering is the milestone; urgency is a `p0/p1/p2` label. Routing for work with no story: **fixing it now → just the PR** (an issue created and closed within the hour is ceremony); **noting it for later → an issue**, because otherwise there is nowhere for it to live.
- **Files / follow-up —** `/track-issue` skill (PR #10). First use surfaced a gap in my own routing table — it had no branch for bugs and chores, which is what issue #13 turned out to be.

---

## 2026-08-30 — Correcting a claim means grepping for it everywhere

**Status:** done

- **Question I raised —** Is this change consistent with the other changes in main and the different PRs?
- **Initially generated —** A docstring and a README that said the opposite of each other about what `test_case_files_are_well_formed` protects against.
- **My concern —** A correction had been applied in one place only, so the code and the docs disagreed.
- **Decision —** Adopt it as a repo convention: when correcting a claim about behaviour, **verify it by running it**, then `git grep` the phrase before pushing — a claim worth writing is usually written in two or three places. Verification leads because both wrong claims came from reasoning about the code instead of executing it. Placed in `CLAUDE.md` under Docs & code style, with comment-the-why and junior-readable, since all three are about keeping documentation honest. Note this is *not* covered by `/new-pr`'s "alter in place, don't duplicate", which is about avoiding a second copy while writing — the opposite failure.
- **Files / follow-up —** `CLAUDE.md` (PR #12, merged). It caught its first real case immediately: a docstring in PR #14 referencing a `server.py` warm-up that does not exist on `main`.

---

## 2026-08-30 — Calendar integrates for deadlines, not for merge events

**Status:** planned

- **Question I raised —** Connect a calendar that updates when a PR is merged — then, on reflection, build it for accurate deadlines instead.
- **Initially generated —** (my first framing) one calendar event per merged PR.
- **My concern —** Reframed it myself: a merged PR is a past event and a calendar is for scheduling future time, so the merge-event version fights the tool. GitHub's own history already records what shipped when.
- **Decision —** Build it for **deadlines**, which are genuine future commitments. GitHub milestones own the due date; the calendar is read for *capacity context* before a date is picked, then written one-way. That is not two-way sync — nothing contests ownership of the date. A new conflicting event prompts a conversation rather than silently moving the deadline, sized by **new commitment ÷ remaining unallocated time before the deadline**, because a one-hour meeting three weeks out and two interview days before a Friday deadline are the same hours and completely different facts. Learning time is scheduled the same way and comes out of the same budget — tied to queued stories (GO-1, DASH-1) rather than abstract skills, so it has a completion criterion and cannot rot.
- **Files / follow-up —** Not built. Calendar connection verified (`p.vishveshkumar@gmail.com`, America/Chicago). Needs: due dates on the milestones, and my real weekly hours plus the shipping/learning split. Note the throughput data cannot distinguish a queue stall from a deliberate pause — PR #2's 13.7 days was interview prep — which is itself an argument for the calendar supplying that context.

---

## 2026-09-01 — Transport is a per-hop question: WebSocket now, SSE would fit better, MQTT later

**Status:** done (WebSocket stays) / planned (revisit on deploy)

- **Question I raised —** Why WebSocket and not MQTT, since this is an IoT project? And separately: there is not much interaction after the codes are read once, so could the frontend just take a server-sent payload initially?
- **Initially generated —** A WebSocket at `/ws`, chosen without the alternatives being written down anywhere — it was an undocumented default rather than a decision.
- **My concern —** Two: that an IoT project should be using an IoT protocol, and that full-duplex is more than a one-way dashboard needs.
- **Decision —** Treat transport as a **per-hop** choice rather than one answer for the system.
  **Car → reader** is not a choice at all: OBD-II is request/response, so `poll_once()` *manufactures* the stream by polling. Nothing is pushed, which also means the sampling rate is a design decision we own (STORE-4).
  **Backend → browser:** WebSocket stays for now, but SSE is the better fit and I was right about that — `ws_endpoint`'s own docstring says the receive loop "exists solely to detect disconnects", so we pay for full-duplex and use half. SSE is plain HTTP with a streaming body, `EventSource` reconnects natively instead of us hand-writing it, and it traverses proxies and load balancers that fight WebSockets — which matters because deploying is the next step. Not switching yet: #3 works and rewriting it now is churn for no user-visible change. **Revisit if the deploy platform fights WebSocket, or the moment the browser needs to send something** (clear codes, change poll rate) — at which point full-duplex stops being unused and WebSocket is retroactively right.
  **Device → backend:** does not exist yet, because the "device" is a serial dongle on the same machine. **MQTT becomes correct if HW-1 happens** — a networked ESP32 is a constrained device on a flaky network, and MQTT's tiny header, QoS, persistent sessions and pub/sub fan-in are built for exactly that. Browsers cannot speak raw MQTT, so it would never replace the browser hop; the end state is both, MQTT for ingress and WebSocket/SSE for egress. That is the standard IoT topology, not a contradiction.
- **Files / follow-up —** `obd_reader/server.py` (PR #3/#4) unchanged. Note that transport is not processing — MQTT moves bytes; what happens after is STORE-1/STORE-4, and at one car at 2 Hz that is Postgres and a background job, not a stream processor.

---

## 2026-09-03 — The BLE adapter is a transport problem, not a decoder problem

**Status:** planned (Web Bluetooth) / done (diagnosis, Veepeak shelved)

- **Question I raised —** Why won't the Veepeak OBDCheck connect to my Mac when it works fine through an app on my phone? Then: would a JS button that connects to BLE adapters solve this?
- **Initially generated —** Claude's first diagnosis was wrong: it read `Connected: VEEPEAK` with RSSI -57 in `system_profiler` and concluded the phone was holding the adapter's single client slot, recommending a power-cycle with the phone's Bluetooth off. It then recommended buying a USB adapter to protect the Wekfest demo.
- **My concern —** Two corrections, both mine. First, the demo was never the point — I wanted the adapter actually solved, not worked around. Second, I asked whether Claude had read the python-obd Connections docs before dismissing the library.
- **Decision —** The adapter is **BLE, and pyserial can never reach it**. The evidence is `Services: 0x802000 < Braille ACL >` — no Serial Port Profile. macOS pairs it anyway as `Minor Type: Headset` and creates `/dev/cu.VEEPEAK`, which opens without error and returns silence at every baud. A device node existing is not evidence that SPP exists behind it.
  Checking the docs settled the library question harder than the original reasoning did: **python-obd is `portstr`-based with no BLE support**, so it would hit the identical wall. Claude's first argument (keep our own decoder because it is the differentiator) was true but weaker than the real one — swapping libraries cannot fix a layer it does not operate at.
  That reframed the whole problem. BLE sits **below** the decoder:

      BLE / GATT                    <- the actual problem.  bleak, or Web Bluetooth
      ELM327 framing (write, read to '>')   <- reader.py _command()
      decode                        <- our decoder.py  ==  python-obd (peers, not layers)

  **Web Bluetooth for desktop and Android; native for iOS.** Web Bluetooth does not exist on any iOS browser (WebKit does not implement it, and Apple requires every iOS browser to use WebKit) — but that costs nothing, because `MOB-2` already specifies a React Native app talking to the adapter directly. The backlog had already split "browser UI" (`MOB-1`) from "native owns the adapter" (`MOB-2`) before this came up.
  **The seam stays at raw ELM327 string -> Python decoder.** Web Bluetooth (JS), React Native BLE, `bleak`, and `FakeSerial` are then all just transports feeding one decoder and one set of golden tests. The rule that keeps this honest: **no transport ever decodes.** JS frames to `>` and forwards the string; it must not reimplement the PID formulas, or two copies drift the way `emission`/`emissions` did in PR #28.
  Accepted cost: if the browser owns the car connection, there is no headless operation. Check that against `TRACK-1` (session capture) and the `PRED-*` logging stories before committing.
  **Veepeak shelved for now.** Nothing is blocked on it — #30, #27, #26, deploy and CI all run against the fixture. Buying a USB or Bluetooth-Classic adapter is still worth doing, not for a demo but as a **known-good reference device**: without one there is no way to separate "my BLE framing is wrong" from "this adapter is weird."
- **Files / follow-up —** Nothing changed in code. `reader.py:56-68` already has the injection point — a transport needs only `write(bytes)` and `read_until(b">")` (`reader.py:83-84`), which is why this is contained. Forget the Veepeak pairing in Bluetooth settings so the dead `/dev/cu.VEEPEAK` node stops looking like a working port; python-obd's auto-scan would find and hang on it. Buying heuristic worth keeping: **"works with iPhone" means BLE**, because iOS forbids Bluetooth Classic SPP — which is exactly why most adapters sold today cannot be reached by pyserial. Needs a BACKLOG story for the Web Bluetooth transport, and it is good LEARN material (frontend gap, fixed contract, clean oracle — the string JS sends should match what `_command()` returns from the fixture).

---

## 2026-09-04 — What a shop can see: codes by default, telemetry only in-shop with consent

**Status:** decided (not built)

- **Question I raised —** What should a mechanic actually be able to see? "Driver owns it, shop gets a revocable grant" is the right principle but says nothing about *what* is granted or *when*.
- **Initially generated —** `docs/market/go-to-market.md` (PR #22) stated the defensible position and stopped there, flagging only that it must be settled before pitching any shop. It named the collision — a shop reasoning "I gave you the dongle, so I see your car" — without resolving it.
- **My concern —** A grant with no scope is a blanket grant in practice. If the shop's expectation is set in the first sales conversation, "revocable" is weak protection once they have already seen everything. The principle needed a shape.
- **Decision —** Two tiers, with disclosure scoped to purpose rather than to relationship:

  **Default — the driver sends fault codes plus a written problem statement.** What they observed: when it happens, what it sounds like, what they were doing. That is what a mechanic needs to *start*, and the problem statement is genuinely valuable in its own right — "only when cold, above 3000rpm, in the rain" is information no telemetry captures and every mechanic asks for anyway. Worth being a first-class field, not a free-text afterthought.

  **On request — historical telemetry (speed, RPM, load, temps), only while the car is in the shop for a specific fix, and only with explicit consent at that moment.** The grant is per-visit and per-purpose, not per-relationship. That is what survives a customer switching shops, which is exactly the property `go-to-market.md` argues for.

  **Why the default is not just politeness:** speed history is a record of where and how fast someone drove. It is discoverable in a crash investigation or an insurance dispute in a way that a fault code is not. Handing it over by default creates a liability for the driver that the diagnosis does not require.

- **Open question — a middle tier (Claude's proposal, not ruled on).** Mode 02 **freeze frame** is a single ECU snapshot captured at the instant the fault set: RPM, load, coolant, speed at that moment. It is most of the diagnostic value of history in *one sample* rather than a trace, so it may belong in the default payload alongside the codes. `PRED-5` already plans to capture it. Decide whether the default is `codes + statement` or `codes + statement + freeze frame`.

- **Also unresolved —** does the grant expire when the job closes, or need explicit revocation? And can the driver see an access log of what a shop actually read? An audit trail is what makes "revocable" meaningful rather than nominal.

- **Files / follow-up —** `docs/market/go-to-market.md` (PR #22) — the open question there should be marked resolved. Shapes **ROLE-4** (sharing as a grant from the driver), **MKT-3** (the mechanic recommendation flow), and **PRED-5** (freeze-frame capture). Nothing built. Worth testing at Wekfest from the mechanic side: ask shops what they would actually want to see, and whether codes plus a description is enough to quote a job.

---

## 2026-09-05 — The VIN: read from the car, cached to the connection, stored only on permission

**Status:** decided (not built)

- **Question I raised —** For PR #21's VIN-derived make, are we using a public API? And if the marketplace needs more than make, who does the lookup — us or the customer?
- **Initially generated —** #21 says the make comes from the VIN's first three characters (the World Manufacturer Identifier) and flags the VIN as identifying data to keep out of URLs and logs. It never says whether the decode is local or remote, which is exactly the ambiguity that prompted the question. Claude's first answer framed it as a two-way choice, local decode vs the NHTSA vPIC API, and proposed a consent prompt.
- **My concern —** Three corrections, all mine. The consent prompt was in the wrong place; the manual alternative is not "type it from memory"; and the VIN should be visible to the user regardless.
- **Decision —**

  **Where it comes from.** Mode 09 PID 02 (`0902`) — the car reports its own VIN, so nobody reads a door jamb. **Not implemented, and it does not fit the current reader:** the VIN spans multiple frames, and `reader.py:88` returns only the first line of a response and discards the rest. Every response handled today is single-line, so this is the first thing that breaks that assumption. Needs a multi-line read path before any of this works.

  **Lifetime, not storage.** The VIN is a constant for a vehicle, read from whichever car is physically plugged in. So it is **cached for as long as the adapter is connected, and dropped on disconnect.** That boundary needs no auth, cannot outlive the thing it describes, and handles the case where a different car is plugged into the same laptop — which a process-lifetime cache would get silently wrong.

  Note "cached for the session" was the original phrasing and there is no session in this codebase: no auth, no users, just a set of sockets and a poll loop. A module-level variable would be indefinite retention wearing a session's clothes. The adapter connection is the real boundary available today.

  **Storage requires permission** — but that prompt cannot be asked yet, because there is nowhere to store it to until ROLE-1 (identity) and STORE-3 (vehicle records) exist. Ship the cache; add the prompt when persistence is real.

  **Displayed, always.** The UI shows the VIN so the user can copy it. Note this means it transits the WebSocket and lands in browser memory and the devtools network log — unavoidable if it is on screen, but "not stored" should be read as *not persisted, not logged, not retained past disconnect*, not as *nowhere*.

  **Make is derived in memory and the VIN discarded.** Characters 1-3 give the manufacturer against a table we ship. Store the *make*, drop the VIN. That satisfies DIAG-3 with **zero VIN retention** — the make is not identifying data, the VIN is. Keep the useful half, drop the risky half.

  **For fitment (MKT-5), two paths, user's choice:**
  - *App does the lookup* — NHTSA vPIC returns make, model, year, engine. Accurate, one step. Costs sending the VIN to a third party in a URL path, which is precisely what #21 warns against.
  - *User does the lookup* — we display the VIN and point them at NHTSA's own vPIC decoder; they read back the details and enter them. **The VIN never reaches our servers or theirs on our behalf.** Not the same as typing from memory: they are reading from an authoritative source, so the accuracy gap mostly closes.

  Point at the government decoder specifically. A commercial site drags in a partner dependency and affiliate questions we do not need.

  **Record the provenance.** Both paths produce the same fields; they do not carry the same confidence. The vehicle record should mark `vpic-verified` vs `user-entered`, and **fitment confidence keys off it** — a part recommendation built on hand-copied fields should be stated softly and confirmed before an expensive purchase. Same pattern as the DIAG-3 guardrail: the fields may come from outside, the confidence is ours to assign.

- **Why the consent prompt is not at setup —** Local WMI decode transmits nothing, so there is nothing to consent to. Asking permission for a purely local operation trains people to click through prompts that carry no meaning. The question is "may we look this up online", it only arises when more than make is needed, and it belongs at that moment. Same reasoning as the 2026-09-04 entry on mechanic access: consent scoped to a purpose, asked at the point of need, never as a blanket grant at the start of a relationship.

- **Open —** does the user-mediated path have enough uptake to be worth building, or does everyone just accept the API? Worth asking at Wekfest: *"would you rather the app read your VIN, or look it up yourself and type in the details?"*

- **Files / follow-up —** Nothing built. `BACKLOG.md` DIAG-3 (via PR #21) should state the decode is local. Needs a story for `0902` multi-frame VIN read — it is a prerequisite for all of this and it changes `reader.py:_command`. Feeds MKT-5 (fitment), ROLE-1/STORE-3 (where storage would live).
