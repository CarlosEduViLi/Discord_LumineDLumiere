import random
import re

import discord
from discord.ext import commands

# ─────────────────────────────────────────────
#  Parser de expressão de dados
#  Suporta: NdX, NdX+M, NdX-M, T#NdX+M
# ─────────────────────────────────────────────

DICE_PATTERN = re.compile(
    r"^(?:(\d+)#)?(\d+)d(\d+)([+-]\d+)?$",
    re.IGNORECASE
)


def parse_roll(expression: str):
    """
    Faz o parse de uma expressão de dados.
    Retorna um dict com:
        times   - quantas vezes rolar (para T#NdX)
        num     - quantidade de dados
        sides   - faces do dado
        modifier - modificador (+N ou -N)
    Lança ValueError se a expressão for inválida.
    """
    expr = expression.strip().replace(" ", "")
    match = DICE_PATTERN.match(expr)
    if not match:
        raise ValueError(f"Expressão inválida: `{expression}`")

    times    = int(match.group(1)) if match.group(1) else 1
    num      = int(match.group(2))
    sides    = int(match.group(3))
    modifier = int(match.group(4)) if match.group(4) else 0

    if times < 1 or times > 100:
        raise ValueError("O número de repetições deve estar entre 1 e 100.")
    if num < 1 or num > 100:
        raise ValueError("A quantidade de dados deve estar entre 1 e 100.")
    if sides < 2 or sides > 10000:
        raise ValueError("O dado precisa ter entre 2 e 10.000 faces.")

    return {"times": times, "num": num, "sides": sides, "modifier": modifier}


def roll_once(num: int, sides: int, modifier: int):
    """Rola `num` dados de `sides` faces e aplica `modifier`."""
    rolls = [random.randint(1, sides) for _ in range(num)]
    total = sum(rolls) + modifier
    return rolls, total


def format_modifier(modifier: int) -> str:
    if modifier == 0:
        return ""
    return f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}"


def build_roll_line(rolls: list, total: int, num: int, sides: int, modifier: int) -> str:
    """
    Formata uma linha de resultado no estilo:
        15 ← [5, 5, 3]  3d6 + 2
    """
    rolls_str    = f"[{', '.join(str(r) for r in rolls)}]"
    expr_str     = f"{num}d{sides}{format_modifier(modifier)}"
    return f"`{total:>3}` ← {rolls_str}  {expr_str}"


# ─────────────────────────────────────────────
#  Cog
# ─────────────────────────────────────────────

class Dice(commands.Cog):
    """🎲 Rolagem de dados com suporte a NdX, NdX+M e T#NdX+M"""

    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    #  Execução compartilhada (comando + listener)
    # ─────────────────────────────────────────────

    async def _executar_rolagem(self, channel, author, expression: str, parsed: dict) -> None:
        """Constrói o embed e envia. Usado pelo comando e pelo listener auto-detect."""
        times    = parsed["times"]
        num      = parsed["num"]
        sides    = parsed["sides"]
        modifier = parsed["modifier"]

        lines = []
        for _ in range(times):
            rolls, total = roll_once(num, sides, modifier)
            lines.append(build_roll_line(rolls, total, num, sides, modifier))

        header = f"🎲 **{expression.strip()}**"

        embed = discord.Embed(color=discord.Color.from_rgb(114, 137, 218))
        embed.set_author(
            name=f"{author.display_name} rolou os dados!",
            icon_url=author.display_avatar.url
        )
        embed.description = header + "\n" + "\n".join(lines)

        if times > 1:
            totals = [int(line.split("`")[1].strip()) for line in lines]
            embed.set_footer(text=f"Soma total das {times} rolagens: {sum(totals)}")

        await channel.send(embed=embed)

    # ─────────────────────────────────────────────
    #  Comando l!roll
    # ─────────────────────────────────────────────

    @commands.command(
        name="roll",
        aliases=["r", "rolar"],
        help="Rola dados. Ex: `l!roll 1d20+2`, `l!roll 3d6`, `l!roll 5#3d6+2`"
    )
    async def roll(self, ctx, *, expression: str):
        try:
            parsed = parse_roll(expression)
        except ValueError as e:
            await ctx.send(f"❌ {e}\n💡 Exemplos válidos: `1d20`, `3d6+2`, `5#2d8-1`")
            return
        await self._executar_rolagem(ctx.channel, ctx.author, expression, parsed)

    @roll.error
    async def roll_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ Você precisa passar uma expressão de dados!\n"
                "💡 Exemplos: `l!roll 1d20`, `l!roll 3d6+2`, `l!roll 5#2d8-1`"
            )

    # ─────────────────────────────────────────────
    #  Auto-detect: mensagens que SÃO só uma rolagem
    # ─────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Se a mensagem for *somente* uma expressão de dado (ex.: '1d20', '3d6+2'),
        a Lumine rola automaticamente sem precisar do prefixo.

        Mensagens com texto adicional ('vc precisa rolar 1d20') NÃO disparam,
        porque o DICE_PATTERN é ancorado em ^...$ e o parse_roll levanta
        ValueError para qualquer coisa que não case 100%.
        """
        # Ignora bots (inclusive a própria Lumine)
        if message.author.bot:
            return
        # Ignora mensagens fora de canais de texto (DMs continuam funcionando)
        if message.guild is None and not isinstance(message.channel, discord.DMChannel):
            return

        content = message.content.strip()
        if not content:
            return

        # Se já começa com o prefixo do bot, deixa o sistema de comandos cuidar
        prefixos = await self.bot.get_prefix(message)
        if isinstance(prefixos, str):
            prefixos = (prefixos,)
        if any(content.startswith(p) for p in prefixos):
            return

        # Tenta interpretar a mensagem inteira como expressão de dado.
        # Se não for, ValueError silencioso e ignoramos.
        try:
            parsed = parse_roll(content)
        except ValueError:
            return

        await self._executar_rolagem(message.channel, message.author, content, parsed)


    def help_meta(self) -> dict:
        """Metadados pro l!help (cardápio + busca por categoria)."""
        return {
            "key": "dados",
            "aliases": ("dado", "roll", "rolar", "dice"),
            "icon": "🎲",
            "category": "Rolagem de Dados",
            "blurb": "Rolo seus dados pra suas aventuras de RPG~ 🎲",
            "intro": "Pronta pra rolar uns dadinhos com você! Boa sorte~ 🍀",
        }

    def help_field(self) -> tuple[str, str]:
        """Retorna o campo de ajuda desta cog para o l!help."""
        name = "🎲 __Comandos de Dados__"
        value = (
            "`l!roll` / `l!r` `<expressão>` — Rola dados 🎲\n"
            "\n"
            "**✨ Atalho mágico:** mande **só** a expressão no chat (ex: `1d20`) "
            "que eu rolo automaticamente, sem precisar de `l!roll`! 💙\n"
            "↳ Funciona quando a mensagem é **apenas** a expressão. Se tiver "
            "texto junto (tipo *\"vc precisa rolar 1d20\"*), eu fico quietinha~\n"
            "\n"
            "**Formatos aceitos:**\n"
            "`NdX` — N dados de X faces. Ex: `3d6`\n"
            "`NdX+M` ou `NdX-M` — com modificador. Ex: `1d20+5`\n"
            "`T#NdX+M` — repete T vezes. Ex: `5#3d6+2`\n"
            "\n"
            "**Limites:** até 100 repetições, 100 dados, 10.000 faces."
        )
        return name, value


async def setup(bot):
    await bot.add_cog(Dice(bot))
