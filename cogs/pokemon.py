"""
pokemon.py — Cog de curiosidades sobre Pokémon da Lumine.

Usa a PokéAPI (https://pokeapi.co/) — gratuita, sem autenticação.

Comandos:
    l!pokemon             → Pokémon aleatório
    l!pokemon <nome>      → Ex: l!pokemon pikachu
    l!pokemon <número>    → Ex: l!pokemon 25
"""

import random
import aiohttp
import discord
from discord.ext import commands


# ─────────────────────────────────────────────
#  Constantes
# ─────────────────────────────────────────────

# Total de Pokémon no Dex Nacional (Gens 1–9)
TOTAL_POKEMON = 1025

POKEAPI_BASE = "https://pokeapi.co/api/v2"

# Cores por tipo primário (RGB)
TYPE_COLORS: dict[str, tuple[int, int, int]] = {
    "fire":     (240, 128,  48),
    "water":    (104, 144, 240),
    "grass":    (120, 200,  80),
    "electric": (248, 208,  48),
    "psychic":  (248,  88, 136),
    "ice":      (152, 216, 216),
    "dragon":   (112,  56, 248),
    "dark":     (112,  88,  72),
    "fairy":    (238, 153, 172),
    "normal":   (168, 168, 120),
    "fighting": (192,  48,  40),
    "flying":   (168, 144, 240),
    "poison":   (160,  64, 160),
    "ground":   (224, 192, 104),
    "rock":     (184, 160,  56),
    "bug":      (168, 184,  32),
    "ghost":    (112,  88, 152),
    "steel":    (184, 184, 208),
}

TYPE_EMOJIS: dict[str, str] = {
    "fire":     "🔥",
    "water":    "💧",
    "grass":    "🌿",
    "electric": "⚡",
    "psychic":  "🔮",
    "ice":      "❄️",
    "dragon":   "🐉",
    "dark":     "🌑",
    "fairy":    "✨",
    "normal":   "⚪",
    "fighting": "🥊",
    "flying":   "🌬️",
    "poison":   "☠️",
    "ground":   "🏔️",
    "rock":     "🪨",
    "bug":      "🐛",
    "ghost":    "👻",
    "steel":    "⚙️",
}

# Geração → nome legível em PT
GEN_NOMES: dict[str, str] = {
    "generation-i":    "Geração I (Kanto)",
    "generation-ii":   "Geração II (Johto)",
    "generation-iii":  "Geração III (Hoenn)",
    "generation-iv":   "Geração IV (Sinnoh)",
    "generation-v":    "Geração V (Unova)",
    "generation-vi":   "Geração VI (Kalos)",
    "generation-vii":  "Geração VII (Alola)",
    "generation-viii": "Geração VIII (Galar)",
    "generation-ix":   "Geração IX (Paldea)",
}


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _limpar_texto(texto: str) -> str:
    """Remove quebras de linha e caracteres de controle dos textos da PokéAPI."""
    return texto.replace("\n", " ").replace("\f", " ").replace("\r", " ").strip()


def _barra_stat(valor: int, maximo: int = 255, tamanho: int = 10) -> str:
    """Gera uma barrinha de progresso simples com blocos Unicode."""
    cheios = round(valor / maximo * tamanho)
    return "█" * cheios + "░" * (tamanho - cheios)


# ─────────────────────────────────────────────
#  Cog
# ─────────────────────────────────────────────

