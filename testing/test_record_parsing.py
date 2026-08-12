"""
Parsing tests for the OBD-2 reader microservice.

The reader turns raw ELM327 responses into "transaction" records that flow
downstream (to storage, fault detection, the agent, etc.). This file tests that
transformation: raw hex in -> correct decoded value / DTC list out.

The parser here mirrors the logic the reader microservice uses. Tests validate it
both with explicit cases and against the shared fixture `sample_obd_output.json`,
so the sample output and the parser can never silently drift apart.

Run:
    pytest testing/test_record_parsing.py
    # or, without pytest installed:
    python3 testing/test_record_parsing.py
"""

import json
import os

try:
    import pytest
except ModuleNotFoundError:  # allow `python3 test_record_parsing.py` without pytest
    import contextlib

    class _ApproxShim:
        def __init__(self, expected, tol=1e-6):
            self.expected, self.tol = expected, tol

        def __eq__(self, other):
            return abs(other - self.expected) <= self.tol

    class _MarkShim:
        def parametrize(self, *_args, **_kwargs):
            return lambda fn: fn  # no-op; parametrized tests only run under pytest

    class _PytestShim:
        mark = _MarkShim()

        @staticmethod
        def approx(expected, tol=1e-6):
            return _ApproxShim(expected, tol)

        @staticmethod
        def raises(exc):
            return contextlib.suppress(exc)  # good enough for standalone import

    pytest = _PytestShim()

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_obd_output.json")
RAW_STREAM_PATH = os.path.join(os.path.dirname(__file__), "sample_obd_raw_stream.txt")

# ---------------------------------------------------------------------------
# Parser under test — raw ELM327 response -> decoded value / DTC codes
# ---------------------------------------------------------------------------

def parse_data_bytes(raw: str) -> list[int]:
    """Strip the ELM327 prompt and turn a hex response into a list of ints.

    "41 0C 1A F8 >" -> [0x41, 0x0C, 0x1A, 0xF8]
    """
    cleaned = raw.replace(">", "").strip()
    if not cleaned:
        raise ValueError("empty response")
    return [int(tok, 16) for tok in cleaned.split()]


# Mode 01 PID decoders. Each takes the data bytes (A, B, ...) after the
# 0x41 + PID-echo header and returns the engineering value.
_PID_DECODERS = {
    "0104": lambda d: round(d[0] * 100 / 255, 1),   # engine load %
    "0105": lambda d: d[0] - 40,                     # coolant temp C
    "010C": lambda d: (d[0] * 256 + d[1]) / 4,       # engine RPM
    "010D": lambda d: d[0],                          # vehicle speed km/h
    "010F": lambda d: d[0] - 40,                     # intake air temp C
    "0110": lambda d: (d[0] * 256 + d[1]) / 100,     # MAF air flow g/s
    "0111": lambda d: round(d[0] * 100 / 255, 1),    # throttle position %
    "0114": lambda d: d[0] / 200,                    # O2 sensor voltage V
    "012F": lambda d: round(d[0] * 100 / 255, 1),    # fuel level %
    "0142": lambda d: (d[0] * 256 + d[1]) / 1000,    # control module voltage V
}


def decode_pid(pid: str, raw: str):
    """Decode a Mode 01 PID response into its engineering value.

    Returns None when the ECU reported NO DATA (PID unsupported / no reading).
    Raises ValueError on an unknown PID or malformed frame.
    """
    if "NO DATA" in raw.upper():
        return None
    if pid not in _PID_DECODERS:
        raise ValueError(f"no decoder for PID {pid}")

    ints = parse_data_bytes(raw)
    if len(ints) < 2 or ints[0] != 0x41:
        raise ValueError(f"not a Mode 01 response: {raw!r}")
    data = ints[2:]  # drop 0x41 + PID echo
    if not data:
        raise ValueError(f"no data bytes in response: {raw!r}")
    return _PID_DECODERS[pid](data)


_DTC_LETTERS = ["P", "C", "B", "U"]


def decode_dtcs(raw: str) -> list[str]:
    """Decode a Mode 03 response into a list of DTC strings (e.g. ['P0217'])."""
    ints = parse_data_bytes(raw)
    if not ints or ints[0] != 0x43:
        raise ValueError(f"not a Mode 03 response: {raw!r}")
    body = ints[1:]
    codes = []
    for i in range(0, len(body) - 1, 2):
        b1, b2 = body[i], body[i + 1]
        if b1 == 0 and b2 == 0:
            continue  # 00 00 = padding / no code
        letter = _DTC_LETTERS[(b1 >> 6) & 0x3]
        first_digit = (b1 >> 4) & 0x3
        second_digit = b1 & 0xF
        codes.append(f"{letter}{first_digit}{second_digit:X}{b2:02X}")
    return codes


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

