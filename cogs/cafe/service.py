from __future__ import annotations

import copy
import math
import random
import re
import time
import unicodedata

from .catalog import (
    BEBIDAS,
    CD_ATENDER,
    CD_CLIENTE,
    CD_PREPARAR,
    CD_TRABALHAR,
    INGREDIENTES,
    NIVEIS,
    PREMIUM_BEBIDAS,
    RECEITAS_SECRETAS,
    UPGRADES_CAFETEIRA,
    VIP_CHANCE,
)
from .conquistas import verificar_conquistas
from .daily import (
    get_bebida_do_dia,
    get_bonus_bebida_venda_pct,
    get_bonus_bebida_xp_pct,
    get_categoria_desconto,
    get_desconto_pct,
)
from .narrative import CLIENTES, CLIENTES_VIP

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
        "conquistas": [],
        "stats": {
            "trabalhos": 0,
            "bebidas_feitas": 0,
            "clientes_atendidos": 0,
            "vip_atendidos": 0,
            "roubos": 0,
            "bebidas_distintas": [],
        },
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
    if not isinstance(user.get("conquistas"), list):
        user["conquistas"] = []
    user.setdefault("conquistas", [])
    stats = user.setdefault("stats", {})
    if not isinstance(stats, dict):
        user["stats"] = {}
        stats = user["stats"]
    for campo in ("trabalhos", "bebidas_feitas", "clientes_atendidos", "vip_atendidos", "roubos"):
        stats.setdefault(campo, 0)
    stats.setdefault("bebidas_distintas", [])
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
    return valor + math.ceil((valor * percentual) / 100)


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
    user["stats"]["trabalhos"] += 1
    novas = verificar_conquistas(user)
    return {"ok": True, "user": user, "ganho": ganho, "conquistas_novas": novas}


