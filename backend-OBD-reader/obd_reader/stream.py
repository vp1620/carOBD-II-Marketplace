"""Decode a raw ELM327 serial capture into reader records.

This is the bridge from "raw bytes on the wire" to the decoded record shape the
reader emits downstream. It lives in the package (not a test) on purpose: it is
the reusable step that both the golden-file test and the future Gherkin/BDD step
definitions call, so a .feature scenario like "When I decode the capture" maps to
a single import here rather than duplicating parsing logic per test framework.
"""

from .decoder import decode_dtcs, decode_pid
from .pids import REGISTRY

# Fixed label the reader gives every Mode 03 record; not derivable from the raw
# frame itself, so pinned here to reconstruct the emitted record shape.
DTC_RECORD_NAME = "active_fault_codes"

_HEX = set("0123456789ABCDEFabcdef")


def _is_response_line(line: str) -> bool:
    """True for an ELM327 data-response line (hex byte tokens starting 41/43).

    Lets us pull just the ECU responses out of a capture that also contains
    commands, prompts, 'OK', and the version banner.
    """
    tokens = line.split()
    if not tokens or tokens[0] not in ("41", "43"):
        return False
    return all(len(t) == 2 and all(c in _HEX for c in t) for t in tokens)


def extract_responses(text: str) -> list[str]:
    """Raw serial capture -> ordered list of normalized hex response strings."""
    return [
        " ".join(line.split()).upper()
        for line in text.splitlines()
        if _is_response_line(line.strip())
    ]


def decode_stream(text: str) -> list[dict]:
    """Decode a raw serial capture into the record shape the reader emits.

    Mode 01 responses echo their PID in the second byte, which we use to look up
    name/unit; Mode 03 responses carry no PID and collapse to a DTC record.
    Returns decoder-owned fields only — timestamp/vehicle_id are runtime metadata
    the reader stamps, not decode output, so they are intentionally absent here.
    """
    records: list[dict] = []
    for raw in extract_responses(text):
        ints = [int(tok, 16) for tok in raw.split()]
        if ints[0] == 0x43:  # Mode 03 — diagnostic trouble codes
            records.append({
                "type": "dtc",
                "name": DTC_RECORD_NAME,
                "raw": raw,
                "codes": decode_dtcs(raw),
            })
            continue
        pid = f"01{ints[1]:02X}"  # rebuild the PID from the echoed byte
        meta = REGISTRY[pid]
        records.append({
            "type": "pid",
            "pid": pid,
            "name": meta.name,
            "raw": raw,
            "value": decode_pid(pid, raw),
            "unit": meta.unit,
        })
    return records
