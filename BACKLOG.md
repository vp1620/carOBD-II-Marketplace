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
  - AC: each reading → `{timestamp, vehicle_id, pid, name, value, unit}`; DTCs decoded to codes; formulas covered by unit tests. *(decoder + tests DONE — `testing/test_record_parsing.py`)*
- **OBD-4** — As a Dev, I want to develop without a car using recorded samples, so I can iterate offline.
  - AC: reader can source from a fixture; the test suite runs with no hardware. *(fixtures DONE — `testing/sample_obd_output.json`, `sample_obd_raw_stream.txt`)*

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

### EPIC: Data Storage
- **STORE-1** — As a Dev, I want readings persisted to PostgreSQL JSONB, so history is retained across sessions.
- **STORE-2** — As a Dev, I want fault events in a TimescaleDB hypertable, so I can query trends and recurrence over time.
- **STORE-3** — As a Dev, I want vehicle/user records in relational tables designed for multi-tenancy, so the CRM layer isn't a painful retrofit later.
- **STORE-4** — As a Dev, I want only a *selected* set of PIDs stored as a bounded timeseries (defined sampling rate + retention window, older data downsampled/aged out), so we keep useful history without unbounded storage cost — deciding **what** and **how much** to store, not everything forever.

### EPIC: Testing & Quality
- **TEST-1** — Unit tests for PID/DTC parsing. *(DONE)*
- **TEST-2** — As a Dev, I want a Gherkin `.feature` describing the OBD-reader microservice contract, so behaviour is documented and verifiable.
- **TEST-3** — As a Dev, I want CI to run the test suite on every push, so regressions are caught early.

---

## Later Phases (stories kept light until they're next)

### EPIC: Agentic Diagnosis
- **AGENT-1** — RAG over owner's-manual PDF chunks (Qdrant).
- **AGENT-2** — RAG over scraped Reddit threads (Qdrant + MongoDB raw store).
- **AGENT-3** — Agent 1 escalates to Agent 2 via `escalate_to_reddit` tool use when confidence is low.
- **AGENT-4** — Background job polls Reddit replies, embeds them, feeds the knowledge base.
- **AGENT-5** — Blog fallback after 72h with no reply; notify platform mechanics.
- **AGENT-6** — Agent output includes **cost estimate + urgency** (the enthusiast "don't get ripped off" value prop).

### EPIC: Marketplace
- **MKT-1** — Region/zone-aware parts catalog routed from the DTC body zone.
- **MKT-2** — SubiMods + JDM Muscle integration (API/scrape) as first vendors.
- **MKT-3** — Recommendation flow: `source` (agent|mechanic), mechanic approval gate, customer accept → book/order.

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

### EPIC: Predictive Maintenance & Track Mode
- **PRED-1** — Trend-rule alerts from TimescaleDB history (zero-ML first).
- **PRED-2** — RUL models once failure data exists.
- **PRED-3** — Per-PID **healthy baseline** (rolling mean + spread) of *normal* readings as the reference for "what this car normally does"; anomalous samples excluded so they don't poison the baseline. Baselines segmented by operating regime (e.g. idle vs. cruising vs. load) since "normal" is state-dependent.
- **PRED-4** — **Anomaly detection** against the baseline — statistical-first (EWMA / z-score band, rate-of-change spikes) before any ML; deviations flagged and stored, not just the raw value.
- **PRED-5** — On a DTC, snapshot the **fault-relevant PIDs'** recent series + baseline deltas (and capture the ECU's own **freeze-frame / Mode 02** if available), so every fault event carries the normal-vs-anomaly context that led up to it — the "connect the fault back to the sensor data" link. DTC→PID relevance routed via the same body/system zone map used by MKT-1.
- **PRED-6** — **Baseline-readiness gate.** Until a PID has enough clean samples *per operating regime* (idle/cruise/load), suppress anomaly flags and baseline-narrowed diagnosis; a DTC then falls back to generic plain-language fixes + severity (DIAG-1/2) plus current value and ECU freeze-frame, clearly labelled *"general guidance — not yet personalized to your vehicle."* Baseline is an **enhancement, not a dependency**: always collect data to build it, only *compare* against it once ready. (The current live reading and Mode 02 freeze-frame need no baseline and are always usable.)
- **PRED-7** — *(later optimization, once multi-tenant data exists)* **Fleet/model baseline** bootstrap: seed a new vehicle's baseline from a per-model aggregate so it isn't blind during warm-up, then blend toward the vehicle's own history as it accumulates. Depends on enough vehicles/data (STORE-3 / ROLE-3).
- **TRACK-1** — Session-scoped, high-frequency "track session" capture mode.
- **TRACK-2** — Phone IMU + GPS sensor fusion for handling/dynamics.
- **TRACK-3** — "Another lap?" advisory: limiting-factor + time-to-limit, framed as advisory (not a safety guarantee).

---

## Automated tracker seeding

This file is structured so a script/agent can create the tracker in one pass:
epics from `###`, stories from `- [ID]`, acceptance criteria from the `AC:` lines.
Use the story ID as the idempotency key so re-runs update rather than duplicate.
