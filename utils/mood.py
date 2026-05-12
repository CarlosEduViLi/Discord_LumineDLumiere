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
    id: str                        # chave canônica, ex: "manha"
    nome: str                      # "Manhã"
    emoji: str                     # "🌅"
    activity_text: str             # texto do status do bot
    activity_type_value: int       # 0=playing, 3=watching (sem import discord aqui)
    saudacoes: tuple[str, ...]     # frases de boas-vindas sorteadas aleatoriamente


_MOODS: dict[str, Mood] = {
    "manha": Mood(
        id="manha",
        nome="Manhã",
        emoji="🌅",
        activity_text="acordando com energia~ ☕",
        activity_type_value=0,
        saudacoes=(
            "🌅 Bom dia! Sou a Lumine, sua maid~ 💙 Que começo de dia animado!",
            "🌅 Oi oi! Bom dia~ Sou a Lumine! Acordei cheia de energia pra te atender hoje! ✨",
            "☀️ Bom diinha! Sou a Lumine, sua maid~ 💙 Vamos começar o dia com o pé direito?",
            "🌄 Uau, você chegou cedo! Sou a Lumine~ Ainda tem cheirinho de café fresquinho aqui! ☕💙",
            "🌅 Que manhã abençoada! Sou a Lumine, sua maid~ 💙 Pronta pra te servir com todo carinho!",
        ),
    ),
    "tarde": Mood(
        id="tarde",
        nome="Tarde",
        emoji="☀️",
        activity_text="servindo no café~ 💙",
        activity_type_value=0,
        saudacoes=(
            "✨ Olá! Sou a Lumine, sua maid~ 💙",
            "💙 Oi, oi! Seja bem-vindo(a)~ Sou a Lumine! Em que posso te ajudar hoje?",
            "✨ Olá, olá! Sou a Lumine, sua maid~ 💙 Que bom ter você por aqui!",
            "🌸 Boa tarde! Sou a Lumine~ 💙 Aqui é um lugar cheio de carinho, pode ficar à vontade!",
            "☀️ Que tarde agradável! Sou a Lumine, sua maid~ 💙 O que posso fazer por você hoje?",
        ),
    ),
    "entardecer": Mood(
        id="entardecer",
        nome="Entardecer",
        emoji="🌆",
        activity_text="observando o céu dourado~ 🌇",
        activity_type_value=3,
        saudacoes=(
            "🌆 Olá... Sou a Lumine~ 💙 Que tarde bonita pra estarmos aqui juntos.",
            "🌇 O céu está ficando laranjado lá fora... mas estou aqui~ Sou a Lumine 💙 Pode pedir!",
            "🌆 Ah, o entardecer chegou~ Sou a Lumine, sua maid 💙 O que posso fazer por você nessa hora dourada?",
            "🌸 Essa luz do fim de tarde é tão bonita... Sou a Lumine~ 💙 O que precisa, com carinho?",
            "🌇 O dia vai cedendo lugar à noite devagarzinho... Sou a Lumine~ 💙 Estou aqui com você.",
        ),
    ),
    "noite": Mood(
        id="noite",
        nome="Noite",
        emoji="🌙",
        activity_text="cuidando de vocês com carinho~ 🌙",
        activity_type_value=0,
        saudacoes=(
            "🌙 Boa noite~ Sou a Lumine, sua maid 💙 Pode chegar, estou aqui...",
            "🌙 Boa noitinha~ Sou a Lumine! Ainda acordada esperando por você com carinho 💙",
            "✨ Boa noite~ Sou a Lumine, sua maid 💙 A noite ficou mais aconchegante com você aqui~",
            "🌙 Hmm... boa noite~ Sou a Lumine 💙 Que bom que você apareceu! O que posso fazer por você?",
            "🌟 Estrelinha da noite apareceu~ Sou a Lumine, sua maid 💙 O que precisa hoje à noite?",
        ),
    ),
    "madrugada": Mood(
        id="madrugada",
        nome="Madrugada",
        emoji="🌌",
        activity_text="velando o silêncio da noite~ 🌌",
        activity_type_value=3,
        saudacoes=(
            "🌌 Hmm... aqui estou, na quietude~ Sou a Lumine 💙 Que você precisa?",
            "🌌 Ainda acordado(a) na madrugada? Sou a Lumine~ 💙 Aqui tudo está quieto e calmo...",
            "🌙 Sssh... a cidade dorme mas eu estou aqui~ Sou a Lumine 💙 O que precisa, baixinho?",
            "🌌 Que horas são essas... Sou a Lumine~ 💙 Na madrugada sou sua companhia silenciosa~",
            "✨ A madrugada tem um charme especial... Sou a Lumine~ 💙 Pode pedir, estou à sua disposição~",
        ),
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


def saudacao_do_humor(humor: Mood) -> str:
    """Sorteia aleatoriamente uma das saudações do humor dado."""
    return random.choice(humor.saudacoes)


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
