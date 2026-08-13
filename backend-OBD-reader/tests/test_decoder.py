"""Package-level decode tests. Mirrors testing/test_record_parsing.py against the
obd_reader package API. Runs standalone (no pytest) or under pytest."""

import os
import sys

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
from obd_reader.reader import FixtureReader


def test_rpm():
    assert decode_pid("010C", "41 0C 1A F8") == 1726.0


def test_speed():
    assert decode_pid("010D", "41 0D 3C") == 60


def test_coolant_overheating():
    assert decode_pid("0105", "41 05 9E") == 118


def test_prompt_stripped():
    assert decode_pid("010D", " 41 0D 3C \r\r> ") == 60


def test_dtc_single():
    assert decode_dtcs("43 02 17") == ["P0217"]


def test_dtc_multiple():
    assert decode_dtcs("43 01 71 03 02") == ["P0171", "P0302"]


def test_no_active_dtcs():
    assert decode_dtcs("43 00") == []


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
