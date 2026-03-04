#!/usr/bin/env python3
"""
Fetch a Browserbase session recording (rrweb DOM replay) and save it for the demo.

Usage:
    python scripts/fetch_session_recording.py [SESSION_ID]

If SESSION_ID is omitted, uses: 81f0c1ba-c7fa-4c36-be58-d8efc37cbfc8

Requires BROWSERBASE_API_KEY in .env or environment.
Output: demo/session_recording.json
"""
import json
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SESSION_ID = "81f0c1ba-c7fa-4c36-be58-d8efc37cbfc8"


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SESSION_ID
    api_key = os.getenv("BROWSERBASE_API_KEY")
    if not api_key:
        print("Error: BROWSERBASE_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    from browserbase import Browserbase

    bb = Browserbase(api_key=api_key)
    print(f"Fetching recording for session {session_id}...")
    recording = bb.sessions.recording.retrieve(session_id)

    # recording is a list of SessionRecording objects; convert to rrweb-compatible dicts
    normalized = []
    for evt in recording:
        if hasattr(evt, "model_dump"):
            d = evt.model_dump()
        elif isinstance(evt, dict):
            d = dict(evt)
        else:
            continue
        # rrweb expects {type, data, timestamp}; strip sessionId/session_id
        d.pop("sessionId", None)
        d.pop("session_id", None)
        normalized.append(d)

    out_dir = Path(__file__).parent.parent / "demo"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "session_recording.json"

    with open(out_path, "w") as f:
        json.dump(normalized, f, indent=2)

    print(f"Saved {len(normalized)} events to {out_path}")
    print(f"Open demo/replay.html in a browser to view the replay.")


if __name__ == "__main__":
    main()
