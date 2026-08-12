"""
Generate a byte-accurate ELM327 RX capture from the JSON fixture.

This is the file to test a from-scratch parser (Go, or anything) against — it uses
the REAL framing an adapter sends: carriage returns (0x0D) between lines and the
'>' prompt (0x3E) as the frame delimiter. NO line feeds (0x0A) — the ELM327 omits
them unless ATL1 is set.

    python3 generate_raw_stream.py   # (re)writes sample_obd_raw_stream.bin

Source of truth is testing/sample_obd_output.json — edit that, regenerate here,
and the bytes stay in sync with the Python parsing test.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# repo layout: <repo>/archive/parser-fixtures/  ->  <repo>/testing/
JSON_PATH = os.path.join(HERE, "..", "..", "testing", "sample_obd_output.json")
BIN_PATH = os.path.join(HERE, "sample_obd_raw_stream.bin")

CR = b"\r"          # 0x0D — line terminator the ELM327 uses
PROMPT = b"\r>"     # adapter prints '\r>' when ready for the next command


def _frame(payload: bytes) -> bytes:
    """One response as the adapter streams it: payload, CR, then the ready prompt.

    Echo is assumed OFF (the reader sends ATE0), so the command is NOT echoed back.
    """
    return payload + CR + PROMPT


def build_stream(records: list) -> bytes:
    """Assemble the RX byte stream a host would read across one polling pass."""
    out = bytearray()

    # Init handshake results (what the adapter returns to ATZ/ATE0/ATL0/ATSP0).
    out += _frame(b"\rELM327 v1.5")   # ATZ -> version banner
    out += _frame(b"OK")              # ATE0
    out += _frame(b"OK")              # ATL0
    out += _frame(b"OK")              # ATSP0

    # Live responses — payload is exactly the `raw` hex from the JSON fixture.
    for rec in records:
        out += _frame(rec["raw"].encode("ascii"))

    return bytes(out)


def main():
    with open(JSON_PATH) as fh:
        records = json.load(fh)["records"]
    data = build_stream(records)
    with open(BIN_PATH, "wb") as fh:
        fh.write(data)
    print(f"wrote {len(data)} bytes to {os.path.basename(BIN_PATH)} "
          f"({len(records)} responses + 4 init frames)")


if __name__ == "__main__":
    main()
