# Later — directional, not planned

**Status: vision.** Deliberately light. These record intent and reasoning so a good idea is
not lost, **not** a commitment to build them.

Read this section as *"here is where this could go"*, not *"here is the plan."* Eleven
epics is a vision; treating it as a schedule is how a solo project reads as overrun.

**Nothing here has exit criteria yet.** That is on purpose — a phase gets criteria when it
becomes next. Writing them now would be inventing measurements for work whose shape is
still unknown.

**Promotion rule:** an epic moves out of this file when there is evidence for it, the way
the Marketplace and Maintenance epics moved into [`phase-2.md`](phase-2.md) after Wekfest.
Evidence, not enthusiasm.

---
### EPIC: Evaluation & Gamified Feedback *(build alongside the AGENT RAG system — this is its eval + labeling layer)*
- **EVAL-1** — As a Dev, I want a **scenario injector** that feeds curated + procedurally-varied PID/anomaly cases into the diagnosis engine, so recommendations are regression-tested against known-correct answers. Scenarios come from a stored bank (DB/JSON), NOT LLM-generated at runtime — cheaper and reproducible; extends `FixtureReader`. LLM used only offline to draft new hard cases that a human verifies once and stores.
- **EVAL-2** — As an Enthusiast/Mechanic, I want a "guess the fault" **game** over known-answer scenarios (quiz mode) that awards points for correct answers, so evaluating the engine is engaging and educational.
- **EVAL-3** — As a Dev, I want player answers + "the computer was wrong" feedback captured as **labels that feed the agent's RAG knowledge base** — gated by confidence + mechanic review before ingestion so the flywheel improves the model without poisoning it. **Wire directly into the RAG ingestion path (AGENT-1.1/2/4).**
- **EVAL-4** — As a Dev, I want **gold-standard honeypot scenarios** seeded among the unknowns + **expert (mechanic) answer weighting**, so crowd-label quality is measurable and gaming-resistant.
- Note: liability — game diagnoses are advisory/educational, never authoritative for a real vehicle. Ground truth exists for curated scenarios; real-case labels rely on consensus + expert weighting until a repair confirms them.

### EPIC: Role-Based UI & Multi-Tenancy
- **ROLE-1** — JWT auth shared across web/mobile, with **Google/OAuth as the identity provider**. OAuth answers *who is this person* (no password to store or leak); the JWT it produces carries the session across web and mobile. The link that matters is user → vehicle, but it is **access, not ownership**: one account *owns* a vehicle and may *grant* access to others (ROLE-4), so every check asks "does this user have a grant?" rather than "is this user the owner?". Building it as ownership first would mean rewriting every access check later. See DIAG-3 on why catalog selection is deliberately *not* part of this.
- **ROLE-2** — Distinct Customer vs. Mechanic views.
- **ROLE-3** — A shop account works on multiple customer vehicles. Note it does **not own** them — each is a grant from that customer (ROLE-4), revocable when the relationship ends. Framing it as ownership would leave a shop with standing access to cars it no longer services.
- **ROLE-4** — As an Enthusiast, I want to share my vehicle with people I choose — family, a friend, my mechanic when something goes wrong — so they can see what the car is reporting without me reading codes down the phone.
  - Access is a **grant**, not ownership: `(vehicle, grantee, scope, granted_by, granted_at, expires_at?)`. One owner, N grantees, and the owner can revoke.
  - **Grants should expire by default.** A mechanic needs access for a repair, not forever. An indefinite share is the exception (a spouse), not the rule — and defaulting to permanent means nobody ever cleans them up.
  - **Scope is not all-or-nothing.** A mechanic needs fault history and freeze-frame; a family member watching a road trip needs live status. Location history, VIN and maintenance records are each things you might not want in every share. Decide the scopes before the UI, because retrofitting them means re-auditing every read path.
  - **The share is a JSON payload, not a rendering.** It carries the *data* — faults, severities, zone names, readings — and each device draws its own 3D model from it. Zones are eight short strings (`engine`, `exhaust`, `emissions`, …), so a share is kilobytes rather than megabytes of geometry, and a phone, a browser and an Android Auto head unit can render the same payload differently. Never put mesh data in the payload.
  - The owner sets the **timer**. The payload is deleted when it expires — that is the same expiry as the grant above, expressed as something the owner controls rather than a system default they never see.
  - Revocation ends *access*, not *copies*. Anything already exported or screenshotted is gone — worth being honest about in the UI rather than implying a share can be un-shared.
  - Distinct from **MAINT-2**, which is a generated report handed to a prospective buyer. That is an artifact, not a grant: no account, no revocation, no live data. Do not build a permissions system for something that is a PDF.
  - Depends on **STORE-3** (vehicle records) and **ROLE-1** (identity). Feeds **ROLE-2** (a grantee with mechanic scope gets the mechanic view) and **MKT-3** (the mechanic approval gate assumes a mechanic can see the vehicle at all).

### EPIC: Mobile / PWA
- **MOB-1** — Installable PWA (offline-capable).
- **MOB-2** — React Native app connecting to the Bluetooth OBD adapter directly.

