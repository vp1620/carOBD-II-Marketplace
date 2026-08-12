# Car OBD-II Marketplace — Development Plan

> Living planning document. Captures the architecture and feature decisions made so far.
> Build order: **get a simple functioning full-stack website working first**, then layer everything else on top.

---

## Vision

A platform that reads OBD-2 fault data from a vehicle, diagnoses issues using an AI agent (with community + owner's-manual knowledge), and connects car owners with mechanics/shops through a marketplace.

Two distinct user types:
- **Customer** (car owner) — sees their vehicle, plain-language diagnoses, receives recommendations.
- **Mechanic / Shop / Merchant** — manages multiple customer vehicles, reviews AI diagnoses, sends recommendations, lists services.

> **Wedge customer (see Future Concepts):** the first target is the **budget-conscious driver enthusiast** — "the least I need to spend to track my car safely." B2C enthusiast product leads; the mechanic/marketplace B2B side is a second segment.

---

## Phase 1 — Simple Full-Stack Website (BUILD FIRST)

The minimum functioning product. Everything else sits on top of this.

- [ ] Backend streams OBD-2 readings (Python now)
- [ ] WebSocket connection pushing live data to the browser
- [ ] React frontend dashboard displaying live readings
- [ ] Fault code (DTC) detection with basic diagnosis
- [ ] Test infrastructure (see Testing section)

**Current state:**
- `backend-OBD-reader/obd-2-parsing.py` — uses `python-obd` to auto-connect and query PIDs
- `testing/sample_obd_output.json` — example reader output (raw ELM327 hex + decoded transaction records)
- `testing/test_record_parsing.py` — pytest validating raw-hex → transaction-record parsing

---

## Hardware & Protocol

- **Adapter:** Bluetooth ELM327 (exposes serial-over-Bluetooth / RFCOMM SPP)
- **Protocol:** ASCII commands over serial at 9600–38400 baud
- **Init sequence:** `ATZ` → `ATE0` → `ATL0` → `ATSP0`
- **Reading PIDs:** e.g. `010C` = RPM, response `41 0C 1A F8`
- **Responses terminate with `>` prompt** (not newline)

**Common PIDs tracked:**

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

### Backend
- **Now:** Python (`python-obd`, WebSocket server)
- **Later:** Go migration — same ELM327 protocol, `go.bug.st/serial`, goroutines for concurrent poll + serve, `gorilla/websocket`
- Migration is gradual: Go can test against the Python simulator's TCP server; replicate each PID decoder and verify parity before cutover

### Frontend
- **Now:** React (website)
- **Later:** React Native (shares components; connects to Bluetooth OBD directly from phone)
- Use React from day one so mobile can reuse components

### Storage (polyglot — right tool per job)

| Data | Storage | Why |
|---|---|---|
| Raw OBD readings (live) | **PostgreSQL JSONB** | Flexible schema, PIDs vary by car |
| Fault events / DTC history | **TimescaleDB** (Postgres extension, hypertable) | Time-series: when a fault started, trends, recurrence |
| Vehicles / users / marketplace | **PostgreSQL** (relational tables) | Structured, needs joins |
| Owner's manual chunks | **Qdrant** | Vector search over PDF embeddings |
| Scraped Reddit embeddings | **Qdrant** | Semantic search, same vector space |
| Raw scraped Reddit data | **MongoDB** | Flexible schema, Reddit JSON varies |
| Agent session state / memory | **Redis** | Fast, TTL for ephemeral state |
| Posted questions + reply tracking | **MongoDB** | Track lifecycle, feed replies back into knowledge base |

> Note: TimescaleDB, JSONB tables, and relational tables all live in **one Postgres instance** — one connection string, one backup. DynamoDB considered but deferred (access patterns must be designed upfront, AWS lock-in, ops complexity too early). Natural migration trigger: if Postgres write throughput from constant polling becomes a bottleneck.

**Language split at a glance:**
- **Python** — Phase 1 + the entire agentic/AI layer (best ecosystem for RAG, embeddings, scraping)
- **Go** — performance-critical serial-read + WebSocket-serve backend, once Phase 1 is proven
- **Kotlin/Java** — only the Android Auto surface
- **JS/TypeScript** — React web, React Native mobile, Three.js 3D

---

## Testing Strategy

- **Unit tests:** `pytest` (Python) → `go test` built-in `testing` package (Go)
- **Microservice contract / BDD:** `pytest-bdd` + Gherkin `.feature` files → `godog` (Go)
- **Gherkin `.feature` files are language-agnostic** — reusable across the Python→Go migration; only step definitions get rewritten

**Structure:**
```
testing/
├── sample_obd_output.json     # example reader output (fixture)
├── test_record_parsing.py     # pytest — raw hex → transaction record (DONE)
├── unit/
│   └── test_pid_encoders.py   # pytest — low-level encoder/decoder
└── integration/
    ├── features/
    │   ├── obd_reader.feature
    │   ├── fault_detection.feature
    │   └── data_api.feature   # one .feature per microservice as they grow
    └── steps/
        └── *_steps.py
```

Run the parsing test: `python3 testing/test_record_parsing.py` (standalone) or `pytest testing/test_record_parsing.py`

---

## Agentic Diagnosis Feature

Multi-agent system triggered when a DTC code arrives.

### Agent 1 — Diagnostic RAG Agent
- Searches owner's manual chunks (Qdrant)
- Searches scraped Reddit thread embeddings (Qdrant)
- Returns diagnosis if confident; escalates if not

### Agent 2 — Social Posting Agent
- Called as a **tool** by Agent 1 (Claude API tool use — `escalate_to_reddit`)
- Posts the question to Reddit / social media
- Post tracked so replies feed back into the knowledge base

### Flow
```
DTC arrives (e.g. P0420)
   → Agent 1 searches Qdrant (manual + Reddit)
   → High confidence? return diagnosis
   → Low confidence? Agent 1 calls escalate_to_reddit tool → Agent 2 posts
```

### Escalation & Fallback (Reddit → Blog)
```
Agent can't answer
   → Post to Reddit (PRAW), MongoDB status: pending_reddit
   → Background job polls replies every 6 hours
       ├── Reply → embed into Qdrant → answer customer → resolved_reddit
       └── No reply after 72 hours (3 days) → post to app blog → escalated_blog
                → notify platform mechanics → mechanic answers
                → embed into Qdrant → resolved_blog
```

**Why the personal blog fallback:** owns the knowledge (feeds Qdrant), no Reddit API cost/limits, verified mechanics answer, becomes a mechanic-acquisition channel (shops answer publicly → get leads → ties into CRM/marketplace).

**Reply ingestion loop is what makes the knowledge base self-improving over time.**

### Key libraries
`PRAW` (Reddit), `pypdf` (manual parsing), `sentence-transformers` (embeddings), `qdrant-client`, `anthropic` (Claude API agent orchestration), `redis-py`, `pymongo`, `Celery` + Redis (background jobs)

**Target subreddits:** `r/MechanicAdvice`, `r/AskAMechanic`

---

## Recommendation Flow

Recommendations can come from **either the app (agent) or a mechanic**.

```
Fault detected → Agent diagnoses → generates recommendation
   → Mechanic reviews (approve / modify / override)   [quality gate — liability]
   → Customer receives → accepts → books service / orders part
```

**Data model (plan now, build later):**
```
recommendations {
    source        # "agent" | "mechanic"
    mechanic_id   # null if from agent
    vehicle_id
    dtc_code
    content
    status        # pending | approved | sent | accepted | dismissed
    created_at
}
```
The `source` field later enables analysis: do mechanic recs outperform agent recs? Improves the agent over time.

---

## Marketplace

- **Region-aware catalog:** the fault's body zone (from the DTC) routes the user to the relevant parts/services.
- **Parts sourcing:** API calls / scraping from reputable third-party vendors.
- **First integrations:** **SubiMods** and **JDM Muscle** (start by scraping / calling these), expanding to more vendors over time.
- Ties into the CRM/mechanic side: shops list services; owners are directed from a diagnosis straight to the parts or service they need.

---

## UI Roadmap (post-website)

```
Website (Phase 1)
  → PWA (installable, offline-capable — quick win before native)
    → Mobile app (React Native — Bluetooth OBD direct connect)
      → CRM features (shop/mechanic management, service history) [most commercially viable]
        → B2B marketplace (owners ↔ mechanics ↔ parts suppliers)
```

### Role-differentiated UI

| Feature | Customer View | Mechanic/Shop View |
|---|---|---|
| OBD dashboard | Their car's live readings | All customer vehicles (fleet) |
| Fault codes | Plain-language explanation | Raw DTC + technical detail |
| Recommendations | Receive from app or mechanic | Send to customer, see app suggestions |
| Agent diagnosis | Read-only result | Full reasoning + confidence |
| Reddit/blog posts | Not visible | See community responses |
| 3D car model | Their car highlighted | Fleet overview |
| Marketplace | Browse parts/services | List services, manage jobs |
| History | Their fault timeline | Customer service records |

> **Plan multi-tenancy into auth from day one.** JWT auth shared across web/mobile/CRM. Data model must allow a shop to own multiple customer vehicles — retrofitting this later is painful.

### In-Car Displays

- **Android Auto** (preferred over CarPlay — CarPlay blocks diagnostic apps entirely; only audio/nav/comms/EV allowed)
- **Concept:** while driving, show a **3D model of the car with the problem area highlighted** (red/amber glow on engine/exhaust/fuel/wheel zone), mapped from DTC category. Not a code list.
- **Constraint:** Android Auto (Car App Library / Jetpack, Kotlin) won't allow interactive 3D on the head unit. Render the 3D scene on the phone → push a flat image frame to the Auto screen.
- **3D tech:** Three.js in a WebView (cross-platform, one model for web/mobile/Auto) is most practical.
- **DTC → body zone mapping:** DTC prefix already encodes the zone:
  - `P01`/`P02` → engine (fuel/air), `P03` → ignition/misfire, `P04` → exhaust/emissions, `P05`/`P06` → engine, `P07`/`P08` → transmission, `C0` → chassis (ABS/steering/suspension), `B0` → body (airbags/electronics), `U0` → network (CAN bus)
- **Future payoff:** recurring faults in the same zone over time → **fault heat map on the car body**, driven by TimescaleDB time-series data.

*(All in-car / 3D work is future — noted so decisions now don't block it.)*

---

## Future Concepts (Recorded, Not Now)

> Ideas discussed and worth keeping. None are Phase 1. Each depends on earlier phases (website → fleet data → mobile app) existing first.

### Primary Persona & Positioning — Budget-Conscious Enthusiast

The wedge customer is a **driver enthusiast who wants the least they need to spend to track their car safely.** Two fused value props:
- **Minimum hardware spend** — a ~$10 ELM327 clone + the app, not a $500 pro scan tool. The architecture already serves this.
- **Minimum repair spend** — honest triage. "These codes matter, this one can wait, here's the real cost." This crowd distrusts dealer/shop upsells, so the agent should be a **"don't get ripped off" engine.**

**Implications:**
- The agent output must include **cost estimates + urgency (urgent vs. deferrable)**, not just a diagnosis.
- Recommendations lead from the **app**, not the mechanic (they distrust shops).
- Go-to-market sequence: **B2C enthusiast wedge first** (builds trust + a data moat) → *then* open the mechanic/CRM/marketplace as a second B2B segment. The enthusiast product is what generates the fleet telemetry that makes predictive maintenance and the marketplace valuable.
- The handling-sim and fault-heat-map features land better with enthusiasts than with general owners.

### Predictive Maintenance / Remaining Useful Life (RUL)

Goal: estimate the life of each part for predictive measures.
- **Not a simulation problem — a data problem.** Learn degradation from fleet telemetry, don't simulate it.
- **Gazebo / FEA rejected for this:** Gazebo simulates robot dynamics (behavior), not part fatigue; FEA (ANSYS/Abaqus) needs per-vehicle CAD + material specs you don't have.
- The **TimescaleDB fault-event history is the training data.** Coolant creeping up over weeks, sagging battery voltage, recurring same-cylinder misfires = the degradation signals.
- **Progression:** (1) accumulate history first, (2) start with simple threshold/trend rules ("coolant averaging >100°C for 2 weeks → flag") — useful with zero ML, (3) graduate to RUL models (survival analysis / gradient-boosted on engineered features) once failure data exists.
- Later refinement: **physics-informed ML** (e.g. Arrhenius for heat-accelerated wear) to need less data.
- **Do now:** ensure the schema captures timestamped per-PID, per-vehicle granularity so history is there when ready to model.

### Handling-Visualization Gimmick

Take predicted part health → translate to degraded physical parameters → run a dynamics sim → show "how your car handles now vs. healthy" (worn brakes = longer stop, tired suspension = sloppier cornering).
- **Plays to a simulator's actual strength** (vehicle dynamics), unlike the RUL idea.
- **The real work is the mapping layer** (part health → physics parameters, e.g. "brake pads 20% → friction 0.35"). This is **simulator-agnostic** and the reusable asset.
- **Don't default to Gazebo** for a web gimmick — it's heavy, ROS-tied, ugly rendering, awkward to embed. Decide later:
  - **CARLA** — driving-specific, photorealistic, GPU-heavy (best if accuracy + looks matter)
  - **Game engine / Three.js browser physics** — lightweight, reuses the Three.js car model, "good enough" for a gimmick (best for shipping fast, stays in-stack)
- Sequenced *after* predictive maintenance exists.

### Track Mode — "Chances of Doing Another Lap Safely"

Signature enthusiast feature. During a track session, monitor **changes in dynamics** and tell the driver whether another lap is safe.
- **Within-session degradation, not long-term RUL** — cares about *rate of change within minutes* (oil temp +4°C/lap, braking zones lengthening lap-over-lap). Real-time and safety-critical.
- **Honest source split — this is a sensor-fusion feature, phone is the star:**
  - **Handling/dynamics** (G-forces, cornering speed, braking profiles, lap times) → **phone IMU + GPS**, NOT OBD-2. OBD-2 does not measure handling/G-forces/brake temp/tire temp at all.
  - **Engine thermal** (coolant `0105`, oil `015C` if supported, intake) → OBD-2.
- **Sample-rate reality:** cheap Bluetooth ELM327 polls slowly (a few PIDs/sec) vs. 50–1000 Hz pro loggers. Fine because temps change slowly and the phone IMU samples fast + free. Disclose it won't match a dedicated logger.
- **Output = limiting factor + time-to-limit, NOT a naked percentage** (false precision + liability). E.g. "Oil temp trending to critical in ~2 laps — cool-down lap recommended," "Brakes stable," "Tire grip holding." Built from simple explainable extrapolation (°C rise/lap; peak braking-G decrease = fade; cornering-G falloff = tire deg).
- **Liability framing (bake in):** advisory trend info, **not a safety guarantee.** Observational language ("oil temp rising toward limits"), never a prescriptive guarantee ("safe to continue"). The driver decides.
- **Schema note to plan now:** anticipate a **session-scoped, high-frequency "track session" capture mode**, distinct from slow ambient polling. Reuses the same dynamics data as the handling-sim gimmick and the same time-series as predictive maintenance.

---

## VS Code Extensions (dev environment)

- **Go** (Google), **Go Test Explorer**
- **Prettier**, **ESLint**, **HTML CSS Support**, **Auto Rename Tag**
- **Thunder Client** / **REST Client** (test endpoints)
- **GitLens**, **Error Lens**, **Docker**, **Path Intellisense**
- **Serial Monitor** (Microsoft) — verify raw OBD serial output

---

## Guiding Principles

1. **Functioning simple website first** — resist building agents/3D/mobile until the core streams data to a browser.
2. **Design the data model for multi-tenancy and roles now**, even if not built yet.
3. **Keep the Python simulator** — it stays useful for testing even after the Go migration.
4. **One Postgres instance** where possible; add specialized stores (Qdrant, Mongo, Redis) only when the feature needs them.
5. **Gherkin `.feature` files survive the language migration** — invest in them.
