# Phase 1 — a working diagnostic tool

**Status: committed.** These stories are specified because they are next. Everything in
[`later.md`](later.md) is deliberately lighter — over-specifying work you have not started
is how a roadmap rots.

---

## Exit criteria — what "done" means

Phase 1 is finished when **all** of these are true. Not a feature checklist; the point is
that each one is observable by someone who is not you.

| # | Criterion | How you know | Status |
|---|---|---|---|
| 1 | A stranger can use it without you present | a URL they can open | ❌ not deployed |
| 2 | It reads a **real car**, not a recording | live PIDs from an adapter on a vehicle | ❌ no working adapter yet |
| 3 | Faults reach the browser on the live path | a real DTC rendered, not a fixture one | ❌ blocked by #30 |
| 4 | The UI never claims something untrue | connected / not-connected / replaying are distinguishable | ❌ #26 |
| 5 | A regression is caught by a machine, not a person | CI red on a bad push | ❌ no CI (TEST-3) |
| 6 | Someone else could run it | one documented command, honest dependencies | ⚠️ #13 |

**Why these and not "the epics are done":** every epic below could be complete while the
project remains a thing that only runs on one laptop. Criteria 1 and 2 are the ones that
turn it from a plan into a product, and both are currently unmet.

**The two highest-leverage gaps are 1 and 5**, and neither is an epic in this file —
deploy has no story anywhere, and TEST-3 is a single line under Testing & Quality. That
imbalance is itself worth noticing.

