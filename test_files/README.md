# test_files/

Recorded input and expected output for the decoder golden test.

**These two files must stay here — do not move them under `backend-OBD-reader/tests/`.**

`sample_obd_output.json` is not only test data. `obd_reader/reader.py`'s `FixtureReader`
loads it at runtime to replay readings when no adapter is connected, which is what makes
offline development possible (OBD-4). Moving it under `tests/` would make production code
depend on a test directory.

`sample_obd_raw_stream.txt` is the recorded ELM327 capture the golden test replays through
the real `SerialReader` via a fake serial port.

Fixtures that *are* purely test data live beside their tests — see
`backend-OBD-reader/tests/faults/cases/`.
