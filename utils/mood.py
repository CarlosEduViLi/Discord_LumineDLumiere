"""
Modo de humor da Lumine — baseado na hora atual no fuso horário do Brasil (UTC-3).

Cinco humores cobrem as 24 horas:
  🌅 Manhã       06–12  Animada, energética
  ☀️  Tarde       12–18  Feliz, tranquila (padrão)
  🌆 Entardecer  18–21  Contemplativa, poética
  🌙 Noite       21–00  Sonolenta, carinhosa
  🌌 Madrugada   00–06  Misteriosa, calma
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

TZ_BR = timezone(timedelta(hours=-3))


@dataclass(frozen=True)
class Mood:
    id: str                    # chave canônica, ex: "manha"
    nome: str                  # "Manhã"
    emoji: str                 # "🌅"
    activity_text: str         # texto do status do bot
    activity_type_value: int   # 0=playing, 3=watching (sem import discord aqui)
    saudacao: str              # frase de boas-vindas usada no l!help


_MOODS: dict[str, Mood] = {
    "manha": Mood(
        id="manha",
        nome="Manhã",
        emoji="🌅",
        activity_text="acordando com energia~ ☕",
        activity_type_value=0,
        saudacao="🌅 Bom dia! Sou a Lumine, sua maid~ 💙 Que começo de dia animado!",
    ),
    "tarde": Mood(
        id="tarde",
        nome="Tarde",
        emoji="☀️",
        activity_text="servindo no café~ 💙",
        activity_type_value=0,
        saudacao="✨ Olá! Sou a Lumine, sua maid~ 💙",
    ),
    "entardecer": Mood(
        id="entardecer",
        nome="Entardecer",
        emoji="🌆",
        activity_text="observando o céu dourado~ 🌇",
        activity_type_value=3,
        saudacao="🌆 Olá... Sou a Lumine~ 💙 Que tarde bonita pra estarmos aqui juntos.",
    ),
    "noite": Mood(
        id="noite",
        nome="Noite",
        emoji="🌙",
        activity_text="cuidando de vocês com carinho~ 🌙",
        activity_type_value=0,
        saudacao="🌙 Boa noite~ Sou a Lumine, sua maid 💙 Pode chegar, estou aqui...",
    ),
    "madrugada": Mood(
        id="madrugada",
        nome="Madrugada",
        emoji="🌌",
        activity_text="velando o silêncio da noite~ 🌌",
        activity_type_value=3,
        saudacao="🌌 Hmm... aqui estou, na quietude~ Sou a Lumine 💙 Que você precisa?",
    ),
}


def get_humor_atual() -> Mood:
    """Retorna o Mood correspondente à hora atual no horário do Brasil (UTC-3)."""
    hora = datetime.now(TZ_BR).hour
    if 6 <= hora < 12:
        return _MOODS["manha"]
    if 12 <= hora < 18:
        return _MOODS["tarde"]
    if 18 <= hora < 21:
        return _MOODS["entardecer"]
    if 21 <= hora < 24:
        return _MOODS["noite"]
    return _MOODS["madrugada"]


def frase_com_humor(
    frases_por_humor: dict[str, list[str]],
    fallback: list[str],
    humor: Mood | None = None,
) -> str:
    """
    Seleciona uma frase aleatória de *frases_por_humor* usando o id do humor atual.
    Se o humor não tiver entradas na dict, tenta "tarde" como neutro.
    Se ainda assim não houver, usa *fallback* (lista plana existente — nunca alterada).
    """
    if humor is None:
        humor = get_humor_atual()
    opcoes = frases_por_humor.get(humor.id) or frases_por_humor.get("tarde")
    return random.choice(opcoes) if opcoes else random.choice(fallback)