def _load_records():
    with open(SAMPLE_PATH) as fh:
        return json.load(fh)["records"]


def _pid_records():
    return [r for r in _load_records() if r["type"] == "pid"]


def _dtc_records():
    return [r for r in _load_records() if r["type"] == "dtc"]


_HEX = set("0123456789ABCDEFabcdef")


def _is_response_line(line: str) -> bool:
    """True for an ELM327 data-response line (hex byte tokens starting with 41/43)."""
    tokens = line.split()
    if not tokens or tokens[0] not in ("41", "43"):
        return False
    return all(len(t) == 2 and all(c in _HEX for c in t) for t in tokens)


def _extract_responses(text: str) -> list[str]:
    """Pull the raw hex responses out of a serial-stream capture, in order.

    Skips commands, prompts, 'OK', the version banner, and blank lines — leaving
    exactly what the parser consumes.
    """
    return [
        " ".join(line.split()).upper()
        for line in text.splitlines()
        if _is_response_line(line.strip())
    ]


# ---------------------------------------------------------------------------
# Tests — against the shared sample fixture
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("record", _pid_records(), ids=lambda r: f"{r['pid']}:{r['name']}")
def test_pid_record_matches_fixture(record):
    """Every PID record's raw hex decodes to its stated value."""
    decoded = decode_pid(record["pid"], record["raw"])
    assert decoded == pytest.approx(record["value"]), (
        f"{record['name']} ({record['pid']}) raw {record['raw']!r} "
        f"decoded to {decoded}, expected {record['value']}"
    )


@pytest.mark.parametrize("record", _dtc_records(), ids=lambda r: r["raw"])
def test_dtc_record_matches_fixture(record):
    """Every DTC record's raw hex decodes to its stated code list."""
    assert decode_dtcs(record["raw"]) == record["codes"]


# ---------------------------------------------------------------------------
# Tests — explicit cases and edge conditions
# ---------------------------------------------------------------------------

def test_rpm_decoding():
    assert decode_pid("010C", "41 0C 1A F8") == 1726.0


def test_speed_decoding():
    assert decode_pid("010D", "41 0D 3C") == 60


def test_coolant_overheating():
    assert decode_pid("0105", "41 05 9E") == 118


def test_prompt_and_whitespace_are_stripped():
    assert decode_pid("010D", "  41 0D 3C \r\r> ") == 60


def test_multiple_dtcs():
    assert decode_dtcs("43 01 71 03 02") == ["P0171", "P0302"]


def test_no_active_dtcs():
    assert decode_dtcs("43 00") == []


def test_no_data_returns_none():
    assert decode_pid("010C", "NO DATA") is None


def test_unknown_pid_raises():
    with pytest.raises(ValueError):
        decode_pid("01FF", "41 FF 00")


def test_wrong_mode_byte_raises():
    with pytest.raises(ValueError):
        decode_pid("010C", "7F 0C 12")  # 0x7F = negative response, not 0x41


# ---------------------------------------------------------------------------
# Correlation — the raw ASCII stream and the JSON fixture must stay in sync
# ---------------------------------------------------------------------------

def test_raw_stream_responses_match_fixture_order():
    """Responses extracted from the raw serial capture equal the fixture `raw`
    fields, in the same order — so the two sample files can't drift apart."""
    with open(RAW_STREAM_PATH) as fh:
        responses = _extract_responses(fh.read())
    fixture_raws = [r["raw"].upper() for r in _load_records()]
    assert responses == fixture_raws


def test_raw_stream_responses_decode_to_fixture_values():
    """Each raw response, decoded, reproduces the fixture's value / codes."""
    with open(RAW_STREAM_PATH) as fh:
        responses = _extract_responses(fh.read())
    for raw, record in zip(responses, _load_records()):
        if record["type"] == "pid":
            assert decode_pid(record["pid"], raw) == pytest.approx(record["value"])
        else:
            assert decode_dtcs(raw) == record["codes"]


# ---------------------------------------------------------------------------
# Runnable without pytest
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    passed = 0
    for rec in _pid_records():
        got = decode_pid(rec["pid"], rec["raw"])
        assert abs(got - rec["value"]) < 1e-6, f"{rec['pid']}: {got} != {rec['value']}"
        passed += 1
    for rec in _dtc_records():
        assert decode_dtcs(rec["raw"]) == rec["codes"], rec["raw"]
        passed += 1

    with open(RAW_STREAM_PATH) as fh:
        responses = _extract_responses(fh.read())
    fixture_raws = [r["raw"].upper() for r in _load_records()]
    assert responses == fixture_raws, "raw stream does not match JSON fixture order"

    print(f"OK — {passed} fixture records parsed correctly")
    print(f"OK — raw stream: {len(responses)} responses correlate 1:1 with the JSON fixture")
