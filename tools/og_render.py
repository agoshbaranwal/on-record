#!/usr/bin/env python3
"""Render og/born-today.png (1200x630) from tools/og-born-today.html with headless Chrome (tools/cdp.py:
no tab anywhere, its own process group, closed on exit)."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from cdp import Chrome
with Chrome(1200, 630) as c:
    c.resize(1200, 630, dpr=1)
    c.goto((ROOT / "tools" / "og-born-today.html").as_uri(), settle=1.0)
    c.shot(str(ROOT / "og" / "born-today.png"))
print("og/born-today.png written")
