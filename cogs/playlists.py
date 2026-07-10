import re

import discord
import wavelink
from discord.ext import commands

from utils.paths import PLAYLISTS_DATA_PATH
from utils.storage import JsonStore

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_MAX_SONGS = 200
_MAX_PLAYLISTS = 5
_PER_PAGE = 10
_NAME_RE = re.compile(r"^[\w\-]{1,20}$")
_SIM = {"sim", "s", "yes", "y", "confirmar", "confirma", "ok"}


# ----------------------------------------------------------------
# View de paginação para músicas da playlist
# ----------------------------------------------------------------

class PlaylistView(discord.ui.View):
    def __init__(
        self,
        cog: "Playlists",
        owner: discord.User,
        pl_name: str,
        tracks: list,
        author: discord.Member,
        page: int,
    ):
        super().__init__(timeout=60)
        self.cog = cog
        self.owner = owner
        self.pl_name = pl_name
        self.tracks = tracks
        self.author = author
        self.current_page = page
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Só quem pediu a playlist pode navegar nela~ 🥺", ephemeral=True
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

    def _total_pages(self) -> int:
        return max(1, (len(self.tracks) + _PER_PAGE - 1) // _PER_PAGE)

    async def _turn(self, interaction: discord.Interaction, delta: int):
        total = self._total_pages()
        self.current_page = (self.current_page - 1 + delta) % total + 1
        await interaction.response.edit_message(
            embed=self.cog._build_playlist_embed(
                self.owner, self.pl_name, self.tracks, self.current_page, total
            )
        )

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, -1)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, +1)


# ----------------------------------------------------------------
# Cog principal
# ----------------------------------------------------------------

