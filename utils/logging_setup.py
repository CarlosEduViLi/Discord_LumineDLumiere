"""
utils/logging_setup.py -- Configuracao centralizada de logging para a Lumine.

Uso:
    from utils.logging_setup import configure_logging
    configure_logging()

Chame UMA VEZ no entry point (core.py / __main__.py) antes de qualquer outra importacao.
"""
from __future__ import annotations

import logging
import os
import sys


def configure_logging(level: str | None = None) -> None:
    """
    Configura o sistema de logging padronizado.

    Args:
        level: Nivel de log desejado (DEBUG, INFO, WARNING, ERROR).
               Se None, usa a variavel de ambiente LOG_LEVEL ou padrao INFO.
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    numeric_level = getattr(logging, level, logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Evita adicionar handlers duplicados em recargas de modulo
    if not root.handlers:
        root.addHandler(handler)

    # Silenciar libs muito verbosas em nivel INFO+
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("wavelink").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
