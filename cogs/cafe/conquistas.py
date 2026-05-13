from __future__ import annotations

from .catalog import BEBIDAS, RECEITAS_SECRETAS

_TODAS_BEBIDAS_PUBLICAS = frozenset(BEBIDAS.keys())
_TOTAL_SECRETAS = len(RECEITAS_SECRETAS)

CONQUISTAS: dict[str, dict] = {
    # Trabalho
    "primeiro_turno": {
        "nome": "Primeiro Dia de Trabalho",
        "emoji": "☕",
        "descricao": "Trabalhou no café pela primeira vez.",
        "check": lambda u: u.get("stats", {}).get("trabalhos", 0) >= 1,
    },
    "trabalhador_incansavel": {
        "nome": "Incansável",
        "emoji": "💼",
        "descricao": "Trabalhou 50 vezes no café.",
        "check": lambda u: u.get("stats", {}).get("trabalhos", 0) >= 50,
    },
    # Bebidas
    "primeira_bebida": {
        "nome": "Aprendiz de Barista",
        "emoji": "🥤",
        "descricao": "Preparou sua primeira bebida.",
        "check": lambda u: u.get("stats", {}).get("bebidas_feitas", 0) >= 1,
    },
    "cem_bebidas": {
        "nome": "Linha de Produção",
        "emoji": "🏭",
        "descricao": "Preparou 100 bebidas no total.",
        "check": lambda u: u.get("stats", {}).get("bebidas_feitas", 0) >= 100,
    },
    "conhecedor_do_cardapio": {
        "nome": "Conhecedor do Cardápio",
        "emoji": "📋",
        "descricao": "Preparou todas as 8 bebidas públicas pelo menos uma vez.",
        "check": lambda u: _TODAS_BEBIDAS_PUBLICAS.issubset(
            set(u.get("stats", {}).get("bebidas_distintas", []))
        ),
    },
    # Receitas Secretas
    "primeira_descoberta": {
        "nome": "Alquimista",
        "emoji": "🧪",
        "descricao": "Descobriu sua primeira receita secreta.",
        "check": lambda u: len(u.get("receitas_desbloqueadas", [])) >= 1,
    },
    "meio_grimorio": {
        "nome": "Meio Grimório",
        "emoji": "📖",
        "descricao": "Descobriu 8 receitas secretas.",
        "check": lambda u: len(u.get("receitas_desbloqueadas", [])) >= 8,
    },
    "grimorio_completo": {
        "nome": "Grimório Completo",
        "emoji": "🔮",
        "descricao": f"Descobriu todas as {_TOTAL_SECRETAS} receitas secretas!",
        "check": lambda u: len(u.get("receitas_desbloqueadas", [])) >= _TOTAL_SECRETAS,
    },
    # Clientes
    "primeiro_cliente": {
        "nome": "Bem-vindo ao Balcão!",
        "emoji": "👥",
        "descricao": "Atendeu seu primeiro cliente.",
        "check": lambda u: u.get("stats", {}).get("clientes_atendidos", 0) >= 1,
    },
    "cem_clientes": {
        "nome": "O Barista da Cidade",
        "emoji": "🌆",
        "descricao": "Atendeu 100 clientes.",
        "check": lambda u: u.get("stats", {}).get("clientes_atendidos", 0) >= 100,
    },
    "servico_vip": {
        "nome": "Serviço de Primeira Classe",
        "emoji": "👑",
        "descricao": "Atendeu um cliente VIP.",
        "check": lambda u: u.get("stats", {}).get("vip_atendidos", 0) >= 1,
    },
    "oportunista": {
        "nome": "Oportunista",
        "emoji": "🏃",
        "descricao": "Roubou o cliente de outro barista.",
        "check": lambda u: u.get("stats", {}).get("roubos", 0) >= 1,
    },
    # Progressão
    "luminepressa": {
        "nome": "Luminepressa Deluxe",
        "emoji": "✨",
        "descricao": "Alcançou o nível máximo da cafeteira.",
        "check": lambda u: u.get("upgrades", {}).get("cafeteira", 0) >= 5,
    },
    "mestre_barista": {
        "nome": "Mestre Barista",
        "emoji": "🌟",
        "descricao": "Alcançou o título de Mestre Barista (1500 XP).",
        "check": lambda u: u.get("xp", 0) >= 1500,
    },
    "lenda_do_cafe": {
        "nome": "Lenda do Café",
        "emoji": "👑",
        "descricao": "Alcançou o lendário título de Lenda do Café (3000 XP).",
        "check": lambda u: u.get("xp", 0) >= 3000,
    },
}


def verificar_conquistas(user_data: dict) -> list[str]:
    """Verifica todas as conquistas, marca as novas em user_data e retorna as chaves desbloqueadas agora."""
    desbloqueadas = user_data.setdefault("conquistas", [])
    novas = []
    for key, conquista in CONQUISTAS.items():
        if key not in desbloqueadas and conquista["check"](user_data):
            desbloqueadas.append(key)
            novas.append(key)
    return novas
