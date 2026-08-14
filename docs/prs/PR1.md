# PR 1 — Backend OBD Reader

**Branch:** `phase1-start-site` → `main`
**Goal:** Turn the loose `python-obd` snippet into a real, tested package that reads
and decodes OBD-2 data into structured records. Headless — no server or UI yet
(those are PRs 3–4). This is the foundation everything else plugs into.

## Why this PR exists
Phase 1 needs one reliable "read a car → produce clean data records" engine that
the WebSocket server and dashboard can consume without caring whether the data
comes from a real adapter or a fixture. This PR builds that engine and locks its
correctness in with tests before anything depends on it.

## Review guide — click through the changes
Suggested reading order (each link opens the file):

| # | File | What it adds & why |
|---|------|--------------------|
| 1 | [`obd_reader/pids.py`](../../backend-OBD-reader/obd_reader/pids.py) | The PID registry + decode formulas. The single source of "what each sensor code means," so the decoder and future UI never hardcode formulas. |
| 2 | [`obd_reader/decoder.py`](../../backend-OBD-reader/obd_reader/decoder.py) | `decode_pid` / `decode_dtcs` — turns raw ELM327 hex into values and fault codes. Ported verbatim from the already-validated `testing/test_record_parsing.py`, so behavior is proven. |
| 3 | [`obd_reader/models.py`](../../backend-OBD-reader/obd_reader/models.py) | The `Reading` record — the one data shape that flows downstream. Matches `testing/sample_obd_output.json` so storage/UI stay consistent. |
| 4 | [`obd_reader/reader.py`](../../backend-OBD-reader/obd_reader/reader.py) | `FixtureReader` (replays sample data, no car) + `SerialReader` (real adapter) behind a common `poll_once()`. Lets every later layer run offline or live without changing code. |
| 5 | [`obd_reader/stream.py`](../../backend-OBD-reader/obd_reader/stream.py) | `decode_stream` — turns a raw serial capture into decoded records. The reusable step shared by the golden-file test and the future Gherkin/BDD scenarios, so the parse-and-decode logic lives in exactly one place. |
| 6 | [`tests/test_decoder.py`](../../backend-OBD-reader/tests/test_decoder.py) | Golden-file test: decodes `testing/sample_obd_raw_stream.txt` via `decode_stream`, writes the result to a file, and diffs it against `testing/sample_obd_output.json` — inputs are no longer hard-coded and the two fixtures can't silently drift. Plus error-path edge cases. Runs standalone or under pytest. |
| 7 | [`.gitignore`](../../.gitignore) | Excludes `__pycache__`, `.DS_Store`, venvs, `.env`. Also untracks the committed `.DS_Store`. |

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
