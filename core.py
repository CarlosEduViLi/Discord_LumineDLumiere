import asyncio
import os
import socket
import subprocess

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

try:
    from utils.mood import get_humor_atual
    _MOOD_OK = True
except Exception:
    _MOOD_OK = False


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
    if is_port_open("127.0.0.1", 2333):
        print("Servidor Lavalink local ja esta rodando.")
        return None

    if not os.path.isfile(JAVA_EXE) or not os.path.isfile(LAVALINK_JAR):
        print("Aviso: Lavalink local nao encontrado.")
        return None

    print("Iniciando servidor Lavalink local...")
    return subprocess.Popen(
        [JAVA_EXE, "-jar", "Lavalink.jar"],
        cwd=BIN_DIR,
        creationflags=0,
    )


lavalink_process = start_lavalink()


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
    "cogs.humor",
]


async def _atualizar_presenca():
    if not _MOOD_OK:
        return
    try:
        humor = get_humor_atual()
        tipo = discord.ActivityType(humor.activity_type_value)
        await bot.change_presence(activity=discord.Activity(type=tipo, name=humor.activity_text))
    except Exception as exc:
        print(f"  Aviso: não foi possível atualizar presença: {exc}")


@tasks.loop(minutes=30)
async def _rotacionar_humor():
    await _atualizar_presenca()


@_rotacionar_humor.before_loop
async def _before_rotacionar():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"{'=' * 40}")
    print(f"  Bot conectado: {bot.user}")
    print(f"  ID: {bot.user.id}")
    print("  Prefixo: l!")
    print(f"{'=' * 40}")
    await _atualizar_presenca()
    if not _rotacionar_humor.is_running():
        _rotacionar_humor.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Argumento faltando! Use `l!help {ctx.command}` para ver como usar.")
        return

    await ctx.send(f"Ocorreu um erro: `{error}`")


async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"  Cog carregado: {cog}")
            except Exception as exc:
                print(f"  Erro ao carregar {cog}: {exc}")

        try:
            await bot.start(TOKEN)
        finally:
            if lavalink_process:
                print("Desligando servidor Lavalink...")
                lavalink_process.terminate()
                try:
                    lavalink_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    lavalink_process.kill()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot desligado manualmente.")
