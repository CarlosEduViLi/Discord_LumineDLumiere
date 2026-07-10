"""
utils/mood.py -- Sistema de humor e presenca da Lumine.

Expoe duas funcoes publicas usadas por core.py e help.py:
    get_humor_atual()        -> HumorAtual com activity_type_value e activity_text
    saudacao_do_humor()      -> str  (saudacao contextual)

O humor varia conforme a hora do dia e tem variacoes aleatorias
para tornar a presenca da Lumine mais natural e expressiva.
"""
from __future__ import annotations

import datetime
import random
from dataclasses import dataclass

import discord


@dataclass
class HumorAtual:
    """Representa o estado de presenca/humor atual da Lumine."""
    activity_type_value: int   # Valor de discord.ActivityType
    activity_text: str         # Texto exibido na presenca
    humor: str                 # Rotulo interno do humor (para saudacoes)
    emoji: str                 # Emoji do humor
    nome: str                  # Nome do humor


# ---------------------------------------------------------------------------
# Tabela de humores por periodo do dia
# discord.ActivityType: playing=0, streaming=1, listening=2, watching=3, competing=5
# ---------------------------------------------------------------------------

_HUMORES_MANHA = [
    (discord.ActivityType.listening.value, "os sons tranquilos da manhã"),
    (discord.ActivityType.playing.value, "acordando devagarinho..."),
    (discord.ActivityType.watching.value, "o amanhecer"),
    (discord.ActivityType.listening.value, "uma playlist para começar o dia"),
    (discord.ActivityType.watching.value, "o céu ficando mais claro"),
    (discord.ActivityType.playing.value, "tentando espantar o sono"),
    (discord.ActivityType.listening.value, "os passarinhos lá fora"),
    (discord.ActivityType.watching.value, "todo mundo começar o dia"),
    (discord.ActivityType.playing.value, "organizando os pensamentos"),
    (discord.ActivityType.listening.value, "músicas calmas"),
    (discord.ActivityType.watching.value, "as nuvens da manhã"),
    (discord.ActivityType.playing.value, "procurando motivos para sorrir"),
    (discord.ActivityType.listening.value, "o silêncio antes da correria"),
    (discord.ActivityType.watching.value, "um novo dia começar"),
    (discord.ActivityType.playing.value, "tentando ser produtiva"),
    (discord.ActivityType.listening.value, "uma música que traz boas lembranças"),
    (discord.ActivityType.watching.value, "o sol entrar pela janela"),
    (discord.ActivityType.playing.value, "desejando um bom dia para você"),
]


_HUMORES_TARDE = [
    (discord.ActivityType.listening.value, "músicas animadas"),
    (discord.ActivityType.watching.value, "o movimento da tarde"),
    (discord.ActivityType.playing.value, "tentando aproveitar o restante do dia"),
    (discord.ActivityType.listening.value, "uma playlist para manter o ânimo"),
    (discord.ActivityType.watching.value, "as horas passarem"),
    (discord.ActivityType.playing.value, "fazendo uma pausa merecida"),
    (discord.ActivityType.listening.value, "músicas que melhoram o humor"),
    (discord.ActivityType.watching.value, "o céu mudar de cor"),
    (discord.ActivityType.playing.value, "torcendo para o seu dia estar indo bem"),
    (discord.ActivityType.competing.value, "uma batalha contra a preguiça"),
    (discord.ActivityType.listening.value, "histórias de quem passa por aqui"),
    (discord.ActivityType.watching.value, "quem aparece para conversar"),
    (discord.ActivityType.playing.value, "tentando deixar o dia mais leve"),
    (discord.ActivityType.listening.value, "uma música antiga e familiar"),
    (discord.ActivityType.watching.value, "o mundo continuar girando"),
    (discord.ActivityType.competing.value, "uma disputa contra o sono da tarde"),
    (discord.ActivityType.playing.value, "esperando por uma boa conversa"),
    (discord.ActivityType.listening.value, "você, caso precise desabafar"),
    (discord.ActivityType.watching.value, "o sol caminhar até o horizonte"),
    (discord.ActivityType.playing.value, "guardando um lugar para você"),
]


