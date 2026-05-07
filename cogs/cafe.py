"""cafe.py — Cog do ☕ Café da Lumine."""
import random, time
import discord
from discord.ext import commands
from cogs.cafe_core import (
    BEBIDAS, CLIENTES, INGREDIENTES, FRASES_TRABALHAR,
    RECEITAS_SECRETAS, FRASES_INVENTAR_ERRO, FRASES_INVENTAR_ACERTO,
    CD_TRABALHAR, CD_ATENDER,
    get_user, save_user, get_all_users, get_nivel,
    cooldown_restante, formatar_tempo, NIVEIS,
    UPGRADES_CAFETEIRA, get_cafeteira_info, get_cafeteira_nivel,
    aplicar_bonus_percentual, escolher_pista_receita,
)
from cogs.cafe_images import fetch_anime_image

COR_CAFE   = discord.Color.from_rgb(139, 90,  43)
COR_OK     = discord.Color.from_rgb(107, 191, 139)
COR_ERRO   = discord.Color.from_rgb(220, 100, 100)
COR_LOJA   = discord.Color.from_rgb(255, 183,  77)
COR_PERFIL = discord.Color.from_rgb(181, 126, 220)
COR_RANK   = discord.Color.from_rgb(255, 215, 100)

LOJA_CATEGORIAS = (
    ("básicos", "☕ Básicos e Grãos"),
    ("laticínios", "🥛 Laticínios"),
    ("xaropes", "🍯 Adoçantes e Xaropes"),
    ("especiarias", "🌿 Especiarias e Ervas"),
    ("frutas", "🍓 Frutas e Extras"),
)


class LojaView(discord.ui.View):
    """Paginação da loja de ingredientes por categoria."""

    def __init__(self, cog: "Cafe", author, page: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.author = author
        self.current_page = page
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Só quem abriu a loja pode navegar nela~ 💙", ephemeral=True
            )
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
        u = get_user(interaction.guild.id, self.author.id)
        await interaction.response.edit_message(
            embed=self.cog._build_loja_embed(u["lumicoins"], self.current_page, total),
            view=self,
        )

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, -1)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, +1)