---
> **Standing check before adding anything** (`docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 3): two of four people at
> Wekfest, independently and unprompted, asked for *simpler* rather than *more*. One of them
> lives on the expert side and named the expert blind spot himself — even when a process seems
> simple to him, he has to explain it simply. The other said he would use it **in that case**,
> a conditional worth taking literally. Eleven epics is a vision, not a plan; re-read this
> before the next feature.

### EPIC: OBD-2 Data Ingestion
- **OBD-1** — As a Dev, I want the backend to connect to an ELM327 adapter over serial/Bluetooth, so the app can read live vehicle data.
  - AC: opens the configured port; runs the `ATZ → ATE0 → ATL0 → ATSP0` init; logs connection status; fails gracefully with a clear error when no adapter is present.
- **OBD-2** — As a Dev, I want to poll a configurable set of PIDs on an interval, so live readings are continuously available.
  - AC: polls a defined PID list (RPM, speed, coolant, throttle, MAF, O2, voltage); parses each response to a value; skips unsupported PIDs (`NO DATA`) without crashing.
- **OBD-3** — As a Dev, I want raw responses decoded into typed transaction records, so downstream services get clean JSON.
  - AC: each reading → `{timestamp, vehicle_id, pid, name, value, unit}`; DTCs decoded to codes; formulas covered by unit tests. *(decoder + tests DONE — `backend-OBD-reader/tests/test_decoder.py`)*
- **OBD-4** — As a Dev, I want to develop without a car using recorded samples, so I can iterate offline.
  - AC: reader can source from a fixture; the test suite runs with no hardware. *(fixtures DONE — `test_files/sample_obd_output.json`, `sample_obd_raw_stream.txt`)*
- **OBD-5** — As a Dev, I want responses the decoder can't handle **captured** (PID, raw frame, error) instead of silently skipped, so I can see what a real car actually sends.
  - AC: on a decode failure the poll loop records the PID, the raw frame and the exception, then carries on; the rest of the cycle still returns; the record is greppable so `sort | uniq -c` shows which PIDs recur.
  - Why now: `poll_once()` currently does `except (NoData, ValueError): continue`, discarding both the exception *and* the raw bytes. A misbehaving PID shows up only as a missing gauge on the dashboard — with no record of which one or why, which is a bad thing to discover sitting in a car park. Nothing downstream (OBD-6, the PRED-4 note) is possible until the evidence is kept.
- **OBD-6** — As a Dev, I want a captured real-car failure replayed as a test fixture, so a frame that broke the reader once can never break it silently again.
  - AC: the recorded bad frame replays through the **real** reader via `FakeSerial`, same as the golden decode test; assertions are **behavioural** — the poll loop survives, the other PIDs still return, the frame is recorded — not a decoded value.
  - Note: the "expected values must come from the OBD-II spec, never from the decoder" guardrail (see DECISIONS.md, the deferred `/new-pid` skill) does **not** bind here. A failure fixture asserts a contract you define, not a value the spec dictates — so there is no oracle problem.
  - Depends on **OBD-5**. Real adapters emit things the clean recorded capture never will (`SEARCHING...`, `BUS INIT: ERROR`, `STOPPED`, `?`, partial frames), so these cases have to be collected from a car, not invented.

### EPIC: Live Dashboard
- **DASH-1** — As an Enthusiast, I want to see my car's live readings in the browser, so I know its real-time status.
  - AC: shows RPM, speed, coolant, etc.; updates in real time; legible at a glance.
- **DASH-2** — As a Dev, I want the backend to stream readings over WebSocket, so the UI updates without polling.
  - AC: `/ws` endpoint; broadcasts each reading as JSON; client auto-reconnects on drop.
- **DASH-3** — As an Enthusiast, I want a clear indicator when a fault is active, so I notice problems immediately.
  - AC: active DTC shown prominently with a plain-language label.

### EPIC: Fault Detection & Basic Diagnosis
- **DIAG-1** — As an Enthusiast, I want fault codes translated to plain language, so I understand them without googling.
  - AC: DTC → human description map; unknown codes show the raw code + a generic message.
- **DIAG-2** — As an Enthusiast, I want simple urgency shown, so I know what needs attention now vs. later.
  - AC: rule-based severity (e.g. overheating = critical); colour-coded.
- **DIAG-3** — As an Enthusiast with a specific make of car, I want **manufacturer-specific** fault codes translated too, so a Subaru-only code isn't shown to me as "unrecognized".
  - Context: fault codes come in two tiers. **Generic** codes (`P0xxx`, `P2xxx`, `P34xx-P39xx`, `C0`, `B0`, `U0`) are set by a published standard and mean the same thing on every car — that fixed list lives in `backend-OBD-reader/obd_reader/data/dtc_generic.json` and needs no database. **Manufacturer-specific** codes (`P1xxx`, `C1/C2`, `B1/B2`, `U1/U2`) mean different things per make: `P1130` is not the same fault on a Subaru as on a Ford. Only this second tier grows over time, and it is the tier that justifies a DB.
  - AC: lookup takes the vehicle's make into account and resolves in order `(make, code)` → generic code → "unrecognized"; a code missing from every tier still degrades gracefully rather than erroring.
  - Depends on **STORE-3** (vehicle records — a manufacturer code can't be resolved without knowing the make) and on a real write path: **AGENT-1.2/AGENT-2.1** (community-sourced knowledge) and **EVAL-3** (mechanic-reviewed labels) are what actually make this set grow. Until at least one of those exists, a DB would be a table nothing writes to.
  - **The make comes from the VIN, not from the user.** A VIN encodes the manufacturer in its first three characters (the World Manufacturer Identifier) and the model year at position 10, so `(make, code)` resolves with no configuration and no question asked at setup. Note a VIN identifies a specific vehicle and, via registration records, potentially a person — treat it as identifying data: keep it out of URLs and casual logs.
    - **The decode is local.** Characters 1-3 are matched against a World Manufacturer Identifier table we ship — no API call, so the VIN never leaves the device for this. Derive the make in memory, store the *make*, discard the VIN: the make is not identifying data, the VIN is, and DIAG-3 needs only the former. A remote decoder (NHTSA vPIC) returns model, year and engine too, but that is a **fitment** need (MKT-5), not a catalog-selection one, and it puts the VIN in a URL — the thing the line above warns against. Decide it there, at the point of need, not here.
    - Prerequisite not yet built: the VIN is read from the car with Mode 09 PID 02 (`0902`), which is **multi-frame**. `reader.py:_command` returns only the first line of a response, so it would truncate the VIN silently. Every response handled today is single-line; this is the first that is not.
  - Catalog *selection* is a lookup, not a permission. Which manufacturer catalog a vehicle needs follows from its VIN; **who may see a vehicle at all** is the authorization question, and it lives one level up on the vehicle record (ROLE-1/ROLE-3). Coupling them would mean catalog resolution could not be tested without standing up auth, and a token bug would present as a missing catalog. The one exception is *licensed* catalog data, where a supplier contract may require access control — a commercial constraint, not a security one.
  - Sizing note: per-make catalogs vary enormously — BMW's proprietary set dwarfs Subaru's — but a car has exactly one make, so only that make's slice is ever loaded. The volume argues for Postgres over files, but the deciding reason is still the write path above, not the size.
  - Guardrail: only `description` may come from a scraped/community source. `severity` stays an editorial judgement made by a human, so the UI never marks something critical on the say-so of a forum post.

### EPIC: Data Storage
- **STORE-1** — As a Dev, I want readings persisted to PostgreSQL JSONB, so history is retained across sessions.
- **STORE-2** — As a Dev, I want fault events in a TimescaleDB hypertable, so I can query trends and recurrence over time.
- **STORE-3** — As a Dev, I want vehicle/user records in relational tables designed for multi-tenancy, so the CRM layer isn't a painful retrofit later.
- **STORE-5** — As a Dev, I want the **sources people actually use** recorded and ranked per platform, so AGENT-1.2's corpus is observed rather than guessed.
  - **Not an agent.** A document store with a write path, feeding AGENT-1.2's routing. MongoDB is already in the stack for scraped forum data.
  - Seeded from conversations, then refined by users naming their **top 3 sources for their platform**. Refinement, not creation — a list that only exists once users arrive cannot bootstrap the agent that attracts them.
  - **Scoped per platform, never global.** A WRX owner's top 3 and an E90 owner's barely overlap; NASIOC means nothing to a BMW driver. A global ranking collapses to "Reddit, Google, YouTube" and says nothing.
  - **Two signals, kept apart:** what people *say* they use (survey), and what actually *produced a good answer* (retrieval feedback, once AGENT-1.2 runs). The second is better evidence and only exists later — design the schema to hold both now rather than migrating.
  - **Preference and ingestibility are separate columns.** A site can top the list and prohibit scraping. Reddit has an API with cost and rate limits; forums are HTML with varying `robots.txt`. Priority informs what to pursue; access is decided per source.
  - Same discipline as OBD-5 and PRED-8: **capture where people look before deciding where to scrape.** One observation already exists — an owner described code → Reddit → part stores, unprompted (`docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 1). Adding *"where do you look first, and what do you do when that fails?"* to the question bank makes this cheap to gather.
