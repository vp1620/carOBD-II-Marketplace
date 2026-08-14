"""Tests for obd_reader.faults. Runs standalone (python3 tests/test_faults.py) or
under pytest. No pytest features are required, so no shim is needed here."""

import os
import sys

# Why: make the package importable when the test is run directly from tests/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from obd_reader.faults import describe, severity_for, zone_for


def test_describe_known_critical():
    d = describe("P0217")
    assert d["severity"] == "critical"
    assert d["zone"] == "engine"
    assert d["deferrable"] is False
    assert "over-temperature" in d["description"].lower()


def test_describe_unknown_is_graceful():
    d = describe("P0XYZ")  # not a real code — must not raise
    assert d["code"] == "P0XYZ"
    assert d["severity"] == "info"
    assert d["deferrable"] is True
    assert d["description"]  # non-empty generic text


def test_zone_prefixes():
    assert zone_for("P0420") == "exhaust"
    assert zone_for("P0700") == "transmission"
    assert zone_for("P0302") == "ignition"
    assert zone_for("C0035") == "chassis"
    assert zone_for("U0100") == "network"
    assert zone_for("B0001") == "body"
    assert zone_for("P0171") == "engine"


def test_severity_levels():
    assert severity_for("P0087") == "critical"
    assert severity_for("P0171") == "warning"
    assert severity_for("P0000") == "info"


def test_misfire_code_described():
    assert "Cylinder 2" in describe("P0302")["description"]


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
