"""
help.py — Comando l!help da Lumine.

Cada Cog que quiser aparecer no help expõe dois métodos:
    help_meta()  -> dict com: key, aliases, icon, category, blurb
    help_field() -> tuple[str, str]  (título e corpo detalhado)

`l!help`            → cardápio com todas as categorias.
`l!help <chave>`    → página detalhada de uma categoria.
"""
import unicodedata

import discord
from discord.ext import commands


COR_LUMINE = discord.Color.from_rgb(100, 180, 255)


def _normaliza(texto: str) -> str:
    """Tira acento, vira minúsculo — pra casar 'música' com 'musica'."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return sem_acento.strip().lower()


class Help(commands.Cog):
    """💙 Atendimento da Lumine"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────────
    # Coleta de cogs com help
    # ──────────────────────────────────────────────────────────────

    def _cogs_com_help(self) -> list:
        """Lista os cogs que têm help_meta() — preserva a ordem de carregamento."""
        return [c for c in self.bot.cogs.values() if hasattr(c, "help_meta")]

    def _busca_cog(self, termo: str):
        """Procura um cog cujo key ou aliases batem com o termo (sem acento, lowercase)."""
        alvo = _normaliza(termo)
        for cog in self._cogs_com_help():
            meta = cog.help_meta()
            chaves = (meta["key"], *meta.get("aliases", ()))
            if any(_normaliza(c) == alvo for c in chaves):
                return cog, meta
        return None, None

    # ──────────────────────────────────────────────────────────────
    # Embeds
    # ──────────────────────────────────────────────────────────────

    def _embed_cardapio(self) -> discord.Embed:
        embed = discord.Embed(
            title="✨ Olá! Sou a Lumine, sua maid~ 💙",
            description=(
                "Estou pronta pra te servir! Posso te ajudar com várias coisinhas~\n"
                "Use `l!help <categoria>` que eu explico tudo direitinho! 🎀\n​"
            ),
            color=COR_LUMINE,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        linhas = []
        for cog in self._cogs_com_help():
            meta = cog.help_meta()
            linhas.append(
                f"{meta['icon']} **`l!help {meta['key']}`** — {meta['blurb']}"
            )

        embed.add_field(
            name="📖 Cardápio de ajudinhas",
            value="\n".join(linhas) or "*Ainda não tenho nada pra te oferecer...* 🥺",
            inline=False,
        )
        embed.set_footer(text="Em que posso te servir hoje? 💙 — Lumine D'Lumière")
        return embed

    def _embed_categoria(self, cog, meta: dict) -> discord.Embed:
        name, value = cog.help_field()
        embed = discord.Embed(
            title=f"{meta['icon']} {meta['category']}",
            description=meta.get("intro", "Aqui está tudo que sei, com carinho~ 💙") + "\n​",
            color=COR_LUMINE,
        )
        embed.add_field(name=name, value=value, inline=False)

        # Injeta campos extras de outros cogs que apontam para esta categoria
        for other_cog in self.bot.cogs.values():
            if other_cog is cog:
                continue
            if hasattr(other_cog, "help_field_extra"):
                target_key, extra_name, extra_value = other_cog.help_field_extra()
                if target_key == meta["key"]:
                    embed.add_field(name=extra_name, value=extra_value, inline=False)

        embed.set_footer(text="Volte sempre! 💙 — Lumine D'Lumière")
        return embed

    def _embed_categoria_nao_encontrada(self, termo: str) -> discord.Embed:
        disponiveis = ", ".join(
            f"`{cog.help_meta()['key']}`" for cog in self._cogs_com_help()
        )
        embed = discord.Embed(
            title="🥺 Hmm... não conheço essa categoria!",
            description=(
                f"Procurei por **{discord.utils.escape_markdown(termo)}** mas não achei nada~\n\n"
                f"As categorias que tenho são: {disponiveis or '*nenhuma agora*'}\n\n"
                "Tenta `l!help` (sem nada depois) que eu te mostro o cardápio inteirinho! 💙"
            ),
            color=COR_LUMINE,
        )
        embed.set_footer(text="Pode tentar de novo, eu não me importo~ ✨")
        return embed

    # ──────────────────────────────────────────────────────────────
    # Comando
    # ──────────────────────────────────────────────────────────────

    @commands.command(name="help", aliases=["ajuda", "comandos"])
    async def help(self, ctx: commands.Context, *, categoria: str | None = None):
        """Mostra o cardápio de ajuda. Use `l!help <categoria>` pra detalhes."""
        if not categoria:
            await ctx.send(embed=self._embed_cardapio())
            return

        cog, meta = self._busca_cog(categoria)
        if cog is None:
            await ctx.send(embed=self._embed_categoria_nao_encontrada(categoria))
            return
        await ctx.send(embed=self._embed_categoria(cog, meta))


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