class Playlists(commands.Cog):
    """🎶 Playlists pessoais da Lumine"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = JsonStore(PLAYLISTS_DATA_PATH)

    # ── JSON helpers ───────────────────────────────────────────────

    async def _load(self) -> dict:
        return await self.store.read()

    async def _save(self, data: dict) -> None:
        await self.store.replace(data)

    def _validate_name(self, name: str) -> str | None:
        name = name.strip().lower()
        return name if _NAME_RE.match(name) else None

    # ── Embed builder ──────────────────────────────────────────────

    def _build_playlist_embed(
        self,
        owner: discord.User,
        pl_name: str,
        tracks: list,
        page: int,
        total_pages: int,
    ) -> discord.Embed:
        start = (page - 1) * _PER_PAGE
        lines = []
        for i, t in enumerate(tracks[start : start + _PER_PAGE], start=start + 1):
            lines.append(f"`{i:>3}.` **{t['title']}** — *{t.get('author', '?')}*")
        embed = discord.Embed(
            title=f"🎵 Playlist **{pl_name}**",
            description="\n".join(lines) or "*Playlist vazia~*",
            color=discord.Color.from_rgb(100, 180, 255),
        )
        embed.set_author(
            name=f"Dono: {owner.display_name}", icon_url=owner.display_avatar.url
        )
        embed.set_footer(
            text=f"Página {page}/{total_pages}  •  {len(tracks)} música(s)  •  💙 Lumine"
        )
        return embed

    # ── Confirm helper ─────────────────────────────────────────────

    async def _confirm(self, ctx: commands.Context, question: str) -> bool:
        await ctx.send(question)

        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=30.0)
        except TimeoutError:
            await ctx.send("⏰ Tempo esgotado! Não fiz nada~ 💙")
            return False
        if reply.content.strip().lower() in _SIM:
            return True
        await ctx.send("Tudo bem! Deixei tudo como estava~ 🎵✨")
        return False

    # ── Public API (usada pelo music.py) ───────────────────────────

    async def get_playlist_tracks(self, user_id: int, pl_name: str) -> list | None:
        """Retorna a lista de faixas de um usuário+playlist, ou None se não encontrada."""
        pl_name = self._validate_name(pl_name)
        if not pl_name:
            return None
        data = await self._load()
        return data.get(str(user_id), {}).get(pl_name)

    # ── Comandos ───────────────────────────────────────────────────

    @commands.group(name="playlist", aliases=["pl"], invoke_without_command=True)
    async def playlist(self, ctx: commands.Context):
        """Gerencia suas playlists favoritas."""
        await ctx.send(
            "💙 Subcomandos disponíveis: `save`, `list`, `show`, `add`, `remove`, `delete`, `rename`~\n"
            "Ex: `l!pl save lofi` ou `l!pl list`. Use `l!help musica` pra ver tudo! ✨"
        )

    # ── save ───────────────────────────────────────────────────────

    @playlist.command(name="save", aliases=["salvar"])
    async def pl_save(self, ctx: commands.Context, *, name: str):
        """Salva a fila atual (+ música tocando) como playlist. Ex: l!pl save lofi"""
        pl_name = self._validate_name(name)
        if not pl_name:
            await ctx.send(
                "😅 Nome inválido! Use só letras, números, `-` ou `_` (máx. 20 caracteres)~"
            )
            return

        player: wavelink.Player | None = ctx.voice_client  # type: ignore
        tracks = []
        if player:
            if player.current:
                t = player.current
                tracks.append({"title": t.title, "uri": t.uri or "", "author": t.author or "?"})
            for t in player.queue:
                tracks.append({"title": t.title, "uri": t.uri or "", "author": t.author or "?"})

        if not tracks:
            await ctx.send(
                "😢 Não tem nenhuma música tocando ou na fila pra salvar agora~\n"
                "*Dica: toque algumas músicas primeiro e depois use `l!pl save`!*"
            )
            return

        data = await self._load()
        uid = str(ctx.author.id)
        user_data = data.setdefault(uid, {})

        if pl_name in user_data:
            if not await self._confirm(
                ctx,
                f"🤔 Já existe uma playlist chamada **{pl_name}** com **{len(user_data[pl_name])}** músicas!\n"
                f"Quer substituir? Responda **sim** ou **não** (30s)~ 💙",
            ):
                return
        elif len(user_data) >= _MAX_PLAYLISTS:
            await ctx.send(
                f"💔 Você já tem **{_MAX_PLAYLISTS}** playlists (o máximo)!\n"
                f"Apague uma com `l!pl delete <nome>` antes de criar outra~"
            )
            return

        if len(tracks) > _MAX_SONGS:
            tracks = tracks[:_MAX_SONGS]
            await ctx.send(
                f"⚠️ A fila tinha mais de {_MAX_SONGS} músicas! Salvei só as primeiras {_MAX_SONGS}~"
            )

        user_data[pl_name] = tracks
        await self._save(data)
        await ctx.send(
            f"💾 Playlist **{pl_name}** salva com **{len(tracks)}** música(s)! 🎵💙\n"
            f"*Toque com `l!play @{pl_name}` quando quiser~* ✨"
        )

    # ── list ───────────────────────────────────────────────────────

    @playlist.command(name="list", aliases=["listar"])
    async def pl_list(self, ctx: commands.Context, member: discord.Member | None = None):
        """Lista suas playlists (ou de outro usuário). Ex: l!pl list @Usuario"""
        target = member or ctx.author
        data = await self._load()
        playlists = data.get(str(target.id), {})

        if not playlists:
            if target == ctx.author:
                await ctx.send(
                    "🎵 Você ainda não tem nenhuma playlist!\n"
                    "Crie uma com `l!pl save <nome>` enquanto estiver ouvindo música~ 💙"
                )
            else:
                await ctx.send(f"😕 **{target.display_name}** ainda não tem playlists~")
            return

        lines = [
            f"`{i}.` **{pname}** — {len(ptracks)} música(s)"
            for i, (pname, ptracks) in enumerate(playlists.items(), 1)
        ]
        embed = discord.Embed(
            title=f"📋 Playlists de {target.display_name}",
            description="\n".join(lines),
            color=discord.Color.from_rgb(100, 180, 255),
        )
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        embed.set_footer(
            text=f"{len(playlists)}/{_MAX_PLAYLISTS} playlists  •  💙 Lumine"
        )
        await ctx.send(embed=embed)

    # ── show ───────────────────────────────────────────────────────

    @playlist.command(name="show", aliases=["ver"])
    async def pl_show(
        self,
        ctx: commands.Context,
        pl_name: str,
        member: discord.Member | None = None,
    ):
        """Mostra músicas de uma playlist. Ex: l!pl show lofi | l!pl show lofi @Usuario"""
        target = member or ctx.author
        name = self._validate_name(pl_name)
        if not name:
            await ctx.send("😅 Nome de playlist inválido~")
            return

        data = await self._load()
        tracks = data.get(str(target.id), {}).get(name)

        if tracks is None:
            owner_str = "Você" if target == ctx.author else f"**{target.display_name}**"
            await ctx.send(f"😕 {owner_str} não tem uma playlist chamada **{name}**~")
            return
        if not tracks:
            await ctx.send(f"😔 A playlist **{name}** está vazia~ Adicione músicas com `l!pl add {name}`!")
            return

        total = max(1, (len(tracks) + _PER_PAGE - 1) // _PER_PAGE)
        embed = self._build_playlist_embed(target, name, tracks, 1, total)
        if total > 1:
            view = PlaylistView(self, target, name, tracks, ctx.author, 1)
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed)

    # ── add ────────────────────────────────────────────────────────

    @playlist.command(name="add", aliases=["adicionar"])
    async def pl_add(self, ctx: commands.Context, pl_name: str, *, arg: str | None = None):
        """Adiciona música à playlist: atual (sem arg), #N da fila, ou URL direta."""
        name = self._validate_name(pl_name)
        if not name:
            await ctx.send("😅 Nome de playlist inválido~")
            return

        data = await self._load()
        uid = str(ctx.author.id)

        if name not in data.get(uid, {}):
            await ctx.send(
                f"😕 Você não tem uma playlist chamada **{name}**~\n"
                f"Crie com `l!pl save {name}` primeiro!"
            )
            return

        user_playlist = data[uid][name]
        if len(user_playlist) >= _MAX_SONGS:
            await ctx.send(
                f"💔 A playlist **{name}** já está cheia! ({_MAX_SONGS} músicas é o máximo)~"
            )
            return

        # Modo URL
        if arg and _URL_RE.match(arg.strip()):
            url = arg.strip()
            async with ctx.typing():
                try:
                    wavelink.Pool.get_node()
                except Exception:
                    await ctx.send("⏳ O Lavalink ainda não está pronto, tente em alguns segundinhos~ 🥺")
                    return
                try:
                    results = await wavelink.Playable.search(url)
                except Exception as exc:
                    await ctx.send(f"😢 Não consegui buscar essa URL... `{exc}`")
                    return
            if not results:
                await ctx.send("😞 Não encontrei nada com essa URL~")
                return
            track = results[0] if not isinstance(results, wavelink.Playlist) else results.tracks[0]
            entry = {"title": track.title, "uri": track.uri or url, "author": track.author or "?"}
            user_playlist.append(entry)
            await self._save(data)
            await ctx.send(
                f"✅ **{track.title}** adicionada à playlist **{name}**! "
                f"({len(user_playlist)}/{_MAX_SONGS}) 💙"
            )
            return

        # Modo #N da fila
        if arg and arg.strip().isdigit():
            idx = int(arg.strip()) - 1
            player: wavelink.Player | None = ctx.voice_client  # type: ignore
            if not player:
                await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
                return
            queue_tracks = list(player.queue)
            if idx < 0 or idx >= len(queue_tracks):
                await ctx.send(
                    f"😕 Número inválido! A fila tem **{len(queue_tracks)}** música(s)~"
                )
                return
            t = queue_tracks[idx]
            entry = {"title": t.title, "uri": t.uri or "", "author": t.author or "?"}
            user_playlist.append(entry)
            await self._save(data)
            await ctx.send(
                f"✅ **{t.title}** adicionada à playlist **{name}**! "
                f"({len(user_playlist)}/{_MAX_SONGS}) 💙"
            )
            return

        # Modo: música tocando agora
        player: wavelink.Player | None = ctx.voice_client  # type: ignore
        if not player or not player.current:
            await ctx.send(
                "😢 Não tem nada tocando agora!\n"
                "Passe uma URL (`l!pl add lofi <url>`) ou o número da fila (`l!pl add lofi 3`)~"
            )
            return
        t = player.current
        entry = {"title": t.title, "uri": t.uri or "", "author": t.author or "?"}
        user_playlist.append(entry)
        await self._save(data)
        await ctx.send(
            f"✅ **{t.title}** adicionada à playlist **{name}**! "
            f"({len(user_playlist)}/{_MAX_SONGS}) 💙"
        )

    # ── remove ─────────────────────────────────────────────────────

    @playlist.command(name="remove", aliases=["remover"])
    async def pl_remove(self, ctx: commands.Context, pl_name: str, index: int):
        """Remove a música #N de uma playlist. Ex: l!pl remove lofi 3"""
        name = self._validate_name(pl_name)
        if not name:
            await ctx.send("😅 Nome de playlist inválido~")
            return

        data = await self._load()
        uid = str(ctx.author.id)

        if name not in data.get(uid, {}):
            await ctx.send(f"😕 Você não tem uma playlist chamada **{name}**~")
            return

        tracks = data[uid][name]
        idx = index - 1
        if idx < 0 or idx >= len(tracks):
            await ctx.send(
                f"😕 Número inválido! A playlist **{name}** tem **{len(tracks)}** música(s)~"
            )
            return

        removed = tracks.pop(idx)
        await self._save(data)
        await ctx.send(f"🗑️ Removi **{removed['title']}** da playlist **{name}**~ 💙")

    # ── delete ─────────────────────────────────────────────────────

    @playlist.command(name="delete", aliases=["deletar", "apagar"])
    async def pl_delete(self, ctx: commands.Context, *, name: str):
        """Deleta uma playlist inteira. Ex: l!pl delete lofi"""
        pl_name = self._validate_name(name)
        if not pl_name:
            await ctx.send("😅 Nome de playlist inválido~")
            return

        data = await self._load()
        uid = str(ctx.author.id)

        if pl_name not in data.get(uid, {}):
            await ctx.send(f"😕 Você não tem uma playlist chamada **{pl_name}**~")
            return

        count = len(data[uid][pl_name])
        if not await self._confirm(
            ctx,
            f"💔 Tem certeza que quer apagar a playlist **{pl_name}** ({count} músicas)?\n"
            f"Responda **sim** ou **não** (30s)~",
        ):
            return

        del data[uid][pl_name]
        if not data[uid]:
            del data[uid]
        await self._save(data)
        await ctx.send(
            f"🗑️ Playlist **{pl_name}** apagada~ 💙\n*Até que foi divertido enquanto durou!*"
        )

    # ── rename ─────────────────────────────────────────────────────

    @playlist.command(name="rename", aliases=["renomear"])
    async def pl_rename(self, ctx: commands.Context, old_name: str, *, new_name: str):
        """Renomeia uma playlist. Ex: l!pl rename lofi chill"""
        old = self._validate_name(old_name)
        new = self._validate_name(new_name)
        if not old or not new:
            await ctx.send(
                "😅 Nome inválido! Use só letras, números, `-` ou `_` (máx. 20 caracteres)~"
            )
            return

        data = await self._load()
        uid = str(ctx.author.id)

        if old not in data.get(uid, {}):
            await ctx.send(f"😕 Você não tem uma playlist chamada **{old}**~")
            return
        if new in data.get(uid, {}):
            await ctx.send(f"😅 Você já tem uma playlist chamada **{new}**! Escolha outro nome~")
            return

        data[uid][new] = data[uid].pop(old)
        await self._save(data)
        await ctx.send(f"✏️ Renomeei **{old}** → **{new}** com todo carinho! 💙✨")

    # ── loop ───────────────────────────────────────────────────────────

    @playlist.command(name="loop", aliases=["loopall"])
    async def pl_loop(self, ctx: commands.Context):
        """Ativa/desativa o loop da fila inteira. Ex: l!pl loop"""
        player: wavelink.Player | None = ctx.voice_client  # type: ignore
        if not player:
            await ctx.send(
                "🥺 Não estou em nenhum canal de voz agora~\n"
                "*Entra num canal e toca uma música primeiro! 💙*"
            )
            return
        if player.queue.mode == wavelink.QueueMode.loop_all:
            player.queue.mode = wavelink.QueueMode.normal
            await ctx.send("🔁 Loop da filinha desativado! Vou tocar tudo uma vez só~ 💙")
        else:
            player.queue.mode = wavelink.QueueMode.loop_all
            await ctx.send(
                "🔁 Loop da filinha ativado! Quando acabar, começo tudo de novo~ 💙✨\n"
                "*Use `l!pl loop` de novo pra desativar quando quiser~*"
            )

    # ── Help injection ─────────────────────────────────────────────

    def help_field_extra(self) -> tuple[str, str, str]:
        """Injeta a seção EXTRA no l!help musica."""
        name = "✨ __EXTRA EXTRA! NOVIDADES VINDA DA LUZ~__ 💫"
        value = (
            "Ei ei ei! A Lumine tem um presente pra vocês~ 🎁💙\n"
            "Agora você pode salvar suas músicas favoritas em **playlists pessoais**!\n\n"
            "`l!pl save <nome>` — Salva a fila atual como playlist 💾\n"
            "`l!pl add <nome>` — Música atual  |  `l!pl add <nome> 3` — #3 da fila\n"
            "`l!pl add <nome> <url>` — Adiciona por link direto 🔗\n"
            "`l!pl list` — Suas playlists 📋  |  `l!pl list @Usuario` — De outra pessoa\n"
            "`l!pl show <nome>` — Espia as músicas (botões ⬅️ ➡️) 👀\n"
            "`l!pl remove <nome> <N>` — Tira uma música 🗑️\n"
            "`l!pl delete <nome>` — Apaga a playlist inteira 💔\n"
            "`l!pl rename <nome> <novo>` — Renomeia com carinho ✏️\n"
            "`l!pl loop` — Loop da fila inteira 🔁 (toca tudo de novo quando acabar)\n\n"
            "🌟 **Para tocar:** `l!play @nome` (sua) ou `l!play @nome @Usuario` (de outra pessoa)\n"
            "*Compartilha sua playlist favorita com os amigos~ 💙✨*"
        )
        return "musica", name, value


async def setup(bot: commands.Bot):
    await bot.add_cog(Playlists(bot))
