# PR 1 — Backend OBD Reader

**Branch:** `phase1-start-site` → `main`
**Goal:** Turn the loose `python-obd` snippet into a real, tested package that reads
and decodes OBD-2 data into structured records. Headless — no server or UI yet
(those are PRs 3–4). This is the foundation everything else plugs into.

## Why this PR exists
Phase 1 needs one reliable "read a car → produce clean data records" engine that
the WebSocket server and dashboard (later PRs) can consume without caring whether
the data comes from a real adapter or a saved sample. This PR builds that engine
and locks its correctness in with tests before anything depends on it.

## Key terms (read this first if you're new to OBD)
Plain-language definitions for the jargon used below:

- **OBD-II** — the standard diagnostics system built into every modern car. You plug a reader into the port under the dashboard to get sensor values and fault codes.
- **PID (Parameter ID)** — a numeric code for one specific reading. You ask the car for a PID and it replies with a value. Example: `010C` = engine RPM.
- **DTC (Diagnostic Trouble Code)** — a fault code the car sets when something is wrong. Example: `P0217` = engine overheating.
- **ELM327** — the common small adapter/chip that sits between the car's OBD-II port and your computer and passes messages over a serial (USB/Bluetooth) connection.
- **Mode 01 / Mode 03** — two request types in the OBD-II protocol. Mode 01 = "give me a live sensor value" (PIDs); Mode 03 = "give me the stored fault codes" (DTCs).
- **hex** — base-16 numbers (digits `0`–`9` then `A`–`F`). The car's responses arrive as hex bytes that we decode into real values.
- **fixture** — a saved sample of real data, so we can build and test the code with no car plugged in.
- **golden-file test** — a test that runs the code, produces an output file, and compares it to a known-correct "golden" file. If they differ, the test fails. This catches accidental changes to the output.
- **Gherkin / BDD (Behaviour-Driven Development)** — plain-English test scenarios written as `Given` / `When` / `Then` steps in `.feature` files.
- **WebSocket** — a always-open, two-way connection between server and browser, used in a later PR to push live readings to the page without it re-requesting.

## Review guide — click through the changes
Suggested reading order (each link opens the file):

| # | File | What it adds & why |
|---|------|--------------------|
| 1 | [`obd_reader/pids.py`](../../backend-OBD-reader/obd_reader/pids.py) | The PID registry + decode formulas. The single source of "what each sensor code means," so the decoder and future UI never hardcode formulas. |
| 2 | [`obd_reader/decoder.py`](../../backend-OBD-reader/obd_reader/decoder.py) | `decode_pid` / `decode_dtcs` — turn the raw hex the car sends back into real values (e.g. `1726.0` rpm) and fault codes (e.g. `P0217`). The logic was copied straight from an older file that already had passing tests (`testing/test_record_parsing.py`), so it's known-good rather than newly written. |
| 3 | [`obd_reader/models.py`](../../backend-OBD-reader/obd_reader/models.py) | The `Reading` record — the one data shape that flows downstream. Matches `testing/sample_obd_output.json` so storage/UI stay consistent. |
| 4 | [`obd_reader/reader.py`](../../backend-OBD-reader/obd_reader/reader.py) | `FixtureReader` (replays sample data, no car) + `SerialReader` (real adapter) behind a common `poll_once()`. Lets every later layer run offline or live without changing code. |
| 5 | [`obd_reader/stream.py`](../../backend-OBD-reader/obd_reader/stream.py) | `decode_stream` — turns a raw serial capture into decoded records. The reusable step shared by the golden-file test and the future Gherkin/BDD scenarios, so the parse-and-decode logic lives in exactly one place. |
| 6 | [`obd_reader/__init__.py`](../../backend-OBD-reader/obd_reader/__init__.py) | Marks the folder as an importable Python package and exposes the public pieces (so other code can `from obd_reader import ...`). |
| 7 | [`tests/test_decoder.py`](../../backend-OBD-reader/tests/test_decoder.py) | Golden-file test: decodes `testing/sample_obd_raw_stream.txt` via `decode_stream`, writes the result to a file, and diffs it against `testing/sample_obd_output.json` — inputs are no longer hard-coded and the two sample files can't silently fall out of sync. Plus a few tests for error cases (bad frame, unknown code, no data). Runs on its own with `python3` or under pytest. |
| 8 | [`BACKLOG.md`](../../BACKLOG.md) | Marks the decoder/fixture stories done and adds the storage/anomaly stories (STORE-4, PRED-3–7) that this reader engine will later feed. |
| 9 | [`.gitignore`](../../.gitignore) | Excludes `__pycache__`, `.DS_Store`, venvs, `.env`. Also untracks the committed `.DS_Store`. |

## Data flow (≠ the reading order above)
The review order above is **dependency-first** (foundations before the code that
uses them), *not* the path a reading actually travels. At runtime the flow is:

```
Live path (SerialReader):
  ELM327 adapter → reader.py (raw hex in) → decoder.py (parse/validate)
                 → pids.py (formula lookup) → models.py (Reading) → downstream

Fixture/test path (offline):
  sample_obd_raw_stream.txt → stream.py: decode_stream → decoder.py + pids.py
                            → records → diff vs sample_obd_output.json
```

Notes: `pids.py` is a lookup *called by* the decoder, not a separate stage;
DTCs skip `pids.py` entirely (`decode_dtcs` needs no registry); `stream.py` is
**not** in the live path — it's the recorded-capture entry used by the test.

## Testing approach — file-driven, Gherkin-ready
The decode test is intentionally **golden-file** rather than hard-coded: raw capture in
(`sample_obd_raw_stream.txt`) → decode → generated file → diff against the expected
fixture (`sample_obd_output.json`). The raw→records transform lives in `stream.py` as a
single importable step so a later Gherkin/BDD layer (`Given` a capture / `When` decoded /
`Then` it matches the fixture) reuses it without duplicating parsing logic. Only
decoder-owned fields are compared; `timestamp`/`vehicle_id` are runtime reader metadata,
not decode output, so they're excluded.

## How to verify
```bash
cd backend-OBD-reader
python3 tests/test_decoder.py     # -> 5/5 passed (no pytest needed)
```

## Not in this PR (coming next)
- PR 2 `feat/fault-detection` — DTC → plain-language + severity
- PR 3 `feat/websocket-server` — stream readings over `/ws`
- PR 4 `feat/web-dashboard` — live browser dashboard
