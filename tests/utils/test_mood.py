"""
tests/utils/test_mood.py
Testes unitários de utils/mood.py.

Usa datetimes injetados para testes determinísticos, independentes do horário real.
"""
from __future__ import annotations

import datetime

import pytest

from utils.mood import HumorAtual, _periodo_do_dia, get_humor_atual, saudacao_do_humor

# ---------------------------------------------------------------------------
# _periodo_do_dia
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hora,esperado", [
    (5,  "manha"),
    (6,  "manha"),
    (11, "manha"),
    (12, "tarde"),
    (17, "tarde"),
    (18, "noite"),
    (22, "noite"),
    (23, "madrugada"),
    (0,  "madrugada"),
    (4,  "madrugada"),
])
def test_periodo_do_dia(hora: int, esperado: str):
    assert _periodo_do_dia(hora) == esperado


# ---------------------------------------------------------------------------
# get_humor_atual
# ---------------------------------------------------------------------------

def _dt(hora: int) -> datetime.datetime:
    """Helper: cria um datetime com a hora fornecida."""
    return datetime.datetime(2025, 1, 15, hora, 0, 0)


def test_get_humor_atual_retorna_humoratual():
    humor = get_humor_atual(agora=_dt(10))
    assert isinstance(humor, HumorAtual)


@pytest.mark.parametrize("hora,periodo_esperado", [
    (6,  "manha"),
    (14, "tarde"),
    (20, "noite"),
    (2,  "madrugada"),
])
def test_get_humor_atual_periodo_correto(hora: int, periodo_esperado: str):
    humor = get_humor_atual(agora=_dt(hora))
    assert humor.humor == periodo_esperado


def test_get_humor_atual_tem_activity_type():
    humor = get_humor_atual(agora=_dt(10))
    assert isinstance(humor.activity_type_value, int)


def test_get_humor_atual_tem_activity_text():
    humor = get_humor_atual(agora=_dt(10))
    assert isinstance(humor.activity_text, str)
    assert len(humor.activity_text) > 0


def test_get_humor_atual_sem_argumento_nao_falha():
    """Sem injetar agora, usa horário real — não deve lançar exceção."""
    humor = get_humor_atual()
    assert isinstance(humor, HumorAtual)
    assert humor.humor in ("manha", "tarde", "noite", "madrugada")


def test_get_humor_atual_manha_valores_validos():
    humor = get_humor_atual(agora=_dt(8))
    assert humor.humor == "manha"
    assert humor.activity_type_value in (0, 1, 2, 3, 5)  # valores de discord.ActivityType


def test_get_humor_atual_tarde_valores_validos():
    humor = get_humor_atual(agora=_dt(15))
    assert humor.humor == "tarde"


def test_get_humor_atual_noite_valores_validos():
    humor = get_humor_atual(agora=_dt(21))
    assert humor.humor == "noite"


def test_get_humor_atual_madrugada_valores_validos():
    humor = get_humor_atual(agora=_dt(3))
    assert humor.humor == "madrugada"


# ---------------------------------------------------------------------------
# saudacao_do_humor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hora", [6, 14, 20, 2])
def test_saudacao_do_humor_retorna_string(hora: int):
    saudacao = saudacao_do_humor(agora=_dt(hora))
    assert isinstance(saudacao, str)
    assert len(saudacao) > 0


def test_saudacao_do_humor_sem_argumento_nao_falha():
    saudacao = saudacao_do_humor()
    assert isinstance(saudacao, str)
    assert len(saudacao) > 0


@pytest.mark.parametrize("hora,periodo", [
    (6, "manha"),
    (14, "tarde"),
    (20, "noite"),
    (2, "madrugada"),
])
def test_saudacao_do_humor_nao_vazia_para_todos_periodos(hora: int, periodo: str):
    for _ in range(5):  # testa múltiplas amostras para cobrir aleatoriedade
        saudacao = saudacao_do_humor(agora=_dt(hora))
        assert saudacao.strip() != "", f"Saudação vazia para período {periodo}"
