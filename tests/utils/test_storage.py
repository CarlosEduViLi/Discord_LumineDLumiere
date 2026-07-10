"""
tests/utils/test_storage.py
Testes unitários de utils/storage.py (JsonStore).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.storage import JsonStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_store(tmp_path: Path) -> JsonStore:
    """JsonStore apontando para arquivo temporário (criado pelo pytest)."""
    return JsonStore(tmp_path / "test_data.json")


@pytest.fixture
def populated_store(tmp_path: Path) -> JsonStore:
    """JsonStore com dados pré-gravados."""
    path = tmp_path / "populated.json"
    path.write_text(json.dumps({"guild": {"user": {"lumicoins": 100}}}), encoding="utf-8")
    return JsonStore(path)


# ---------------------------------------------------------------------------
# read()
# ---------------------------------------------------------------------------

async def test_read_missing_file_returns_empty(tmp_path: Path):
    store = JsonStore(tmp_path / "nao_existe.json")
    result = await store.read()
    assert result == {}


async def test_read_returns_dict(populated_store: JsonStore):
    result = await populated_store.read()
    assert result["guild"]["user"]["lumicoins"] == 100


async def test_read_returns_deep_copy(populated_store: JsonStore):
    result1 = await populated_store.read()
    result1["guild"]["user"]["lumicoins"] = 9999
    result2 = await populated_store.read()
    assert result2["guild"]["user"]["lumicoins"] == 100  # não foi mutado


async def test_read_invalid_json_returns_empty(tmp_path: Path):
    path = tmp_path / "broken.json"
    path.write_text("{ invalid json }", encoding="utf-8")
    store = JsonStore(path)
    result = await store.read()
    assert result == {}


async def test_read_non_dict_json_returns_empty(tmp_path: Path):
    path = tmp_path / "list.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    store = JsonStore(path)
    result = await store.read()
    assert result == {}


# ---------------------------------------------------------------------------
# replace()
# ---------------------------------------------------------------------------

async def test_replace_writes_and_reads_back(tmp_store: JsonStore):
    await tmp_store.replace({"a": 1, "b": 2})
    result = await tmp_store.read()
    assert result == {"a": 1, "b": 2}


async def test_replace_does_not_mutate_original(tmp_store: JsonStore):
    data = {"x": 42}
    await tmp_store.replace(data)
    data["x"] = 99  # mutação após replace
    result = await tmp_store.read()
    assert result["x"] == 42  # snapshot foi gravado, não a referência mutada


async def test_replace_creates_parent_dirs(tmp_path: Path):
    store = JsonStore(tmp_path / "sub" / "dir" / "data.json")
    await store.replace({"ok": True})
    result = await store.read()
    assert result == {"ok": True}


async def test_replace_no_leftover_tmp_file(tmp_store: JsonStore):
    await tmp_store.replace({"key": "value"})
    tmp_path = tmp_store.path.with_name(f"{tmp_store.path.name}.tmp")
    assert not tmp_path.exists()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------

async def test_update_mutates_and_saves(tmp_store: JsonStore):
    await tmp_store.replace({"counter": 0})

    def increment(data: dict) -> dict:
        data["counter"] += 1
        return data

    result = await tmp_store.update(increment)
    assert result["counter"] == 1

    # Verifica que a gravação persistiu
    saved = await tmp_store.read()
    assert saved["counter"] == 1


async def test_update_returns_mutator_result(tmp_store: JsonStore):
    await tmp_store.replace({"coins": 50})

    def add_coins(data: dict) -> int:
        data["coins"] += 10
        return data["coins"]

    returned = await tmp_store.update(add_coins)
    assert returned == 60


async def test_update_on_empty_store(tmp_store: JsonStore):
    def init(data: dict) -> dict:
        data.setdefault("users", [])
        data["users"].append("alice")
        return data

    result = await tmp_store.update(init)
    assert result["users"] == ["alice"]
    saved = await tmp_store.read()
    assert saved["users"] == ["alice"]


async def test_update_sequential_calls_are_consistent(tmp_store: JsonStore):
    """Duas chamadas sequenciais a update devem acumular corretamente."""
    await tmp_store.replace({"n": 0})

    async def inc():
        await tmp_store.update(lambda d: d.update({"n": d["n"] + 1}) or d)

    await inc()
    await inc()
    await inc()

    result = await tmp_store.read()
    assert result["n"] == 3
