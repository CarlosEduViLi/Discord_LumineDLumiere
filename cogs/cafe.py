"""cafe.py — Cog do ☕ Café da Lumine."""
import random, time
import discord
from discord.ext import commands
from cogs.cafe_core import (
    BEBIDAS, CLIENTES, INGREDIENTES, FRASES_TRABALHAR,
    CD_TRABALHAR, CD_ATENDER,
    get_user, save_user, get_all_users, get_nivel,
    cooldown_restante, formatar_tempo, NIVEIS,
)

COR_CAFE   = discord.Color.from_rgb(139, 90,  43)
COR_OK     = discord.Color.from_rgb(107, 191, 139)
COR_ERRO   = discord.Color.from_rgb(220, 100, 100)
COR_LOJA   = discord.Color.from_rgb(255, 183,  77)
COR_PERFIL = discord.Color.from_rgb(181, 126, 220)
COR_RANK   = discord.Color.from_rgb(255, 215, 100)


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
        emb.set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • próximo turno em 30min")
        await ctx.send(embed=emb)

    # ── l!loja ───────────────────────────────────────────────────────────────

    @commands.command(name="loja", aliases=["shop"], help="Ingredientes disponíveis para comprar.")
    async def loja(self, ctx):
        u = get_user(ctx.guild.id, ctx.author.id)
        emb = discord.Embed(
            title="🏪 Loja de Ingredientes",
            description=f"Saldo: **{u['lumicoins']} 🪙** — Use `l!comprar <ingrediente>`\n\u200b",
            color=COR_LOJA)
        for key, ing in INGREDIENTES.items():
            emb.add_field(name=f"{ing['emoji']} {ing['nome']}",
                          value=f"`l!comprar {key}` — **{ing['preco']} 🪙**", inline=True)
        emb.set_footer(text="Lumine Café ☕")
        await ctx.send(embed=emb)

    # ── l!comprar ────────────────────────────────────────────────────────────

    @commands.command(name="comprar", aliases=["buy"], help="Compre ingredientes. Ex: l!comprar leite 3")
    async def comprar(self, ctx, item: str, quantidade: int = 1):
        item = item.lower().strip()
        if item not in INGREDIENTES:
            return await ctx.send(f"❌ Ingrediente `{item}` não existe! Use `l!loja` para ver as opções.")
        if not 1 <= quantidade <= 99:
            return await ctx.send("❌ Quantidade deve ser entre 1 e 99.")
        ing = INGREDIENTES[item]
        custo = ing["preco"] * quantidade
        u = get_user(ctx.guild.id, ctx.author.id)
        if u["lumicoins"] < custo:
            return await ctx.send(embed=discord.Embed(
                description=f"💸 Faltam **{custo - u['lumicoins']} 🪙**! Use `l!trabalhar` para ganhar mais.",
                color=COR_ERRO))
        u["lumicoins"] -= custo
        u["ingredientes"][item] = u["ingredientes"].get(item, 0) + quantidade
        save_user(ctx.guild.id, ctx.author.id, u)
        await ctx.send(embed=discord.Embed(
            title="🛍️ Compra realizada!",
            description=f"**{quantidade}× {ing['emoji']} {ing['nome']}** por **{custo} 🪙**!\n"
                        f"Saldo restante: **{u['lumicoins']} 🪙**",
            color=COR_OK).set_footer(text="Lumine Café ☕"))

    @comprar.error
    async def comprar_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Use: `l!comprar <ingrediente> [quantidade]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ A quantidade precisa ser um número inteiro!")

    # ── l!cardapio ───────────────────────────────────────────────────────────

    @commands.command(name="cardapio", aliases=["menu"], help="Veja todas as bebidas disponíveis.")
    async def cardapio(self, ctx):
        emb = discord.Embed(title="📋 Cardápio da Lumine Café",
                            description="Use `l!preparar <bebida>` para fazer uma!\n\u200b",
                            color=COR_CAFE)
        for key, beb in BEBIDAS.items():
            receita = "  ".join(
                f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in beb["receita"].items())
            emb.add_field(
                name=f"{beb['emoji']} {beb['nome']} — {beb['preco_venda']} 🪙 | +{beb['xp']} ⭐",
                value=f"`l!preparar {key}`  •  {receita}", inline=False)
        emb.set_footer(text="Lumine Café ☕ • Feito com amor!")
        await ctx.send(embed=emb)

    # ── l!preparar ───────────────────────────────────────────────────────────

    @commands.command(name="preparar", aliases=["fazer", "brew"], help="Prepare uma bebida. Ex: l!preparar cappuccino")
    async def preparar(self, ctx, *, bebida: str):
        bebida = bebida.lower().strip().replace(" ", "_")
        if bebida not in BEBIDAS:
            lista = ", ".join(f"`{k}`" for k in BEBIDAS)
            return await ctx.send(f"❌ Bebida não encontrada! Opções: {lista}\nVeja o `l!cardapio`!")
        beb = BEBIDAS[bebida]
        u = get_user(ctx.guild.id, ctx.author.id)
        faltando = [
            f"{INGREDIENTES[k]['emoji']} {INGREDIENTES[k]['nome']}: tem {u['ingredientes'].get(k,0)}, precisa {v}"
            for k, v in beb["receita"].items() if u["ingredientes"].get(k, 0) < v
        ]
        if faltando:
            return await ctx.send(embed=discord.Embed(
                title=f"😢 Faltam ingredientes para {beb['emoji']} {beb['nome']}!",
                description="\n".join(faltando) + "\n\nUse `l!comprar` para abastecer!",
                color=COR_ERRO))
        for k, v in beb["receita"].items():
            u["ingredientes"][k] -= v
            if u["ingredientes"][k] == 0:
                del u["ingredientes"][k]
        u["estoque"][bebida] = u["estoque"].get(bebida, 0) + 1
        u["xp"] += beb["xp"]
        save_user(ctx.guild.id, ctx.author.id, u)
        nivel = get_nivel(u["xp"])
        receita_str = "  ".join(f"{INGREDIENTES[k]['emoji']}×{v}" for k, v in beb["receita"].items())
        await ctx.send(embed=discord.Embed(
            title=f"☕ {beb['emoji']} {beb['nome']} preparado!",
            description=f"*Que cheirinho gostoso...* ✨\n\n"
                        f"**Receita:** {receita_str}\n"
                        f"**XP ganho:** +{beb['xp']} ⭐  |  XP total: {u['xp']} ⭐\n\n"
                        f"Bebida no estoque! Use `l!vender {bebida}` para vender. 🏪",
            color=COR_OK).set_footer(text=f"{nivel['emoji']} {nivel['titulo']}"))

    @preparar.error
    async def preparar_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Use: `l!preparar <bebida>`  •  Veja o `l!cardapio`!")

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
            beb = BEBIDAS[key]
            valor = beb["preco_venda"] * qtd
            total += valor
            linhas.append(f"{beb['emoji']} **{beb['nome']}** ×{qtd} — {valor} 🪙")
        await ctx.send(embed=discord.Embed(
            title="🧺 Seu estoque de bebidas",
            description="\n".join(linhas) + f"\n\n💰 Valor total: **{total} 🪙**",
            color=COR_CAFE).set_footer(text="Use l!vender <bebida> para vender!"))

    # ── l!vender ─────────────────────────────────────────────────────────────

    @commands.command(name="vender", aliases=["sell"], help="Venda uma bebida do estoque. Ex: l!vender cappuccino")
    async def vender(self, ctx, *, bebida: str):
        bebida = bebida.lower().strip().replace(" ", "_")
        if bebida not in BEBIDAS:
            return await ctx.send(f"❌ Bebida `{bebida}` não existe! Use `l!estoque` para ver o que você tem.")
        u = get_user(ctx.guild.id, ctx.author.id)
        if not u["estoque"].get(bebida, 0):
            beb_nome = BEBIDAS[bebida]["nome"]
            return await ctx.send(f"😢 Sem **{beb_nome}** no estoque! Use `l!preparar {bebida}`.")
        beb = BEBIDAS[bebida]
        u["estoque"][bebida] -= 1
        if u["estoque"][bebida] == 0:
            del u["estoque"][bebida]
        u["lumicoins"] += beb["preco_venda"]
        save_user(ctx.guild.id, ctx.author.id, u)
        await ctx.send(embed=discord.Embed(
            title="💰 Venda realizada!",
            description=f"Vendeu **{beb['emoji']} {beb['nome']}** por **{beb['preco_venda']} 🪙**!\n"
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
        est_str = ("  ".join(f"{BEBIDAS[k]['emoji']}×{v}" for k, v in u["estoque"].items())
                   or "*vazio — prepare em `l!preparar`!*")
        cd_t = cooldown_restante(u["cd_trabalhar"], CD_TRABALHAR)
        cd_a = cooldown_restante(u["cd_atender"], CD_ATENDER)
        emb = discord.Embed(title=f"{nivel['emoji']} {ctx.author.display_name} — Barista", color=COR_PERFIL)
        emb.set_thumbnail(url=ctx.author.display_avatar.url)
        emb.add_field(name="🏅 Título",       value=f"{nivel['emoji']} **{nivel['titulo']}**", inline=True)
        emb.add_field(name="🪙 Lumicoins",    value=f"**{u['lumicoins']}**", inline=True)
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
            return await ctx.send(embed=discord.Embed(
                title=f"😢 {cliente['emoji']} {cliente['nome']} foi embora...",
                description=f"*\"{random.choice(cliente['recusa'])}\"*\n\n{motivo}",
                color=COR_ERRO))

        bonus_moedas = random.randint(20, 60)
        bonus_xp     = random.randint(5, 15)
        u["estoque"][bebida_oferecida] -= 1
        if u["estoque"][bebida_oferecida] == 0:
            del u["estoque"][bebida_oferecida]
        u["lumicoins"] += bonus_moedas
        u["xp"] += bonus_xp
        u.pop("cliente_pendente", None)
        save_user(ctx.guild.id, ctx.author.id, u)
        nivel = get_nivel(u["xp"])
        await ctx.send(embed=discord.Embed(
            title=f"✨ {cliente['emoji']} {cliente['nome']} foi atendido!",
            description=f"*\"{random.choice(cliente['agradecimento'])}\"*\n\n"
                        f"🪙 **+{bonus_moedas} Lumicoins** | ⭐ **+{bonus_xp} XP**\n"
                        f"Saldo: **{u['lumicoins']} 🪙** | XP: **{u['xp']} ⭐**",
            color=COR_OK).set_footer(text=f"{nivel['emoji']} {nivel['titulo']} • Lumine Café ☕"))


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
            "`l!loja` — Ingredientes à venda 🏪  |  `l!comprar <item> [qtd]` — Compre 🛍️\n"
            "`l!cardapio` — Veja receitas e preços 📋\n"
            "`l!preparar <bebida>` — Prepare uma bebida ☕\n"
            "`l!estoque` — Bebidas prontas 🧺  |  `l!vender <bebida>` — Venda 💰\n"
            "`l!atender [bebida]` — Atenda um cliente especial! 👥\n"
            "`l!cafe` — Seu perfil de barista ⭐  |  `l!ranking cafe` — Top 10 🏆"
        )
        return name, value


async def setup(bot: commands.Bot):
    await bot.add_cog(Cafe(bot))
