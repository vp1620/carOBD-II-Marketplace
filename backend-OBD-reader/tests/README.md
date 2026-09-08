# Tests

One folder per feature. Each holds the tests for that feature and, where it has them,
the fixtures they read.

```
tests/
├── decoder/            raw ELM327 bytes → Reading records
│   └── test_decoder.py
└── faults/             DTC → description / severity / zone
    ├── test_golden.py      mappings, driven by cases/
    ├── test_contract.py    guarantees
    └── cases/              one JSON file per scenario
```

## Two kinds of test, and why they are separate files

| | asserts | a failure means |
|---|---|---|
| `test_golden.py` | **mappings** — this code lands in that zone, at that severity | a mapping is wrong |
| `test_contract.py` | **guarantees** — never raises, returns every key, degrades instead of failing | a guarantee broke |

Keeping them apart means a red run tells you *which kind* of thing broke without reading
the test. It also matters technically: a guarantee like "must not raise" cannot be
expressed as a value comparison — written as a golden case it would silently pass the
moment the function started returning a constant.

**Adding a mapping is a new JSON file** in `cases/`, not a new test function. Adding a
guarantee is a new function in `test_contract.py`. See `faults/cases/README.md` for the
case format and the rule about never generating expected values from the code under test.

## Why fixtures are co-located — except one

`faults/cases/` sits beside the test that reads it because nothing else reads it.

`test_files/sample_obd_output.json` at the repo root **cannot move here**, even though
the decoder golden test uses it: `reader.py`'s `FixtureReader` loads it at runtime to
replay readings with no car attached. It is production input as well as test data, and
production code must not depend on a test directory. `test_files/README.md` says the
same thing next to the file.

## Running them

```bash
# everything, via pytest
.venv/bin/python -m pytest backend-OBD-reader/tests -q

# one feature
.venv/bin/python -m pytest backend-OBD-reader/tests/faults -q

# no pytest installed — every file runs standalone
cd backend-OBD-reader && python3 tests/faults/test_golden.py
```

The standalone runners exist so the suite works on a clean machine with nothing
installed, which is the same property that lets the decoder tests run with no car
attached (OBD-4).

## Adding a feature folder

Create `tests/<feature>/` with an `__init__.py`. **The `__init__.py` is not optional** —
without it, two folders each containing a `test_golden.py` collide during pytest
collection, because both import as the same top-level module name.
