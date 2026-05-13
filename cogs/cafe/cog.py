from __future__ import annotations

import random
import time as _time

import discord
from discord.ext import commands, tasks

from .catalog import BEBIDAS, CD_CLIENTE, CD_ATENDER, CD_TRABALHAR, INGREDIENTES, LOJA_CATEGORIAS, NIVEIS, RECEITAS_SECRETAS, UPGRADES_CAFETEIRA
from .conquistas import CONQUISTAS
from .daily import get_bebida_do_dia, get_bonus_bebida_venda_pct, get_bonus_bebida_xp_pct, get_categoria_desconto, get_desconto_pct
from .images import fetch_anime_image
from .narrative import CLIENTES, CLIENTES_VIP, FRASES_BEBIDA_DO_DIA, FRASES_CATEGORIA_DESCONTO, FRASES_INVENTAR_ACERTO, FRASES_INVENTAR_ERRO, FRASES_TRABALHAR, FRASES_TRABALHAR_POR_HUMOR, escolher_pista_receita

try:
    from utils.mood import frase_com_humor as _frase_humor
    _MOOD_CAFE_OK = True
except Exception:
    _MOOD_CAFE_OK = False
from .repository import CafeRepository
from .service import (
    comprar as regra_comprar,
    cooldown_restante,
    dar_moedas as regra_dar,
    executar_troca as regra_trocar,
    formatar_tempo,
    get_cafeteira_info,
    get_cafeteira_nivel,
    get_nivel,
    iniciar_atendimento,
    inventar as regra_inventar,
    is_client_expired,
    melhorar_cafeteira,
    normalizar_ingrediente,
    preparar as regra_preparar,
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


def _cooldown_status(restante: float) -> str:
    return f"⏳ **{formatar_tempo(restante)}**" if restante else "✅ **pronto**"


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


def _parse_trade_side(tokens: list[str]) -> tuple[str | None, int, str]:
    """Interpreta um lado da troca (ex: ["grão", "5"] ou ["leite", "condensado", "2"]).
    Retorna (chave_ingrediente | None, quantidade, nome_digitado)."""
    if not tokens:
        return None, 1, ""
    qtd = 1
    name_tokens = list(tokens)
    if name_tokens[-1].isdigit():
        qtd = max(1, int(name_tokens[-1]))
        name_tokens = name_tokens[:-1]
    if not name_tokens:
        return None, qtd, ""
    raw = " ".join(name_tokens)
    return normalizar_ingrediente(raw), qtd, raw


class TradeView(discord.ui.View):
    def __init__(
        self,
        cog: "Cafe",
        sender: discord.abc.User,
        receiver: discord.abc.User,
        guild_id: int,
        ing_a: str,
        qtd_a: int,
        ing_b: str,
        qtd_b: int,
    ):
        super().__init__(timeout=60)
        self.cog = cog
        self.sender = sender
        self.receiver = receiver
        self.guild_id = guild_id
        self.ing_a = ing_a
        self.qtd_a = qtd_a
        self.ing_b = ing_b
        self.qtd_b = qtd_b
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.receiver:
            await interaction.response.send_message(
                "Só quem recebeu a proposta pode responder~ 💙", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore
        if self.message:
            try:
                ing_a_info = INGREDIENTES[self.ing_a]
                ing_b_info = INGREDIENTES[self.ing_b]
                embed = discord.Embed(
                    title="⏰ Proposta expirada",
                    description=(
                        f"**{self.sender.display_name}** ofereceu **{self.qtd_a}× {ing_a_info['emoji']} {ing_a_info['nome']}**"
                        f" por **{self.qtd_b}× {ing_b_info['emoji']} {ing_b_info['nome']}**\n\n"
                        f"{self.receiver.display_name} não respondeu a tempo."
                    ),
                    color=COR_ERRO,
                )
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Aceitar", emoji="🤝", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self.cog.repo.trocar_ingredientes(
            self.guild_id, self.sender.id, self.receiver.id,
            self.ing_a, self.qtd_a, self.ing_b, self.qtd_b,
        )
        ing_a_info = INGREDIENTES[self.ing_a]
        ing_b_info = INGREDIENTES[self.ing_b]
        for item in self.children:
            item.disabled = True  # type: ignore
        if result["ok"]:
            embed = discord.Embed(
                title="✅ Troca realizada!",
                description=(
                    f"**{self.sender.display_name}** entregou **{self.qtd_a}× {ing_a_info['emoji']} {ing_a_info['nome']}**\n"
                    f"**{self.receiver.display_name}** entregou **{self.qtd_b}× {ing_b_info['emoji']} {ing_b_info['nome']}**\n\n"
                    "Troca concluída com sucesso~ 🤝💙"
                ),
                color=COR_OK,
            )
        else:
            reason = result["reason"]
            if reason == "sem_ingredientes_a":
                quem = self.sender.display_name
                ing_info = ing_a_info
                tem, precisa = result["tem"], result["precisa"]
            else:
                quem = self.receiver.display_name
                ing_info = ing_b_info
                tem, precisa = result["tem"], result["precisa"]
            embed = discord.Embed(
                title="❌ Troca cancelada!",
                description=(
                    f"**{quem}** não tem ingredientes suficientes!\n"
                    f"{ing_info['emoji']} **{ing_info['nome']}**: tem **{tem}**, precisava de **{precisa}**."
                ),
                color=COR_ERRO,
            )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Recusar", emoji="❌", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ing_a_info = INGREDIENTES[self.ing_a]
        ing_b_info = INGREDIENTES[self.ing_b]
        for item in self.children:
            item.disabled = True  # type: ignore
        embed = discord.Embed(
            title="❌ Proposta recusada",
            description=(
                f"**{self.receiver.display_name}** recusou a troca de "
                f"**{self.qtd_a}× {ing_a_info['emoji']} {ing_a_info['nome']}**"
                f" por **{self.qtd_b}× {ing_b_info['emoji']} {ing_b_info['nome']}**."
            ),
            color=COR_ERRO,
        )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=self)


