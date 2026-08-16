"""Golden-file test for the obd_reader package — driven through the LIVE path.

Instead of hard-coding decode inputs/outputs, this replays a recorded ELM327
capture (testing/sample_obd_raw_stream.txt) through the *real* SerialReader, writes
the decoded result to a file, and asserts that file matches the golden fixture
(testing/sample_obd_output.json). "Golden-file" = we compare fresh output against a
known-correct committed file; if they differ, the test fails.

Why a FakeSerial instead of stream.py: the reader talks to the adapter through a
serial port object (write the request, read_until the ">" prompt). FakeSerial is a
dumb stand-in for that port that ignores the request and returns the next recorded
response chunk. So the test exercises the SAME code a real car drives —
SerialReader.connect/_command -> decoder -> Reading — not a parallel parser that
could silently drift from it. (This is what let us delete the old stream.py.)

timestamp/vehicle_id are stamped by the reader at runtime and are non-deterministic,
so they are excluded from the golden comparison.

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

from obd_reader.decoder import NoData, decode_dtcs, decode_pid
from obd_reader.reader import FixtureReader, SerialReader

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_STREAM_PATH = os.path.join(_REPO_ROOT, "testing", "sample_obd_raw_stream.txt")
GOLDEN_PATH = os.path.join(_REPO_ROOT, "testing", "sample_obd_output.json")

# The scripted session recorded in sample_obd_raw_stream.txt: one Mode 01 sweep of
# these 9 PIDs (in this order), then 3 Mode 03 fault-code reads. The PID order must
# match the capture, because FakeSerial replays responses positionally.
CAPTURE_PIDS = ["010C", "010D", "0105", "0111", "0110", "0114", "0142", "0105", "010C"]
CAPTURE_DTC_READS = 3

# Reader stamps these per reading at runtime; not derivable from a capture, so they
# are excluded from the golden comparison.
_RUNTIME_FIELDS = ("timestamp", "vehicle_id")


class FakeSerial:
    """Minimal stand-in for a pyserial port that REPLAYS a recorded capture.

    It ignores what is written and, on each read_until, returns the next chunk of
    the capture up to and including the ">" prompt — a dumb, positional byte replay.
    This is the seam that lets the offline test run the real SerialReader without
    any hardware or pyserial installed.
    """

    def __init__(self, capture: bytes):
        self._buf = capture
        self._pos = 0

    def write(self, data: bytes) -> int:
        return len(data)  # request ignored; replay is positional, not request-matched

    def read_until(self, expected: bytes = b">") -> bytes:
        idx = self._buf.find(expected, self._pos)
        end = len(self._buf) if idx == -1 else idx + len(expected)
        chunk = self._buf[self._pos:end]
        self._pos = end
        return chunk


def _emitted(reading) -> dict:
    """A reader Reading reduced to its deterministic, golden-comparable fields."""
    return {k: v for k, v in reading.to_dict().items() if k not in _RUNTIME_FIELDS}


# ---------------------------------------------------------------------------
# Golden-file test — replay the capture through the real reader, write it out,
# diff against the committed fixture.
# ---------------------------------------------------------------------------

def test_reader_live_path_matches_golden_file():
    """Replaying sample_obd_raw_stream.txt through SerialReader and writing the
    result to a file reproduces sample_obd_output.json (on deterministic fields)."""
    with open(RAW_STREAM_PATH, "rb") as fh:
        capture = fh.read()

    reader = SerialReader(port="fake", pids=CAPTURE_PIDS, transport=FakeSerial(capture))
    readings = reader.poll_once()  # 9 Mode 01 sensor readings
    for _ in range(CAPTURE_DTC_READS):
        readings += reader.poll_dtcs()  # 3 Mode 03 fault-code reads

    # Write to a real file, read it back, then diff — the literal "the file the
    # reader produced == the golden file" check, not just an in-memory compare.
    out_path = os.path.join(tempfile.mkdtemp(), "sample_obd_output.json")
    with open(out_path, "w") as fh:
        json.dump({"records": [_emitted(r) for r in readings]}, fh, indent=2)

    with open(out_path) as fh:
        got = json.load(fh)["records"]
    with open(GOLDEN_PATH) as fh:
        want = json.load(fh)["records"]

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
# Edge cases the golden capture can't express (error paths, DTC decoding, robustness)
# ---------------------------------------------------------------------------

def test_prompt_and_whitespace_are_stripped():
    assert decode_pid("010D", " 41 0D 3C \r\r> ") == 60


def test_no_data_raises():
    with pytest.raises(NoData):
        decode_pid("010C", "NO DATA")


def test_unknown_pid_raises():
    with pytest.raises(ValueError):
        decode_pid("01FF", "41 FF 00")


def test_dtc_decoding():
    # The same decoder poll_dtcs() uses: one code, multiple codes, and the
    # explicit "no active faults" case (empty list, not an error).
    assert decode_dtcs("43 02 17") == ["P0217"]
    assert decode_dtcs("43 01 71 03 02") == ["P0171", "P0302"]
    assert decode_dtcs("43 00") == []


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
