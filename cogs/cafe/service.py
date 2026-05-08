from __future__ import annotations

import copy
import random
import re
import time
import unicodedata

from .catalog import BEBIDAS, CD_ATENDER, CD_TRABALHAR, INGREDIENTES, NIVEIS, RECEITAS_SECRETAS, UPGRADES_CAFETEIRA
from .narrative import CLIENTES


_SPACE_RE = re.compile(r"[\s\-]+")
_CLEAN_RE = re.compile(r"[^\w\s\-]")


def normalizar_texto(texto: str) -> str:
    texto = texto.strip().lower().replace("$", "")
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = _CLEAN_RE.sub("", texto)
    return _SPACE_RE.sub("_", texto).strip("_")


INGREDIENTE_ALIASES: dict[str, str] = {
    "grao": "grao",
    "graos": "grao",
    "grao_de_cafe": "grao",
    "graos_de_cafe": "grao",
    "cafe": "grao",
    "gelo": "gelo",
    "agua": "agua",
    "leite": "leite",
    "chantilly": "chantilly",
    "leite_cond": "leite_cond",
    "leite_condensado": "leite_cond",
    "condensado": "leite_cond",
    "acucar": "acucar",
    "açucar": "acucar",
    "caramelo": "caramelo",
    "chocolate": "chocolate",
    "mel": "mel",
    "baunilha": "baunilha",
    "matcha": "matcha",
    "canela": "canela",
    "menta": "menta",
    "pimenta": "pimenta",
    "sal": "sal",
    "sal_marinho": "sal",
    "gengibre": "gengibre",
    "limao": "limao",
    "morango": "morango",
    "coco": "coco",
    "sakura": "sakura",
    "flor_de_cerejeira": "sakura",
    "cerejeira": "sakura",
}


BEBIDA_ALIASES: dict[str, str] = {
    **{key: key for key in BEBIDAS},
    **{key: key for key in RECEITAS_SECRETAS},
    "cafe": "cafe_simples",
    "cafezinho": "cafe_simples",
    "cafe_simples": "cafe_simples",
    "cafe_gelado": "cafe_gelado",
    "caramel_macchiato": "caramel_macchiato",
    "macchiato": "caramel_macchiato",
    "matcha_latte": "matcha_latte",
}

for _key, _bebida in {**BEBIDAS, **RECEITAS_SECRETAS}.items():
    BEBIDA_ALIASES.setdefault(normalizar_texto(_bebida["nome"]), _key)


def normalizar_ingrediente(texto: str) -> str | None:
    return INGREDIENTE_ALIASES.get(normalizar_texto(texto))


def normalizar_bebida(texto: str) -> str:
    chave = normalizar_texto(texto)
    return BEBIDA_ALIASES.get(chave, chave)


def default_user() -> dict:
    return {
        "lumicoins": 0,
        "xp": 0,
        "ingredientes": {},
        "estoque": {},
        "cd_trabalhar": 0,
        "cd_atender": 0,
        "receitas_desbloqueadas": [],
        "upgrades": {"cafeteira": 0},
    }


def normalizar_user_data(user_data: dict | None) -> dict:
    user = copy.deepcopy(user_data or {})
    defaults = default_user()
    for key, value in defaults.items():
        user.setdefault(key, copy.deepcopy(value))
    if not isinstance(user.get("ingredientes"), dict):
        user["ingredientes"] = {}
    if not isinstance(user.get("estoque"), dict):
        user["estoque"] = {}
    if not isinstance(user.get("receitas_desbloqueadas"), list):
        user["receitas_desbloqueadas"] = []
    if not isinstance(user.get("upgrades"), dict):
        user["upgrades"] = {}
    user["upgrades"].setdefault("cafeteira", 0)
    return user


def get_nivel(xp: int) -> dict:
    atual = NIVEIS[0]
    for nivel in NIVEIS:
        if xp >= nivel["xp_min"]:
            atual = nivel
    return atual


def get_cafeteira_nivel(user_data: dict) -> int:
    upgrades = user_data.setdefault("upgrades", {})
    if not isinstance(upgrades, dict):
        user_data["upgrades"] = {}
        upgrades = user_data["upgrades"]
    nivel = int(upgrades.get("cafeteira", 0) or 0)
    return max(0, min(nivel, len(UPGRADES_CAFETEIRA) - 1))


def get_cafeteira_info(user_data: dict) -> dict:
    return UPGRADES_CAFETEIRA[get_cafeteira_nivel(user_data)]


