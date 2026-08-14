"""Golden-file decode test for the obd_reader package.

Rather than hard-coding decode inputs/outputs inline, this drives the decoder
from the committed serial capture (testing/sample_obd_raw_stream.txt), writes the
decoded result to a real file, and asserts that file matches the golden fixture
(testing/sample_obd_output.json). This means the test exercises the same path a
real capture takes and can never silently drift from the shared fixtures.

Only the decoder-owned fields are compared; `timestamp` and `vehicle_id` are
runtime metadata the reader stamps (not derivable from a raw capture), so they
are excluded from the golden comparison.

Runs standalone (`python3 tests/test_decoder.py`) or under pytest.
"""

import json
import os
import sys
import tempfile

try:
    import pytest
except ModuleNotFoundError:  # allow standalone `python3 tests/test_decoder.py`
    import contextlib

    class _PytestShim:
        @staticmethod
        def raises(exc):
            return contextlib.suppress(exc)

    pytest = _PytestShim()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from obd_reader.decoder import NoData, decode_pid
from obd_reader.reader import FixtureReader
from obd_reader.stream import decode_stream  # the shared raw-capture -> records step

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_STREAM_PATH = os.path.join(_REPO_ROOT, "testing", "sample_obd_raw_stream.txt")
GOLDEN_PATH = os.path.join(_REPO_ROOT, "testing", "sample_obd_output.json")

# Fields the decoder is actually responsible for producing. timestamp/vehicle_id
# are deliberately excluded — they are reader runtime metadata, not decode output.
_DECODER_FIELDS = ("type", "pid", "name", "raw", "value", "unit", "codes")


def _project(record: dict) -> dict:
    """Keep only decoder-owned fields, so generated and golden records compare
    on what the decoder actually produces."""
    return {k: record[k] for k in _DECODER_FIELDS if k in record}


# ---------------------------------------------------------------------------
# Golden-file test — decode the raw capture, write it out, diff vs the fixture
# ---------------------------------------------------------------------------

def test_decoded_stream_matches_golden_file():
    """Decoding sample_obd_raw_stream.txt and writing it to a file reproduces
    sample_obd_output.json (on decoder-owned fields)."""
    with open(RAW_STREAM_PATH) as fh:
        generated = {"records": decode_stream(fh.read())}

    # Write the decoder output to a real file, then read it back and diff — this
    # is the "file created == golden file" check, not just an in-memory compare.
    out_path = os.path.join(tempfile.mkdtemp(), "sample_obd_output.json")
    with open(out_path, "w") as fh:
        json.dump(generated, fh, indent=2)

    with open(out_path) as fh:
        got = [_project(r) for r in json.load(fh)["records"]]
    with open(GOLDEN_PATH) as fh:
        want = [_project(r) for r in json.load(fh)["records"]]

    assert got == want, _diff(want, got)


def _diff(want: list[dict], got: list[dict]) -> str:
    """Readable first-mismatch report for a failed golden comparison."""
    if len(want) != len(got):
        return f"record count differs: golden {len(want)} vs generated {len(got)}"
    for i, (w, g) in enumerate(zip(want, got)):
        if w != g:
            return f"record {i} differs:\n  golden:    {w}\n  generated: {g}"
    return "records differ"


# ---------------------------------------------------------------------------
# Edge cases the golden fixture can't express (error paths, robustness)
# ---------------------------------------------------------------------------

def test_prompt_and_whitespace_are_stripped():
    assert decode_pid("010D", " 41 0D 3C \r\r> ") == 60


def test_no_data_raises():
    with pytest.raises(NoData):
        decode_pid("010C", "NO DATA")


def test_unknown_pid_raises():
    with pytest.raises(ValueError):
        decode_pid("01FF", "41 FF 00")


def test_fixture_reader_cycles():
    r = FixtureReader()
    first = r.poll_once()
    assert first and first[0].vehicle_id == "veh_fixture"
    for _ in range(20):
        assert r.poll_once()


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
