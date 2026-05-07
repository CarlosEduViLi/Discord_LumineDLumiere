"""
cafe_core.py — Dados, constantes e persistência do ☕ Café da Lumine.
"""
import json
import os
import time

DATA_PATH = os.path.join(os.path.dirname(__file__), "cafe_data.json")

# ─────────────────────────────────────────────
#  INGREDIENTES
# ─────────────────────────────────────────────
INGREDIENTES: dict[str, dict] = {
    # Básicos & Grãos
    "grao":       {"nome": "Grão de Café",      "emoji": "🫘", "preco": 10, "categoria": "básicos"},
    "gelo":       {"nome": "Gelo",               "emoji": "🧊", "preco": 3,  "categoria": "básicos"},
    "agua":       {"nome": "Água",               "emoji": "💧", "preco": 2,  "categoria": "básicos"},
    
    # Laticínios
    "leite":      {"nome": "Leite",              "emoji": "🥛", "preco": 8,  "categoria": "laticínios"},
    "chantilly":  {"nome": "Chantilly",          "emoji": "🍦", "preco": 12, "categoria": "laticínios"},
    "leite_cond": {"nome": "Leite Condensado",   "emoji": "🍮", "preco": 15, "categoria": "laticínios"},

    # Adoçantes & Xaropes
    "acucar":     {"nome": "Açúcar",             "emoji": "🍬", "preco": 5,  "categoria": "xaropes"},
    "caramelo":   {"nome": "Caramelo",           "emoji": "🍯", "preco": 15, "categoria": "xaropes"},
    "chocolate":  {"nome": "Chocolate",          "emoji": "🍫", "preco": 14, "categoria": "xaropes"},
    "mel":        {"nome": "Mel",                "emoji": "🐝", "preco": 18, "categoria": "xaropes"},
    "baunilha":   {"nome": "Baunilha",           "emoji": "🌼", "preco": 16, "categoria": "xaropes"},

    # Especiarias & Ervas
    "matcha":     {"nome": "Matcha",             "emoji": "🍵", "preco": 20, "categoria": "especiarias"},
    "canela":     {"nome": "Canela",             "emoji": "🪵", "preco": 12, "categoria": "especiarias"},
    "menta":      {"nome": "Menta",              "emoji": "🌿", "preco": 14, "categoria": "especiarias"},
    "pimenta":    {"nome": "Pimenta",            "emoji": "🌶️", "preco": 25, "categoria": "especiarias"},
    "sal":        {"nome": "Sal Marinho",        "emoji": "🧂", "preco": 10, "categoria": "especiarias"},
    "gengibre":   {"nome": "Gengibre",           "emoji": "🫚", "preco": 15, "categoria": "especiarias"},

    # Frutas & Extras
    "limao":      {"nome": "Limão",              "emoji": "🍋", "preco": 10, "categoria": "frutas"},
    "morango":    {"nome": "Morango",            "emoji": "🍓", "preco": 22, "categoria": "frutas"},
    "coco":       {"nome": "Coco",               "emoji": "🥥", "preco": 18, "categoria": "frutas"},
    "sakura":     {"nome": "Flor de Cerejeira",  "emoji": "🌸", "preco": 30, "categoria": "frutas"},
}

# ─────────────────────────────────────────────
#  BEBIDAS
# ─────────────────────────────────────────────
# receita: dict { ingrediente_key: quantidade }
BEBIDAS: dict[str, dict] = {
    "cafe_simples": {
        "nome": "Café Simples",
        "emoji": "☕",
        "receita": {"grao": 1},
        "preco_venda": 20,
        "xp": 5,
    },
    "cappuccino": {
        "nome": "Cappuccino",
        "emoji": "🧋",
        "receita": {"grao": 1, "leite": 1},
        "preco_venda": 35,
        "xp": 10,
    },
    "latte": {
        "nome": "Latte",
        "emoji": "🥤",
        "receita": {"grao": 1, "leite": 2},
        "preco_venda": 40,
        "xp": 12,
    },
    "cafe_gelado": {
        "nome": "Café Gelado",
        "emoji": "🧊",
        "receita": {"grao": 1, "gelo": 2},
        "preco_venda": 45,
        "xp": 14,
    },
    "frappuccino": {
        "nome": "Frappuccino",
        "emoji": "🥛",
        "receita": {"grao": 1, "leite": 1, "gelo": 2, "chantilly": 1},
        "preco_venda": 70,
        "xp": 20,
    },
    "caramel_macchiato": {
        "nome": "Caramel Macchiato",
        "emoji": "🍯",
        "receita": {"grao": 1, "leite": 1, "caramelo": 1},
        "preco_venda": 65,
        "xp": 18,
    },
    "matcha_latte": {
        "nome": "Matcha Latte",
        "emoji": "🍵",
        "receita": {"matcha": 1, "leite": 2},
        "preco_venda": 60,
        "xp": 17,
    },
    "mocha": {
        "nome": "Mocha",
        "emoji": "🍫",
        "receita": {"grao": 1, "leite": 1, "chocolate": 1},
        "preco_venda": 60,
        "xp": 17,
    },
}

