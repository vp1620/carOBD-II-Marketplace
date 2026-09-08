"""Entry point: run the OBD WebSocket server.

Why: lets you start everything with `python3 backend-OBD-reader/main.py` without
needing to know the uvicorn import path or set PYTHONPATH yourself.
"""

import os
import sys

# Why: put this folder on sys.path so the "obd_reader.server:app" import string
# resolves regardless of the directory you launch from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    # host 0.0.0.0 so a phone/other device on the same network can reach the dashboard.
    uvicorn.run("obd_reader.server:app", host="0.0.0.0", port=8000)
