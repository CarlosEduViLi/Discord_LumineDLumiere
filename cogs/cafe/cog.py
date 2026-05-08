from __future__ import annotations

import random

import discord
from discord.ext import commands

from .catalog import BEBIDAS, INGREDIENTES, LOJA_CATEGORIAS, NIVEIS, RECEITAS_SECRETAS, UPGRADES_CAFETEIRA
from .images import fetch_anime_image
from .narrative import FRASES_INVENTAR_ACERTO, FRASES_INVENTAR_ERRO, FRASES_TRABALHAR, escolher_pista_receita
from .repository import CafeRepository
from .service import (
    comprar as regra_comprar,
    formatar_tempo,
    get_cafeteira_info,
    get_cafeteira_nivel,
    get_nivel,
    iniciar_atendimento,
    inventar as regra_inventar,
    melhorar_cafeteira,
    preparar as regra_preparar,
    servir_atendimento,
    trabalhar as regra_trabalhar,
    vender as regra_vender,
)


COR_CAFE = discord.Color.from_rgb(139, 90, 43)
COR_OK = discord.Color.from_rgb(107, 191, 139)
COR_ERRO = discord.Color.from_rgb(220, 100, 100)
COR_LOJA = discord.Color.from_rgb(255, 183, 77)
COR_PERFIL = discord.Color.from_rgb(181, 126, 220)
COR_RANK = discord.Color.from_rgb(255, 215, 100)


def _receita_str(receita: dict[str, int]) -> str:
    return "  ".join(f"{INGREDIENTES[key]['emoji']}×{qtd}" for key, qtd in receita.items())


def _faltando_str(faltando: list[dict]) -> str:
    return "\n".join(
        f"{INGREDIENTES[item['key']]['emoji']} {INGREDIENTES[item['key']]['nome']}: "
        f"tem {item['tem']}, precisa {item['precisa']}"
        for item in faltando
    )


def _ingredientes_str(itens: dict[str, int]) -> str:
    return "  ".join(f"{INGREDIENTES[key]['emoji']}×{qtd}" for key, qtd in itens.items())


class LojaView(discord.ui.View):
    def __init__(self, cog: "Cafe", author: discord.abc.User, page: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.author = author
        self.current_page = page
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("Só quem abriu a loja pode navegar nela~ 💙", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def _turn(self, interaction: discord.Interaction, delta: int):
        if interaction.guild is None:
            return
        total = len(LOJA_CATEGORIAS)
        self.current_page = (self.current_page - 1 + delta) % total + 1
        user = await self.cog.repo.get_user(interaction.guild.id, self.author.id)
        await interaction.response.edit_message(
            embed=self.cog._build_loja_embed(user["lumicoins"], self.current_page, total),
            view=self,
        )

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, -1)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, +1)