- **STORE-6** — As a Dev, I want a **shared answer cache keyed by (platform, code)**, so the same fault on the same platform is not diagnosed from scratch for every owner.
  - **Not a read replica.** A replica is a full database copy for read scaling; this is a cache of *answers*. Redis is already in the stack for agent session state.
  - Key on **platform, not model** — an EJ25 misfire answer serves a WRX, a Forester XT and a Legacy GT. Keying per model fragments the cache and loses most of the benefit. Same routing insight as AGENT-1.2.
  - **The first genuine network effect here:** every diagnosis makes the next owner's faster, and the value grows with users rather than with our spend.
  - **Privacy is easy in this one**, unlike the shop-access tiering (see DECISIONS.md, 2026-09-04): the cached thing is the answer to a *public* question. No VIN, no telemetry, no identity. That is why it is safe to share by default.
  - Needs invalidation: answers go stale when sources change or a mechanic corrects one (EVAL-3). TTL or explicit bust.
  - Known limitation: the same code can have different causes on a stock versus a heavily modded car. The cache can be confidently wrong in that direction — worth knowing before it is built.
- **STORE-4** — As a Dev, I want only a *selected* set of PIDs stored as a bounded timeseries (defined sampling rate + retention window, older data downsampled/aged out), so we keep useful history without unbounded storage cost — deciding **what** and **how much** to store, not everything forever.

### EPIC: Testing & Quality
- **TEST-1** — Unit tests for PID/DTC parsing. *(DONE)*
- **TEST-2** — As a Dev, I want a Gherkin `.feature` describing the OBD-reader microservice contract, so behaviour is documented and verifiable.
- **TEST-3** — As a Dev, I want CI to run the test suite on every push, so regressions are caught early.
- **TEST-4** — As a Dev, I want each test to fail *loudly and specifically* — logging what it checked and raising a descriptive, test-specific error — instead of a bare `AssertionError`, so a red run tells me **what broke and why** without decoding a traceback.
  - AC: on failure, each test emits a clear message identifying the scenario, the expected vs. actual, and the likely cause (e.g. "PID 010C decode formula changed: expected 1726.0, got 1725.0"); the golden-file test names the first mismatching record and field; consider custom exception types (e.g. `GoldenMismatchError`, `DecodeContractError`) and structured logging so CI output is diagnosable at a glance. Extends the existing `_diff()` helper rather than replacing it. Applies to both the standalone runner and pytest.

---