class Cafe(commands.Cog):
    """☕ Minigame de cafeteria da Lumine."""

    def __init__(self, bot: commands.Bot, repo: CafeRepository | None = None):
        self.bot = bot
        self.repo = repo or CafeRepository()

    async def cog_load(self) -> None:
        self._verificar_timeouts.start()

    async def cog_unload(self) -> None:
        self._verificar_timeouts.cancel()

    @tasks.loop(seconds=30)
    async def _verificar_timeouts(self) -> None:
        """Verifica a cada 30s se algum cliente expirou (5 min sem ser atendido)."""
        agora = _time.time()
        try:
            pendentes = await self.repo.get_all_pending_clients()
        except Exception:
            return

        for guild_id, user_id, pendente in pendentes:
            ts = pendente.get("ts", agora)
            if agora - ts < CD_CLIENTE:
                continue
            channel_id = pendente.get("channel_id")
            try:
                await self.repo.remover_cliente_pendente(guild_id, user_id)
                await self._notificar_timeout(user_id, channel_id, pendente)
            except Exception:
                pass

    @_verificar_timeouts.before_loop
    async def _before_verificar(self) -> None:
        await self.bot.wait_until_ready()

    async def _notificar_timeout(self, user_id: int, channel_id: int | None, pendente: dict) -> None:
        if not channel_id:
            return
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return

        cliente_nome = pendente.get("cliente", "")
        vip = pendente.get("vip", False)
        all_clients = CLIENTES + CLIENTES_VIP
        cliente = next((c for c in all_clients if c["nome"] == cliente_nome), None)

        if cliente:
            emoji = cliente["emoji"]
            fala = random.choice(cliente.get("timeout", ["...Parece que esqueceram de mim."]))
            if vip:
                embed = discord.Embed(
                    title=f"💸 {emoji} {cliente_nome} foi embora sem ser atendido!",
                    description=f'*"{fala}"*\n\nVocê perdeu um **cliente VIP**! 😰 O cooldown continua...',
                    color=COR_ERRO,
                )
                embed.set_footer(text="Clientes VIP não esperam pra sempre... 💔")
            else:
                embed = discord.Embed(
                    title=f"😔 {emoji} {cliente_nome} foi embora...",
                    description=f'*"{fala}"*\n\nEsperou 5 minutos e desistiu. O cooldown continua.',
                    color=COR_ERRO,
                )
        else:
            embed = discord.Embed(
                description="⏰ Um cliente esperou demais e foi embora sem ser atendido.",
                color=COR_ERRO,
            )

        try:
            await channel.send(content=f"<@{user_id}>", embed=embed)
        except discord.HTTPException:
            pass

    def _bonus_cafeteira_linhas(self, info: dict) -> list[str]:
        linhas = []
        if info["bonus_venda"]:
            linhas.append(f"💰 +{info['bonus_venda']}% valor de venda")
        if info["bonus_xp"]:
            linhas.append(f"⭐ +{info['bonus_xp']}% XP ao preparar")
        if info["bonus_atendimento"]:
            linhas.append(f"🪙 +{info['bonus_atendimento']}% gorjeta ao atender")
        return linhas or ["Sem bônus ativos ainda."]

    def _build_loja_embed(self, saldo: int, page: int, total_pages: int) -> discord.Embed:
        categoria_key, titulo = LOJA_CATEGORIAS[page - 1]
        cat_desconto = get_categoria_desconto()
        em_promo = categoria_key == cat_desconto
        linhas = []
        for key, ing in INGREDIENTES.items():
            if ing.get("categoria") != categoria_key:
                continue
            preco_orig = ing["preco"]
            if em_promo:
                preco_desc = max(1, preco_orig * (100 - get_desconto_pct()) // 100)
                linha = f"{ing['emoji']} **{ing['nome']}** — ~~{preco_orig}~~ **{preco_desc} 🪙** 🏷️ | `l!comprar {key}`"
            else:
                linha = f"{ing['emoji']} **{ing['nome']}** — {preco_orig} 🪙 | `l!comprar {key}`"
            linhas.append(linha)
        titulo_campo = f"{titulo} {'🏷️ PROMOÇÃO HOJE!' if em_promo else ''}"
        embed = discord.Embed(
            title="🏪 Loja de Ingredientes",
            description=(
                f"Saldo: **{saldo} 🪙** — Use `l!comprar <ingrediente> [qtd]`\n"
                "Ex.: `l!comprar grao 2 leite 3` ou `l!comprar leite condensado 2`\n​"
            ),
            color=COR_LOJA,
        )
        embed.add_field(name=titulo_campo, value="\n".join(linhas) or "*Nada por aqui ainda.*", inline=False)
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
                f"*{_frase_humor(FRASES_TRABALHAR_POR_HUMOR, FRASES_TRABALHAR) if _MOOD_CAFE_OK else random.choice(FRASES_TRABALHAR)}*\n\n"
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
        await self._notificar_conquistas(ctx, result)

    @commands.command(name="loja", aliases=["shop"], help="Ingredientes disponíveis para comprar.")
    @commands.guild_only()
    async def loja(self, ctx: commands.Context, page: int = 1):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        total = len(LOJA_CATEGORIAS)
        page = max(1, min(page, total))
        view = LojaView(self, ctx.author, page)

        # Frase da Lumine sobre a promoção do dia
        cat_key = get_categoria_desconto()
        cat_nome = next((titulo for key, titulo in LOJA_CATEGORIAS if key == cat_key), cat_key)
        frase = random.choice(FRASES_CATEGORIA_DESCONTO).format(
            categoria=cat_nome, desconto=get_desconto_pct()
        )
        await ctx.send(f"*{frase}*")
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
        await self._notificar_conquistas(ctx, result)

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
        embed = discord.Embed(
            title="🛍️ Compra realizada!",
            description="\n".join(
                f"{'🏷️ ' if item.get('em_promocao') else ''}**{item['quantidade']}× {INGREDIENTES[item['key']]['emoji']} {INGREDIENTES[item['key']]['nome']}** — {item['subtotal']} 🪙"
                for item in result["linhas"]
            ) + (
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

        bebida_dia_key = get_bebida_do_dia()
        bebida_dia_data = BEBIDAS.get(bebida_dia_key)

        embed = discord.Embed(
            title="📋 Cardápio da Lumine Café",
            description="Use `l!preparar <bebida>` para fazer uma!\n​",
            color=COR_CAFE,
        )
        for key, bebida in BEBIDAS.items():
            estrela = " ⭐" if key == bebida_dia_key else ""
            embed.add_field(
                name=f"{bebida['emoji']} {bebida['nome']}{estrela} — {bebida['preco_venda']} 🪙 | +{bebida['xp']} ⭐",
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

        # Frase da Lumine sobre a bebida do dia
        if bebida_dia_data:
            frase = random.choice(FRASES_BEBIDA_DO_DIA).format(
                bebida=bebida_dia_data["nome"],
                emoji=bebida_dia_data["emoji"],
                bonus_xp=get_bonus_bebida_xp_pct(),
                bonus_venda=get_bonus_bebida_venda_pct(),
            )
            await ctx.send(f"*{frase}*")

        await ctx.send(embed=embed)

    @commands.command(name="preparar", aliases=["fazer", "brew"], help="Prepare uma bebida. Ex: l!preparar cappuccino 3")
    @commands.guild_only()
    async def preparar(self, ctx: commands.Context, *, bebida: str):
        # Parseia quantidade opcional no final: "cappuccino 3" → bebida="cappuccino", qtd=3
        tokens = bebida.strip().split()
        quantidade = 1
        if len(tokens) >= 2 and tokens[-1].isdigit():
            quantidade = max(1, min(int(tokens[-1]), 20))
            bebida = " ".join(tokens[:-1])

        result = await self.repo.update_user(
            ctx.guild.id, ctx.author.id,
            lambda user: regra_preparar(user, bebida, quantidade),
        )
        if not result["ok"]:
            if result["reason"] == "bebida_invalida":
                opcoes = ", ".join(f"`{opcao}`" for opcao in result["opcoes"])
                return await ctx.send(f"❌ Bebida não encontrada! Opções: {opcoes}\nVeja o `l!cardapio`!")
            bebida_data = BEBIDAS.get(result.get("bebida")) or RECEITAS_SECRETAS.get(result.get("bebida"))
            title = "😢 Faltam ingredientes!"
            if bebida_data:
                qtd_label = f" ×{quantidade}" if quantidade > 1 else ""
                title = f"😢 Faltam ingredientes para {quantidade}× {bebida_data['emoji']} {bebida_data['nome']}!" if quantidade > 1 else f"😢 Faltam ingredientes para {bebida_data['emoji']} {bebida_data['nome']}!"
            return await ctx.send(embed=discord.Embed(
                title=title,
                description=_faltando_str(result["faltando"]) + "\n\nUse `l!comprar` para abastecer!",
                color=COR_ERRO,
            ))

        user = result["user"]
        bebida_data = result["bebida_data"]
        qtd = result["quantidade"]
        xp_ganho = result["xp_ganho"]
        bonus_dia_xp = result["bonus_dia_xp"]
        nivel = get_nivel(user["xp"])

        bonus_str = ""
        xp_cafeteira = xp_ganho - bebida_data["xp"] * qtd - bonus_dia_xp
        if xp_cafeteira > 0:
            bonus_str += f"\n**Bônus da cafeteira:** +{xp_cafeteira} XP ✨"
        if bonus_dia_xp:
            bonus_str += f"\n**⭐ Bebida do dia:** +{bonus_dia_xp} XP bônus! 🌟"

        if qtd == 1:
            titulo = f"☕ {bebida_data['emoji']} {bebida_data['nome']} preparado!"
            intro = "*Que cheirinho gostoso...* ✨\n\n"
            rodape = f"Bebida no estoque! Use `l!vender {result['bebida']}` para vender. 🏪"
        else:
            titulo = f"☕ {bebida_data['emoji']} {bebida_data['nome']} ×{qtd} preparados!"
            intro = f"*Que produção! {qtd} xícaras quentinhas a postos...* ✨\n\n"
            rodape = f"{qtd} bebidas no estoque! Use `l!vender {result['bebida']}` para vender. 🏪"

        await ctx.send(embed=discord.Embed(
            title=titulo,
            description=(
                f"{intro}"
                f"**Receita:** {_receita_str(bebida_data['receita'])}\n"
                f"**XP ganho:** +{xp_ganho} ⭐  |  XP total: {user['xp']} ⭐"
                f"{bonus_str}\n\n"
                f"{rodape}"
            ),
            color=COR_OK,
        ).set_footer(text=f"{nivel['emoji']} {nivel['titulo']}"))
        await self._notificar_conquistas(ctx, result)


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
        await self._notificar_conquistas(ctx, result)

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
            bonus_cafeteira = result["valor_venda"] - bebida_data["preco_venda"] - result.get("bonus_dia_venda", 0)
            if bonus_cafeteira > 0:
                bonus_str += f"\nBônus da cafeteira: **+{bonus_cafeteira} 🪙** ✨"
        if result.get("bonus_dia_venda"):
            bonus_str += f"\n🌟 **Bebida do dia:** +{result['bonus_dia_venda']} 🪙 bônus!"
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
        trabalho_cd = cooldown_restante(user["cd_trabalhar"], CD_TRABALHAR)
        atender_cd = cooldown_restante(user["cd_atender"], CD_ATENDER)
        cooldowns = [
            f"💼 Trabalhar: {_cooldown_status(trabalho_cd)}",
            f"👥 Atender: {_cooldown_status(atender_cd)}",
        ]
        if user.get("cliente_pendente"):
            pendente = user["cliente_pendente"]
            bebida = BEBIDAS.get(pendente.get("bebida"))
            if bebida:
                cooldowns.append(f"🪑 Cliente esperando: **{pendente['cliente']}** quer {bebida['emoji']} **{bebida['nome']}**")
        cafeteira = get_cafeteira_info(user)
        embed = discord.Embed(title=f"{nivel['emoji']} {ctx.author.display_name} — Barista", color=COR_PERFIL)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="🏅 Título", value=f"{nivel['emoji']} **{nivel['titulo']}**", inline=True)
        embed.add_field(name="🪙 Lumicoins", value=f"**{user['lumicoins']}**", inline=True)
        embed.add_field(name="☕ Cafeteira", value=f"Nível **{cafeteira['nivel']}** — {cafeteira['nome']}", inline=True)
        embed.add_field(name="⭐ XP", value=xp_str, inline=False)
        embed.add_field(name="⏱️ Cooldowns", value="\n".join(cooldowns), inline=False)
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
                bebida_key = pendente["bebida"]
                bebida = BEBIDAS.get(bebida_key) or RECEITAS_SECRETAS.get(bebida_key)
                if not bebida:
                    return await ctx.send("❓ Nenhum cliente esperando no momento.")
                restante = max(0, CD_CLIENTE - (_time.time() - pendente.get("ts", _time.time())))
                vip_tag = " 👑 VIP" if pendente.get("vip") else ""
                return await ctx.send(
                    f"👥{vip_tag} **{pendente['cliente']}** ainda está esperando por "
                    f"**{bebida['emoji']} {bebida['nome']}**!\n"
                    f"Use `l!atender {bebida_key}` para servir! ⏰ {formatar_tempo(restante)} restantes."
                )
            cliente = result["cliente"]
            bebida_key = result["bebida"]
            bebida = result["bebida_data"]
            eh_vip = result["vip"]

            # Salva o canal para o background task de timeout
            await self.repo.set_client_channel_id(ctx.guild.id, ctx.author.id, ctx.channel.id)

            cor_embed = discord.Color.gold() if eh_vip else COR_CAFE
            vip_prefix = "👑 **CLIENTE VIP** — " if eh_vip else ""
            recompensa_str = "**80–220 🪙** | **15–40 ⭐**" if eh_vip else "20–60 🪙 | 5–15 ⭐"
            embed = discord.Embed(
                title=f"{vip_prefix}{cliente['emoji']} {cliente['nome']} chegou!",
                description=(
                    f"*\"{result['intro']}\"*\n\n"
                    f"Sirva com `l!atender {bebida_key}` (**{bebida['emoji']} {bebida['nome']}**)!\n"
                    f"⏰ Você tem **5 minutos** antes de {cliente['nome']} ir embora!"
                ),
                color=cor_embed,
            )
            embed.add_field(name="💰 Recompensa potencial", value=recompensa_str, inline=True)
            tipo_str = f"{cliente['personalidade'].capitalize()} • {'👑 VIP' if eh_vip else 'Cliente regular'}"
            embed.set_footer(text=f"{tipo_str} • Lumine Café ☕")
            img_url = await fetch_anime_image(cliente.get("image_tags", {}).get("pedido", "smile"))
            if img_url:
                embed.set_thumbnail(url=img_url)
            return await ctx.send(embed=embed)


        result = await self.repo.atender_com_roubo(ctx.guild.id, ctx.author.id, bebida_oferecida)
        if not result["ok"]:
            reason = result["reason"]
            if reason == "cliente_expirado":
                return await ctx.send(embed=discord.Embed(
                    description="⏰ O cliente já foi embora antes de ser atendido... tente `l!atender` para chamar um novo!",
                    color=COR_ERRO,
                ))
            if reason == "bebida_invalida":
                return await ctx.send(f"❌ Bebida `{result['bebida']}` não existe! Veja o `l!cardapio`.")
            if reason == "sem_estoque":
                bebida_data = result["bebida_data"]
                return await ctx.send(
                    f"🧺 Você não tem **{bebida_data['emoji']} {bebida_data['nome']}** no estoque! "
                    f"Prepare com `l!preparar {result['bebida']}` antes de tentar atender."
                )
            if reason == "sem_cliente_roubavel":
                bebida_data = result["bebida_data"]
                return await ctx.send(
                    f"👥 Nenhum cliente de outro balcão aceitou **{bebida_data['emoji']} {bebida_data['nome']}** agora. "
                    "Use `l!atender` para chamar um cliente seu."
                )
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

        if result["status"] == "roubo":
            try:
                alvo_id = int(result["alvo_id"])
                alvo = ctx.guild.get_member(alvo_id) or await ctx.guild.fetch_member(alvo_id)
                alvo_nome = alvo.display_name
            except (ValueError, discord.HTTPException):
                alvo_nome = f"Barista #{str(result['alvo_id'])[-5:]}"

            falas = cliente.get("roubado_atendido") or [
                "Ah... troca de balcão inesperada, mas o pedido chegou direitinho."
            ]
            embed = discord.Embed(
                title=f"🏃 {cliente['emoji']} {cliente['nome']} mudou de balcão!",
                description=(
                    f"*\"{random.choice(falas)}\"*\n\n"
                    f"**Cliente de:** {alvo_nome}\n"
                    f"**Bebida servida:** {bebida_data['emoji']} {bebida_data['nome']}\n"
                    f"🪙 **+{result['bonus_moedas']} Lumicoins** | ⭐ **+{result['bonus_xp']} XP**\n"
                    f"Saldo: **{user['lumicoins']} 🪙** | XP: **{user['xp']} ⭐**"
                    f"{bonus_str}\n\n"
                    f"{alvo_nome} perdeu o cliente e o cooldown continua contando. Vacilou, dançou."
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
            await self._notificar_conquistas(ctx, result)
            return

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
        await self._notificar_conquistas(ctx, result)

    @commands.command(name="dar", aliases=["give", "pagar"], help="Dê Lumicoins para outro barista. Ex: l!dar @user 100")
    @commands.guild_only()
    async def dar(self, ctx: commands.Context, membro: discord.Member, quantidade: int):
        if membro == ctx.author:
            return await ctx.send(embed=discord.Embed(
                description="💙 Você não pode dar moedas para si mesmo~", color=COR_ERRO,
            ))
        if membro.bot:
            return await ctx.send(embed=discord.Embed(
                description="🤖 Bots não precisam de Lumicoins~", color=COR_ERRO,
            ))
        result = await self.repo.dar_moedas(ctx.guild.id, ctx.author.id, membro.id, quantidade)
        if not result["ok"]:
            if result["reason"] == "quantidade_invalida":
                return await ctx.send(embed=discord.Embed(
                    description="❌ A quantidade precisa ser pelo menos **1 🪙**.", color=COR_ERRO,
                ))
            return await ctx.send(embed=discord.Embed(
                title="💸 Saldo insuficiente!",
                description=(
                    f"Você tem **{result['saldo']} 🪙** mas tentou dar **{quantidade} 🪙**.\n"
                    "Use `l!trabalhar` para ganhar mais!"
                ),
                color=COR_ERRO,
            ))
        embed = discord.Embed(
            title="💸 Lumicoins enviados!",
            description=(
                f"**{ctx.author.display_name}** deu **{quantidade} 🪙** para **{membro.display_name}**~ 💙\n\n"
                f"Saldo restante: **{result['user_sender']['lumicoins']} 🪙**"
            ),
            color=COR_OK,
        )
        embed.set_footer(text="Lumine Café ☕ • Que generoso~")
        await ctx.send(embed=embed)

    @commands.command(name="trocar", aliases=["trade", "troca"], help="Proponha uma troca de ingredientes. Ex: l!trocar @user grão 5 por leite 3")
    @commands.guild_only()
    async def trocar(self, ctx: commands.Context, membro: discord.Member, *args: str):
        _USO = "❌ Formato: `l!trocar @user <ingrediente> [qtd] por <ingrediente> [qtd]`\nEx: `l!trocar @Carlos grão 5 por leite 3`"
        if membro == ctx.author:
            return await ctx.send(embed=discord.Embed(description="💙 Você não pode trocar consigo mesmo~", color=COR_ERRO))
        if membro.bot:
            return await ctx.send(embed=discord.Embed(description="🤖 Bots não têm ingredientes pra trocar~", color=COR_ERRO))
        if not args:
            return await ctx.send(_USO)

        combined = " ".join(args)
        parts = combined.split(" por ", 1)
        if len(parts) != 2:
            return await ctx.send(_USO)

        key_a, qtd_a, raw_a = _parse_trade_side(parts[0].split())
        key_b, qtd_b, raw_b = _parse_trade_side(parts[1].split())

        if key_a is None:
            return await ctx.send(f"❌ Ingrediente `{raw_a}` não existe! Use `l!loja` para ver as opções.")
        if key_b is None:
            return await ctx.send(f"❌ Ingrediente `{raw_b}` não existe! Use `l!loja` para ver as opções.")

        # Valida pré-proposta: sender tem o que vai dar
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        tem = user["ingredientes"].get(key_a, 0)
        if tem < qtd_a:
            ing_info = INGREDIENTES[key_a]
            return await ctx.send(embed=discord.Embed(
                title="😢 Ingredientes insuficientes!",
                description=f"Você tem **{tem}× {ing_info['emoji']} {ing_info['nome']}** mas quer dar **{qtd_a}×**.",
                color=COR_ERRO,
            ))

        ing_a_info = INGREDIENTES[key_a]
        ing_b_info = INGREDIENTES[key_b]
        embed = discord.Embed(
            title="🤝 Proposta de troca!",
            description=(
                f"**{ctx.author.display_name}** quer trocar com {membro.mention}:\n\n"
                f"Dá: **{qtd_a}× {ing_a_info['emoji']} {ing_a_info['nome']}**\n"
                f"Recebe: **{qtd_b}× {ing_b_info['emoji']} {ing_b_info['nome']}**\n\n"
                f"⏰ {membro.mention}, você tem **60 segundos** para responder!"
            ),
            color=COR_LOJA,
        )
        embed.set_footer(text="Lumine Café ☕ • Negociação em andamento~")
        view = TradeView(self, ctx.author, membro, ctx.guild.id, key_a, qtd_a, key_b, qtd_b)
        view.message = await ctx.send(embed=embed, view=view)

    async def _notificar_conquistas(self, ctx: commands.Context, result: dict) -> None:
        for key in result.get("conquistas_novas", []):
            conquista = CONQUISTAS.get(key)
            if not conquista:
                continue
            embed = discord.Embed(
                title="🏆 Conquista desbloqueada!",
                description=f"{conquista['emoji']} **{conquista['nome']}**\n_{conquista['descricao']}_",
                color=COR_RANK,
            )
            embed.set_footer(text="Lumine Café ☕ • Parabéns~! 💙")
            await ctx.send(embed=embed)

    @commands.command(name="conquistas", aliases=["achievements", "badges"], help="Veja suas conquistas no café.")
    @commands.guild_only()
    async def conquistas(self, ctx: commands.Context):
        user = await self.repo.get_user(ctx.guild.id, ctx.author.id)
        desbloqueadas = user.get("conquistas", [])
        total = len(CONQUISTAS)

        linhas_desbloq = []
        linhas_bloq = []
        for key, c in CONQUISTAS.items():
            if key in desbloqueadas:
                linhas_desbloq.append(f"✅ {c['emoji']} **{c['nome']}** — _{c['descricao']}_")
            else:
                linhas_bloq.append(f"🔒 {c['emoji']} {c['nome']}")

        embed = discord.Embed(
            title=f"🏆 Conquistas — {ctx.author.display_name}",
            description=f"**{len(desbloqueadas)}/{total}** conquistas desbloqueadas\n​",
            color=COR_RANK,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        if linhas_desbloq:
            embed.add_field(name="✅ Desbloqueadas", value="\n".join(linhas_desbloq), inline=False)
        if linhas_bloq:
            embed.add_field(name="🔒 Bloqueadas", value="\n".join(linhas_bloq), inline=False)
        embed.set_footer(text="Lumine Café ☕")
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
            "`l!preparar <bebida> [qtd]` — Prepare uma ou várias bebidas de uma vez ☕ (ex: `l!preparar cappuccino 3`)\n"
            "`l!inventar <ing1> <ing2> ...` — Misture ingredientes pra descobrir receitas secretas! 🧪✨\n"
            "`l!estoque` — Bebidas prontas 🧺  |  `l!vender <bebida>` — Venda 💰\n"
            "`l!atender [bebida]` — Atenda cliente seu ou fisgue cliente distraído! 👥\n"
            "`l!cafe` — Seu perfil de barista ⭐  |  `l!ranking cafe` — Top 10 🏆\n"
            "`l!dar @user <qtd>` — Dê Lumicoins para outro barista 💸\n"
            "`l!trocar @user <ing> [qtd] por <ing> [qtd]` — Proponha troca de ingredientes 🤝\n"
            "`l!conquistas` — Veja suas conquistas 🏆",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Cafe(bot))
