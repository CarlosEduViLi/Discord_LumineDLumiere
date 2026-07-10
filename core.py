import asyncio
import logging
import os
import secrets
import socket
import subprocess

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.logging_setup import configure_logging

# Configurar logging ANTES de qualquer outra importacao
configure_logging()

logger = logging.getLogger(__name__)

try:
    from utils.mood import get_humor_atual
    _MOOD_OK = True
    logger.info("Modulo utils.mood carregado com sucesso.")
except Exception as exc:
    _MOOD_OK = False
    logger.warning("Modulo utils.mood nao disponivel: %s", exc)


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN nao foi encontrado no arquivo .env.")


# ------------------------------------------------------------
# Helpers de porta
# ------------------------------------------------------------
def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


# ------------------------------------------------------------
# Lavalink local
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
JAVA_EXE = os.path.join(BIN_DIR, "jre", "bin", "java.exe")
LAVALINK_JAR = os.path.join(BIN_DIR, "Lavalink.jar")


def start_lavalink() -> subprocess.Popen | None:
    # Se LAVALINK_MANAGED=false, nao tenta iniciar o servidor local.
    # Util quando se usa um no Lavalink externo/publico (ex: deploy no Railway).
    if os.getenv("LAVALINK_MANAGED", "true").lower() == "false":
        logger.info("Lavalink gerenciado desativado (LAVALINK_MANAGED=false). Usando no externo.")
        return None

    if is_port_open("127.0.0.1", 2333):
        logger.info("Servidor Lavalink local ja esta rodando.")
        return None

    if not os.path.isfile(JAVA_EXE) or not os.path.isfile(LAVALINK_JAR):
        logger.warning("Aviso: Lavalink local nao encontrado. Musica pode nao funcionar.")
        return None

    logger.info("Iniciando servidor Lavalink local...")
    return subprocess.Popen(
        [JAVA_EXE, "-jar", "Lavalink.jar"],
        cwd=BIN_DIR,
        creationflags=0,
    )





# ------------------------------------------------------------
# Bot
# ------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

COGS = [
    "cogs.help",
    "cogs.dice",
    "cogs.music",
    "cogs.cafe",
    "cogs.playlists",
    "cogs.pokemon",
]


async def _atualizar_presenca():
    if not _MOOD_OK:
        return
    try:
        humor = get_humor_atual()
        tipo = discord.ActivityType(humor.activity_type_value)
        await bot.change_presence(activity=discord.Activity(type=tipo, name=humor.activity_text))
    except Exception as exc:
        logger.warning("Nao foi possivel atualizar presenca: %s", exc)


@tasks.loop(minutes=30)
async def _rotacionar_humor():
    await _atualizar_presenca()


@_rotacionar_humor.before_loop
async def _before_rotacionar():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    logger.info("=" * 40)
    logger.info("Bot conectado: %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Prefixo: l!")
    logger.info("=" * 40)
    await _atualizar_presenca()
    if not _rotacionar_humor.is_running():
        _rotacionar_humor.start()


@bot.event
async def on_command_error(ctx, error):
    # Erros esperados — mensagem direta e informativa
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"Falta um argumento obrigatorio! Use `l!help {ctx.command}` para ver como usar."
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            f"Argumento invalido! Use `l!help {ctx.command}` para ver o formato correto."
        )
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send("Voce nao tem permissao para usar este comando aqui.")
        return

    if isinstance(error, commands.CommandOnCooldown):
        segundos = round(error.retry_after)
        await ctx.send(f"Aguarde **{segundos}s** antes de usar este comando novamente.")
        return

    # Erros inesperados — codigo de ocorrencia + log completo
    codigo = secrets.token_hex(4).upper()
    logger.exception(
        "Erro inesperado [%s] no comando '%s' (guild=%s, user=%s): %s",
        codigo,
        ctx.command,
        getattr(ctx.guild, "id", "DM"),
        ctx.author.id,
        error,
    )
    await ctx.send(
        f"Algo deu errado ao processar seu comando. "
        f"Se o problema persistir, mencione o codigo `{codigo}` ao reportar."
    )


async def main():
    lavalink_process = start_lavalink()
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                logger.info("Cog carregado: %s", cog)
            except Exception as exc:
                logger.error("Erro ao carregar %s: %s", cog, exc, exc_info=True)

        try:
            await bot.start(TOKEN)
        finally:
            if lavalink_process:
                logger.info("Desligando servidor Lavalink...")
                lavalink_process.terminate()
                try:
                    lavalink_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    lavalink_process.kill()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot desligado manualmente.")
