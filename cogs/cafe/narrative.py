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
        "vip": False,
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
        "roubado_atendido": [
            "e-eu achei que tinham esquecido... obrigada por perceber meu pedido.",
            "ah... você trouxe? que alívio... ficou muito gostoso.",
        ],
        "timeout": [
            "e-eu... acho que ninguém me viu... vou embora então... *esconde o rosto*",
            "não tem problema... eu sempre posso voltar... talvez...",
            "*suspira baixinho e sai na ponta dos pés sem chamar atenção*",
        ],
    },
    {
        "nome": "Rex",
        "emoji": "🐶",
        "personalidade": "animado",
        "vip": False,
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
        "roubado_atendido": [
            "TROCA DE BALCÃO RELÂMPAGO!! Isso foi muito eficiente!!",
            "UAU!! Você apareceu com meu pedido como se fosse uma corrida!! Amei!!",
        ],
        "timeout": [
            "ESPEREI TANTO TEMPO!! Tô indo embora com MUITA fome!! 😤🐾",
            "que decepção!! eu tava tão animado... vou embora TRISTE!! 🐾💔",
            "não aguento esperar mais!! adeeeeus!! *sai correndo pela porta*",
        ],
    },
    {
        "nome": "Lúcia",
        "emoji": "🦊",
        "personalidade": "elegante",
        "vip": False,
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
        "roubado_atendido": [
            "Interessante. Eficiência também é uma forma de hospitalidade.",
            "Obrigada. A troca de barista foi inesperada, mas muito bem executada.",
        ],
        "timeout": [
            "Aguardei além do razoável. Boa tarde.",
            "Percebo que estão ocupados. Retornarei quando o serviço melhorar.",
            "Considerarei outras opções. Sem ressentimentos.",
        ],
    },
    {
        "nome": "Pip",
        "emoji": "🐹",
        "personalidade": "curioso",
        "vip": False,
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
        "roubado_atendido": [
            "Espera, isso conta como logística avançada de cafeteria?",
            "Nossa!! Meu pedido mudou de balcão e chegou mesmo assim! Fascinante!",
        ],
        "timeout": [
            "Interessante... então cafeterias também têm filas invisíveis? Vou pesquisar isso.",
            "Hmm, esperei bastante. Será que há um padrão nesse tempo de resposta? Indo embora!",
            "Ok, analisei os dados e... ninguém vai me atender hoje. Tchau! 🔬",
        ],
    },
    {
        "nome": "Stella",
        "emoji": "🐰",
        "personalidade": "sonhadora",
        "vip": False,
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
        "roubado_atendido": [
            "...talvez o destino só tenha mudado minha mesa de lugar...",
            "...achei bonito. Como se a bebida tivesse encontrado outro caminho até mim...",
        ],
        "timeout": [
            "...às vezes as coisas que esperamos nunca chegam... e tudo bem.",
            "...vou embora devagar, como as nuvens... sem pressa, sem mágoa... 🌫️",
            "...talvez não fosse o momento certo. Até a próxima, se houver uma...",
        ],
    },
    {
        "nome": "Bruno",
        "emoji": "🐻",
        "personalidade": "faminto",
        "vip": False,
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
        "roubado_atendido": [
            "Opa!! Chegou, então tá valendo! Barriga não liga pra balcão!",
            "Boa!! O importante é que veio rápido. Agora sim!",
        ],
        "timeout": [
            "Minha barriga não espera mais não!! Vou comer o biscoito em casa mesmo! 🍪",
            "Eita... fui ignorado... vou no mercado que é mais rápido!",
            "Passei da hora do almoço esperando... não tô bravo, tô com FOME! Tchau!",
        ],
    },
]


