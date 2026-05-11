from __future__ import annotations

import datetime
import random

from .catalog import BEBIDAS, LOJA_CATEGORIAS


def _hoje_seed() -> int:
    """Semente determinística baseada na data atual (UTC-3)."""
    agora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    return agora.toordinal()


def get_categoria_desconto() -> str:
    """Retorna a chave da categoria em promoção hoje (determinístico por dia)."""
    rng = random.Random(_hoje_seed())
    return rng.choice([cat[0] for cat in LOJA_CATEGORIAS])


def get_bebida_do_dia() -> str:
    """Retorna a chave da bebida do dia (determinístico por dia, semente diferente)."""
    rng = random.Random(_hoje_seed() + 1)
    return rng.choice(list(BEBIDAS.keys()))


def get_desconto_pct() -> int:
    """Percentual de desconto do ingrediente em promoção."""
    return 30


def get_bonus_bebida_xp_pct() -> int:
    """Bônus de XP ao preparar a bebida do dia."""
    return 50


def get_bonus_bebida_venda_pct() -> int:
    """Bônus no preço de venda da bebida do dia."""
    return 30