class Pokemon(commands.Cog):
    """🎮 Curiosidades sobre Pokémon via PokéAPI"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._session: aiohttp.ClientSession | None = None

    async def cog_load(self) -> None:
        self._session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Fetch ────────────────────────────────────────────────────────────────

    async def _fetch(self, url: str) -> dict | None:
        """Faz um GET e retorna o JSON ou None em caso de erro."""
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None

    # ── Build Embed ──────────────────────────────────────────────────────────

    async def _build_embed(self, identifier: int | str) -> discord.Embed | None:
        """
        Busca os dados do Pokémon na PokéAPI e monta o embed.
        `identifier` pode ser um int (número) ou str (nome).
        Retorna None se o Pokémon não for encontrado.
        """
        base = await self._fetch(f"{POKEAPI_BASE}/pokemon/{identifier}")
        if not base:
            return None

        species = await self._fetch(f"{POKEAPI_BASE}/pokemon-species/{base['id']}")

        # ── Dados básicos ──
        nome    = base["name"].replace("-", " ").title()
        poke_id = base["id"]
        tipos   = [t["type"]["name"] for t in base["types"]]
        altura  = base["height"] / 10    # decímetros → metros
        peso    = base["weight"] / 10    # hectogramas → kg

        # ── Cor pelo tipo primário ──
        cor_rgb = TYPE_COLORS.get(tipos[0] if tipos else "normal", (100, 180, 255))
        cor     = discord.Color.from_rgb(*cor_rgb)

        # ── Texto da Pokédex ──
        flavor = ""
        if species:
            entradas = species.get("flavor_text_entries", [])
            # Prioriza pt-BR, cai para inglês
            pool_pt = [e["flavor_text"] for e in entradas if e["language"]["name"] == "pt-BR"]
            pool_en = [e["flavor_text"] for e in entradas if e["language"]["name"] == "en"]
            pool    = pool_pt or pool_en
            if pool:
                flavor = _limpar_texto(random.choice(pool))

        # ── Geração ──
        geracao = ""
        if species:
            gen_key = species.get("generation", {}).get("name", "")
            geracao = GEN_NOMES.get(gen_key, gen_key.replace("generation-", "Gen ").upper())

        # ── Badge (lendário / mítico) ──
        badge = ""
        if species:
            if species.get("is_legendary"):
                badge = " 🌟 Lendário"
            elif species.get("is_mythical"):
                badge = " ✨ Mítico"

        # ── Habilidades ──
        habs_normais = [
            a["ability"]["name"].replace("-", " ").title()
            for a in base["abilities"]
            if not a["is_hidden"]
        ]
        habs_ocultas = [
            a["ability"]["name"].replace("-", " ").title()
            for a in base["abilities"]
            if a["is_hidden"]
        ]

        # ── Stats ──
        stats = {s["stat"]["name"]: s["base_stat"] for s in base["stats"]}
        hp      = stats.get("hp", 0)
        ataque  = stats.get("attack", 0)
        defesa  = stats.get("defense", 0)
        sp_atk  = stats.get("special-attack", 0)
        sp_def  = stats.get("special-defense", 0)
        veloc   = stats.get("speed", 0)
        total   = sum(stats.values())

        # ── Sprite (artwork oficial, com fallback) ──
        sprite_url = (
            base["sprites"]
            .get("other", {})
            .get("official-artwork", {})
            .get("front_default")
            or base["sprites"].get("front_default")
        )

        # ── Monta o embed ──
        embed = discord.Embed(
            title=f"#{poke_id:04d}  {nome}{badge}",
            description=f'*"{flavor}"*' if flavor else "",
            color=cor,
        )

        if sprite_url:
            embed.set_thumbnail(url=sprite_url)

        # Tipos
        tipos_str = "  ".join(
            f"{TYPE_EMOJIS.get(t, '')} {t.capitalize()}" for t in tipos
        )
        embed.add_field(name="🏷️ Tipo",         value=tipos_str,      inline=True)
        embed.add_field(name="🌍 Geração",       value=geracao or "?", inline=True)
        embed.add_field(
            name="📏 Medidas",
            value=f"{peso} kg  •  {altura} m",
            inline=True,
        )

        # Habilidades
        if habs_normais:
            embed.add_field(
                name="💪 Habilidades",
                value=", ".join(habs_normais),
                inline=True,
            )
        if habs_ocultas:
            embed.add_field(
                name="🔒 Hab. Oculta",
                value=", ".join(habs_ocultas),
                inline=True,
            )

        # Stats com barrinha visual
        stats_lines = [
            f"`HP ` {_barra_stat(hp)}  **{hp}**",
            f"`ATK` {_barra_stat(ataque)}  **{ataque}**",
            f"`DEF` {_barra_stat(defesa)}  **{defesa}**",
            f"`SpA` {_barra_stat(sp_atk)}  **{sp_atk}**",
            f"`SpD` {_barra_stat(sp_def)}  **{sp_def}**",
            f"`SPD` {_barra_stat(veloc)}  **{veloc}**",
            f"**Total: {total}**",
        ]
        embed.add_field(
            name="📊 Stats base",
            value="\n".join(stats_lines),
            inline=False,
        )

        embed.set_footer(text="Dados via PokéAPI • l!pokemon [nome/número] para buscar outro~ 🎮")
        return embed

    # ── Comando ──────────────────────────────────────────────────────────────

    @commands.command(
        name="pokemon",
        aliases=["pokedex", "pokédex", "poke", "pokémon"],
        help="Curiosidade sobre um Pokémon! Ex: l!pokemon pikachu  ou  l!pokemon 25",
    )
    async def pokemon(self, ctx: commands.Context, *, nome: str = None):
        async with ctx.typing():
            if nome is None:
                # Sorteia um Pokémon aleatório
                identifier: int | str = random.randint(1, TOTAL_POKEMON)
            else:
                # Nome passado pelo usuário (slug ou número)
                identifier = nome.lower().strip().replace(" ", "-")

            embed = await self._build_embed(identifier)

            if embed is None:
                await ctx.send(
                    f"❌ Não encontrei o Pokémon `{nome}`!\n"
                    "💡 Tente o nome em inglês ou o número da Pokédex. "
                    "Exemplos: `l!pokemon pikachu`, `l!pokemon charizard`, `l!pokemon 25`"
                )
                return

            await ctx.send(embed=embed)

    @pokemon.error
    async def pokemon_error(self, ctx: commands.Context, error: Exception):
        await ctx.send(
            "❌ Algo deu errado ao buscar o Pokémon! Tente novamente em instantes~ 🥺"
        )

    # ── Help ─────────────────────────────────────────────────────────────────

    def help_meta(self) -> dict:
        return {
            "key":      "pokemon",
            "aliases":  ("pokémon", "pokedex", "pokédex", "poke"),
            "icon":     "🎮",
            "category": "Pokémon",
            "blurb":    "Descubra curiosidades sobre qualquer Pokémon~ 🎮",
            "intro": (
                "Que Pokémon você quer conhecer hoje? "
                "Posso te contar sobre qualquer um! 🎮✨"
            ),
        }

    def help_field(self) -> tuple[str, str]:
        name = "🎮 __Comandos de Pokémon__"
        value = (
            "`l!pokemon` — Curiosidade sobre um Pokémon **aleatório**! 🎲\n"
            "`l!pokemon <nome>` — Ex: `l!pokemon pikachu`, `l!pokemon charizard`\n"
            "`l!pokemon <número>` — Ex: `l!pokemon 25`, `l!pokemon 006`\n"
            "\n"
            "**Exibe:** tipo, geração, habilidades, texto da Pokédex, stats e mais~\n"
            "**Aliases:** `l!pokedex`, `l!poke`"
        )
        return name, value


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Pokemon(bot))