# ─────────────────────────────────────────────
#  RECEITAS SECRETAS
# ─────────────────────────────────────────────
RECEITAS_SECRETAS: dict[str, dict] = {
    "cafe_arabias": {
        "nome": "Café das Arábias",
        "emoji": "🧞‍♂️",
        "receita": {"grao": 1, "canela": 1, "pimenta": 1},
        "preco_venda": 120,
        "xp": 50,
    },
    "mocha_inverno": {
        "nome": "Mocha Branco de Inverno",
        "emoji": "❄️",
        "receita": {"grao": 1, "leite": 1, "baunilha": 1, "chantilly": 1},
        "preco_venda": 150,
        "xp": 60,
    },
    "cold_brew_limao": {
        "nome": "Cold Brew de Limão",
        "emoji": "🍋",
        "receita": {"grao": 1, "agua": 1, "gelo": 1, "limao": 1},
        "preco_venda": 110,
        "xp": 45,
    },
    "cafe_sal_marinho": {
        "nome": "Café com Sal Marinho",
        "emoji": "🌊",
        "receita": {"grao": 1, "caramelo": 1, "sal": 1},
        "preco_venda": 130,
        "xp": 55,
    },
    "frape_morango": {
        "nome": "Frapê de Morango Selvagem",
        "emoji": "🍓",
        "receita": {"leite": 1, "gelo": 1, "morango": 1, "chantilly": 1},
        "preco_venda": 160,
        "xp": 65,
    },
    "latte_sakura": {
        "nome": "Latte de Flor de Cerejeira",
        "emoji": "🌸",
        "receita": {"grao": 1, "leite": 1, "sakura": 1, "mel": 1},
        "preco_venda": 200,
        "xp": 80,
    },
    "choconta": {
        "nome": "Choconta",
        "emoji": "🌿",
        "receita": {"chocolate": 1, "leite": 1, "menta": 1},
        "preco_venda": 140,
        "xp": 55,
    },
    "gingerbread_latte": {
        "nome": "Gingerbread Latte",
        "emoji": "🍪",
        "receita": {"grao": 1, "leite": 1, "gengibre": 1, "canela": 1},
        "preco_venda": 150,
        "xp": 60,
    },
    "cocoa_espresso": {
        "nome": "Cocoa Espresso",
        "emoji": "🥥",
        "receita": {"grao": 1, "leite": 1, "coco": 1, "chocolate": 1},
        "preco_venda": 160,
        "xp": 65,
    },
    "lagrimas_anjo": {
        "nome": "Lágrimas de Anjo",
        "emoji": "👼",
        "receita": {"agua": 1, "gelo": 1, "sakura": 1, "limao": 1},
        "preco_venda": 250,
        "xp": 100,
    },
    "honey_citrus_tea": {
        "nome": "Honey Citrus Tea",
        "emoji": "🍯",
        "receita": {"agua": 1, "mel": 1, "limao": 1, "gengibre": 1},
        "preco_venda": 140,
        "xp": 55,
    },
    "bomba_gelo": {
        "nome": "Bomba de Gelo",
        "emoji": "🥶",
        "receita": {"grao": 1, "gelo": 2, "menta": 1},
        "preco_venda": 120,
        "xp": 45,
    },
    "cafe_cubano": {
        "nome": "Café Cubano",
        "emoji": "🌴",
        "receita": {"grao": 1, "acucar": 2},
        "preco_venda": 90,
        "xp": 35,
    },
    "pink_matcha": {
        "nome": "Pink Matcha",
        "emoji": "🎀",
        "receita": {"matcha": 1, "leite": 1, "morango": 1},
        "preco_venda": 170,
        "xp": 70,
    },
    "beijo_caramelo_salgado": {
        "nome": "Beijo de Caramelo Salgado",
        "emoji": "💋",
        "receita": {"grao": 1, "leite_cond": 1, "caramelo": 1, "sal": 1},
        "preco_venda": 180,
        "xp": 75,
    },
}