class Cafe(commands.Cog):
    """☕ Minigame de cafeteria da Lumine!"""

    def __init__(self, bot):
        self.bot = bot

    # ── l!trabalhar ──────────────────────────────────────────────────────────

    @commands.command(name="trabalhar", aliases=["work", "trab"],
                      help="Trabalhe e ganhe Lumicoins! (cooldown 30min)")
    async def trabalhar(self, ctx):
        u = get_user(ctx.guild.id, ctx.author.id)
        cd = cooldown_restante(u["cd_trabalhar"], CD_TRABALHAR)
        if cd:
            return await ctx.send(embed=discord.Embed(
                description=f"☕ Ainda cansada! Descanse por **{formatar_tempo(cd)}**. 💤",
                color=COR_ERRO).set_footer(text="Lumine Café ☕"))

        ganho = random.randint(30, 90)
        u["lumicoins"] += ganho
        u["cd_trabalhar"] = time.time()
        save_user(ctx.guild.id, ctx.author.id, u)
        nivel = get_nivel(u["xp"])
        emb = discord.Embed(
            title="💼 Turno concluído!",
            description=f"*{random.choice(FRASES_TRABALHAR)}*\n\n"
                        f"Ganhou **{ganho} Lumicoins** 🪙 — Saldo: **{u['lumicoins']} 🪙**",
            color=COR_OK)
        emb.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        pista = escolher_pista_receita(u, "lumine", 20)
        if pista:
            emb.add_field(name="🤫 Inspiração da Lumine", value=pista, inline=False)
        emb.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • próximo turno em 30min")
        await ctx.send(embed=emb)

    # ── l!loja ───────────────────────────────────────────────────────────────

    def _build_loja_embed(self, saldo: int, page: int, total_pages: int) -> discord.Embed:
        categoria_key, titulo = LOJA_CATEGORIAS[page - 1]
        linhas = [
            f"{ing['emoji']} **{ing['nome']}** — {ing['preco']} 🪙 | `l!comprar {key}`"
            for key, ing in INGREDIENTES.items()
            if ing.get("categoria") == categoria_key
        ]
        emb = discord.Embed(
            title="🏪 Loja de Ingredientes",
            description=(
                f"Saldo: **{saldo} 🪙** — Use `l!comprar <ingrediente> [qtd]`\n"
                "Ex.: `l!comprar grao 2 leite 3`\n​"
            ),
            color=COR_LOJA)
        emb.add_field(name=titulo, value="\n".join(linhas) or "*Nada por aqui ainda.*", inline=False)
        emb.set_footer(text=f"Página {page}/{total_pages} • Lumine Café ☕")
        return emb

    @commands.command(name="loja", aliases=["shop"], help="Ingredientes disponíveis para comprar.")
    async def loja(self, ctx, page: int = 1):
        u = get_user(ctx.guild.id, ctx.author.id)
        total = len(LOJA_CATEGORIAS)
        page = max(1, min(page, total))
        embed = self._build_loja_embed(u["lumicoins"], page, total)
        view = LojaView(self, ctx.author, page)
        view.message = await ctx.send(embed=embed, view=view)

    # ── l!cafeteira / l!melhorar ─────────────────────────────────────────────

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

    @commands.command(name="cafeteira", aliases=["upgrades"], help="Veja e melhore sua cafeteira.")
    async def cafeteira(self, ctx):
        u = get_user(ctx.guild.id, ctx.author.id)
        nivel = get_cafeteira_nivel(u)
        atual = UPGRADES_CAFETEIRA[nivel]
        emb = discord.Embed(
            title="☕ Cafeteira da Lumine",
            description=(
                f"Nível atual: **{nivel} — {atual['nome']}**\n"
                f"Saldo: **{u['lumicoins']} 🪙**"
            ),
            color=COR_CAFE,
        )
        emb.add_field(name="Bônus ativos", value="\n".join(self._bonus_cafeteira_linhas(atual)), inline=False)

        if nivel + 1 < len(UPGRADES_CAFETEIRA):
            prox = UPGRADES_CAFETEIRA[nivel + 1]
            emb.add_field(
                name=f"Próximo upgrade: nível {prox['nivel']} — {prox['nome']}",
                value=(
                    f"Custo: **{prox['custo']} 🪙**\n"
                    f"Bônus: {', '.join(self._bonus_cafeteira_linhas(prox))}\n"
                    "Use `l!melhorar cafeteira` para comprar."
                ),
                inline=False,
            )
        else:
            emb.add_field(
                name="Próximo upgrade",
                value="Sua cafeteira já está no nível máximo. Coisa fina demais.",
                inline=False,
            )
        emb.set_footer(text="Lumine Café ☕")
        await ctx.send(embed=emb)

    @commands.command(name="melhorar", aliases=["upgrade"], help="Melhore sua cafeteira com Lumicoins.")
    async def melhorar(self, ctx, *, alvo: str = "cafeteira"):
        alvo = alvo.lower().strip()
        if alvo not in ("cafeteira", "cafe", "café"):
            return await ctx.send("❌ Por enquanto só dá para melhorar a `cafeteira`.")

        u = get_user(ctx.guild.id, ctx.author.id)
        nivel = get_cafeteira_nivel(u)
        if nivel + 1 >= len(UPGRADES_CAFETEIRA):
            return await ctx.send(embed=discord.Embed(
                title="☕ Cafeteira no máximo!",
                description="Sua cafeteira já está tinindo no nível máximo.",
                color=COR_CAFE))

        prox = UPGRADES_CAFETEIRA[nivel + 1]
        custo = prox["custo"]
        if u["lumicoins"] < custo:
            return await ctx.send(embed=discord.Embed(
                title="💸 Lumicoins insuficientes!",
                description=(
                    f"Upgrade: **nível {prox['nivel']} — {prox['nome']}**\n"
                    f"Custo: **{custo} 🪙**\n"
                    f"Seu saldo: **{u['lumicoins']} 🪙**\n"
                    f"Faltam: **{custo - u['lumicoins']} 🪙**"
                ),
                color=COR_ERRO))

        u["lumicoins"] -= custo
        u.setdefault("upgrades", {})["cafeteira"] = prox["nivel"]
        save_user(ctx.guild.id, ctx.author.id, u)

        emb = discord.Embed(
            title=f"✨ Cafeteira melhorada para nível {prox['nivel']}!",
            description=(
                f"Agora você tem a **{prox['nome']}**.\n"
                f"Gastou **{custo} 🪙** — saldo: **{u['lumicoins']} 🪙**"
            ),
            color=COR_OK,
        )
        emb.add_field(name="Novos bônus", value="\n".join(self._bonus_cafeteira_linhas(prox)), inline=False)
        emb.set_footer(text="Lumine Café ☕ • Upgrade instalado")
        await ctx.send(embed=emb)

    # ── l!comprar ────────────────────────────────────────────────────────────

    @commands.command(
        name="comprar",
        aliases=["buy"],
        help=(
            "Compre ingredientes. Aceita um ou vários de uma vez!\n"
            "Ex: l!comprar leite 3  •  l!comprar grao 2 leite 3 acucar 5"
        ),
    )
    async def comprar(self, ctx, *args: str):
        if not args:
            return await ctx.send(
                "❌ Use: `l!comprar <ingrediente> [qtd] [ingrediente] [qtd] ...`\n"
                "Ex.: `l!comprar grao 2 leite 3 acucar 5`"
            )

        # Parser tolerante: aceita "grao 2 leite 3", "grao leite 2", "$grao 2 $leite 3"
        pedidos: dict[str, int] = {}
        i = 0
        tokens = list(args)
        while i < len(tokens):
            nome = tokens[i].lstrip("$").lower().strip().strip(",")
            if not nome:
                i += 1
                continue
            if nome not in INGREDIENTES:
                return await ctx.send(
                    f"❌ Ingrediente `{nome}` não existe! Use `l!loja` para ver as opções."
                )
            qtd = 1
            if i + 1 < len(tokens) and tokens[i + 1].lstrip("$").strip(",").isdigit():
                qtd = int(tokens[i + 1].lstrip("$").strip(","))
                i += 2
            else:
                i += 1
            if qtd < 1:
                return await ctx.send(f"❌ Quantidade de `{nome}` precisa ser pelo menos 1.")
            pedidos[nome] = pedidos.get(nome, 0) + qtd

        if not pedidos:
            return await ctx.send("❌ Não consegui entender o pedido! Ex.: `l!comprar grao 2 leite 3`")

        # Limita por ingrediente (depois de somar repetições)
        for k, v in pedidos.items():
            if v > 99:
                return await ctx.send(
                    f"❌ Máx. **99** por ingrediente — você pediu **{v}× {INGREDIENTES[k]['nome']}**."
                )

        # Calcula custo total
        custo_total = sum(INGREDIENTES[k]["preco"] * v for k, v in pedidos.items())

        u = get_user(ctx.guild.id, ctx.author.id)
        if u["lumicoins"] < custo_total:
            return await ctx.send(embed=discord.Embed(
                title="💸 Saldo insuficiente!",
                description=(
                    f"Compra total: **{custo_total} 🪙**\n"
                    f"Seu saldo:    **{u['lumicoins']} 🪙**\n"
                    f"Faltam:       **{custo_total - u['lumicoins']} 🪙**\n\n"
                    f"Use `l!trabalhar` pra ganhar mais!"
                ),
                color=COR_ERRO))

        # Aplica a compra
        u["lumicoins"] -= custo_total
        linhas = []
        for k, v in pedidos.items():
            ing = INGREDIENTES[k]
            subtotal = ing["preco"] * v
            u["ingredientes"][k] = u["ingredientes"].get(k, 0) + v
            linhas.append(f"**{v}× {ing['emoji']} {ing['nome']}** — {subtotal} 🪙")
        save_user(ctx.guild.id, ctx.author.id, u)

        emb = discord.Embed(
            title="🛍️ Compra realizada!",
            description="\n".join(linhas) + (
                f"\n\n💰 **Total:** {custo_total} 🪙\n"
                f"💳 Saldo restante: **{u['lumicoins']} 🪙**"
            ),
            color=COR_OK,
        ).set_footer(text="Lumine Café ☕")
        await ctx.send(embed=emb)

    @comprar.error
    async def comprar_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ Use: `l!comprar <ingrediente> [qtd] [ingrediente] [qtd] ...`\n"
                "Ex.: `l!comprar grao 2 leite 3 acucar 5`"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Não entendi o pedido! Ex.: `l!comprar grao 2 leite 3`")

    # ── l!cardapio ───────────────────────────────────────────────────────────

    @commands.command(name="cardapio", aliases=["menu"], help="Veja todas as bebidas disponíveis.")
    async def cardapio(self, ctx):
        u = get_user(ctx.guild.id, ctx.author.id)
        emb = discord.Embed(title="📋 Cardápio da Lumine Café",
                            description="Use `l!preparar <bebida>` para fazer uma!\n​",
                            color=COR_CAFE)
        for key, beb in BEBIDAS.items():
            receita = "  ".join(
                f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in beb["receita"].items())
            emb.add_field(
                name=f"{beb['emoji']} {beb['nome']} — {beb['preco_venda']} 🪙 | +{beb['xp']} ⭐",
                value=f"`l!preparar {key}`  •  {receita}", inline=False)

        # Receitas secretas desbloqueadas pelo barista
        desbloqueadas = [k for k in u.get("receitas_desbloqueadas", []) if k in RECEITAS_SECRETAS]
        if desbloqueadas:
            emb.add_field(name="​",
                          value="✨ **Receitas Secretas (suas descobertas!)** ✨",
                          inline=False)
            for key in desbloqueadas:
                beb = RECEITAS_SECRETAS[key]
                receita = "  ".join(
                    f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in beb["receita"].items())
                emb.add_field(
                    name=f"{beb['emoji']} {beb['nome']} — {beb['preco_venda']} 🪙 | +{beb['xp']} ⭐",
                    value=f"`l!preparar {key}`  •  {receita}", inline=False)

        # Dica de progresso pra incentivar a inventar
        total_secretas = len(RECEITAS_SECRETAS)
        descobertas = len(desbloqueadas)
        if descobertas < total_secretas:
            emb.add_field(
                name="🤫 Receitas Secretas",
                value=(
                    f"Você descobriu **{descobertas}/{total_secretas}** receitas secretas!\n"
                    f"Use `l!inventar <ing1> <ing2> ...` pra experimentar combinações~ ✨"
                ),
                inline=False)
        emb.set_footer(text="Lumine Café ☕ • Feito com amor!")
        await ctx.send(embed=emb)

    # ── l!preparar ───────────────────────────────────────────────────────────

    @commands.command(name="preparar", aliases=["fazer", "brew"], help="Prepare uma bebida. Ex: l!preparar cappuccino")
    async def preparar(self, ctx, *, bebida: str):
        bebida = bebida.lower().strip().replace(" ", "_")
        u = get_user(ctx.guild.id, ctx.author.id)
        # Receitas secretas desbloqueadas também podem ser preparadas normalmente
        catalogo = dict(BEBIDAS)
        for k in u.get("receitas_desbloqueadas", []):
            if k in RECEITAS_SECRETAS:
                catalogo[k] = RECEITAS_SECRETAS[k]
        if bebida not in catalogo:
            lista = ", ".join(f"`{k}`" for k in catalogo)
            return await ctx.send(f"❌ Bebida não encontrada! Opções: {lista}\nVeja o `l!cardapio`!")
        beb = catalogo[bebida]
        faltando = [
            f"{INGREDIENTES[k]['emoji']} {INGREDIENTES[k]['nome']}: tem {u['ingredientes'].get(k,0)}, precisa {v}"
            for k, v in beb["receita"].items() if u["ingredientes"].get(k, 0) < v
        ]
        if faltando:
            return await ctx.send(embed=discord.Embed(
                title=f"😢 Faltam ingredientes para {beb['emoji']} {beb['nome']}!",
                description="\n".join(faltando) + "\n\nUse `l!comprar` para abastecer!",
                color=COR_ERRO))

        cafeteira = get_cafeteira_info(u)
        ingrediente_poupado = None
        if cafeteira["chance_economizar"] and random.randint(1, 100) <= cafeteira["chance_economizar"]:
            ingrediente_poupado = random.choice(list(beb["receita"].keys()))

        for k, v in beb["receita"].items():
            consumido = v - (1 if k == ingrediente_poupado else 0)
            if consumido <= 0:
                continue
            u["ingredientes"][k] -= consumido
            if u["ingredientes"][k] == 0:
                del u["ingredientes"][k]
        u["estoque"][bebida] = u["estoque"].get(bebida, 0) + 1
        xp_ganho = aplicar_bonus_percentual(beb["xp"], cafeteira["bonus_xp"])
        u["xp"] += xp_ganho
        save_user(ctx.guild.id, ctx.author.id, u)
        nivel = get_nivel(u["xp"])
        receita_str = "  ".join(f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in beb["receita"].items())
        bonus_str = ""
        if xp_ganho > beb["xp"]:
            bonus_str += f"\n**Bônus da cafeteira:** +{xp_ganho - beb['xp']} XP ✨"
        if ingrediente_poupado:
            ing = INGREDIENTES[ingrediente_poupado]
            bonus_str += f"\n**Economia da cafeteira:** poupou 1× {ing['emoji']} {ing['nome']} 🎒"
        await ctx.send(embed=discord.Embed(
            title=f"☕ {beb['emoji']} {beb['nome']} preparado!",
            description=f"*Que cheirinho gostoso...* ✨\n\n"
                        f"**Receita:** {receita_str}\n"
                        f"**XP ganho:** +{xp_ganho} ⭐  |  XP total: {u['xp']} ⭐"
                        f"{bonus_str}\n\n"
                        f"Bebida no estoque! Use `l!vender {bebida}` para vender. 🏪",
            color=COR_OK).set_footer(text=f"{nivel['emoji']} {nivel['titulo']}"))

    @preparar.error
    async def preparar_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Use: `l!preparar <bebida>`  •  Veja o `l!cardapio`!")

    # ── l!inventar ───────────────────────────────────────────────────────────

    @commands.command(
        name="inventar",
        aliases=["experimentar", "misturar"],
        help="Misture ingredientes pra tentar descobrir uma receita secreta! Ex: l!inventar grao canela pimenta",
    )
    async def inventar(self, ctx, *ingredientes: str):
        if not ingredientes:
            return await ctx.send(embed=discord.Embed(
                title="🧪 Como inventar?",
                description=(
                    "Misture **2 ou mais ingredientes** e veja o que sai!\n"
                    "Ex: `l!inventar grao canela pimenta`\n\n"
                    "*Acertando uma receita secreta, eu anoto no caderninho e libero pra você no cardápio~* ✨"
                ),
                color=COR_CAFE).set_footer(text="Lumine Café ☕ • Cuidado com as gororobas!"))

        if len(ingredientes) < 2:
            return await ctx.send(embed=discord.Embed(
                description="🧪 Use **pelo menos 2 ingredientes** pra inventar algo, tá? ♡",
                color=COR_ERRO))

        # Normaliza e valida
        chaves = [i.lower().strip() for i in ingredientes]
        invalidos = [k for k in chaves if k not in INGREDIENTES]
        if invalidos:
            lista_inv = ", ".join(f"`{k}`" for k in invalidos)
            return await ctx.send(embed=discord.Embed(
                title="❓ Ingrediente desconhecido",
                description=f"Não conheço esses aqui: {lista_inv}\nDá uma olhadinha na `l!loja` pra ver o que existe! 💙",
                color=COR_ERRO))

        # Conta a tentativa
        tentativa: dict[str, int] = {}
        for k in chaves:
            tentativa[k] = tentativa.get(k, 0) + 1

        # Verifica estoque do barista
        u = get_user(ctx.guild.id, ctx.author.id)
        faltando = [
            f"{INGREDIENTES[k]['emoji']} {INGREDIENTES[k]['nome']}: tem {u['ingredientes'].get(k,0)}, precisa {v}"
            for k, v in tentativa.items() if u["ingredientes"].get(k, 0) < v
        ]
        if faltando:
            return await ctx.send(embed=discord.Embed(
                title="😢 Você não tem ingredientes suficientes!",
                description="\n".join(faltando) + "\n\nUse `l!comprar` pra abastecer antes de experimentar! 💙",
                color=COR_ERRO))

        # Consome ingredientes (tanto no acerto quanto no erro)
        for k, v in tentativa.items():
            u["ingredientes"][k] -= v
            if u["ingredientes"][k] == 0:
                del u["ingredientes"][k]

        # Procura receita secreta correspondente (match exato de receita)
        chave_acerto = None
        for sk, sb in RECEITAS_SECRETAS.items():
            if sb["receita"] == tentativa:
                chave_acerto = sk
                break

        ing_str = "  ".join(f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in tentativa.items())

        if chave_acerto is None:
            # GORORÔBA — fala aleatória de erro
            save_user(ctx.guild.id, ctx.author.id, u)
            fala = random.choice(FRASES_INVENTAR_ERRO)
            emb = discord.Embed(
                title="🥴 Que gororoba foi essa?!",
                description=(
                    f"*\"{fala}\"*\n\n"
                    f"**Você usou:** {ing_str}\n"
                    f"Os ingredientes foram pro lixo... mas faz parte de aprender! Tente outra combinação~ 💙"
                ),
                color=COR_ERRO)
            emb.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            emb.set_footer(text="Lumine Café ☕ • Não desista, barista!")
            return await ctx.send(embed=emb)

        # ACERTOU! — fala aleatória de sucesso
        beb = RECEITAS_SECRETAS[chave_acerto]
        ja_desbloqueada = chave_acerto in u.get("receitas_desbloqueadas", [])
        if not ja_desbloqueada:
            u.setdefault("receitas_desbloqueadas", []).append(chave_acerto)
        # Adiciona ao estoque pra poder vender
        u["estoque"][chave_acerto] = u["estoque"].get(chave_acerto, 0) + 1
        # Recompensas: XP em dobro na primeira vez (descoberta!), normal nas próximas
        xp_ganho = beb["xp"] * (2 if not ja_desbloqueada else 1)
        bonus_moedas = 100 if not ja_desbloqueada else 0
        u["xp"] += xp_ganho
        u["lumicoins"] += bonus_moedas
        save_user(ctx.guild.id, ctx.author.id, u)

        nivel = get_nivel(u["xp"])
        fala = random.choice(FRASES_INVENTAR_ACERTO)
        if not ja_desbloqueada:
            titulo = f"✨ DESCOBERTA! {beb['emoji']} {beb['nome']}!"
            extras = (
                f"🎉 **Receita secreta desbloqueada!** Agora aparece no seu `l!cardapio`!\n"
                f"⭐ **+{xp_ganho} XP** (dobrado pela descoberta!)  •  🪙 **+{bonus_moedas} Lumicoins** de bônus!\n"
            )
        else:
            titulo = f"☕ {beb['emoji']} {beb['nome']} pronto de novo!"
            extras = f"⭐ **+{xp_ganho} XP**  •  Já tava no caderninho, mas saiu liiindo! 💙\n"

        emb = discord.Embed(
            title=titulo,
            description=(
                f"*\"{fala}\"*\n\n"
                f"**Combinação:** {ing_str}\n"
                f"{extras}"
                f"A bebida foi pro seu estoque — use `l!vender {chave_acerto}` ou sirva nos clientes! 🧺"
            ),
            color=COR_OK)
        emb.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        emb.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • Lumine Café ☕")
        await ctx.send(embed=emb)

    @inventar.error
    async def inventar_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Use: `l!inventar <ingrediente1> <ingrediente2> ...`")

    # ── l!estoque ────────────────────────────────────────────────────────────

    @commands.command(name="estoque", aliases=["stock"], help="Veja suas bebidas prontas.")
    async def estoque(self, ctx):
        u = get_user(ctx.guild.id, ctx.author.id)
        if not u["estoque"]:
            return await ctx.send(embed=discord.Embed(
                description="🧺 Estoque vazio! Use `l!preparar <bebida>` para fazer algo. ☕",
                color=COR_ERRO))
        linhas, total = [], 0
        for key, qtd in u["estoque"].items():
            beb = BEBIDAS.get(key) or RECEITAS_SECRETAS.get(key)
            if beb is None:
                continue
            valor = beb["preco_venda"] * qtd
            total += valor
            marca = "✨ " if key in RECEITAS_SECRETAS else ""
            linhas.append(f"{marca}{beb['emoji']} **{beb['nome']}** ×{qtd} — {valor} 🪙")
        await ctx.send(embed=discord.Embed(
            title="🧺 Seu estoque de bebidas",
            description="\n".join(linhas) + f"\n\n💰 Valor total: **{total} 🪙**",
            color=COR_CAFE).set_footer(text="Use l!vender <bebida> para vender!"))

    # ── l!vender ─────────────────────────────────────────────────────────────

    @commands.command(name="vender", aliases=["sell"], help="Venda uma bebida do estoque. Ex: l!vender cappuccino")
    async def vender(self, ctx, *, bebida: str):
        bebida = bebida.lower().strip().replace(" ", "_")
        beb = BEBIDAS.get(bebida) or RECEITAS_SECRETAS.get(bebida)
        if beb is None:
            return await ctx.send(f"❌ Bebida `{bebida}` não existe! Use `l!estoque` para ver o que você tem.")
        u = get_user(ctx.guild.id, ctx.author.id)
        if not u["estoque"].get(bebida, 0):
            return await ctx.send(f"😢 Sem **{beb['nome']}** no estoque! Use `l!preparar {bebida}`.")
        u["estoque"][bebida] -= 1
        if u["estoque"][bebida] == 0:
            del u["estoque"][bebida]
        cafeteira = get_cafeteira_info(u)
        valor_venda = aplicar_bonus_percentual(beb["preco_venda"], cafeteira["bonus_venda"])
        u["lumicoins"] += valor_venda
        save_user(ctx.guild.id, ctx.author.id, u)
        bonus_str = ""
        if valor_venda > beb["preco_venda"]:
            bonus_str = f"\nBônus da cafeteira: **+{valor_venda - beb['preco_venda']} 🪙** ✨"
        await ctx.send(embed=discord.Embed(
            title="💰 Venda realizada!",
            description=f"Vendeu **{beb['emoji']} {beb['nome']}** por **{valor_venda} 🪙**!{bonus_str}\n"
                        f"Saldo: **{u['lumicoins']} 🪙**",
            color=COR_OK).set_footer(text="Lumine Café ☕ • Ótimo negócio!"))

    @vender.error
    async def vender_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Use: `l!vender <bebida>`")

    # ── l!cafe (perfil) ──────────────────────────────────────────────────────

    @commands.command(name="cafe", aliases=["barista"], help="Veja seu perfil de barista.")
    async def cafe_perfil(self, ctx):
        u = get_user(ctx.guild.id, ctx.author.id)
        nivel = get_nivel(u["xp"])
        idx = next((i for i, n in enumerate(NIVEIS) if n["nivel"] == nivel["nivel"]), None)
        if idx is not None and idx + 1 < len(NIVEIS):
            prox = NIVEIS[idx + 1]
            xp_str = f"{u['xp']} ⭐  (faltam **{prox['xp_min'] - u['xp']}** para {prox['titulo']})"
        else:
            xp_str = f"{u['xp']} ⭐ — **Nível máximo!** 👑"
        inv_str = ("  ".join(f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in u["ingredientes"].items())
                   or "*vazio — compre em `l!loja`!*")
        def _emoji_bebida(k):
            beb = BEBIDAS.get(k) or RECEITAS_SECRETAS.get(k)
            return beb["emoji"] if beb else "❔"
        est_str = ("  ".join(f"{_emoji_bebida(k)}×{v}" for k, v in u["estoque"].items())
                   or "*vazio — prepare em `l!preparar`!*")
        cd_t = cooldown_restante(u["cd_trabalhar"], CD_TRABALHAR)
        cd_a = cooldown_restante(u["cd_atender"], CD_ATENDER)
        cafeteira = get_cafeteira_info(u)
        emb = discord.Embed(title=f"{nivel['emoji']} {ctx.author.display_name} — Barista", color=COR_PERFIL)
        emb.set_thumbnail(url=ctx.author.display_avatar.url)
        emb.add_field(name="🏅 Título",       value=f"{nivel['emoji']} **{nivel['titulo']}**", inline=True)
        emb.add_field(name="🪙 Lumicoins",    value=f"**{u['lumicoins']}**", inline=True)
        emb.add_field(name="☕ Cafeteira",     value=f"Nível **{cafeteira['nivel']}** — {cafeteira['nome']}", inline=True)
        emb.add_field(name="⭐ XP",           value=xp_str, inline=False)
        emb.add_field(name="🎒 Ingredientes", value=inv_str, inline=False)
        emb.add_field(name="🧺 Bebidas",      value=est_str, inline=False)
        emb.add_field(name="💼 l!trabalhar",  value=("🟢 disponível!" if not cd_t else f"🔴 {formatar_tempo(cd_t)}"), inline=True)
        emb.add_field(name="👥 l!atender",    value=("🟢 disponível!" if not cd_a else f"🔴 {formatar_tempo(cd_a)}"), inline=True)
        emb.set_footer(text="Lumine Café ☕")
        await ctx.send(embed=emb)

    # ── l!ranking ────────────────────────────────────────────────────────────

    @commands.command(name="ranking", aliases=["rank", "top"], help="Ranking da cafeteria: l!ranking cafe")
    async def ranking(self, ctx, *, modo: str = "cafe"):
        if modo.strip().lower() not in ("cafe", "café"):
            return await ctx.send("ℹ️ Use `l!ranking cafe` para o ranking da cafeteria!")
        todos = get_all_users(ctx.guild.id)
        if not todos:
            return await ctx.send("😢 Nenhum barista ainda! Use `l!trabalhar` para começar.")
        ordenados = sorted(todos.items(), key=lambda x: x[1].get("lumicoins", 0), reverse=True)[:10]
        medalhas = ["🥇", "🥈", "🥉"]
        linhas = []
        for i, (uid, data) in enumerate(ordenados):
            pos = medalhas[i] if i < 3 else f"**{i+1}.**"
            try:
                membro = ctx.guild.get_member(int(uid)) or await ctx.guild.fetch_member(int(uid))
                nome = membro.display_name
            except Exception:
                nome = f"Usuário #{uid[:5]}"
            nivel = get_nivel(data.get("xp", 0))
            linhas.append(f"{pos} **{nome}** — {data.get('lumicoins',0)} 🪙  {nivel['emoji']} {nivel['titulo']}")
        await ctx.send(embed=discord.Embed(
            title="🏆 Ranking da Cafeteria",
            description="\n".join(linhas),
            color=COR_RANK).set_footer(text="Lumine Café ☕ • Top 10 baristas"))

    # ── l!atender ────────────────────────────────────────────────────────────

    @commands.command(name="atender", aliases=["cliente", "servir"], help="Atenda um cliente! (cooldown 1h)")
    async def atender(self, ctx, *, bebida_oferecida: str = None):
        u = get_user(ctx.guild.id, ctx.author.id)
        cd = cooldown_restante(u["cd_atender"], CD_ATENDER)

        # Sem argumento e sem cliente pendente → gera novo cliente
        pendente = u.get("cliente_pendente")
        if bebida_oferecida is None and not pendente:
            if cd:
                return await ctx.send(embed=discord.Embed(
                    description=f"👥 Nenhum cliente novo agora! Próximo em **{formatar_tempo(cd)}**. 🕐",
                    color=COR_ERRO))
            cliente = random.choice(CLIENTES)
            bebida_key = random.choice(list(BEBIDAS.keys()))
            beb = BEBIDAS[bebida_key]
            intro = random.choice(cliente["pedido_intro"]).format(bebida=beb["nome"])
            u["cliente_pendente"] = {"cliente": cliente["nome"], "bebida": bebida_key}
            u["cd_atender"] = time.time()
            save_user(ctx.guild.id, ctx.author.id, u)
            emb = discord.Embed(
                title=f"{cliente['emoji']} {cliente['nome']} chegou!",
                description=f"*\"{intro}\"*\n\n"
                            f"Sirva com `l!atender {bebida_key}` "
                            f"(**{beb['emoji']} {beb['nome']}**)!",
                color=COR_CAFE)
            emb.set_footer(text=f"Personalidade: {cliente['personalidade'].capitalize()} • Lumine Café ☕")
            # Imagem de anime conforme a personalidade do cliente (momento: pedido)
            tag = cliente.get("image_tags", {}).get("pedido", "smile")
            img_url = await fetch_anime_image(tag)
            if img_url:
                emb.set_thumbnail(url=img_url)
            return await ctx.send(embed=emb)

        # Sem argumento mas já tem cliente pendente → lembra o jogador
        if bebida_oferecida is None and pendente:
            beb = BEBIDAS[pendente["bebida"]]
            return await ctx.send(
                f"👥 {pendente['cliente']} ainda está esperando por **{beb['emoji']} {beb['nome']}**!\n"
                f"Use `l!atender {pendente['bebida']}` para servir!")

        # Tentativa de servir
        bebida_oferecida = bebida_oferecida.lower().strip().replace(" ", "_")
        if not pendente:
            return await ctx.send("❓ Nenhum cliente esperando! Use `l!atender` para chamar um.")

        cliente = next((c for c in CLIENTES if c["nome"] == pendente["cliente"]), random.choice(CLIENTES))
        bebida_key = pendente["bebida"]
        beb = BEBIDAS[bebida_key]

        errou = (bebida_oferecida != bebida_key) or (not u["estoque"].get(bebida_oferecida, 0))
        if errou:
            motivo = (f"Você não tem **{beb['emoji']} {beb['nome']}** no estoque!"
                      if bebida_oferecida == bebida_key
                      else f"{cliente['emoji']} {cliente['nome']} queria **{beb['emoji']} {beb['nome']}**!")
            u.pop("cliente_pendente", None)
            save_user(ctx.guild.id, ctx.author.id, u)
            emb = discord.Embed(
                title=f"😢 {cliente['emoji']} {cliente['nome']} foi embora...",
                description=f"*\"{random.choice(cliente['recusa'])}\"*\n\n{motivo}",
                color=COR_ERRO)
            # Imagem reflete o momento triste
            tag = cliente.get("image_tags", {}).get("triste", "cry")
            img_url = await fetch_anime_image(tag)
            if img_url:
                emb.set_thumbnail(url=img_url)
            return await ctx.send(embed=emb)

        bonus_base   = random.randint(20, 60)
        cafeteira = get_cafeteira_info(u)
        bonus_moedas = aplicar_bonus_percentual(bonus_base, cafeteira["bonus_atendimento"])
        bonus_xp     = random.randint(5, 15)
        u["estoque"][bebida_oferecida] -= 1
        if u["estoque"][bebida_oferecida] == 0:
            del u["estoque"][bebida_oferecida]
        u["lumicoins"] += bonus_moedas
        u["xp"] += bonus_xp
        u.pop("cliente_pendente", None)
        save_user(ctx.guild.id, ctx.author.id, u)
        nivel = get_nivel(u["xp"])
        bonus_str = ""
        if bonus_moedas > bonus_base:
            bonus_str = f"\nBônus da cafeteira: **+{bonus_moedas - bonus_base} 🪙** ✨"
        emb = discord.Embed(
            title=f"✨ {cliente['emoji']} {cliente['nome']} foi atendido!",
            description=f"*\"{random.choice(cliente['agradecimento'])}\"*\n\n"
                        f"🪙 **+{bonus_moedas} Lumicoins** | ⭐ **+{bonus_xp} XP**\n"
                        f"Saldo: **{u['lumicoins']} 🪙** | XP: **{u['xp']} ⭐**"
                        f"{bonus_str}",
            color=COR_OK)
        pista = escolher_pista_receita(u, "cliente", 25, cliente=cliente)
        if pista:
            emb.add_field(name="🤫 Pista de cliente", value=pista, inline=False)
        emb.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • Lumine Café ☕")
        # Imagem grande como recompensa visual do atendimento bem-sucedido
        tag = cliente.get("image_tags", {}).get("feliz", "happy")
        img_url = await fetch_anime_image(tag)
        if img_url:
            emb.set_image(url=img_url)
        await ctx.send(embed=emb)


    def help_meta(self) -> dict:
        """Metadados pro l!help (cardápio + busca por categoria)."""
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
        """Retorna o campo de ajuda desta cog para o l!help."""
        name = "☕ __Comandos do Café__"
        value = (
            "`l!trabalhar` — Ganhe Lumicoins (cooldown 30min) 💼\n"
            "`l!loja` — Ingredientes à venda 🏪  |  `l!comprar <item> [qtd] ...` — Compre (vários!) 🛍️\n"
            "`l!cafeteira` — Veja upgrades ☕  |  `l!melhorar cafeteira` — Gaste Lumicoins em melhorias ✨\n"
            "`l!cardapio` — Veja receitas e preços 📋\n"
            "`l!preparar <bebida>` — Prepare uma bebida ☕\n"
            "`l!inventar <ing1> <ing2> ...` — Misture ingredientes pra descobrir receitas secretas! 🧪✨\n"
            "`l!estoque` — Bebidas prontas 🧺  |  `l!vender <bebida>` — Venda 💰\n"
            "`l!atender [bebida]` — Atenda um cliente especial! 👥\n"
            "`l!cafe` — Seu perfil de barista ⭐  |  `l!ranking cafe` — Top 10 🏆"
        )
        return name, value


async def setup(bot: commands.Bot):
    await bot.add_cog(Cafe(bot))
