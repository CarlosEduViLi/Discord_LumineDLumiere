from __future__ import annotations

import random

from .catalog import RECEITAS_SECRETAS


PISTAS_RECEITAS_SECRETAS: dict[str, dict[str, str]] = {
    "cafe_arabias": {
        "tema": "Tem bebida que parece cruzar um mercado antigo, quente e perfumado.",
        "categoria": "Ela nasce de um grão forte e de especiarias que aquecem a xícara.",
        "ingrediente": "Uma pitada ardida pode transformar um café comum em algo lendário.",
    },
    "mocha_inverno": {
        "tema": "Algumas bebidas parecem feitas para dias frios e mãos geladas.",
        "categoria": "Procure algo cremoso, doce e com perfume macio de confeitaria.",
        "ingrediente": "Baunilha costuma deixar o inverno bem mais gentil.",
    },
    "cold_brew_limao": {
        "tema": "Essa pista tem gosto de tarde clara, copo suado e frescor cítrico.",
        "categoria": "Pense em café frio, água, gelo e um toque de fruta azedinha.",
        "ingrediente": "Limão combina melhor com café gelado do que muita gente imagina.",
    },
    "cafe_sal_marinho": {
        "tema": "Às vezes o doce fica mais bonito quando encontra uma brisa do mar.",
        "categoria": "Essa bebida mistura grão, doçura dourada e um detalhe salgado.",
        "ingrediente": "Sal marinho pode fazer o caramelo brilhar.",
    },
    "frape_morango": {
        "tema": "Tem segredo que parece sobremesa rosa batida com risada de verão.",
        "categoria": "Procure algo gelado, cremoso, frutado e com final de vitrine.",
        "ingrediente": "Morango gosta de aparecer quando a bebida vira quase sobremesa.",
    },
    "latte_sakura": {
        "tema": "Essa xícara parece uma flor caindo devagar sobre leite quente.",
        "categoria": "Ela combina grão, laticínio, flor e uma doçura delicada.",
        "ingrediente": "Flor de cerejeira pede companhia suave, não exagero.",
    },
    "choconta": {
        "tema": "Uma bebida pode ser doce e fresca ao mesmo tempo, como sobremesa depois da chuva.",
        "categoria": "Pense em chocolate, cremosidade e uma erva refrescante.",
        "ingrediente": "Menta deixa o chocolate com cara de descoberta.",
    },
    "gingerbread_latte": {
        "tema": "Essa receita cheira a biscoito saindo do forno.",
        "categoria": "Ela pede café, leite e especiarias de cozinha aconchegante.",
        "ingrediente": "Gengibre dá aquele calorzinho que fica no fundo da garganta.",
    },
    "cocoa_espresso": {
        "tema": "Alguns cafés parecem sobremesa tropical com energia de espresso.",
        "categoria": "A pista aponta para grão, leite, chocolate e um toque de fruta cremosa.",
        "ingrediente": "Coco pode deixar o chocolate mais redondo.",
    },
    "lagrimas_anjo": {
        "tema": "Essa bebida é clara, fria e delicada, como uma gota brilhando no copo.",
        "categoria": "Não começa com café: procure água, gelo, flor e cítrico.",
        "ingrediente": "Flor de cerejeira também sabe ser refrescante.",
    },
    "honey_citrus_tea": {
        "tema": "Tem segredo que parece remédio carinhoso para dia cansado.",
        "categoria": "Pense em água, doçura natural, cítrico e uma raiz quente.",
        "ingrediente": "Mel e gengibre costumam conversar muito bem.",
    },
    "bomba_gelo": {
        "tema": "Essa é para quem quer acordar até os pensamentos.",
        "categoria": "É café frio com mais gelo do que juízo e uma erva refrescante.",
        "ingrediente": "Menta pode deixar o gelo ainda mais intenso.",
    },
    "cafe_cubano": {
        "tema": "Pequeno, forte e doce, como um empurrãozinho de energia.",
        "categoria": "Não complique demais: grão e uma doçura generosa já contam uma história.",
        "ingrediente": "Às vezes a resposta é adoçar mais do que parece sensato.",
    },
    "pink_matcha": {
        "tema": "Essa bebida parece ter vestido uma fita rosa.",
        "categoria": "Verde, cremoso e frutado: a pista mora nesse contraste.",
        "ingrediente": "Matcha também pode ficar delicado com fruta vermelha.",
    },
    "beijo_caramelo_salgado": {
        "tema": "Esse segredo parece doce de balcão com um final salgado.",
        "categoria": "Misture café, doçura cremosa, caramelo e um toque de mar.",
        "ingrediente": "Leite condensado deixa essa pista bem mais grudenta.",
    },
}

PISTAS_FALAS: dict[str, object] = {
    "lumine": [
        'Enquanto arrumava a bancada, a Lumine comentou: "{pista}"',
        'Lumine rabiscou algo no caderninho de receitas e sorriu: "{pista}"',
        'Entre uma mesa e outra, Lumine deixou escapar uma inspiração: "{pista}"',
    ],
    "cliente": {
        "tímida": [
            '{nome} falou baixinho, quase escondendo o rosto: "{pista}"',
            '{nome} mexeu na xícara e murmurou: "{pista}"',
        ],
        "animado": [
            '{nome} abriu um sorriso enorme: "{pista}"',
            '{nome} quase pulou da cadeira com a ideia: "{pista}"',
        ],
        "elegante": [
            '{nome} observou com calma: "{pista}"',
            '{nome} ajeitou a postura e comentou: "{pista}"',
        ],
        "curioso": [
            '{nome} inclinou a cabeça, cheio de perguntas: "{pista}"',
            '{nome} anotou mentalmente e perguntou: "{pista}"',
        ],
        "sonhadora": [
            '{nome} olhou pela janela como se lembrasse de um sonho: "{pista}"',
            '{nome} sorriu de um jeito distante: "{pista}"',
        ],
        "faminto": [
            '{nome} pensou em voz alta entre uma mordida imaginária e outra: "{pista}"',
            '{nome} bateu na barriga e comentou: "{pista}"',
        ],
    },
}

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


def escolher_pista_receita(user_data: dict, fonte: str, chance: int, cliente: dict | None = None) -> str | None:
    if chance <= 0 or random.randint(1, 100) > chance:
        return None

    descobertas = set(user_data.get("receitas_desbloqueadas", []))
    candidatas = [k for k in RECEITAS_SECRETAS if k not in descobertas and k in PISTAS_RECEITAS_SECRETAS]
    if not candidatas:
        return None

    receita_key = random.choice(candidatas)
    camada = random.choice(("tema", "categoria", "ingrediente"))
    pista = PISTAS_RECEITAS_SECRETAS[receita_key][camada]

    if fonte == "lumine":
        return random.choice(PISTAS_FALAS["lumine"]).format(pista=pista)

    if fonte == "cliente" and cliente:
        personalidade = cliente.get("personalidade", "curioso")
        templates_por_persona = PISTAS_FALAS["cliente"]
        templates = templates_por_persona.get(personalidade) or templates_por_persona["curioso"]
        return random.choice(templates).format(nome=cliente["nome"], pista=pista)

    return pista