# ─────────────────────────────────────────────
#  CLIENTES (diversidade de personalidades)
# ─────────────────────────────────────────────
CLIENTES: list[dict] = [
    {
        "nome": "Mia",
        "emoji": "🐱",
        "personalidade": "tímida",
        "image_tags": {"pedido": "blush", "feliz": "smile", "triste": "cry"},
        "pedido_intro": [
            "psst... com licença... você tem {bebida}? perguntou baixinho, corando.",
            "é... um {bebida} por favor... s-se não for pedir muito...",
        ],
        "agradecimento": [
            "o-obrigada... ficou delicioso... ♡",
            "*murmura* estava ótimo... v-voltarei...",
        ],
        "recusa": [
            "ah... não tem problema... fico com água mesmo... *suspiro*",
            "tudo bem... vou tentar no próximo dia...",
        ],
    },
    {
        "nome": "Rex",
        "emoji": "🐶",
        "personalidade": "animado",
        "image_tags": {"pedido": "wave", "feliz": "happy", "triste": "pout"},
        "pedido_intro": [
            "OLÁ!! Quero um {bebida} agora pleaseee!! 🐾",
            "BOA TARDE!! Me dá um {bebida}? tô com MUITA fome!!",
        ],
        "agradecimento": [
            "UAU!! Que delícia!! Voltarei amanhã!! 🐾✨",
            "INCRÍVEL!! O melhor café da cidade!! Muito obrigado!! 🎉",
        ],
        "recusa": [
            "aw... nããão... mas tudo bem, tentarei de novo!! 🐾",
            "que pena! mas você é incrível do mesmo jeito!! 💛",
        ],
    },
    {
        "nome": "Lúcia",
        "emoji": "🦊",
        "personalidade": "elegante",
        "image_tags": {"pedido": "nod", "feliz": "smug", "triste": "shrug"},
        "pedido_intro": [
            "Boa tarde. Gostaria de um {bebida}, por favor.",
            "Posso pedir um {bebida}? Sem pressa.",
        ],
        "agradecimento": [
            "Excelente. Bem preparado. Voltarei em breve.",
            "Perfeito. Exatamente como esperava.",
        ],
        "recusa": [
            "Compreendo. Talvez na próxima visita.",
            "Sem problema. Boa sorte com o estoque.",
        ],
    },
    {
        "nome": "Pip",
        "emoji": "🐹",
        "personalidade": "curioso",
        "image_tags": {"pedido": "think", "feliz": "wink", "triste": "pout"},
        "pedido_intro": [
            "Oi!! O que é {bebida}? Tem gosto de quê? Posso provar?? 🌟",
            "Hm hm hm... {bebida} parece interessante... me conta mais!",
        ],
        "agradecimento": [
            "Nossa!! Nunca tinha tomado assim!! Que descoberta!! ✨",
            "Incrível! Aprendi muito hoje! Obrigado barista!! 🌱",
        ],
        "recusa": [
            "Ah é? Mas por que não tem? Como se faz? 🤔",
            "Entendo... mas e se eu trouxesse os ingredientes?",
        ],
    },
    {
        "nome": "Stella",
        "emoji": "🐰",
        "personalidade": "sonhadora",
        "image_tags": {"pedido": "stare", "feliz": "smile", "triste": "cry"},
        "pedido_intro": [
            "...achei que {bebida} combina com dias nublados... posso pedir um? 🌧️",
            "você sabe... {bebida} me lembra algo... posso tomar um?",
        ],
        "agradecimento": [
            "...estava quente, cheiroso e gostoso... obrigada ♡",
            "...foi como um abraço em forma de bebida... 🌸",
        ],
        "recusa": [
            "...não tem problema... às vezes o que queremos não está disponível...",
            "...tudo bem... há outras bebidas no mundo ♡",
        ],
    },
    {
        "nome": "Bruno",
        "emoji": "🐻",
        "personalidade": "faminto",
        "image_tags": {"pedido": "bored", "feliz": "happy", "triste": "shake"},
        "pedido_intro": [
            "Oi!! Tô com uma fome danada... tem {bebida}? E tem petisco? 🍪",
            "Hm... {bebida} dá pra acompanhar com biscoito? Perguntei só perguntando.",
        ],
        "agradecimento": [
            "Aaahh que bom!! Precisava disso!! Obrigado!! 🍪",
            "Delicioso!! Agora só falta o lanche!! Haha!!",
        ],
        "recusa": [
            "Eita... tudo bem, vou só comer o biscoito que trouxe então.",
            "Que pena... da próxima vez preparo mais cedo!",
        ],
    },
]

