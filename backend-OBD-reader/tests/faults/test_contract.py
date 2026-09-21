"""Contract tests for obd_reader.faults — guarantees, not mappings.

The split from test_golden.py is deliberate, and it is about what a red test *tells* you:

  test_golden.py   "a mapping is wrong"  — this code should land in that zone
  test_contract.py "a guarantee broke"   — describe() raised, or returned a half-record

Mappings belong in data (cases/*.json) because there are eventually thousands of them and
they are all the same shape. Guarantees belong here because they are about behaviour and
shape — "does not raise", "returns every key", "degrades instead of failing" — none of
which a value-comparison table can express. Encoded as a golden case, "must not raise"
would silently pass the moment the function started returning a constant.

Runs standalone (python3 tests/faults/test_contract.py) or under pytest.
"""

import os
import sys

# Why: make the package importable when the test is run directly from its folder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from obd_reader.faults import describe, severity_for, zone_for

# The full record every caller is entitled to. Why pinned here and not in a case file:
# a case only checks the fields it names, so no number of cases can notice a *missing*
# key. This is the one place the shape itself is asserted.
EXPECTED_KEYS = {"code", "description", "severity", "zone", "deferrable"}


def test_describe_returns_the_complete_record():
    """Every call returns all five fields with usable types.

    Why: the dashboard and the agent both destructure this record. A dropped or renamed
    key would surface as a KeyError in the UI at runtime rather than here, and the golden
    cases cannot catch it — they only look at fields they explicitly name.
    """
    d = describe("P0217")
    missing = EXPECTED_KEYS - set(d)
    assert not missing, f"describe() is missing {sorted(missing)}; returned {sorted(d)}"
    assert isinstance(d["code"], str)
    assert isinstance(d["description"], str) and d["description"]
    assert d["severity"] in {"critical", "warning", "info"}, f"bad severity {d['severity']!r}"
    assert isinstance(d["zone"], str) and d["zone"]
    assert isinstance(d["deferrable"], bool), f"deferrable must be a bool, got {type(d['deferrable'])}"


def test_uncatalogued_code_degrades_instead_of_failing():
    """A code we have never seen still produces a usable record.

    Why: cars report codes we have not catalogued — every manufacturer-specific code
    today (DIAG-3), and anything added to the standard since. The live feed has to keep
    working and show the driver *something*, so this must never be an error path.
    """
    d = describe("P0XYZ")
    assert d["code"] == "P0XYZ", "the raw code must survive so the driver can look it up"
    assert d["description"], "an uncatalogued code still needs text to show"
    assert d["severity"] == "info", "no catalogued judgement means no urgency claim"
    assert d["deferrable"] is True


def test_odd_input_never_raises():
    """Garbage in, a zone string out — never an exception.

    Why: zone_for() runs on whatever the ECU reports, inside the poll loop. One
    malformed frame must not take down the live feed for every other reading. The
    truncated case is the specific one that bit us: "P04" has no third digit, so an
    index would raise where a slice does not.
    """
    for bad in ("", "P04", "P0XYZ", "?", "NO DATA", "p0442"):
        try:
            got = zone_for(bad)
        except Exception as exc:                      # noqa: BLE001 — that is the point
            raise AssertionError(f"zone_for({bad!r}) raised {type(exc).__name__}: {exc}") from exc
        assert isinstance(got, str) and got, f"zone_for({bad!r}) returned {got!r}"


def test_severity_never_raises_and_stays_in_range():
    """severity_for() answers for any string, always with a known level.

    Why: severity drives UI colour. An unexpected value means a fault renders with no
    styling at all — visually indistinguishable from "fine".
    """
    for code in ("P0217", "P0XYZ", "", "U0100"):
        assert severity_for(code) in {"critical", "warning", "info"}


def test_catalog_is_actually_wired_up():
    """A catalogued code gets its real description, not the generic fallback.

    Why this is a contract and not a mapping: it does not assert *what* P0217 says —
    that is the catalog's business and would be tautological here. It asserts that the
    lookup path reaches the catalog at all. If the data file went missing, moved, or
    failed to parse, every code would quietly fall back to "unrecognized" and the golden
    cases would still pass, because they only check zone and severity.
    """
    catalogued = describe("P0217")["description"]
    unknown = describe("P0XYZ")["description"]
    assert catalogued != unknown, (
        "P0217 returned the same text as an uncatalogued code — the catalog is not being "
        "read. Check data/dtc_generic.json exists and parses."
    )


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