def aplicar_bonus_percentual(valor: int, percentual: int) -> int:
    if percentual <= 0:
        return valor
    return valor * (100 + percentual) // 100


def cooldown_restante(ts_ultimo: float, duracao: float, agora: float | None = None) -> float:
    agora = time.time() if agora is None else agora
    return max(0.0, duracao - (agora - ts_ultimo))


def formatar_tempo(segundos: float) -> str:
    segundos = int(segundos)
    if segundos < 60:
        return f"{segundos}s"
    minutos, resto = divmod(segundos, 60)
    return f"{minutos}min {resto}s" if resto else f"{minutos}min"


def _clone_user(user_data: dict) -> dict:
    return normalizar_user_data(copy.deepcopy(user_data))


def _consume_ingredient(tokens: list[str], index: int) -> tuple[str | None, int, str]:
    clean = [t.strip().strip(",") for t in tokens]
    max_width = min(3, len(clean) - index)
    for width in range(max_width, 0, -1):
        raw = " ".join(clean[index:index + width])
        key = normalizar_ingrediente(raw)
        if key:
            return key, width, raw
    return None, 1, clean[index]


def parse_purchase_tokens(tokens: tuple[str, ...] | list[str]) -> dict:
    pedidos: dict[str, int] = {}
    i = 0
    tokens = list(tokens)
    while i < len(tokens):
        if not tokens[i].strip().strip(","):
            i += 1
            continue

        key, consumed, raw = _consume_ingredient(tokens, i)
        if not key:
            return {"ok": False, "reason": "ingrediente_invalido", "ingrediente": raw}
        i += consumed

        qtd = 1
        if i < len(tokens):
            qtd_raw = tokens[i].lstrip("$").strip().strip(",")
            if qtd_raw.isdigit():
                qtd = int(qtd_raw)
                i += 1
        if qtd < 1:
            return {"ok": False, "reason": "quantidade_invalida", "ingrediente": key}
        pedidos[key] = pedidos.get(key, 0) + qtd

    if not pedidos:
        return {"ok": False, "reason": "vazio"}
    for key, qtd in pedidos.items():
        if qtd > 99:
            return {"ok": False, "reason": "quantidade_maxima", "ingrediente": key, "quantidade": qtd}
    return {"ok": True, "pedidos": pedidos}


def parse_ingredient_sequence(tokens: tuple[str, ...] | list[str]) -> dict:
    chaves: list[str] = []
    invalidos: list[str] = []
    i = 0
    tokens = list(tokens)
    while i < len(tokens):
        key, consumed, raw = _consume_ingredient(tokens, i)
        if not key:
            invalidos.append(raw)
            i += 1
            continue
        chaves.append(key)
        i += consumed

    if invalidos:
        return {"ok": False, "reason": "ingrediente_invalido", "invalidos": invalidos}
    if len(chaves) < 2:
        return {"ok": False, "reason": "minimo_ingredientes"}

    tentativa: dict[str, int] = {}
    for key in chaves:
        tentativa[key] = tentativa.get(key, 0) + 1
    return {"ok": True, "tentativa": tentativa}


def _missing_ingredients(user: dict, receita: dict[str, int]) -> list[dict]:
    return [
        {"key": key, "tem": user["ingredientes"].get(key, 0), "precisa": qtd}
        for key, qtd in receita.items()
        if user["ingredientes"].get(key, 0) < qtd
    ]


def _catalogo_do_usuario(user: dict) -> dict[str, dict]:
    catalogo = dict(BEBIDAS)
    for key in user.get("receitas_desbloqueadas", []):
        if key in RECEITAS_SECRETAS:
            catalogo[key] = RECEITAS_SECRETAS[key]
    return catalogo


def trabalhar(user_data: dict, agora: float | None = None, rng=random) -> dict:
    user = _clone_user(user_data)
    cd = cooldown_restante(user["cd_trabalhar"], CD_TRABALHAR, agora)
    if cd:
        return {"ok": False, "reason": "cooldown", "cooldown": cd}
    ganho = rng.randint(30, 90)
    user["lumicoins"] += ganho
    user["cd_trabalhar"] = time.time() if agora is None else agora
    return {"ok": True, "user": user, "ganho": ganho}


