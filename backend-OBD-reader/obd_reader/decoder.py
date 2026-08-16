"""Decode raw ELM327 responses into values and DTC codes.

Pure decode logic (no I/O), verified by backend-OBD-reader/tests/test_decoder.py
against the shared golden fixture (testing/sample_obd_output.json).
"""

from .pids import REGISTRY


class NoData(Exception):
    """The ECU reported NO DATA (PID unsupported / no reading)."""


def parse_data_bytes(raw: str) -> list[int]:
    """"41 0C 1A F8 >" -> [0x41, 0x0C, 0x1A, 0xF8]."""
    cleaned = raw.replace(">", "").strip()
    if not cleaned:
        raise ValueError("empty response")
    return [int(tok, 16) for tok in cleaned.split()]


def decode_pid(pid: str, raw: str) -> float:
    """Decode a Mode 01 response into its engineering value.

    Raises NoData when the ECU had no reading, ValueError on unknown PID / bad frame.
    """
    if "NO DATA" in raw.upper():
        raise NoData(pid)
    if pid not in REGISTRY:
        raise ValueError(f"no decoder for PID {pid}")
    ints = parse_data_bytes(raw)
    if len(ints) < 2 or ints[0] != 0x41:
        raise ValueError(f"not a Mode 01 response: {raw!r}")
    data = ints[2:]  # drop 0x41 + PID echo
    if not data:
        raise ValueError(f"no data bytes: {raw!r}")
    return REGISTRY[pid].decode(data)


_DTC_LETTERS = ["P", "C", "B", "U"]


def decode_dtcs(raw: str) -> list[str]:
    """Decode a Mode 03 response into DTC strings, e.g. ['P0217']."""
    ints = parse_data_bytes(raw)
    if not ints or ints[0] != 0x43:
        raise ValueError(f"not a Mode 03 response: {raw!r}")
    body = ints[1:]
    codes = []
    for i in range(0, len(body) - 1, 2):
        b1, b2 = body[i], body[i + 1]
        if b1 == 0 and b2 == 0:
            continue
        letter = _DTC_LETTERS[(b1 >> 6) & 0x3]
        first = (b1 >> 4) & 0x3
        second = b1 & 0xF
        codes.append(f"{letter}{first}{second:X}{b2:02X}")
    return codes
