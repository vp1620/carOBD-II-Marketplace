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