def comprar(user_data: dict, tokens: tuple[str, ...] | list[str]) -> dict:
    parsed = parse_purchase_tokens(tokens)
    if not parsed["ok"]:
        return parsed

    user = _clone_user(user_data)
    pedidos = parsed["pedidos"]
    custo_total = sum(INGREDIENTES[key]["preco"] * qtd for key, qtd in pedidos.items())
    if user["lumicoins"] < custo_total:
        return {
            "ok": False,
            "reason": "saldo_insuficiente",
            "custo_total": custo_total,
            "saldo": user["lumicoins"],
        }

    user["lumicoins"] -= custo_total
    linhas = []
    for key, qtd in pedidos.items():
        ing = INGREDIENTES[key]
        subtotal = ing["preco"] * qtd
        user["ingredientes"][key] = user["ingredientes"].get(key, 0) + qtd
        linhas.append({"key": key, "quantidade": qtd, "subtotal": subtotal})
    return {"ok": True, "user": user, "pedidos": pedidos, "linhas": linhas, "custo_total": custo_total}


def melhorar_cafeteira(user_data: dict, alvo: str = "cafeteira") -> dict:
    alvo_norm = normalizar_texto(alvo)
    if alvo_norm not in ("cafeteira", "cafe"):
        return {"ok": False, "reason": "alvo_invalido"}

    user = _clone_user(user_data)
    nivel = get_cafeteira_nivel(user)
    if nivel + 1 >= len(UPGRADES_CAFETEIRA):
        return {"ok": False, "reason": "nivel_maximo", "nivel": nivel}
    prox = UPGRADES_CAFETEIRA[nivel + 1]
    custo = prox["custo"]
    if user["lumicoins"] < custo:
        return {"ok": False, "reason": "saldo_insuficiente", "upgrade": prox, "saldo": user["lumicoins"]}
    user["lumicoins"] -= custo
    user.setdefault("upgrades", {})["cafeteira"] = prox["nivel"]
    return {"ok": True, "user": user, "upgrade": prox, "custo": custo}


def preparar(user_data: dict, bebida_raw: str, rng=random) -> dict:
    user = _clone_user(user_data)
    bebida = normalizar_bebida(bebida_raw)
    catalogo = _catalogo_do_usuario(user)
    if bebida not in catalogo:
        return {"ok": False, "reason": "bebida_invalida", "opcoes": list(catalogo)}

    bebida_data = catalogo[bebida]
    faltando = _missing_ingredients(user, bebida_data["receita"])
    if faltando:
        return {"ok": False, "reason": "ingredientes_insuficientes", "bebida": bebida, "faltando": faltando}

    cafeteira = get_cafeteira_info(user)
    ingrediente_poupado = None
    if cafeteira["chance_economizar"] and rng.randint(1, 100) <= cafeteira["chance_economizar"]:
        ingrediente_poupado = rng.choice(list(bebida_data["receita"].keys()))

    for key, qtd in bebida_data["receita"].items():
        consumido = qtd - (1 if key == ingrediente_poupado else 0)
        if consumido <= 0:
            continue
        user["ingredientes"][key] -= consumido
        if user["ingredientes"][key] == 0:
            del user["ingredientes"][key]
    user["estoque"][bebida] = user["estoque"].get(bebida, 0) + 1
    xp_ganho = aplicar_bonus_percentual(bebida_data["xp"], cafeteira["bonus_xp"])
    user["xp"] += xp_ganho
    return {
        "ok": True,
        "user": user,
        "bebida": bebida,
        "bebida_data": bebida_data,
        "xp_ganho": xp_ganho,
        "ingrediente_poupado": ingrediente_poupado,
    }


def inventar(user_data: dict, ingredientes: tuple[str, ...] | list[str]) -> dict:
    parsed = parse_ingredient_sequence(ingredientes)
    if not parsed["ok"]:
        return parsed

    user = _clone_user(user_data)
    tentativa = parsed["tentativa"]
    faltando = _missing_ingredients(user, tentativa)
    if faltando:
        return {"ok": False, "reason": "ingredientes_insuficientes", "faltando": faltando}

    for key, qtd in tentativa.items():
        user["ingredientes"][key] -= qtd
        if user["ingredientes"][key] == 0:
            del user["ingredientes"][key]

    chave_acerto = next(
        (key for key, bebida in RECEITAS_SECRETAS.items() if bebida["receita"] == tentativa),
        None,
    )
    if chave_acerto is None:
        return {"ok": True, "user": user, "acertou": False, "tentativa": tentativa}

    bebida_data = RECEITAS_SECRETAS[chave_acerto]
    ja_desbloqueada = chave_acerto in user.get("receitas_desbloqueadas", [])
    if not ja_desbloqueada:
        user.setdefault("receitas_desbloqueadas", []).append(chave_acerto)
    user["estoque"][chave_acerto] = user["estoque"].get(chave_acerto, 0) + 1
    xp_ganho = bebida_data["xp"] * (2 if not ja_desbloqueada else 1)
    bonus_moedas = 100 if not ja_desbloqueada else 0
    user["xp"] += xp_ganho
    user["lumicoins"] += bonus_moedas
    return {
        "ok": True,
        "user": user,
        "acertou": True,
        "tentativa": tentativa,
        "bebida": chave_acerto,
        "bebida_data": bebida_data,
        "ja_desbloqueada": ja_desbloqueada,
        "xp_ganho": xp_ganho,
        "bonus_moedas": bonus_moedas,
    }