# ─────────────────────────────────────────────
#  NÍVEIS DE BARISTA
# ─────────────────────────────────────────────
NIVEIS: list[dict] = [
    {"nivel": 1, "titulo": "Barista Novato",      "emoji": "☕",  "xp_min": 0},
    {"nivel": 2, "titulo": "Barista Aprendiz",    "emoji": "☕",  "xp_min": 100},
    {"nivel": 3, "titulo": "Barista Experiente",  "emoji": "☕",  "xp_min": 300},
    {"nivel": 4, "titulo": "Barista Sênior",      "emoji": "🌟", "xp_min": 700},
    {"nivel": 5, "titulo": "Mestre Barista",      "emoji": "🌟", "xp_min": 1500},
    {"nivel": 6, "titulo": "Lenda do Café",       "emoji": "👑", "xp_min": 3000},
]


def get_nivel(xp: int) -> dict:
    """Retorna o dict de nível correspondente ao XP."""
    atual = NIVEIS[0]
    for n in NIVEIS:
        if xp >= n["xp_min"]:
            atual = n
    return atual


# ─────────────────────────────────────────────
#  UPGRADES
# ─────────────────────────────────────────────
UPGRADES_CAFETEIRA: list[dict] = [
    {
        "nivel": 0,
        "nome": "Cafeteira Inicial",
        "custo": 0,
        "bonus_venda": 0,
        "bonus_xp": 0,
        "bonus_atendimento": 0,
        "chance_economizar": 0,
    },
    {
        "nivel": 1,
        "nome": "Cafeteira Polida",
        "custo": 300,
        "bonus_venda": 5,
        "bonus_xp": 5,
        "bonus_atendimento": 0,
        "chance_economizar": 0,
    },
    {
        "nivel": 2,
        "nome": "Caldeira Reforçada",
        "custo": 750,
        "bonus_venda": 10,
        "bonus_xp": 10,
        "bonus_atendimento": 0,
        "chance_economizar": 0,
    },
    {
        "nivel": 3,
        "nome": "Moedor Embutido",
        "custo": 1500,
        "bonus_venda": 15,
        "bonus_xp": 15,
        "bonus_atendimento": 5,
        "chance_economizar": 0,
    },
    {
        "nivel": 4,
        "nome": "Máquina Profissional",
        "custo": 3000,
        "bonus_venda": 20,
        "bonus_xp": 20,
        "bonus_atendimento": 10,
        "chance_economizar": 0,
    },
    {
        "nivel": 5,
        "nome": "Luminepressa Deluxe",
        "custo": 6000,
        "bonus_venda": 30,
        "bonus_xp": 25,
        "bonus_atendimento": 15,
        "chance_economizar": 5,
    },
]


def get_cafeteira_nivel(user_data: dict) -> int:
    upgrades = user_data.setdefault("upgrades", {})
    if not isinstance(upgrades, dict):
        upgrades = {}
        user_data["upgrades"] = upgrades
    nivel = int(upgrades.get("cafeteira", 0) or 0)
    return max(0, min(nivel, len(UPGRADES_CAFETEIRA) - 1))


def get_cafeteira_info(user_data: dict) -> dict:
    return UPGRADES_CAFETEIRA[get_cafeteira_nivel(user_data)]


def aplicar_bonus_percentual(valor: int, percentual: int) -> int:
    if percentual <= 0:
        return valor
    return valor * (100 + percentual) // 100


# ─────────────────────────────────────────────
#  COOLDOWNS (em segundos)
# ─────────────────────────────────────────────
CD_TRABALHAR = 30 * 60   # 30 minutos
CD_ATENDER   = 60 * 60   # 1 hora

# ─────────────────────────────────────────────
#  TRABALHAR — frases temáticas
# ─────────────────────────────────────────────
FRASES_TRABALHAR: list[str] = [
    "Você limpou as mesas e deixou tudo cheiroso! ✨",
    "Você atendeu a fila do almoço sem deixar ninguém esperando! 🏃",
    "Você preparou o mise en place do dia com perfeição! 📋",
    "Você ajudou o caixa e distribuiu sorriso pra todo mundo! 😊",
    "Você calibrou a máquina de café e ela ficou perfeita! ⚙️",
    "Você organizou a vitrine de doces lindamente! 🍰",
    "Você decorou a lousa do cardápio com sua melhor letra! 🖊️",
    "Você recebeu os fornecedores e organizou o estoque! 📦",
    "Você varreu o salão e fez tudo brilhar! ✨",
    "Você ensinou uma receita nova a um colega barista! 👩‍🍳",
]