def comprar(user_data: dict, tokens: tuple[str, ...] | list[str]) -> dict:
    parsed = parse_purchase_tokens(tokens)
    if not parsed["ok"]:
        return parsed

    user = _clone_user(user_data)
    pedidos = parsed["pedidos"]

    # Desconto diário de categoria
    cat_desconto = get_categoria_desconto()
    desconto_pct = get_desconto_pct()

    custo_total = 0
    linhas = []
    for key, qtd in pedidos.items():
        ing = INGREDIENTES[key]
        preco_unit = ing["preco"]
        em_promocao = ing.get("categoria") == cat_desconto
        if em_promocao:
            preco_unit = max(1, preco_unit * (100 - desconto_pct) // 100)
        subtotal = preco_unit * qtd
        custo_total += subtotal
        linhas.append({"key": key, "quantidade": qtd, "subtotal": subtotal, "em_promocao": em_promocao})

    if user["lumicoins"] < custo_total:
        return {
            "ok": False,
            "reason": "saldo_insuficiente",
            "custo_total": custo_total,
            "saldo": user["lumicoins"],
        }

    user["lumicoins"] -= custo_total
    for item in linhas:
        user["ingredientes"][item["key"]] = user["ingredientes"].get(item["key"], 0) + item["quantidade"]
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
    novas = verificar_conquistas(user)
    return {"ok": True, "user": user, "upgrade": prox, "custo": custo, "conquistas_novas": novas}


def preparar(user_data: dict, bebida_raw: str, quantidade: int = 1, agora: float | None = None, rng=random) -> dict:
    user = _clone_user(user_data)
    agora_ts = time.time() if agora is None else agora

    cd = cooldown_restante(user.get("cd_preparar", 0), CD_PREPARAR, agora_ts)
    if cd:
        return {"ok": False, "reason": "cooldown", "cooldown": cd}

    bebida = normalizar_bebida(bebida_raw)
    catalogo = _catalogo_do_usuario(user)
    if bebida not in catalogo:
        return {"ok": False, "reason": "bebida_invalida", "opcoes": list(catalogo)}

    quantidade = max(1, min(quantidade, 20))  # limite: 1–20 por vez
    bebida_data = catalogo[bebida]

    # Verifica se tem ingredientes para TODAS as unidades antes de começar
    receita_total = {key: qtd * quantidade for key, qtd in bebida_data["receita"].items()}
    faltando = _missing_ingredients(user, receita_total)
    if faltando:
        return {"ok": False, "reason": "ingredientes_insuficientes", "bebida": bebida, "faltando": faltando}

    cafeteira = get_cafeteira_info(user)
    bebida_dia = get_bebida_do_dia()
    xp_base_unit = aplicar_bonus_percentual(bebida_data["xp"], cafeteira["bonus_xp"])
    bonus_dia_xp_unit = 0
    if bebida == bebida_dia:
        bonus_dia_xp_unit = max(1, bebida_data["xp"] * get_bonus_bebida_xp_pct() // 100)

    xp_total = 0
    bonus_dia_xp_total = 0

    for _ in range(quantidade):
        for key, qtd in bebida_data["receita"].items():
            user["ingredientes"][key] = user["ingredientes"].get(key, 0) - qtd
            if user["ingredientes"][key] <= 0:
                del user["ingredientes"][key]

        user["estoque"][bebida] = user["estoque"].get(bebida, 0) + 1
        xp_total += xp_base_unit + bonus_dia_xp_unit
        bonus_dia_xp_total += bonus_dia_xp_unit

    user["xp"] += xp_total
    user["stats"]["bebidas_feitas"] += quantidade
    if bebida in BEBIDAS and bebida not in user["stats"]["bebidas_distintas"]:
        user["stats"]["bebidas_distintas"].append(bebida)
    user["cd_preparar"] = agora_ts
    novas = verificar_conquistas(user)
    return {
        "ok": True,
        "user": user,
        "bebida": bebida,
        "bebida_data": bebida_data,
        "quantidade": quantidade,
        "xp_ganho": xp_total,
        "bonus_dia_xp": bonus_dia_xp_total,
        "e_bebida_do_dia": bebida == bebida_dia,
        "conquistas_novas": novas,
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
        return {"ok": True, "user": user, "acertou": False, "tentativa": tentativa, "conquistas_novas": []}

    bebida_data = RECEITAS_SECRETAS[chave_acerto]
    ja_desbloqueada = chave_acerto in user.get("receitas_desbloqueadas", [])
    if not ja_desbloqueada:
        user.setdefault("receitas_desbloqueadas", []).append(chave_acerto)
    user["estoque"][chave_acerto] = user["estoque"].get(chave_acerto, 0) + 1
    xp_ganho = bebida_data["xp"] * (2 if not ja_desbloqueada else 1)
    bonus_moedas = 100 if not ja_desbloqueada else 0
    user["xp"] += xp_ganho
    user["lumicoins"] += bonus_moedas
    novas = verificar_conquistas(user)
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
        "conquistas_novas": novas,
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
    # Bônus extra se for a bebida do dia
    bebida_dia = get_bebida_do_dia()
    bonus_dia_venda = 0
    if bebida == bebida_dia:
        bonus_dia_venda = max(1, bebida_data["preco_venda"] * get_bonus_bebida_venda_pct() // 100)
        valor_venda += bonus_dia_venda
    user["lumicoins"] += valor_venda
    return {
        "ok": True,
        "user": user,
        "bebida": bebida,
        "bebida_data": bebida_data,
        "valor_venda": valor_venda,
        "bonus_dia_venda": bonus_dia_venda,
        "e_bebida_do_dia": bebida == bebida_dia,
    }


def _cliente_por_nome(nome: str, rng=random) -> dict:
    for cliente in CLIENTES:
        if cliente["nome"] == nome:
            return cliente
    return rng.choice(CLIENTES)


def is_client_expired(user_data: dict, agora: float | None = None) -> bool:
    """Retorna True se o cliente pendente já expirou (passou CD_CLIENTE)."""
    pendente = user_data.get("cliente_pendente")
    if not isinstance(pendente, dict):
        return False
    agora = time.time() if agora is None else agora
    return (agora - pendente.get("ts", agora)) >= CD_CLIENTE


def _aplicar_recompensa_atendimento(user: dict, bebida: str, bebida_data: dict, vip: bool = False, rng=random) -> dict:
    if vip:
        gorjeta_base = rng.randint(80, 220)
        bonus_xp = rng.randint(15, 40)
    else:
        gorjeta_base = rng.randint(20, 60)
        bonus_xp = rng.randint(5, 15)

    cafeteira = get_cafeteira_info(user)

    gorjeta = aplicar_bonus_percentual(gorjeta_base, cafeteira["bonus_atendimento"])
    valor_venda = aplicar_bonus_percentual(bebida_data.get("preco_venda", 0), cafeteira.get("bonus_venda", 0))

    bonus_moedas = valor_venda + gorjeta

    user["estoque"][bebida] -= 1
    if user["estoque"][bebida] == 0:
        del user["estoque"][bebida]
    user["lumicoins"] += bonus_moedas
    user["xp"] += bonus_xp
    return {
        "bonus_base": gorjeta_base,
        "valor_venda": valor_venda,
        "bonus_moedas": bonus_moedas,
        "bonus_xp": bonus_xp,
    }


def iniciar_atendimento(user_data: dict, agora: float | None = None, rng=random) -> dict:
    user = _clone_user(user_data)
    agora_ts = time.time() if agora is None else agora

    # Se já tem cliente pendente verifica se expirou
    pendente = user.get("cliente_pendente")
    if pendente:
        if is_client_expired(user, agora_ts):
            # Cliente já foi embora — limpa silenciosamente
            user.pop("cliente_pendente", None)
        else:
            return {"ok": True, "user": user, "status": "pendente", "pendente": pendente}

    cd = cooldown_restante(user["cd_atender"], CD_ATENDER, agora_ts)
    if cd:
        return {"ok": False, "reason": "cooldown", "cooldown": cd}

    # Decide se o cliente é VIP
    eh_vip = rng.randint(1, 100) <= VIP_CHANCE
    if eh_vip:
        cliente = rng.choice(CLIENTES_VIP)
        # VIP pede receita secreta desbloqueada (se tiver) ou bebida premium
        desbloqueadas = [k for k in user.get("receitas_desbloqueadas", []) if k in RECEITAS_SECRETAS]
        pool_vip = desbloqueadas or PREMIUM_BEBIDAS
        bebida = rng.choice(pool_vip)
        catalogo_bebida = BEBIDAS.get(bebida) or RECEITAS_SECRETAS.get(bebida)
    else:
        cliente = rng.choice(CLIENTES)
        bebida = rng.choice(list(BEBIDAS.keys()))
        catalogo_bebida = BEBIDAS[bebida]

    user["cliente_pendente"] = {
        "cliente": cliente["nome"],
        "bebida": bebida,
        "ts": agora_ts,
        "vip": eh_vip,
    }
    user["cd_atender"] = agora_ts
    intro = rng.choice(cliente["pedido_intro"]).format(bebida=catalogo_bebida["nome"])
    return {
        "ok": True,
        "user": user,
        "status": "novo",
        "cliente": cliente,
        "bebida": bebida,
        "bebida_data": catalogo_bebida,
        "intro": intro,
        "vip": eh_vip,
    }


def servir_atendimento(user_data: dict, bebida_raw: str, rng=random) -> dict:
    user = _clone_user(user_data)
    pendente = user.get("cliente_pendente")
    if not pendente:
        return {"ok": False, "reason": "sem_cliente"}

    # Checa expiração
    if is_client_expired(user):
        user.pop("cliente_pendente", None)
        return {"ok": False, "reason": "cliente_expirado", "user": user}

    bebida_oferecida = normalizar_bebida(bebida_raw)
    all_clients = CLIENTES + CLIENTES_VIP
    cliente = next((c for c in all_clients if c["nome"] == pendente["cliente"]), rng.choice(CLIENTES))
    bebida_pedida = pendente["bebida"]
    eh_vip = pendente.get("vip", False)
    bebida_data = BEBIDAS.get(bebida_pedida) or RECEITAS_SECRETAS.get(bebida_pedida)

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
            "vip": eh_vip,
            "conquistas_novas": [],
        }

    recompensa = _aplicar_recompensa_atendimento(user, bebida_pedida, bebida_data, vip=eh_vip, rng=rng)
    user.pop("cliente_pendente", None)
    user["stats"]["clientes_atendidos"] += 1
    if eh_vip:
        user["stats"]["vip_atendidos"] += 1
    novas = verificar_conquistas(user)
    return {
        "ok": True,
        "user": user,
        "status": "sucesso",
        "cliente": cliente,
        "bebida": bebida_pedida,
        "bebida_data": bebida_data,
        "vip": eh_vip,
        "conquistas_novas": novas,
        **recompensa,
    }


def dar_moedas(user_sender: dict, user_receiver: dict, quantidade: int) -> dict:
    if quantidade < 1:
        return {"ok": False, "reason": "quantidade_invalida"}
    sender = _clone_user(user_sender)
    receiver = _clone_user(user_receiver)
    if sender["lumicoins"] < quantidade:
        return {"ok": False, "reason": "saldo_insuficiente", "saldo": sender["lumicoins"]}
    sender["lumicoins"] -= quantidade
    receiver["lumicoins"] += quantidade
    return {"ok": True, "user_sender": sender, "user_receiver": receiver, "quantidade": quantidade}


def executar_troca(
    user_a: dict, user_b: dict,
    ing_a: str, qtd_a: int,
    ing_b: str, qtd_b: int,
) -> dict:
    if ing_a not in INGREDIENTES:
        return {"ok": False, "reason": "ingrediente_invalido", "ingrediente": ing_a}
    if ing_b not in INGREDIENTES:
        return {"ok": False, "reason": "ingrediente_invalido", "ingrediente": ing_b}
    a = _clone_user(user_a)
    b = _clone_user(user_b)
    if a["ingredientes"].get(ing_a, 0) < qtd_a:
        return {
            "ok": False, "reason": "sem_ingredientes_a",
            "ingrediente": ing_a,
            "tem": a["ingredientes"].get(ing_a, 0),
            "precisa": qtd_a,
        }
    if b["ingredientes"].get(ing_b, 0) < qtd_b:
        return {
            "ok": False, "reason": "sem_ingredientes_b",
            "ingrediente": ing_b,
            "tem": b["ingredientes"].get(ing_b, 0),
            "precisa": qtd_b,
        }
    a["ingredientes"][ing_a] -= qtd_a
    if a["ingredientes"][ing_a] == 0:
        del a["ingredientes"][ing_a]
    a["ingredientes"][ing_b] = a["ingredientes"].get(ing_b, 0) + qtd_b

    b["ingredientes"][ing_b] -= qtd_b
    if b["ingredientes"][ing_b] == 0:
        del b["ingredientes"][ing_b]
    b["ingredientes"][ing_a] = b["ingredientes"].get(ing_a, 0) + qtd_a

    return {
        "ok": True,
        "user_a": a, "user_b": b,
        "ing_a": ing_a, "qtd_a": qtd_a,
        "ing_b": ing_b, "qtd_b": qtd_b,
    }


def roubar_atendimento(user_data: dict, bebida_raw: str, candidatos: list[tuple[str, dict]], rng=random) -> dict:
    user = _clone_user(user_data)
    if user.get("cliente_pendente"):
        return {"ok": False, "reason": "cliente_proprio_pendente"}

    bebida = normalizar_bebida(bebida_raw)
    bebida_data = BEBIDAS.get(bebida)
    if bebida_data is None:
        return {"ok": False, "reason": "bebida_invalida", "bebida": bebida}
    if not user["estoque"].get(bebida, 0):
        return {"ok": False, "reason": "sem_estoque", "bebida": bebida, "bebida_data": bebida_data}

    opcoes: list[tuple[float, str, dict, dict]] = []
    for alvo_id, alvo_data in candidatos:
        alvo = _clone_user(alvo_data)
        pendente = alvo.get("cliente_pendente")
        if not isinstance(pendente, dict) or pendente.get("bebida") != bebida:
            continue
        # Não roubar clientes já expirados
        if is_client_expired(alvo):
            continue
        opcoes.append((float(alvo.get("cd_atender") or 0), str(alvo_id), alvo, pendente))

    if not opcoes:
        return {"ok": False, "reason": "sem_cliente_roubavel", "bebida": bebida, "bebida_data": bebida_data}

    _, alvo_id, alvo, pendente = min(opcoes, key=lambda item: item[0])
    eh_vip = pendente.get("vip", False)
    all_clients = CLIENTES + CLIENTES_VIP
    cliente = next((c for c in all_clients if c["nome"] == pendente.get("cliente", "")), rng.choice(CLIENTES))
    recompensa = _aplicar_recompensa_atendimento(user, bebida, bebida_data, vip=eh_vip, rng=rng)
    alvo.pop("cliente_pendente", None)
    user["stats"]["clientes_atendidos"] += 1
    user["stats"]["roubos"] += 1
    if eh_vip:
        user["stats"]["vip_atendidos"] += 1
    novas = verificar_conquistas(user)
    return {
        "ok": True,
        "user": user,
        "status": "roubo",
        "alvo_id": alvo_id,
        "alvo_user": alvo,
        "cliente": cliente,
        "bebida": bebida,
        "bebida_data": bebida_data,
        "vip": eh_vip,
        "conquistas_novas": novas,
        **recompensa,
    }