_HUMORES_NOITE = [
    (discord.ActivityType.listening.value, "músicas tranquilas"),
    (discord.ActivityType.watching.value, "as estrelas no céu"),
    (discord.ActivityType.playing.value, "diminuindo o ritmo..."),
    (discord.ActivityType.listening.value, "lo-fi para relaxar"),
    (discord.ActivityType.watching.value, "as luzes da cidade"),
    (discord.ActivityType.playing.value, "pensando em como foi o dia"),
    (discord.ActivityType.listening.value, "uma canção antes de descansar"),
    (discord.ActivityType.watching.value, "a lua aparecer"),
    (discord.ActivityType.playing.value, "se preparando para uma noite tranquila"),
    (discord.ActivityType.listening.value, "o silêncio confortável da noite"),
    (discord.ActivityType.watching.value, "o céu escurecer"),
    (discord.ActivityType.playing.value, "torcendo para você estar bem"),
    (discord.ActivityType.listening.value, "músicas que parecem um abraço"),
    (discord.ActivityType.watching.value, "o mundo ficar mais calmo"),
    (discord.ActivityType.playing.value, "guardando as preocupações por hoje"),
    (discord.ActivityType.listening.value, "lembranças de um dia distante"),
    (discord.ActivityType.watching.value, "as nuvens passarem pela lua"),
    (discord.ActivityType.playing.value, "procurando um pouco de paz"),
    (discord.ActivityType.listening.value, "quem precisa de companhia"),
    (discord.ActivityType.watching.value, "a noite cuidar de tudo"),
]


_HUMORES_MADRUGADA = [
    (discord.ActivityType.watching.value, "a madrugada passar"),
    (discord.ActivityType.listening.value, "o silêncio... ou quase"),
    (discord.ActivityType.playing.value, "shhh... quase dormindo"),
    (discord.ActivityType.watching.value, "as estrelas fazerem companhia"),
    (discord.ActivityType.listening.value, "os poucos sons da madrugada"),
    (discord.ActivityType.playing.value, "tentando não dormir sentada"),
    (discord.ActivityType.watching.value, "quem ainda está acordado"),
    (discord.ActivityType.listening.value, "uma música baixinha"),
    (discord.ActivityType.playing.value, "esperando o sono chegar"),
    (discord.ActivityType.watching.value, "a lua pela janela"),
    (discord.ActivityType.listening.value, "pensamentos que não querem dormir"),
    (discord.ActivityType.playing.value, "fazendo companhia para você"),
    (discord.ActivityType.watching.value, "as horas passarem em silêncio"),
    (discord.ActivityType.listening.value, "o vento lá fora"),
    (discord.ActivityType.playing.value, "prometendo dormir daqui a pouco"),
    (discord.ActivityType.watching.value, "o céu antes do amanhecer"),
    (discord.ActivityType.listening.value, "uma canção para acalmar a mente"),
    (discord.ActivityType.playing.value, "espantando os pensamentos ruins"),
    (discord.ActivityType.watching.value, "a noite proteger quem ainda não dormiu"),
    (discord.ActivityType.listening.value, "você, caso ainda esteja por aqui"),
]


def _periodo_do_dia(hora: int) -> str:
    """Classifica a hora em periodo do dia."""
    if 5 <= hora < 12:
        return "manha"
    if 12 <= hora < 18:
        return "tarde"
    if 18 <= hora < 23:
        return "noite"
    return "madrugada"


def get_humor_atual(agora: datetime.datetime | None = None) -> HumorAtual:
    """
    Retorna o humor atual da Lumine com base na hora do dia.

    Args:
        agora: datetime opcional para testes deterministicos.
               Se None, usa o horario local atual.

    Returns:
        HumorAtual com activity_type_value, activity_text e humor.
    """
    if agora is None:
        agora = datetime.datetime.now()

    periodo = _periodo_do_dia(agora.hour)

    tabela = {
        "manha": _HUMORES_MANHA,
        "tarde": _HUMORES_TARDE,
        "noite": _HUMORES_NOITE,
        "madrugada": _HUMORES_MADRUGADA,
    }

    tipo_val, texto = random.choice(tabela[periodo])

    info_periodo = {
        "manha": ("🌅", "Manhã"),
        "tarde": ("☕", "Tarde"),
        "noite": ("🌙", "Noite"),
        "madrugada": ("🌌", "Madrugada"),
    }
    emoji, nome = info_periodo.get(periodo, ("✨", "Desconhecido"))

    return HumorAtual(
        activity_type_value=tipo_val,
        activity_text=texto,
        humor=periodo,
        emoji=emoji,
        nome=nome,
    )


