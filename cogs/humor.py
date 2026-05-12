"""
humor.py — Comando l!humor da Lumine.

Mostra em qual estado de espírito a Lumine está no momento,
baseado na hora atual no horário do Brasil (UTC-3).
"""
import discord
from discord.ext import commands

from utils.mood import get_humor_atual

COR_LUMINE = discord.Color.from_rgb(100, 180, 255)

_DESCRICOES: dict[str, str] = {
    "manha":      "Estou toda animada e pronta pra começar o dia com vocês! ✨",
    "tarde":      "Tô no meu ritmo tranquilo de tarde, servindo com alegria~ 💙",
    "entardecer": "O entardecer me deixa um pouco mais poética e contemplativa... 🌸",
    "noite":      "A noite me deixa mais calma e carinhosa com todo mundo~ 🌙",
    "madrugada":  "Na madrugada fico no meu próprio mundo, quieta e misteriosa... 🌌",
}


class Humor(commands.Cog):
    """🌙 Humor da Lumine"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="humor", aliases=["mood", "estado"])
    async def humor(self, ctx: commands.Context):
        """Mostra como a Lumine está se sentindo agora."""
        h = get_humor_atual()
        embed = discord.Embed(
            title=f"{h.emoji} Meu humor agora: {h.nome}",
            description=f"{h.saudacao}\n\n*{_DESCRICOES[h.id]}*",
            color=COR_LUMINE,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Meu humor muda conforme o horário do dia~ 💙 — Lumine")
        await ctx.send(embed=embed)

    def help_meta(self) -> dict:
        return {
            "key": "humor",
            "aliases": ("mood", "estado"),
            "icon": "🌙",
            "category": "Humor",
            "blurb": "Veja como a Lumine está se sentindo agora~",
            "intro": "Meu humor muda ao longo do dia! De manhã sou animada, à noite fico sonolenta~ 💙",
        }

    def help_field(self) -> tuple[str, str]:
        return (
            "🌙 Estado de espírito",
            "`l!humor` — Descubra como estou me sentindo agora~\n"
            "*Aliases: `l!mood`, `l!estado`*",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Humor(bot))
