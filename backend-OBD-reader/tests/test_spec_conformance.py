"""Check the decoder against the OBD-II standard, not against itself.

The golden-file test proves the reader still does what it used to do. It cannot prove
the formulas are *right*: regenerate the fixture from a wrong decoder and the golden
test goes green while every reading is wrong. `1726` and `1732` both look like RPM.

So this file re-implements the SAE J1979 formulas independently and asserts the decoder
agrees. Two implementations of the same published standard, written from the standard
rather than from each other — if they disagree, one of them is wrong and you go read
J1979 to find out which.

Why the duplication is deliberate here, when duplication is normally the enemy: an
oracle has to be independent of the thing it checks. Importing `pids.REGISTRY` would
make this file assert that the decoder equals itself, which is always true and proves
nothing. That is the same rule DECISIONS.md records as "expected values must never be
generated from the code under test".

**If you change a formula in pids.py, do NOT copy the change here.** Look it up in the
standard and write it again. A test you edit to match the code has stopped being a test.
"""

import pytest

from obd_reader.decoder import decode_dtcs, decode_pid
from obd_reader.pids import REGISTRY

# SAE J1979 Mode 01. `d` is the data bytes with the 0x41 marker and PID echo removed.
# Sources: SAE J1979 / ISO 15031-5. Cross-checkable against the Wikipedia "OBD-II PIDs"
# table, which lists the same formulas.
J1979 = {
    "0104": ("engine_load",            "percent", lambda d: round(d[0] * 100 / 255, 1)),
    "0105": ("coolant_temp",           "C",       lambda d: d[0] - 40),
    "010C": ("engine_rpm",             "rpm",     lambda d: (d[0] * 256 + d[1]) / 4),
    "010D": ("vehicle_speed",          "km/h",    lambda d: float(d[0])),
    "010F": ("intake_air_temp",        "C",       lambda d: d[0] - 40),
    "0110": ("maf_air_flow",           "g/s",     lambda d: (d[0] * 256 + d[1]) / 100),
    "0111": ("throttle_position",      "percent", lambda d: round(d[0] * 100 / 255, 1)),
    "0114": ("o2_sensor_voltage",      "V",       lambda d: d[0] / 200),
    "012F": ("fuel_level",             "percent", lambda d: round(d[0] * 100 / 255, 1)),
    "0142": ("control_module_voltage", "V",       lambda d: (d[0] * 256 + d[1]) / 1000),
}

# Byte patterns per PID. Boundaries matter more than typical values: 0x00 and 0xFF are
# where an off-by-one or a sign error shows up, and a mid-range value catches scaling.
SAMPLES = {
    1: [(0x00,), (0x7F,), (0xFF,)],
    2: [(0x00, 0x00), (0x1A, 0xF8), (0xFF, 0xFF)],
}


def _frame(pid: str, data: tuple[int, ...]) -> str:
    """Build the Mode 01 response an adapter would send for these data bytes."""
    return " ".join(f"{b:02X}" for b in (0x41, int(pid[2:], 16), *data))


def _arity(pid: str) -> int:
    """How many data bytes this PID's formula reads."""
    return 2 if pid in ("010C", "0110", "0142") else 1


@pytest.mark.parametrize("pid", sorted(J1979))
def test_decoder_matches_j1979(pid):
    """decode_pid() reproduces the standard's formula across the byte range."""
    name, unit, formula = J1979[pid]
    for data in SAMPLES[_arity(pid)]:
        raw = _frame(pid, data)
        expected = formula(list(data))
        actual = decode_pid(pid, raw)
        assert actual == expected, (
            f"{pid} ({name}) decoded {raw!r} as {actual} {unit}; "
            f"SAE J1979 gives {expected} {unit}. "
            f"One of pids.py or this file's formula is wrong — check the standard."
        )


@pytest.mark.parametrize("pid", sorted(J1979))
def test_registry_metadata_matches_j1979(pid):
    """The name and unit attached to each PID match the standard's quantity."""
    name, unit, _ = J1979[pid]
    entry = REGISTRY[pid]
    assert entry.name == name, f"{pid}: registry calls it {entry.name!r}, J1979 is {name!r}"
    assert entry.unit == unit, f"{pid}: registry unit {entry.unit!r}, J1979 is {unit!r}"


def test_every_registered_pid_has_a_spec_check():
    """A PID added to REGISTRY without an entry here would go unverified.

    Why this exists: the risk is not a wrong formula, it is a formula nobody checked.
    Adding a PID is easy; remembering to write its independent oracle is not.
    """
    unchecked = set(REGISTRY) - set(J1979)
    assert not unchecked, (
        f"PIDs in REGISTRY with no J1979 cross-check: {sorted(unchecked)}. "
        f"Look the formula up in the standard and add it above — do not copy it "
        f"from pids.py, that defeats the point."
    )


# --- SAE J2012: DTC bit layout ------------------------------------------------------
# The first byte packs the system letter and the first two digits:
#   bits 7-6 -> P/C/B/U    bits 5-4 -> first digit    bits 3-0 -> second digit
# The second byte is the last two digits, read straight as hex.

def _encode_dtc(code: str) -> tuple[int, int]:
    """Build the two bytes an ECU would send for a DTC string, per J2012."""
    letter = "PCBU".index(code[0]) << 6
    first = int(code[1]) << 4
    second = int(code[2], 16)
    return letter | first | second, int(code[3:5], 16)


@pytest.mark.parametrize("code", [
    "P0217",  # powertrain, the fixture's overheat code
    "P0300",  # powertrain, misfire
    "C0035",  # chassis  — exercises the letter bits
    "B0001",  # body     — exercises the letter bits
    "U0100",  # network  — exercises the letter bits
    "P3FFF",  # boundary: every digit at maximum
])
def test_dtc_decoding_matches_j2012(code):
    """decode_dtcs() inverts the J2012 bit packing for every system letter."""
    b1, b2 = _encode_dtc(code)
    raw = f"43 {b1:02X} {b2:02X}"
    assert decode_dtcs(raw) == [code], (
        f"encoded {code} as {raw!r} per SAE J2012; decoder returned "
        f"{decode_dtcs(raw)}. Check the bit shifts in decoder.py:decode_dtcs."
    )


def test_dtc_padding_is_skipped_not_decoded():
    """0x0000 is the ECU's padding, not a real code.

    Mode 03 responses are padded to a fixed length, so a car with one fault still sends
    trailing zero pairs. Decoding them would invent a P0000 that the ECU never reported.
    """
    b1, b2 = _encode_dtc("P0217")
    assert decode_dtcs(f"43 {b1:02X} {b2:02X} 00 00") == ["P0217"]
