from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

CAFE_DATA_PATH = DATA_DIR / "cafe_data.json"
PLAYLISTS_DATA_PATH = DATA_DIR / "playlists.json"