# ---------------------------------------------------------------------------
# Saudacoes por periodo do dia
# ---------------------------------------------------------------------------

_SAUDACOES: dict[str, list[str]] = {
    "manha": [
        "Bom dia! Espero que você tenha dormido bem ☀️",
        "Bom diaaa! Vamos tentar fazer hoje ser um dia bonito.",
        "Olá! Fico feliz em te ver por aqui logo cedo.",
        "Bom dia! Não esqueça de tomar água e cuidar de você, viu?",
        "Espero que a manhã esteja sendo gentil com você ✨",
        "Bom dia! Que hoje traga pelo menos uma coisa boa para você sorrir.",
        "O sol já apareceu, então acho que é hora de começar mais uma aventura.",
        "Bom dia! Espero que as coisas deem certo hoje.",
        "Dormiu bem? Espero que sim.",
        "Mais um dia começando. Vamos fazer o melhor que pudermos.",
        "Bom dia! Espero que seu café esteja gostoso e o dia seja tranquilo.",
        "É sempre bom ver alguém aparecendo por aqui pela manhã.",
    ],

    "tarde": [
        "Boa tarde! Como está sendo o seu dia até agora?",
        "Olá! Espero que a tarde esteja sendo tranquila para você.",
        "Boa tarde! Se estiver cansado(a), lembre-se de fazer uma pausa às vezes.",
        "Fico feliz em te ver por aqui ✨",
        "Boa tarde! Espero que as coisas estejam correndo bem.",
        "Ainda temos bastante dia pela frente.",
        "Espero que algo bom tenha acontecido hoje.",
        "Boa tarde! Às vezes tudo o que precisamos é de alguns minutos para respirar e reorganizar as ideias.",
        "Como foi a manhã? Espero que ela tenha sido gentil com você.",
        "Boa tarde! Espero conseguir deixar seu dia um pouquinho melhor.",
        "Obrigada por aparecer por aqui hoje.",
        "Boa tarde! Vamos seguir em frente, um passo de cada vez.",
    ],

    "noite": [
        "Boa noite! Espero que seu dia tenha sido bom 🌙",
        "Olá! Como foi o seu dia?",
        "Boa noite! Espero que você consiga descansar um pouco hoje.",
        "As noites costumam ser mais calmas... eu gosto disso.",
        "Boa noite! Obrigada por passar por aqui.",
        "Espero que o mundo tenha sido gentil com você hoje.",
        "Mesmo que o dia tenha sido difícil, ele finalmente está chegando ao fim.",
        "Boa noite! Não esqueça de cuidar de você também.",
        "Às vezes sobreviver ao dia já é uma vitória enorme.",
        "Boa noite! Espero que amanhã seja um pouco melhor do que hoje.",
        "Ainda acordado(a)? Espero que esteja tudo bem.",
        "Boa noite! Que você tenha sonhos tranquilos quando for descansar.",
    ],

    "madrugada": [
        "Ei... você ainda está acordado(a)?",
        "Boa madrugada! Espero que esteja tudo bem por aí 🌙",
        "Não esqueça que descansar também é importante.",
        "A madrugada costuma deixar tudo mais silencioso.",
        "Se estiver estudando ou trabalhando, desejo boa sorte.",
        "Promete que vai dormir quando puder?",
        "Ainda acordado(a)? Cuide de você, tá bem?",
        "Talvez seja uma boa hora para pegar um cobertor e descansar um pouco.",
        "As coisas costumam parecer maiores durante a madrugada.",
        "Você não precisa carregar tudo sozinho(a), sabia?",
        "Boa madrugada! Obrigada por passar por aqui mesmo tão tarde.",
        "Espero que amanhã seja um dia melhor para você.",
        "Mesmo nas madrugadas mais silenciosas, você não está completamente sozinho(a).",
    ],
}


def saudacao_do_humor(agora: datetime.datetime | None = None) -> str:
    """
    Retorna uma saudacao contextual baseada na hora do dia.

    Args:
        agora: datetime opcional para testes deterministicos.

    Returns:
        String com a saudacao da Lumine.
    """
    if agora is None:
        agora = datetime.datetime.now()

    periodo = _periodo_do_dia(agora.hour)
    return random.choice(_SAUDACOES[periodo])