def vender(user_data: dict, bebida_raw: str) -> dict:
    user = _clone_user(user_data)
    bebida = normalizar_bebida(bebida_raw)
    bebida_data = BEBIDAS.get(bebida) or RECEITAS_SECRETAS.get(bebida)
    if bebida_data is None:
        return {"ok": False, "reason": "bebida_invalida", "bebida": bebida}
    if not user["estoque"].get(bebida, 0):
        return {"ok": False, "reason": "sem_estoque", "bebida": bebida, "bebida_data": bebida_data}

    user["estoque"][bebida] -= 1
    if user["estoque"][bebida] == 0:
        del user["estoque"][bebida]
    cafeteira = get_cafeteira_info(user)
    valor_venda = aplicar_bonus_percentual(bebida_data["preco_venda"], cafeteira["bonus_venda"])
    user["lumicoins"] += valor_venda
    return {"ok": True, "user": user, "bebida": bebida, "bebida_data": bebida_data, "valor_venda": valor_venda}


def iniciar_atendimento(user_data: dict, agora: float | None = None, rng=random) -> dict:
    user = _clone_user(user_data)
    pendente = user.get("cliente_pendente")
    if pendente:
        return {"ok": True, "user": user, "status": "pendente", "pendente": pendente}

    cd = cooldown_restante(user["cd_atender"], CD_ATENDER, agora)
    if cd:
        return {"ok": False, "reason": "cooldown", "cooldown": cd}

    cliente = rng.choice(CLIENTES)
    bebida = rng.choice(list(BEBIDAS.keys()))
    user["cliente_pendente"] = {"cliente": cliente["nome"], "bebida": bebida}
    user["cd_atender"] = time.time() if agora is None else agora
    intro = rng.choice(cliente["pedido_intro"]).format(bebida=BEBIDAS[bebida]["nome"])
    return {"ok": True, "user": user, "status": "novo", "cliente": cliente, "bebida": bebida, "intro": intro}


def servir_atendimento(user_data: dict, bebida_raw: str, rng=random) -> dict:
    user = _clone_user(user_data)
    pendente = user.get("cliente_pendente")
    if not pendente:
        return {"ok": False, "reason": "sem_cliente"}

    bebida_oferecida = normalizar_bebida(bebida_raw)
    cliente = next((c for c in CLIENTES if c["nome"] == pendente["cliente"]), rng.choice(CLIENTES))
    bebida_pedida = pendente["bebida"]
    bebida_data = BEBIDAS[bebida_pedida]

    errou = bebida_oferecida != bebida_pedida or not user["estoque"].get(bebida_oferecida, 0)
    if errou:
        motivo = "sem_estoque" if bebida_oferecida == bebida_pedida else "bebida_errada"
        user.pop("cliente_pendente", None)
        return {
            "ok": True,
            "user": user,
            "status": "erro",
            "motivo": motivo,
            "cliente": cliente,
            "bebida": bebida_pedida,
            "bebida_data": bebida_data,
        }

    bonus_base = rng.randint(20, 60)
    cafeteira = get_cafeteira_info(user)
    bonus_moedas = aplicar_bonus_percentual(bonus_base, cafeteira["bonus_atendimento"])
    bonus_xp = rng.randint(5, 15)
    user["estoque"][bebida_oferecida] -= 1
    if user["estoque"][bebida_oferecida] == 0:
        del user["estoque"][bebida_oferecida]
    user["lumicoins"] += bonus_moedas
    user["xp"] += bonus_xp
    user.pop("cliente_pendente", None)
    return {
        "ok": True,
        "user": user,
        "status": "sucesso",
        "cliente": cliente,
        "bebida": bebida_pedida,
        "bebida_data": bebida_data,
        "bonus_base": bonus_base,
        "bonus_moedas": bonus_moedas,
        "bonus_xp": bonus_xp,
    }
