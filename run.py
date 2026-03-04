#!/usr/bin/env python3
"""Launch the Glamping Market Research AI Streamlit app."""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent / "frontend" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port=8501"], check=True)