class Cafe(commands.Cog):
    """☕ Minigame de cafeteria da Lumine."""

    def __init__(self, bot: commands.Bot, repo: CafeRepository | None = None):
        self.bot = bot
        self.repo = repo or CafeRepository()

    def _bonus_cafeteira_linhas(self, info: dict) -> list[str]:
        linhas = []
        if info["bonus_venda"]:
            linhas.append(f"💰 +{info['bonus_venda']}% valor de venda")
        if info["bonus_xp"]:
            linhas.append(f"⭐ +{info['bonus_xp']}% XP ao preparar")
        if info["bonus_atendimento"]:
            linhas.append(f"🪙 +{info['bonus_atendimento']}% gorjeta ao atender")
        if info["chance_economizar"]:
            linhas.append(f"🎒 {info['chance_economizar']}% de chance de poupar 1 ingrediente")
        return linhas or ["Sem bônus ativos ainda."]

    def _build_loja_embed(self, saldo: int, page: int, total_pages: int) -> discord.Embed:
        categoria_key, titulo = LOJA_CATEGORIAS[page - 1]
        linhas = [
            f"{ing['emoji']} **{ing['nome']}** — {ing['preco']} 🪙 | `l!comprar {key}`"
            for key, ing in INGREDIENTES.items()
            if ing.get("categoria") == categoria_key
        ]
        embed = discord.Embed(
            title="🏪 Loja de Ingredientes",
            description=(
                f"Saldo: **{saldo} 🪙** — Use `l!comprar <ingrediente> [qtd]`\n"
                "Ex.: `l!comprar grao 2 leite 3` ou `l!comprar leite condensado 2`\n​"
            ),
            color=COR_LOJA,
        )
        embed.add_field(name=titulo, value="\n".join(linhas) or "*Nada por aqui ainda.*", inline=False)
        embed.set_footer(text=f"Página {page}/{total_pages} • Lumine Café ☕")
        return embed

    @commands.command(name="trabalhar", aliases=["work", "trab"], help="Trabalhe e ganhe Lumicoins! (cooldown 30min)")
    @commands.guild_only()
    async def trabalhar(self, ctx: commands.Context):
        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, regra_trabalhar)
        if not result["ok"]:
            return await ctx.send(embed=discord.Embed(
                description=f"☕ Ainda cansada! Descanse por **{formatar_tempo(result['cooldown'])}**. 💤",
                color=COR_ERRO,
            ).set_footer(text="Lumine Café ☕"))

        user = result["user"]
        nivel = get_nivel(user["xp"])
        embed = discord.Embed(
            title="💼 Turno concluído!",
            description=(
                f"*{random.choice(FRASES_TRABALHAR)}*\n\n"
                f"Ganhou **{result['ganho']} Lumicoins** 🪙 — Saldo: **{user['lumicoins']} 🪙**"
            ),
            color=COR_OK,
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        pista = escolher_pista_receita(user, "lumine", 20)
        if pista:
            embed.add_field(name="🤫 Inspiração da Lumine", value=pista, inline=False)
        embed.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • próximo turno em 30min")
        await ctx.send(embed=embed)

    @commands.command(name="loja", aliases=["shop"], help="Ingredientes disponíveis para comprar.")
    @commands.guild_only()
    async def loja(self, ctx: commands.Context, page: int = 1):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        total = len(LOJA_CATEGORIAS)
        page = max(1, min(page, total))
        view = LojaView(self, ctx.author, page)
        view.message = await ctx.send(embed=self._build_loja_embed(user["lumicoins"], page, total), view=view)

    @commands.command(name="cafeteira", aliases=["upgrades"], help="Veja e melhore sua cafeteira.")
    @commands.guild_only()
    async def cafeteira(self, ctx: commands.Context):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        nivel = get_cafeteira_nivel(user)
        atual = UPGRADES_CAFETEIRA[nivel]
        embed = discord.Embed(
            title="☕ Cafeteira da Lumine",
            description=f"Nível atual: **{nivel} — {atual['nome']}**\nSaldo: **{user['lumicoins']} 🪙**",
            color=COR_CAFE,
        )
        embed.add_field(name="Bônus ativos", value="\n".join(self._bonus_cafeteira_linhas(atual)), inline=False)
        if nivel + 1 < len(UPGRADES_CAFETEIRA):
            prox = UPGRADES_CAFETEIRA[nivel + 1]
            embed.add_field(
                name=f"Próximo upgrade: nível {prox['nivel']} — {prox['nome']}",
                value=(
                    f"Custo: **{prox['custo']} 🪙**\n"
                    f"Bônus: {', '.join(self._bonus_cafeteira_linhas(prox))}\n"
                    "Use `l!melhorar cafeteira` para comprar."
                ),
                inline=False,
            )
        else:
            embed.add_field(name="Próximo upgrade", value="Sua cafeteira já está no nível máximo.", inline=False)
        embed.set_footer(text="Lumine Café ☕")
        await ctx.send(embed=embed)

    @commands.command(name="melhorar", aliases=["upgrade"], help="Melhore sua cafeteira com Lumicoins.")
    @commands.guild_only()
    async def melhorar(self, ctx: commands.Context, *, alvo: str = "cafeteira"):
        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, lambda user: melhorar_cafeteira(user, alvo))
        if not result["ok"]:
            if result["reason"] == "alvo_invalido":
                return await ctx.send("❌ Por enquanto só dá para melhorar a `cafeteira`.")
            if result["reason"] == "nivel_maximo":
                return await ctx.send(embed=discord.Embed(
                    title="☕ Cafeteira no máximo!",
                    description="Sua cafeteira já está tinindo no nível máximo.",
                    color=COR_CAFE,
                ))
            upgrade = result["upgrade"]
            return await ctx.send(embed=discord.Embed(
                title="💸 Lumicoins insuficientes!",
                description=(
                    f"Upgrade: **nível {upgrade['nivel']} — {upgrade['nome']}**\n"
                    f"Custo: **{upgrade['custo']} 🪙**\n"
                    f"Seu saldo: **{result['saldo']} 🪙**\n"
                    f"Faltam: **{upgrade['custo'] - result['saldo']} 🪙**"
                ),
                color=COR_ERRO,
            ))

        user = result["user"]
        upgrade = result["upgrade"]
        embed = discord.Embed(
            title=f"✨ Cafeteira melhorada para nível {upgrade['nivel']}!",
            description=f"Agora você tem a **{upgrade['nome']}**.\nGastou **{result['custo']} 🪙** — saldo: **{user['lumicoins']} 🪙**",
            color=COR_OK,
        )
        embed.add_field(name="Novos bônus", value="\n".join(self._bonus_cafeteira_linhas(upgrade)), inline=False)
        embed.set_footer(text="Lumine Café ☕ • Upgrade instalado")
        await ctx.send(embed=embed)

    @commands.command(name="comprar", aliases=["buy"], help="Compre ingredientes. Ex: l!comprar grao 2 leite condensado 1")
    @commands.guild_only()
    async def comprar(self, ctx: commands.Context, *args: str):
        if not args:
            return await ctx.send("❌ Use: `l!comprar <ingrediente> [qtd] [ingrediente] [qtd] ...`")

        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, lambda user: regra_comprar(user, args))
        if not result["ok"]:
            reason = result["reason"]
            if reason == "ingrediente_invalido":
                return await ctx.send(f"❌ Ingrediente `{result['ingrediente']}` não existe! Use `l!loja` para ver as opções.")
            if reason == "quantidade_maxima":
                ing = INGREDIENTES[result["ingrediente"]]
                return await ctx.send(f"❌ Máx. **99** por ingrediente — você pediu **{result['quantidade']}× {ing['nome']}**.")
            if reason == "saldo_insuficiente":
                return await ctx.send(embed=discord.Embed(
                    title="💸 Saldo insuficiente!",
                    description=(
                        f"Compra total: **{result['custo_total']} 🪙**\n"
                        f"Seu saldo:    **{result['saldo']} 🪙**\n"
                        f"Faltam:       **{result['custo_total'] - result['saldo']} 🪙**\n\n"
                        "Use `l!trabalhar` pra ganhar mais!"
                    ),
                    color=COR_ERRO,
                ))
            return await ctx.send("❌ Não consegui entender o pedido! Ex.: `l!comprar grao 2 leite 3`")

        user = result["user"]
        linhas = []
        for item in result["linhas"]:
            ing = INGREDIENTES[item["key"]]
            linhas.append(f"**{item['quantidade']}× {ing['emoji']} {ing['nome']}** — {item['subtotal']} 🪙")
        embed = discord.Embed(
            title="🛍️ Compra realizada!",
            description="\n".join(linhas) + (
                f"\n\n💰 **Total:** {result['custo_total']} 🪙\n"
                f"💳 Saldo restante: **{user['lumicoins']} 🪙**"
            ),
            color=COR_OK,
        ).set_footer(text="Lumine Café ☕")
        await ctx.send(embed=embed)

    @commands.command(name="cardapio", aliases=["menu"], help="Veja todas as bebidas disponíveis.")
    @commands.guild_only()
    async def cardapio(self, ctx: commands.Context):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        embed = discord.Embed(
            title="📋 Cardápio da Lumine Café",
            description="Use `l!preparar <bebida>` para fazer uma!\n​",
            color=COR_CAFE,
        )
        for key, bebida in BEBIDAS.items():
            embed.add_field(
                name=f"{bebida['emoji']} {bebida['nome']} — {bebida['preco_venda']} 🪙 | +{bebida['xp']} ⭐",
                value=f"`l!preparar {key}`  •  {_receita_str(bebida['receita'])}",
                inline=False,
            )

        desbloqueadas = [key for key in user.get("receitas_desbloqueadas", []) if key in RECEITAS_SECRETAS]
        if desbloqueadas:
            embed.add_field(name="​", value="✨ **Receitas Secretas (suas descobertas!)** ✨", inline=False)
            for key in desbloqueadas:
                bebida = RECEITAS_SECRETAS[key]
                embed.add_field(
                    name=f"{bebida['emoji']} {bebida['nome']} — {bebida['preco_venda']} 🪙 | +{bebida['xp']} ⭐",
                    value=f"`l!preparar {key}`  •  {_receita_str(bebida['receita'])}",
                    inline=False,
                )
        if len(desbloqueadas) < len(RECEITAS_SECRETAS):
            embed.add_field(
                name="🤫 Receitas Secretas",
                value=f"Você descobriu **{len(desbloqueadas)}/{len(RECEITAS_SECRETAS)}** receitas secretas!\nUse `l!inventar <ing1> <ing2> ...` pra experimentar combinações~ ✨",
                inline=False,
            )
        embed.set_footer(text="Lumine Café ☕ • Feito com amor!")
        await ctx.send(embed=embed)

    @commands.command(name="preparar", aliases=["fazer", "brew"], help="Prepare uma bebida. Ex: l!preparar cappuccino")
    @commands.guild_only()
    async def preparar(self, ctx: commands.Context, *, bebida: str):
        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, lambda user: regra_preparar(user, bebida))
        if not result["ok"]:
            if result["reason"] == "bebida_invalida":
                opcoes = ", ".join(f"`{opcao}`" for opcao in result["opcoes"])
                return await ctx.send(f"❌ Bebida não encontrada! Opções: {opcoes}\nVeja o `l!cardapio`!")
            bebida_data = BEBIDAS.get(result.get("bebida")) or RECEITAS_SECRETAS.get(result.get("bebida"))
            title = "😢 Faltam ingredientes!"
            if bebida_data:
                title = f"😢 Faltam ingredientes para {bebida_data['emoji']} {bebida_data['nome']}!"
            return await ctx.send(embed=discord.Embed(
                title=title,
                description=_faltando_str(result["faltando"]) + "\n\nUse `l!comprar` para abastecer!",
                color=COR_ERRO,
            ))

        user = result["user"]
        bebida_data = result["bebida_data"]
        bonus_str = ""
        if result["xp_ganho"] > bebida_data["xp"]:
            bonus_str += f"\n**Bônus da cafeteira:** +{result['xp_ganho'] - bebida_data['xp']} XP ✨"
        if result["ingrediente_poupado"]:
            ing = INGREDIENTES[result["ingrediente_poupado"]]
            bonus_str += f"\n**Economia da cafeteira:** poupou 1× {ing['emoji']} {ing['nome']} 🎒"
        nivel = get_nivel(user["xp"])
        await ctx.send(embed=discord.Embed(
            title=f"☕ {bebida_data['emoji']} {bebida_data['nome']} preparado!",
            description=(
                "*Que cheirinho gostoso...* ✨\n\n"
                f"**Receita:** {_receita_str(bebida_data['receita'])}\n"
                f"**XP ganho:** +{result['xp_ganho']} ⭐  |  XP total: {user['xp']} ⭐"
                f"{bonus_str}\n\n"
                f"Bebida no estoque! Use `l!vender {result['bebida']}` para vender. 🏪"
            ),
            color=COR_OK,
        ).set_footer(text=f"{nivel['emoji']} {nivel['titulo']}"))

    @commands.command(name="inventar", aliases=["experimentar", "misturar"], help="Misture ingredientes para descobrir uma receita secreta.")
    @commands.guild_only()
    async def inventar(self, ctx: commands.Context, *ingredientes: str):
        if not ingredientes:
            return await ctx.send(embed=discord.Embed(
                title="🧪 Como inventar?",
                description="Misture **2 ou mais ingredientes** e veja o que sai!\nEx: `l!inventar grao canela pimenta`",
                color=COR_CAFE,
            ).set_footer(text="Lumine Café ☕ • Cuidado com as gororobas!"))

        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, lambda user: regra_inventar(user, ingredientes))
        if not result["ok"]:
            if result["reason"] == "ingrediente_invalido":
                invalidos = ", ".join(f"`{item}`" for item in result["invalidos"])
                return await ctx.send(embed=discord.Embed(
                    title="❓ Ingrediente desconhecido",
                    description=f"Não conheço esses aqui: {invalidos}\nDá uma olhadinha na `l!loja` pra ver o que existe! 💙",
                    color=COR_ERRO,
                ))
            if result["reason"] == "minimo_ingredientes":
                return await ctx.send(embed=discord.Embed(description="🧪 Use **pelo menos 2 ingredientes** pra inventar algo, tá? ♡", color=COR_ERRO))
            return await ctx.send(embed=discord.Embed(
                title="😢 Você não tem ingredientes suficientes!",
                description=_faltando_str(result["faltando"]) + "\n\nUse `l!comprar` pra abastecer antes de experimentar! 💙",
                color=COR_ERRO,
            ))

        ing_str = _ingredientes_str(result["tentativa"])
        if not result["acertou"]:
            embed = discord.Embed(
                title="🥴 Que gororoba foi essa?!",
                description=(
                    f"*\"{random.choice(FRASES_INVENTAR_ERRO)}\"*\n\n"
                    f"**Você usou:** {ing_str}\n"
                    "Os ingredientes foram pro lixo... mas faz parte de aprender! Tente outra combinação~ 💙"
                ),
                color=COR_ERRO,
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            embed.set_footer(text="Lumine Café ☕ • Não desista, barista!")
            return await ctx.send(embed=embed)

        user = result["user"]
        bebida_data = result["bebida_data"]
        if result["ja_desbloqueada"]:
            titulo = f"☕ {bebida_data['emoji']} {bebida_data['nome']} pronto de novo!"
            extras = f"⭐ **+{result['xp_ganho']} XP**  •  Já tava no caderninho, mas saiu liiindo! 💙\n"
        else:
            titulo = f"✨ DESCOBERTA! {bebida_data['emoji']} {bebida_data['nome']}!"
            extras = (
                "🎉 **Receita secreta desbloqueada!** Agora aparece no seu `l!cardapio`!\n"
                f"⭐ **+{result['xp_ganho']} XP** (dobrado pela descoberta!)  •  🪙 **+{result['bonus_moedas']} Lumicoins** de bônus!\n"
            )
        embed = discord.Embed(
            title=titulo,
            description=(
                f"*\"{random.choice(FRASES_INVENTAR_ACERTO)}\"*\n\n"
                f"**Combinação:** {ing_str}\n"
                f"{extras}"
                f"A bebida foi pro seu estoque — use `l!vender {result['bebida']}` ou sirva nos clientes! 🧺"
            ),
            color=COR_OK,
        )
        nivel = get_nivel(user["xp"])
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • Lumine Café ☕")
        await ctx.send(embed=embed)

    @commands.command(name="estoque", aliases=["stock"], help="Veja suas bebidas prontas.")
    @commands.guild_only()
    async def estoque(self, ctx: commands.Context):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        if not user["estoque"]:
            return await ctx.send(embed=discord.Embed(
                description="🧺 Estoque vazio! Use `l!preparar <bebida>` para fazer algo. ☕",
                color=COR_ERRO,
            ))
        linhas, total = [], 0
        for key, qtd in user["estoque"].items():
            bebida = BEBIDAS.get(key) or RECEITAS_SECRETAS.get(key)
            if not bebida:
                continue
            valor = bebida["preco_venda"] * qtd
            total += valor
            marca = "✨ " if key in RECEITAS_SECRETAS else ""
            linhas.append(f"{marca}{bebida['emoji']} **{bebida['nome']}** ×{qtd} — {valor} 🪙")
        await ctx.send(embed=discord.Embed(
            title="🧺 Seu estoque de bebidas",
            description="\n".join(linhas) + f"\n\n💰 Valor total: **{total} 🪙**",
            color=COR_CAFE,
        ).set_footer(text="Use l!vender <bebida> para vender!"))

    @commands.command(name="vender", aliases=["sell"], help="Venda uma bebida do estoque. Ex: l!vender cappuccino")
    @commands.guild_only()
    async def vender(self, ctx: commands.Context, *, bebida: str):
        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, lambda user: regra_vender(user, bebida))
        if not result["ok"]:
            if result["reason"] == "bebida_invalida":
                return await ctx.send(f"❌ Bebida `{result['bebida']}` não existe! Use `l!estoque` para ver o que você tem.")
            return await ctx.send(f"😢 Sem **{result['bebida_data']['nome']}** no estoque! Use `l!preparar {result['bebida']}`.")

        user = result["user"]
        bebida_data = result["bebida_data"]
        bonus_str = ""
        if result["valor_venda"] > bebida_data["preco_venda"]:
            bonus_str = f"\nBônus da cafeteira: **+{result['valor_venda'] - bebida_data['preco_venda']} 🪙** ✨"
        await ctx.send(embed=discord.Embed(
            title="💰 Venda realizada!",
            description=f"Vendeu **{bebida_data['emoji']} {bebida_data['nome']}** por **{result['valor_venda']} 🪙**!{bonus_str}\nSaldo: **{user['lumicoins']} 🪙**",
            color=COR_OK,
        ).set_footer(text="Lumine Café ☕ • Ótimo negócio!"))

    @commands.command(name="cafe", aliases=["barista"], help="Veja seu perfil de barista.")
    @commands.guild_only()
    async def cafe_perfil(self, ctx: commands.Context):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        nivel = get_nivel(user["xp"])
        idx = next((i for i, item in enumerate(NIVEIS) if item["nivel"] == nivel["nivel"]), None)
        if idx is not None and idx + 1 < len(NIVEIS):
            prox = NIVEIS[idx + 1]
            xp_str = f"{user['xp']} ⭐  (faltam **{prox['xp_min'] - user['xp']}** para {prox['titulo']})"
        else:
            xp_str = f"{user['xp']} ⭐ — **Nível máximo!** 👑"

        inv_str = _ingredientes_str(user["ingredientes"]) or "*vazio — compre em `l!loja`!*"

        def emoji_bebida(key: str) -> str:
            bebida = BEBIDAS.get(key) or RECEITAS_SECRETAS.get(key)
            return bebida["emoji"] if bebida else "❔"

        est_str = "  ".join(f"{emoji_bebida(key)}×{qtd}" for key, qtd in user["estoque"].items()) or "*vazio — prepare em `l!preparar`!*"
        cafeteira = get_cafeteira_info(user)
        embed = discord.Embed(title=f"{nivel['emoji']} {ctx.author.display_name} — Barista", color=COR_PERFIL)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="🏅 Título", value=f"{nivel['emoji']} **{nivel['titulo']}**", inline=True)
        embed.add_field(name="🪙 Lumicoins", value=f"**{user['lumicoins']}**", inline=True)
        embed.add_field(name="☕ Cafeteira", value=f"Nível **{cafeteira['nivel']}** — {cafeteira['nome']}", inline=True)
        embed.add_field(name="⭐ XP", value=xp_str, inline=False)
        embed.add_field(name="🎒 Ingredientes", value=inv_str, inline=False)
        embed.add_field(name="🧺 Bebidas", value=est_str, inline=False)
        await ctx.send(embed=embed.set_footer(text="Lumine Café ☕"))

    @commands.command(name="ranking", aliases=["rank", "top"], help="Ranking da cafeteria: l!ranking cafe")
    @commands.guild_only()
    async def ranking(self, ctx: commands.Context, *, modo: str = "cafe"):
        if modo.strip().lower() not in ("cafe", "café"):
            return await ctx.send("ℹ️ Use `l!ranking cafe` para o ranking da cafeteria!")
        todos = await self.repo.get_all_users(ctx.guild.id)
        if not todos:
            return await ctx.send("😢 Nenhum barista ainda! Use `l!trabalhar` para começar.")
        ordenados = sorted(todos.items(), key=lambda item: item[1].get("lumicoins", 0), reverse=True)[:10]
        medalhas = ["🥇", "🥈", "🥉"]
        linhas = []
        for i, (uid, data) in enumerate(ordenados):
            pos = medalhas[i] if i < 3 else f"**{i + 1}.**"
            try:
                membro = ctx.guild.get_member(int(uid)) or await ctx.guild.fetch_member(int(uid))
                nome = membro.display_name
            except Exception:
                nome = f"Usuário #{uid[:5]}"
            nivel = get_nivel(data.get("xp", 0))
            linhas.append(f"{pos} **{nome}** — {data.get('lumicoins', 0)} 🪙  {nivel['emoji']} {nivel['titulo']}")
        await ctx.send(embed=discord.Embed(
            title="🏆 Ranking da Cafeteria",
            description="\n".join(linhas),
            color=COR_RANK,
        ).set_footer(text="Lumine Café ☕ • Top 10 baristas"))

    @commands.command(name="atender", aliases=["cliente", "servir"], help="Atenda um cliente! (cooldown 1h)")
    @commands.guild_only()
    async def atender(self, ctx: commands.Context, *, bebida_oferecida: str = None):
        if bebida_oferecida is None:
            result = await self.repo.update_user(ctx.guild.id, ctx.author.id, iniciar_atendimento)
            if not result["ok"]:
                return await ctx.send(embed=discord.Embed(
                    description=f"👥 Nenhum cliente novo agora! Próximo em **{formatar_tempo(result['cooldown'])}**. 🕐",
                    color=COR_ERRO,
                ))
            if result["status"] == "pendente":
                pendente = result["pendente"]
                bebida = BEBIDAS[pendente["bebida"]]
                return await ctx.send(
                    f"👥 {pendente['cliente']} ainda está esperando por **{bebida['emoji']} {bebida['nome']}**!\n"
                    f"Use `l!atender {pendente['bebida']}` para servir!"
                )
            cliente = result["cliente"]
            bebida = BEBIDAS[result["bebida"]]
            embed = discord.Embed(
                title=f"{cliente['emoji']} {cliente['nome']} chegou!",
                description=f"*\"{result['intro']}\"*\n\nSirva com `l!atender {result['bebida']}` (**{bebida['emoji']} {bebida['nome']}**)!",
                color=COR_CAFE,
            )
            embed.set_footer(text=f"Personalidade: {cliente['personalidade'].capitalize()} • Lumine Café ☕")
            img_url = await fetch_anime_image(cliente.get("image_tags", {}).get("pedido", "smile"))
            if img_url:
                embed.set_thumbnail(url=img_url)
            return await ctx.send(embed=embed)

        result = await self.repo.update_user(ctx.guild.id, ctx.author.id, lambda user: servir_atendimento(user, bebida_oferecida))
        if not result["ok"]:
            return await ctx.send("❓ Nenhum cliente esperando! Use `l!atender` para chamar um.")

        cliente = result["cliente"]
        bebida_data = result["bebida_data"]
        if result["status"] == "erro":
            motivo = (
                f"Você não tem **{bebida_data['emoji']} {bebida_data['nome']}** no estoque!"
                if result["motivo"] == "sem_estoque"
                else f"{cliente['emoji']} {cliente['nome']} queria **{bebida_data['emoji']} {bebida_data['nome']}**!"
            )
            embed = discord.Embed(
                title=f"😢 {cliente['emoji']} {cliente['nome']} foi embora...",
                description=f"*\"{random.choice(cliente['recusa'])}\"*\n\n{motivo}",
                color=COR_ERRO,
            )
            img_url = await fetch_anime_image(cliente.get("image_tags", {}).get("triste", "cry"))
            if img_url:
                embed.set_thumbnail(url=img_url)
            return await ctx.send(embed=embed)

        user = result["user"]
        bonus_str = ""
        if result["bonus_moedas"] > result["bonus_base"]:
            bonus_str = f"\nBônus da cafeteira: **+{result['bonus_moedas'] - result['bonus_base']} 🪙** ✨"
        embed = discord.Embed(
            title=f"✨ {cliente['emoji']} {cliente['nome']} foi atendido!",
            description=(
                f"*\"{random.choice(cliente['agradecimento'])}\"*\n\n"
                f"🪙 **+{result['bonus_moedas']} Lumicoins** | ⭐ **+{result['bonus_xp']} XP**\n"
                f"Saldo: **{user['lumicoins']} 🪙** | XP: **{user['xp']} ⭐**"
                f"{bonus_str}"
            ),
            color=COR_OK,
        )
        pista = escolher_pista_receita(user, "cliente", 25, cliente=cliente)
        if pista:
            embed.add_field(name="🤫 Pista de cliente", value=pista, inline=False)
        nivel = get_nivel(user["xp"])
        embed.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • Lumine Café ☕")
        img_url = await fetch_anime_image(cliente.get("image_tags", {}).get("feliz", "happy"))
        if img_url:
            embed.set_image(url=img_url)
        await ctx.send(embed=embed)

    def help_meta(self) -> dict:
        return {
            "key": "cafe",
            "aliases": ("café", "cafeteria", "barista", "lumicoins"),
            "icon": "☕",
            "category": "Café da Lumine",
            "blurb": "Venha trabalhar comigo na cafeteria~ ☕✨",
            "intro": (
                "Bem-vindo ao meu cafézinho! Aqui você trabalha, compra ingredientes, "
                "prepara bebidas e atende clientes pra ganhar Lumicoins~ 🪙💙"
            ),
        }

    def help_field(self) -> tuple[str, str]:
        return (
            "☕ __Comandos do Café__",
            "`l!trabalhar` — Ganhe Lumicoins (cooldown 30min) 💼\n"
            "`l!loja` — Ingredientes à venda 🏪  |  `l!comprar <item> [qtd] ...` — Compre (vários!) 🛍️\n"
            "`l!cafeteira` — Veja upgrades ☕  |  `l!melhorar cafeteira` — Gaste Lumicoins em melhorias ✨\n"
            "`l!cardapio` — Veja receitas e preços 📋\n"
            "`l!preparar <bebida>` — Prepare uma bebida ☕\n"
            "`l!inventar <ing1> <ing2> ...` — Misture ingredientes pra descobrir receitas secretas! 🧪✨\n"
            "`l!estoque` — Bebidas prontas 🧺  |  `l!vender <bebida>` — Venda 💰\n"
            "`l!atender [bebida]` — Atenda um cliente especial! 👥\n"
            "`l!cafe` — Seu perfil de barista ⭐  |  `l!ranking cafe` — Top 10 🏆",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Cafe(bot))