CLIENTES_VIP: list[dict] = [
    {
        "nome": "Lady Carmela",
        "emoji": "🦋",
        "personalidade": "aristocrata",
        "vip": True,
        "image_tags": {"pedido": "smug", "feliz": "smile", "triste": "shrug"},
        "pedido_intro": [
            "*ergue o queixo* Estou de passagem pela cidade e espero que {bebida} aqui seja à altura da minha reputação.",
            "Darling, pedi {bebida} em Paris, Tóquio e Nova York. Convença-me de que vocês merecem meu patronato.",
        ],
        "agradecimento": [
            "*pausa longa* ...Surpreendente. Não esperava tanto de um estabelecimento tão... humilde. Voltarei.",
            "Magistral. Anote meu cartão — recebo visitas de outros connoisseurs. Sua fama precederá você.",
            "Impressionante. Reconheço talento quando o provo. Você passou no meu teste, barista.",
        ],
        "recusa": [
            "*franze as sobrancelhas* Não tem? Decepcionante. Esperava mais de um estabelecimento que se diz cafeteria.",
            "Que pena. Direi às minhas amigas que o menu é... limitado. Boa tarde.",
        ],
        "roubado_atendido": [
            "Hm. Troca de barista sem aviso prévio. Incomum, mas o resultado justifica o método. Aceito.",
            "*examina a bebida com lupa imaginária* ...Adequado. Seus colegas poderiam aprender com sua agilidade.",
        ],
        "timeout": [
            "Fiz reserva em três países para ser ignorada aqui? Considerarei isso um insulto diplomático. Adieu.",
            "*dobra a luva lentamente* Nunca mais. Esta cafeteria não constará em meu guia particular.",
            "Cinco minutos. Cronometrei. No continente, isso seria um escândalo gastronômico. Boa tarde.",
        ],
    },
    {
        "nome": "Mestre Yuki",
        "emoji": "🍵",
        "personalidade": "critico",
        "vip": True,
        "image_tags": {"pedido": "think", "feliz": "nod", "triste": "stare"},
        "pedido_intro": [
            "Solicito {bebida}. Temperatura ideal, proporções exatas. Estarei avaliando cada aspecto.",
            "*abre um caderninho* {bebida}. Avaliarei aroma, textura, equilíbrio e finalização. Pode começar.",
        ],
        "agradecimento": [
            "*faz anotações* Aroma: 9.2. Textura: 8.8. Equilíbrio: 9.5. Final: excepcional. Nota geral: aprovado com distinção.",
            "Raramente atribuo nota máxima. Você acabou de receber uma. Guarde este momento.",
            "*fecha o caderninho com satisfação* Publicarei uma avaliação positiva. Esperem movimento de novos clientes.",
        ],
        "recusa": [
            "Ausência de {bebida} no estoque indica planejamento inadequado. Registrado. Até a próxima auditoria.",
            "*faz uma anotação* Falha de estoque. Desclassificado desta rodada de avaliações.",
        ],
        "roubado_atendido": [
            "Redistribuição eficiente de atendimento. Metodologia não convencional, porém resultado satisfatório.",
            "*observa atentamente* Interessante estratégia logística. Está documentada no meu relatório.",
        ],
        "timeout": [
            "*escreve com calma* Tempo de espera: superior ao tolerável. Classificação do serviço: insuficiente. Publicando.",
            "Monitorei o relógio. Cinco minutos sem atendimento é dado objetivo. Minha conclusão: reprovar.",
            "Lamentável. Um bom barista administra tempo e qualidade. Aqui faltou o primeiro. Boa tarde.",
        ],
    },
    {
        "nome": "O Barão",
        "emoji": "🎩",
        "personalidade": "excêntrico",
        "vip": True,
        "image_tags": {"pedido": "wink", "feliz": "happy", "triste": "pout"},
        "pedido_intro": [
            "MINHA QUERIDA CAFETERIA! Quero {bebida} — e que seja digna de um homem de meu porte! Pago o dobro se for excepcional!",
            "*bate a bengala no chão* {bebida}! Rápido! Tenho um avião particular esperando e o piloto cobra por hora!",
        ],
        "agradecimento": [
            "EXTRAORDINÁRIO!! Estou emocionado!! Vou comprar esta cafeteria!! Quanto você quer?! NADA É CARO DEMAIS!",
            "*chora de emoção* Nunca, em 47 países visitados, provei algo assim!! Você tem talento ABSURDO!!",
            "Meu mordomo também vai querer provar isso. Mandarei minha limusine amanhã com a encomenda! ESPLÊNDIDO!",
        ],
        "recusa": [
            "Como assim NÃO TEM?! Compro a cidade inteira para cultivar os ingredientes!! Mas... tudo bem. Desta vez.",
            "*suspira dramaticamente* Uma tragédia. Uma TRAGÉDIA de proporções épicas. Voltarei quando o estoque melhorar.",
        ],
        "roubado_atendido": [
            "QUE SERVIÇO DINÂMICO!! Mudou de barista sem eu perceber!! ADORO SURPRESAS!! Excelente!",
            "*aplaude entusiasticamente* Drama! Tensão! Troca de guardiões da bebida! MELHOR CAFETERIA DO MUNDO!",
        ],
        "timeout": [
            "*olha para o relógio de ouro* Cinco minutos?! Meu iate não espera tanto! ADEUS! Voltarei... talvez!",
            "Abandonado!! Como um diamante esquecido numa gaveta!! Partirei com minha dignidade intacta!!",
            "*drama máximo* Esperança perdida... sonho não realizado... barista ausente... *sai com capa esvoaçante*",
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



# ---------------------------------------------------------------------------
# Frases: Categoria em promoção do dia (usada no l!loja)
# Placeholder {categoria} = nome da categoria (ex: "🥛 Laticínios")
# Placeholder {desconto} = percentual de desconto (ex: 30)
# ---------------------------------------------------------------------------
FRASES_CATEGORIA_DESCONTO: list[str] = [
    "Psst! Hoje os ingredientes de **{categoria}** estão com **{desconto}% de desconto**! Aproveita enquanto dura~ 🏷️",
    "Ei, olha que sorte! A categoria **{categoria}** está em promoção hoje com **{desconto}% off**! Não perde não~ 💙",
    "Hoje eu resolvi dar uma forcinha especial: **{categoria}** sai a **{desconto}%** mais barato! Vai lá~ ☕✨",
    "Você veio na hora certa! **{categoria}** está com **{desconto}% de desconto** hoje! Boa compra~ 🛍️",
    "Hmm, deixa eu te contar um segredinho... **{categoria}** está com promoção relâmpago hoje! **{desconto}% off**~ 🤫💛",
    "Ah, que boa hora de visitar a loja! **{categoria}** está {desconto}% mais em conta hoje. Eu mesma escolhi essa! ✨",
    "Tinha que avisar: **{categoria}** está em oferta hoje com **{desconto}% de desconto**. Não deixa pra amanhã~ 🌸",
    "Pst! Hoje eu botei **{categoria}** na promoção com **{desconto}% off**. Minha forma de dizer que me importo~ 💙",
    "Bom te ver por aqui! **{categoria}** está com **{desconto}% de desconto** hoje. Aproveita, tá? 🎉",
    "Olha a promoção de hoje! Os itens de **{categoria}** estão **{desconto}% mais baratos**. Corre antes que acabe~ ⏰",
    "Hoje a loja está generosa! **{categoria}** saindo com **{desconto}% off**. Fica de olho no estoque~ 🧺",
    "Que dia especial pra comprar! **{categoria}** está em promoção hoje, **{desconto}% de desconto**. Capricha no pedido~ 💫",
]

# ---------------------------------------------------------------------------
# Frases: Bebida do dia (usada no l!cardapio)
# Placeholder {bebida} = nome da bebida (ex: "Cappuccino")
# Placeholder {emoji} = emoji da bebida (ex: "🧋")
# Placeholder {bonus_xp} = bônus de XP em % (ex: 50)
# Placeholder {bonus_venda} = bônus de venda em % (ex: 30)
# ---------------------------------------------------------------------------
FRASES_BEBIDA_DO_DIA: list[str] = [
    "Hoje eu escolhi o {emoji} **{bebida}** como a bebida do dia! Ele dá **+{bonus_xp}% XP** e vende **+{bonus_venda}%** a mais~ 🌟",
    "Hmm, acordei pensando no {emoji} **{bebida}**... então ela é a bebida do dia! Prepare bastante, vale mais hoje~ ✨",
    "Sabe o que combina com hoje? {emoji} **{bebida}**! A bebida do dia dá **+{bonus_xp}% XP** ao preparar e **+{bonus_venda}%** na venda~ 💙",
    "A dica quente de hoje é: faça muito {emoji} **{bebida}**! É a bebida do dia e rende bônus especiais~ 🔥",
    "Não fica só olhando o cardápio não! O {emoji} **{bebida}** é a estrela de hoje: **+{bonus_xp}% XP** e **+{bonus_venda}%** de valor~ ⭐",
    "Coração escolheu o {emoji} **{bebida}** pra ser a bebida do dia! Ela tá rendendo mais XP e mais moedas agora~ 💛",
    "Hoje o {emoji} **{bebida}** merece atenção especial! É a bebida do dia — prepare e lucre **+{bonus_venda}%** a mais~ 🏆",
    "Psst! O segredo de hoje é: {emoji} **{bebida}**! Vende mais, dá mais XP... é a escolha certa do dia~ 🤫",
    "Que tal caprichar no {emoji} **{bebida}** hoje? Ela é a bebida do dia e está com bônus especiais de **+{bonus_xp}% XP**~ 🌸",
    "Abriu o cardápio na hora certa! O {emoji} **{bebida}** é a favorita de hoje com **+{bonus_xp}% XP** e **+{bonus_venda}%** na venda~ 🎀",
    "Tô com saudade de {emoji} **{bebida}**... Que bom que ela é a bebida do dia! Prepare logo~ ☕💙",
    "Você perguntou, o cardápio respondeu! {emoji} **{bebida}** é a bebida do dia — não deixa pra depois~ 🕐✨",
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
