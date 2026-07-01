"""Vercel-compatible FastAPI entrypoint.

Vercel discovers conventional files such as ``app.py`` automatically.  The
project uses a ``src`` layout, so add that directory before importing the real
application object.
"""

# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from anime_oscilloscope.main import app

__all__ = ["app"]
