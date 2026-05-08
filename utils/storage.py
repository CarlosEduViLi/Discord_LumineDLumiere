from __future__ import annotations

import asyncio
import copy
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar


T = TypeVar("T")


class JsonStore:
    """Small JSON store with per-file async locking and atomic writes."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = asyncio.Lock()

    def _load_unlocked(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_unlocked(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_name(f"{self.path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, self.path)

    async def read(self) -> dict:
        async with self._lock:
            return copy.deepcopy(self._load_unlocked())

    async def replace(self, data: dict) -> None:
        async with self._lock:
            self._save_unlocked(data)

    async def update(self, mutator: Callable[[dict], T]) -> T:
        async with self._lock:
            data = self._load_unlocked()
            result = mutator(data)
            self._save_unlocked(data)
            return result