# ─────────────────────────────────────────────
#  INVENTAR — frases de sucesso e erro
# ─────────────────────────────────────────────
FRASES_INVENTAR_ERRO: list[str] = [
    "Ai não... a mistura espumou até o teto! Acho que precisamos limpar isso... 💦",
    "Ugh... o cheiro disso não está muito bom... Que tal não servirmos pra ninguém? 🤢",
    "Puxa vida, a cor ficou um verde musgo muito esquisito... Melhor jogarmos fora com cuidado! 🧪",
    "Acho que isso derreteu o copo... De onde você tirou essa ideia? 🥺",
    "Oops! Virou uma pedra! Talvez sirva como peso de papel? 🪨",
    "Hmm, provei e... ah não, minha língua tá dormente! Não faça mais isso! 😵‍💫",
    "Sabe, a criatividade é importante, mas isso aqui é um desastre culinário... 🌪️",
    "Essa mistura fez um barulho estranho... como se estivesse chorando! 😢 Melhor descartar!",
    "Ahhh! Por que está brilhando no escuro?! Ingredientes normais não fazem isso! ☢️",
    "Acho que criamos uma nova forma de vida... e ela parece zangada! Corre! 🦠",
]

FRASES_INVENTAR_ACERTO: list[str] = [
    "UAU! O aroma que subiu dessa xícara é maravilhoso! Você é um gênio! ✨",
    "Meu Deus, isso ficou perfeito! O sabor é indescritível... Temos um novo sucesso! 🏆",
    "Incrível! Como você pensou nessa combinação?! As proporções estão exatas! 🌟",
    "Que delícia!! Eu já posso imaginar os clientes fazendo fila pra provar isso! 🤤",
    "Isso não é apenas uma bebida, é arte em forma líquida! Parabéns! 🎨",
    "A textura, a cor, o cheirinho... Tudo ficou per-fei-to! Você arrasou! 💖",
    "Você conseguiu! Acabamos de descobrir um tesouro escondido no nosso estoque! 💎",
    "Nossa! É tão gostoso que me deu vontade de chorar de emoção... 🥺💙",
    "Magia pura! Parece até que foi feito por fadas... Parabéns pela descoberta! 🧚‍♀️",
    "Anotado no caderno de receitas secretas com letras de ouro! Ficou sensacional! 👑",
]

# ─────────────────────────────────────────────
#  PERSISTÊNCIA JSON
# ─────────────────────────────────────────────

def _load_raw() -> dict:
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _default_user() -> dict:
    return {
        "lumicoins": 0,
        "xp": 0,
        "ingredientes": {},   # { key: quantidade }
        "estoque": {},        # { bebida_key: quantidade }
        "cd_trabalhar": 0,    # timestamp unix do último trabalho
        "cd_atender": 0,      # timestamp unix do último atendimento
        "receitas_desbloqueadas": [], # lista de chaves de receitas secretas
        "upgrades": {"cafeteira": 0},
    }


def get_user(guild_id: int, user_id: int) -> dict:
    """Retorna os dados do usuário (cria se não existir)."""
    data = _load_raw()
    gkey = str(guild_id)
    ukey = str(user_id)
    data.setdefault(gkey, {})
    data[gkey].setdefault(ukey, _default_user())
    # Garante campos novos em contas antigas
    for k, v in _default_user().items():
        data[gkey][ukey].setdefault(k, v)
    if not isinstance(data[gkey][ukey].get("upgrades"), dict):
        data[gkey][ukey]["upgrades"] = {}
    data[gkey][ukey].setdefault("upgrades", {})
    data[gkey][ukey]["upgrades"].setdefault("cafeteira", 0)
    return data[gkey][ukey]


def save_user(guild_id: int, user_id: int, user_data: dict) -> None:
    """Salva os dados do usuário no JSON."""
    data = _load_raw()
    gkey = str(guild_id)
    ukey = str(user_id)
    data.setdefault(gkey, {})
    data[gkey][ukey] = user_data
    _save_raw(data)


def get_all_users(guild_id: int) -> dict[str, dict]:
    """Retorna todos os usuários de uma guild."""
    data = _load_raw()
    return data.get(str(guild_id), {})


# ─────────────────────────────────────────────
#  HELPERS de cooldown
# ─────────────────────────────────────────────

def cooldown_restante(ts_ultimo: float, duracao: float) -> float:
    """Retorna segundos restantes do cooldown (0 se já liberado)."""
    restante = duracao - (time.time() - ts_ultimo)
    return max(0.0, restante)


def formatar_tempo(segundos: float) -> str:
    """Formata segundos em string legível: 'Xmin Ys'."""
    segundos = int(segundos)
    if segundos < 60:
        return f"{segundos}s"
    m, s = divmod(segundos, 60)
    return f"{m}min {s}s" if s else f"{m}min"