### EPIC: Go Backend Migration
- **GO-0** — *(do this **before** porting anything)* Confirm the Python decoders match an **external** reference. `python-obd` is already a declared dependency and is an independent implementation of the same standard, so diffing its formulas against our nine `REGISTRY` entries is a real oracle; the [Wikipedia OBD-II PIDs table](https://en.wikipedia.org/wiki/OBD-II_PIDs) is the other free cross-check.
  - Why first: **fixture parity between Python and Go proves they agree with each other, not that either is correct.** Port a wrong formula and Go reproduces it faithfully, the golden file agrees with both, and every test is green. Same failure as generating golden values from the decoder under test.
- **GO-1** — Port the PID/DTC decoder to Go. *(skeleton parked in `archive/go-backend`)*
- **GO-2** — Serial client with read-until-`>` framing (`go.bug.st/serial`).
- **GO-3** — WebSocket parity with Python; verify decoders against the shared fixtures.
- **GO-4** — **Shadow-run before cutover.** Go decodes the same live input as Python, outputs are diffed and divergences logged, but **Python's result is what gets served**. Fixtures cover cases we thought of; shadow-running covers the ones we did not — real adapter quirks, manufacturer oddities, malformed frames from a car nobody tested on.
  - Run it until divergences stop appearing, not for a fixed period.
  - **Say what "diffed" means, per field.** A shadow run that compares everything strictly drowns in false positives and stops being read by week two. Classify every field on one axis — **exact, or tolerance-bounded**:
    - *Exact, always:* DTC strings, PID names, units, record counts, the `type` field. `P0302` is `P0302`; a difference here is a bug with no benign explanation.
    - *Tolerance-bounded:* float values, with an epsilon chosen deliberately rather than discovered.
  - **The variance is float precision, not sensor drift.** Both implementations decode the **same bytes**, so a decoder is deterministic — `41 0D 3C` is 60 km/h in Go, in Python and in python-obd, every time. Speed only differs if the two read the car at different moments, and they must not: an ELM327 is single-client and the serial port is exclusive, so two independent readers is not a design that exists. Shadow at the **byte** level, not the reading level, and the whole class of "the car changed between reads" disappears.
  - **The divergence to expect:** `_r1()` (`pids.py:19`) rounds the three percentage PIDs, and **Python's `round()` uses banker's rounding while Go's `math.Round` rounds half away from zero**. At a boundary value those differ. Either replicate the rounding exactly in Go, or widen the tolerance to absorb it — but decide which, because otherwise GO-4 reports the same three PIDs diverging on every cycle from the first frame onward.
  - **A long fixture is for coverage, not latency.** More frames means more byte patterns, and boundaries (`0x00`, `0xFF`) are where rounding and sign errors surface. `tests/test_spec_conformance.py` already samples that way; the Go fixture should match it rather than inventing its own cases.
  - **Measure latency separately from correctness.** Whether Go keeps up is a real question and a different one. Folding it into the value diff means a slow run looks like a wrong run, and the two need different responses.
  - **Live-data variance is OBD-5, not GO-4.** Running against a real car does not measure Go against Python — it measures what an adapter emits that fixtures never do. Same data collection either way; do not let it justify a second live reader.
- **GO-5** — Cutover, with a switch back to Python — **and a date to delete it**.
  - Be precise about what the switch does: it catches Go **crashing or hanging**. It cannot catch Go returning `1725.0` where Python returns `1726.0`, because neither implementation failed — they disagree. Availability is the switch's job; correctness is GO-0's and GO-4's. A fallback with nothing watching for divergence gives false confidence.
  - **Give the switch an expiry when it is added**, same rule as the feature-flag expiry test. Two implementations that must both stay correct is not a migration, it is double maintenance — every new PID goes in twice, every fix goes in twice, and one will get missed. The migration is finished only when the Python decoder is deleted.

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
  - **A second use, from the field** (`docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 6): **mod validation.** An owner collects his own cooling data to check a build is stable *before committing to it*, because mods sourced from Reddit are unvalidated and a DIY is a risk he is deliberately measuring. Same machinery, different question — *does this build run hotter than it did before?*
  - Easier to sell than predictive maintenance, for two reasons: he is **already doing it manually**, so the value is not hypothetical; and someone validating a mod captures a clean **before/after baseline by design**, which softens PRED-6's readiness gate rather than fighting it.
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

---

# Notes moved from the README, 2026-09-11

Design detail that was sitting in the README under *Agentic Diagnosis*, *Marketplace*
and *Future Concepts*. Reasoning rather than roadmap, kept because several are
constraints that would be expensive to rediscover.

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

```

**Recommendation flow:** fault → agent diagnoses + generates recommendation → mechanic reviews (approve/modify/override — quality gate for liability) → customer accepts → books service / orders part. A `source` field (`agent` | `mechanic`) on each recommendation later reveals which performs better.

**Role-differentiated UI:** customers see their car + plain-language diagnoses; mechanics see a fleet of customer vehicles + raw DTCs + full agent reasoning. Plan multi-tenancy into auth from day one — a shop owns many customer vehicles; retrofitting this is painful.

**In-car (future):** Android Auto (CarPlay blocks diagnostic apps). Show a 3D car model with the problem area highlighted, mapped from DTC prefix (`P01/P02`→engine, `P03`→ignition, `P04`→exhaust *or* emissions — see below, `P07/P08`→transmission, `C0`→chassis, `B0`→body, `U0`→network). The `P04` range is "auxiliary emission controls" and is **not** all exhaust hardware, so it splits on the third digit: `P042/P043` (catalyst) and `P047` (exhaust pressure) → exhaust, while `P040` (EGR), `P041` (secondary air) and `P044/P045` (EVAP — the fuel-vapour system, often just a loose fuel cap) → emissions. This matters because the zone also routes the parts catalog (MKT-1): a wrong zone recommends the wrong parts. Render 3D on the phone, push a flat image to the head unit. Recurring same-zone faults over time → a fault heat map on the car body.
