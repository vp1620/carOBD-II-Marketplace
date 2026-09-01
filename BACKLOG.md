# Backlog — Roadmap Stories

Epics and user stories derived from `DEVELOPMENT_PLAN.md`. Phase 1 stories carry
acceptance criteria (they're next); later epics are lighter on purpose — don't
over-specify future work.

**Personas:** **Enthusiast** (budget-conscious car owner, primary) · **Mechanic**
(shop/merchant) · **Dev** (you, for infra/tooling stories).

Story IDs are stable handles for a tracker (Jira/GitHub). Format for seeding an
automated tracker: each `###` epic → an Epic; each `- [ID]` → a Story under it.

---

## Phase 1 — Simple Full-Stack Website (BUILD FIRST)

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
  - Depends on **STORE-3** (vehicle records — a manufacturer code can't be resolved without knowing the make) and on a real write path: **AGENT-2/AGENT-4** (community-sourced knowledge) and **EVAL-3** (mechanic-reviewed labels) are what actually make this set grow. Until at least one of those exists, a DB would be a table nothing writes to.
  - Guardrail: only `description` may come from a scraped/community source. `severity` stays an editorial judgement made by a human, so the UI never marks something critical on the say-so of a forum post.

### EPIC: Data Storage
- **STORE-1** — As a Dev, I want readings persisted to PostgreSQL JSONB, so history is retained across sessions.
- **STORE-2** — As a Dev, I want fault events in a TimescaleDB hypertable, so I can query trends and recurrence over time.
- **STORE-3** — As a Dev, I want vehicle/user records in relational tables designed for multi-tenancy, so the CRM layer isn't a painful retrofit later.
- **STORE-4** — As a Dev, I want only a *selected* set of PIDs stored as a bounded timeseries (defined sampling rate + retention window, older data downsampled/aged out), so we keep useful history without unbounded storage cost — deciding **what** and **how much** to store, not everything forever.

### EPIC: Testing & Quality
- **TEST-1** — Unit tests for PID/DTC parsing. *(DONE)*
- **TEST-2** — As a Dev, I want a Gherkin `.feature` describing the OBD-reader microservice contract, so behaviour is documented and verifiable.
- **TEST-3** — As a Dev, I want CI to run the test suite on every push, so regressions are caught early.
- **TEST-4** — As a Dev, I want each test to fail *loudly and specifically* — logging what it checked and raising a descriptive, test-specific error — instead of a bare `AssertionError`, so a red run tells me **what broke and why** without decoding a traceback.
  - AC: on failure, each test emits a clear message identifying the scenario, the expected vs. actual, and the likely cause (e.g. "PID 010C decode formula changed: expected 1726.0, got 1725.0"); the golden-file test names the first mismatching record and field; consider custom exception types (e.g. `GoldenMismatchError`, `DecodeContractError`) and structured logging so CI output is diagnosable at a glance. Extends the existing `_diff()` helper rather than replacing it. Applies to both the standalone runner and pytest.

---

## Later Phases (stories kept light until they're next)

### EPIC: Agentic Diagnosis
- **AGENT-1** — RAG over owner's-manual PDF chunks (Qdrant).
- **AGENT-2** — RAG over scraped Reddit threads (Qdrant + MongoDB raw store).
- **AGENT-3** — Agent 1 escalates to Agent 2 via `escalate_to_reddit` tool use when confidence is low.
- **AGENT-4** — Background job polls Reddit replies, embeds them, feeds the knowledge base.
- **AGENT-5** — Blog fallback after 72h with no reply; notify platform mechanics.
- **AGENT-6** — Agent output includes **cost estimate + urgency** (the enthusiast "don't get ripped off" value prop).

### EPIC: Evaluation & Gamified Feedback *(build alongside the AGENT RAG system — this is its eval + labeling layer)*
- **EVAL-1** — As a Dev, I want a **scenario injector** that feeds curated + procedurally-varied PID/anomaly cases into the diagnosis engine, so recommendations are regression-tested against known-correct answers. Scenarios come from a stored bank (DB/JSON), NOT LLM-generated at runtime — cheaper and reproducible; extends `FixtureReader`. LLM used only offline to draft new hard cases that a human verifies once and stores.
- **EVAL-2** — As an Enthusiast/Mechanic, I want a "guess the fault" **game** over known-answer scenarios (quiz mode) that awards points for correct answers, so evaluating the engine is engaging and educational.
- **EVAL-3** — As a Dev, I want player answers + "the computer was wrong" feedback captured as **labels that feed the agent's RAG knowledge base** — gated by confidence + mechanic review before ingestion so the flywheel improves the model without poisoning it. **Wire directly into the RAG ingestion path (AGENT-1/2/4).**
- **EVAL-4** — As a Dev, I want **gold-standard honeypot scenarios** seeded among the unknowns + **expert (mechanic) answer weighting**, so crowd-label quality is measurable and gaming-resistant.
- Note: liability — game diagnoses are advisory/educational, never authoritative for a real vehicle. Ground truth exists for curated scenarios; real-case labels rely on consensus + expert weighting until a repair confirms them.

### EPIC: Marketplace
- **MKT-1** — Region/zone-aware parts catalog routed from the DTC body zone.
- **MKT-2** — SubiMods + JDM Muscle integration (API/scrape) as first vendors.
- **MKT-3** — Recommendation flow: `source` (agent|mechanic), mechanic approval gate, customer accept → book/order.

### EPIC: Maintenance Records & Resale
- **MAINT-1** — As an Enthusiast, I want to log a completed maintenance event with **multi-modal evidence** — photos of the work, a video of it being performed, and a screenshot/receipt of the parts order — so each service is documented and verifiable.
- **MAINT-2** — As an Enthusiast, I want the app to **generate a clean maintenance report** per event (and a full service history), so I can *prove upkeep when selling the car* and command a better price — an owner-generated, verifiable service record.
- **MAINT-3** — As a Dev, I want maintenance evidence auto-linked to the **parts order (MKT-3)** and the **vehicle record (STORE-3)**, so the report ties the work to the actual part and car, not just a loose photo.
- Note: storage — media (photos/video) to object storage (S3/GCS) with metadata in Postgres; keep media costs bounded (compression, retention). A later RAG/agent tie-in could summarize the history or flag gaps.

### EPIC: Role-Based UI & Multi-Tenancy
- **ROLE-1** — JWT auth shared across web/mobile.
- **ROLE-2** — Distinct Customer vs. Mechanic views.
- **ROLE-3** — A shop account owns multiple customer vehicles.

### EPIC: Mobile / PWA
- **MOB-1** — Installable PWA (offline-capable).
- **MOB-2** — React Native app connecting to the Bluetooth OBD adapter directly.

### EPIC: Go Backend Migration
- **GO-1** — Port the PID/DTC decoder to Go. *(skeleton parked in `archive/go-backend`)*
- **GO-2** — Serial client with read-until-`>` framing (`go.bug.st/serial`).
- **GO-3** — WebSocket parity with Python; verify decoders against the shared fixtures.

### EPIC: Hardware *(parked — buy, don't build, until volume says otherwise)*
- **HW-1** — *(learning project / parked)* Build a read-only OBD-II reader instead of buying an ELM327: ESP32 with its built-in CAN controller plus a transceiver (e.g. SN65HVD230), powered off the port's 12V pin. Roughly $10-15 in parts, and open designs exist to work from (comma.ai panda, Macchina M2, CANtact).
  - What changes in our code: **`pids.py` is untouched** — the formulas are the OBD-II standard, not the adapter. `decoder.py`'s framing largely disappears, since `parse_data_bytes` exists to read ASCII hex and wait for the `>` prompt, and raw CAN hands you bytes. `reader.py` swaps transport, which is exactly what the injected `transport` seam was built for.
  - What it would unlock: an ESP32 has WiFi/BLE, so the device could push readings itself rather than needing a phone in the middle — and **buffer when nothing is connected**, which fixes "readings are broadcast and discarded" at the source rather than in Postgres.
  - Why parked: hardware is a different discipline (PCB, enclosure, FCC once there is a radio, manufacturing, field firmware updates), and a CAN-only device drops pre-2008 cars on ISO 9141 / J1850 that an ELM327 already handles. Phase 1 is not finished and a $15 dongle works today.
  - **Read-only, strictly.** A device on the CAN bus can write to it; a bug that transmits malformed frames can interfere with vehicle systems. Do not test on a car you need to drive home.
  - Revisit if the shop-giveaway program (see `docs/market/`) reaches volume where $8 custom versus $20 off-the-shelf actually matters. That is thousands of units, not tens.

### EPIC: Predictive Maintenance & Track Mode
- **PRED-1** — Trend-rule alerts from TimescaleDB history (zero-ML first).
- **PRED-2** — RUL models once failure data exists.
- **PRED-3** — Per-PID **healthy baseline** (rolling mean + spread) of *normal* readings as the reference for "what this car normally does"; anomalous samples excluded so they don't poison the baseline. Baselines segmented by operating regime (e.g. idle vs. cruising vs. load) since "normal" is state-dependent.
- **PRED-4** — **Anomaly detection** against the baseline — statistical-first (EWMA / z-score band, rate-of-change spikes) before any ML; deviations flagged and stored, not just the raw value.
- Note: **error-rate anomaly** — "this PID is failing abnormally often" is PRED-3/4 pointed at *decode failures* instead of sensor values, fed by **OBD-5**. Same rolling baseline, same window, same flagging — build it as a second consumer of that machinery, not a parallel detector with its own thresholds. Gate with **PRED-6** until there is enough history to know what "normal" is. At one-vehicle scale a log plus `uniq -c` already answers this; it earns its keep at **STORE-3** multi-vehicle scale, where you can't eyeball it.
- **PRED-5** — On a DTC, snapshot the **fault-relevant PIDs'** recent series + baseline deltas (and capture the ECU's own **freeze-frame / Mode 02** if available), so every fault event carries the normal-vs-anomaly context that led up to it — the "connect the fault back to the sensor data" link. DTC→PID relevance routed via the same body/system zone map used by MKT-1.
- **PRED-6** — **Baseline-readiness gate.** Until a PID has enough clean samples *per operating regime* (idle/cruise/load), suppress anomaly flags and baseline-narrowed diagnosis; a DTC then falls back to generic plain-language fixes + severity (DIAG-1/2) plus current value and ECU freeze-frame, clearly labelled *"general guidance — not yet personalized to your vehicle."* Baseline is an **enhancement, not a dependency**: always collect data to build it, only *compare* against it once ready. (The current live reading and Mode 02 freeze-frame need no baseline and are always usable.)
- **PRED-7** — *(later optimization, once multi-tenant data exists)* **Fleet/model baseline** bootstrap: seed a new vehicle's baseline from a per-model aggregate so it isn't blind during warm-up, then blend toward the vehicle's own history as it accumulates. Depends on enough vehicles/data (STORE-3 / ROLE-3).
- **PRED-8** — As an Enthusiast, I want the app to listen for **abnormal noises** and flag changes over time, so problems that never set a fault code still get caught.
  - Why it is not redundant with OBD: OBD-2 only knows what has a sensor. Wheel/alternator/water-pump bearings, belt squeal, CV joint clicking, exhaust leaks, rod knock and suspension clunks set **no DTC at all** — yet "what's that noise?" is the most common question an enthusiast asks. Sound is the diagnostic channel for a whole class of faults the fault codes cannot see.
  - **Our unfair advantage is RPM.** The standard technique for rotating machinery is *order analysis* — tracking how a sound's frequency scales with shaft speed, so a defect appears at a known multiple of rotation rather than at some absolute frequency. That requires a tachometer signal, which a standalone audio app does not have and we already poll (`010C` RPM, `010D` speed). Even with no ML, "does this noise scale with engine RPM, with wheel speed, or neither?" splits belt/accessory faults from bearing/driveline faults — which is exactly how a mechanic triages by ear.
  - Build it as a second modality on **PRED-3/4**, not a new system: per-vehicle acoustic baseline per operating regime (idle / cruise / load), flag deviation from *this car's* normal. "Your car sounds different at 40 mph than it did three months ago" is far more tractable than classifying a sound absolutely, and needs no labelled dataset. Gate with **PRED-6** until the baseline is ready.
  - AC: audio captured alongside the OBD stream, timestamped together so samples can be correlated with RPM/speed; features extracted **on-device**; deviation from baseline flagged, not raw classification.
  - **Privacy is a design constraint, not a policy note.** Two independent layers: (1) an explicit user-controlled mic toggle — consent; (2) store extracted features (spectral bands, order magnitudes), **never the waveform** — blast radius. With no audio retained there is no conversation to leak, subpoena or breach, which is also what makes the toggle something a user will actually switch on. Note a passenger never touched that toggle, and Illinois is an all-party-consent state for private conversations — worth a real legal check before shipping, not a guess. Conveniently the private-by-design architecture is also the cheap one: features are orders of magnitude smaller than audio, work offline, and need no round trip.
  - Do not start with a model. Start by **capturing audio + OBD together and looking at it** — same "capture before you build" rule as OBD-5. Labelled fault-sound data barely exists publicly; ground truth needs someone to actually open the part up, which is what the EVAL epic's mechanic-review flywheel is for.
  - Note: phone mics fight this — automatic gain control, noise suppression and voice-tuned band limits actively destroy the signal. Unprocessed capture is a deliberate configuration on both platforms, and mic placement (mount vs cupholder vs pocket) changes the result materially.
- **TRACK-1** — Session-scoped, high-frequency "track session" capture mode.
- **TRACK-2** — Phone IMU + GPS sensor fusion for handling/dynamics.
- **TRACK-3** — "Another lap?" advisory: limiting-factor + time-to-limit, framed as advisory (not a safety guarantee).

---

## Automated tracker seeding

This file is structured so a script/agent can create the tracker in one pass:
epics from `###`, stories from `- [ID]`, acceptance criteria from the `AC:` lines.
Use the story ID as the idempotency key so re-runs update rather than duplicate.
