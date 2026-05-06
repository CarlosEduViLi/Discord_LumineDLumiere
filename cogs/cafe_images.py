"""
cafe_images.py — Helper de imagens de anime para o ☕ Café da Lumine.

Busca imagens em APIs públicas (nekos.best → waifu.pics como fallback)
e mantém um pool em memória com TTL para reduzir chamadas externas.

Uso:
    from cogs.cafe_images import fetch_anime_image
    url = await fetch_anime_image("blush")  # str | None
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Optional

import aiohttp

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
TTL_SEGUNDOS   = 60 * 60      # 1h de cache por categoria
TIMEOUT_FETCH  = 3.0          # segundos por requisição
POOL_TAMANHO   = 8            # imagens guardadas por categoria

# Categorias suportadas (whitelist defensiva — só passa adiante o que conhecemos)
CATEGORIAS_VALIDAS: set[str] = {
    "happy", "smile", "blush", "shrug", "pout", "cry", "wave", "wink",
    "bored", "nod", "shake", "think", "smug", "stare", "pat", "wag",
}

# Tradução de categoria → endpoint específico de cada API.
# Se uma categoria não existe na API X, mapeamos pra algo equivalente.
_NEKOS_MAP = {
    "happy":  "happy",  "smile":  "smile",  "blush":  "blush",
    "shrug":  "shrug",  "pout":   "pout",   "cry":    "cry",
    "wave":   "wave",   "wink":   "wink",   "bored":  "bored",
    "nod":    "nod",    "shake":  "shake",  "think":  "think",
    "smug":   "smug",   "stare":  "stare",  "pat":    "pat",
    "wag":    "wave",   # nekos.best não tem "wag", caímos pra "wave"
}

_WAIFU_MAP = {
    "happy":  "happy",  "smile":  "smile",  "blush":  "blush",
    "shrug":  "shrug",  "pout":   "pout",   "cry":    "cry",
    "wave":   "wave",   "wink":   "wink",   "bored":  "bored",
    "nod":    "nom",    "shake":  "bonk",   "think":  "smug",
    "smug":   "smug",   "stare":  "smug",   "pat":    "pat",
    "wag":    "wave",
}

# ─────────────────────────────────────────────
#  CACHE
# ─────────────────────────────────────────────
_pool: dict[str, list[str]]  = {}  # categoria → [urls]
_pool_ts: dict[str, float]   = {}  # categoria → timestamp do último refill


def _pool_quente(categoria: str) -> bool:
    """True se temos urls válidas em cache para a categoria."""
    if categoria not in _pool or not _pool[categoria]:
        return False
    return (time.time() - _pool_ts.get(categoria, 0)) < TTL_SEGUNDOS


# ─────────────────────────────────────────────
#  FETCHERS
# ─────────────────────────────────────────────
async def _try_nekos_best(categoria: str, qtd: int) -> list[str]:
    """Tenta nekos.best — retorna lista de urls (vazia em caso de erro)."""
    endpoint = _NEKOS_MAP.get(categoria)
    if not endpoint:
        return []
    url = f"https://nekos.best/api/v2/{endpoint}?amount={qtd}"
    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_FETCH)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    log.warning("nekos.best retornou %s para %s", resp.status, categoria)
                    return []
                data = await resp.json()
                # Formato: {"results": [{"url": "..."}, ...]}
                return [r["url"] for r in data.get("results", []) if r.get("url")]
    except (asyncio.TimeoutError, aiohttp.ClientError, ValueError, KeyError) as e:
        log.warning("falha em nekos.best (%s): %s", categoria, e)
        return []


async def _try_waifu_pics(categoria: str, qtd: int) -> list[str]:
    """Tenta waifu.pics — retorna lista de urls (vazia em caso de erro).

    A API só retorna 1 url por chamada (sfw/<cat>), então fazemos `qtd` chamadas
    em paralelo e deduplicamos.
    """
    endpoint = _WAIFU_MAP.get(categoria)
    if not endpoint:
        return []
    url = f"https://api.waifu.pics/sfw/{endpoint}"

    async def _one(session: aiohttp.ClientSession) -> Optional[str]:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data.get("url")
        except (asyncio.TimeoutError, aiohttp.ClientError, ValueError):
            return None

    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_FETCH * 2)  # várias chamadas
        async with aiohttp.ClientSession(timeout=timeout) as session:
            results = await asyncio.gather(*[_one(session) for _ in range(qtd)])
        return list({u for u in results if u})  # dedup
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        log.warning("falha em waifu.pics (%s): %s", categoria, e)
        return []


# ─────────────────────────────────────────────
#  API PÚBLICA
# ─────────────────────────────────────────────
async def fetch_anime_image(categoria: str) -> Optional[str]:
    """Retorna URL de uma imagem de anime para a categoria ou None se falhar.

    Estratégia:
      1. Se há pool quente em cache, sorteia uma url dele.
      2. Senão, tenta nekos.best.
      3. Se falhar, tenta waifu.pics.
      4. Se tudo falhar, retorna None (chamador deve tolerar).
    """
    if categoria not in CATEGORIAS_VALIDAS:
        log.debug("categoria desconhecida: %s — usando 'smile'", categoria)
        categoria = "smile"

    if _pool_quente(categoria):
        return random.choice(_pool[categoria])

    urls = await _try_nekos_best(categoria, POOL_TAMANHO)
    if not urls:
        urls = await _try_waifu_pics(categoria, POOL_TAMANHO)

    if urls:
        _pool[categoria] = urls
        _pool_ts[categoria] = time.time()
        return random.choice(urls)

    log.warning("nenhuma imagem disponível para categoria '%s'", categoria)
    return None


def limpar_cache() -> None:
    """Esvazia o pool — útil em testes ou para forçar refresh."""
    _pool.clear()
    _pool_ts.clear()
