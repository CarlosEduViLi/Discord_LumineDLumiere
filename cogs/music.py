import asyncio
import os
import random
import re

import discord
import wavelink
from discord.ext import commands

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_SPOTIFY_RE = re.compile(
    r"https?://open\.spotify\.com/(track|album|playlist|artist)/[\w]+",
    re.IGNORECASE,
)
_SIM = {"sim", "s", "yes", "y", "confirmar", "confirma", "ok"}
_PER_PAGE = 10


# ----------------------------------------------------------------
# View de paginação — botões nativos do Discord (sem reações)
# ----------------------------------------------------------------

class QueueView(discord.ui.View):
    """Paginação por botões: sem race condition, sem double-click."""

    def __init__(self, cog: "Music", player: wavelink.Player, author: discord.Member, page: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.player = player
        self.author = author
        self.current_page = page
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Só quem pediu a fila pode navegar nela~ 🥺", ephemeral=True
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

    def _total_pages(self, tracks: list) -> int:
        return max(1, (len(tracks) + _PER_PAGE - 1) // _PER_PAGE) if tracks else 1

    async def _turn(self, interaction: discord.Interaction, delta: int):
        tracks = list(self.player.queue)
        total = self._total_pages(tracks)
        self.current_page = (self.current_page - 1 + delta) % total + 1
        await interaction.response.edit_message(
            embed=self.cog._build_queue_embed(self.player, tracks, self.current_page, total)
        )

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, -1)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._turn(interaction, +1)


# ----------------------------------------------------------------
# Frases fofas da Lumine — sorteadas aleatoriamente
# ----------------------------------------------------------------

_EMPTY_CHANNEL_MSGS = [
    "Hmm... parece que todos foram embora e me deixaram sozinha aqui... 🥺💙 Tudo bem! Estarei aqui quando me chamarem de volta~",
    "Ah... o silêncio ficou grande demais pra mim aguentar sozinha... 🌙 Saí por agora, mas estarei aqui quando precisarem de música! 💙",
    "Esperei bastante, mas parece que ficou só eu no canal... 🌸 Vou embora por enquanto! Quando quiserem música, é só me chamar~",
    "Bem, eu amo companhia, mas tocar pra ninguém é um pouquinho solitário... 😢💫 Até logo! Cuida-se bem!",
    "Ficou tão silencioso... 🤍 Vou descansar um pouco! Quando a turma voltar, me chama que eu corro~ 🎵",
]

_PAUSE_REMINDER_MSGS = [
    "Ei, {mention}~ 🥺 A musiquinha ainda está pausada aqui... Tudo bem com você? Quando quiser continuar é só falar!",
    "Oi {mention}! 🌸 Só passando pra lembrar que a música está pausada esperando por você~ Use `l!resume` quando quiser!",
    "{mention}, você sumiu! 😊 A musiquinha e eu ficamos esperando com carinho... Pode continuar quando quiser! 🎵",
    "Hm~ {mention}, notei que ainda está pausado(a)... 🌙 Sem pressa, tá? Só me avisa quando quiser continuar!",
    "Psiu, {mention}~ 💫 A Lumine aqui lembrando que sua música ainda está esperando por você com todo carinho~",
    "{mention}! 🎵 A musiquinha tá na pausa te esperando com saudade... Quando tiver pronto(a) é só usar `l!resume`!",
    "Oi oi, {mention}~ 🤍 Só um lembrete fofo: a música ainda está pausadinha aqui me esperando com você!",
    "{mention}, a Lumine não foi embora não~ 💙 Continuo aqui esperando você retomar a música quando quiser!",
    "Lembrete de carinho: {mention}~ 🌟 Sua música está me esperando! Quando estiver pronto(a), `l!resume` resolve!",
    "Ainda aqui~ 🌸 {mention}, não esquece de mim! A musiquinha está pausada esperando seu retorno com ansiedade!",
    "{mention}! 💫 Você me deixou em pausa faz um tempinho... Não que eu me importe, mas a música sente falta de você~ 🎶",
    "Oi {mention}~ 🥺 Passei só pra checar se está tudo bem! A música continua parada esperando por você com carinho~",
    "Hmm, {mention}... 🌙 Estou guardando sua música com todo cuidado aqui! É só falar quando quiser continuar~ 💙",
    "{mention}! 🎵 Lembrete fofo da sua Lumine: `l!resume` faz a magia acontecer quando você estiver pronto(a)~",
    "Continuando meu trabalho de guardiã da música~ 🌸 {mention}, ainda aqui! Pode voltar quando quiser, tá? 💙✨",
]


class Music(commands.Cog):
    """🎵 Música com carinho da Lumine 💙"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # guild_id → asyncio.Task do monitor de canal vazio
        self._empty_timers: dict[int, asyncio.Task] = {}
        # guild_id → asyncio.Task do monitor de pause
        self._pause_timers: dict[int, asyncio.Task] = {}
        # guild_id → user_id de quem pausou a música
        self._pause_who: dict[int, int] = {}

    async def cog_load(self):
        self.bot.loop.create_task(self._connect_nodes())

    async def _connect_nodes(self):
        await self.bot.wait_until_ready()
        node = wavelink.Node(
                uri="http://127.0.0.1:2333",
                password=os.getenv("LAVALINK_PASSWORD", "youshallnotpass"),
            )
        for attempt in range(1, 16):
            try:
                await wavelink.Pool.connect(nodes=[node], client=self.bot, cache_capacity=100)
                print("  Cog music: conectado ao Lavalink.")
                return
            except Exception as exc:
                print(f"  Cog music: aguardando Lavalink... tentativa {attempt}/15 ({exc})")
                await asyncio.sleep(3)
        print("  Cog music: não foi possível conectar após 15 tentativas.")

    # ---- Helpers de timer ----

    def _cancel_empty_timer(self, guild_id: int):
        """Cancela o timer de canal vazio para uma guild."""
        task = self._empty_timers.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    def _cancel_pause_timer(self, guild_id: int):
        """Cancela o timer de pause para uma guild."""
        task = self._pause_timers.pop(guild_id, None)
        if task and not task.done():
            task.cancel()
        self._pause_who.pop(guild_id, None)

    def _cancel_all_timers(self, guild_id: int):
        """Cancela ambos os timers de uma guild."""
        self._cancel_empty_timer(guild_id)
        self._cancel_pause_timer(guild_id)

    async def _empty_channel_watcher(self, player: wavelink.Player):
        """Aguarda 2 min; se o canal ainda estiver vazio, manda mensagem fofa e desconecta."""
        await asyncio.sleep(120)  # 2 minutos
        guild_id = player.guild.id
        self._empty_timers.pop(guild_id, None)
        # Re-verifica se ainda está vazio (pode ter alguém entrado)
        vc = player.channel
        humans = [m for m in vc.members if not m.bot]
        if humans:
            return  # Alguém voltou, cancela
        ch = getattr(player, "reply_channel", None)
        if ch:
            await ch.send(random.choice(_EMPTY_CHANNEL_MSGS))
        self._cancel_all_timers(guild_id)
        await player.disconnect()

    async def _pause_watcher(self, player: wavelink.Player, pauser_id: int):
        """Pinga quem pausou a cada 10 min em loop, sem nunca sair da call por causa de pause."""
        guild_id = player.guild.id
        mention = f"<@{pauser_id}>"
        ch = getattr(player, "reply_channel", None)
        while True:
            await asyncio.sleep(600)  # 10 minutos
            # Se o task foi cancelado (resume/stop), asyncio.CancelledError sobe aqui
            if ch:
                msg = random.choice(_PAUSE_REMINDER_MSGS).format(mention=mention)
                await ch.send(msg)

    # ---- Wavelink events ----

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"  ✅ Node {payload.node.identifier} está pronto!")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Detecta quando o canal da Lumine fica vazio e inicia o timer de saída."""
        guild = member.guild
        player: wavelink.Player | None = guild.voice_client  # type: ignore
        if not player or not isinstance(player, wavelink.Player):
            return
        vc = player.channel
        if not vc:
            return
        # Verificar se o bot foi movido ou desconectado manualmente
        if member == guild.me:
            if after.channel is None:
                # Bot foi desconectado manualmente
                self._cancel_all_timers(guild.id)
            return
        # Contar humanos no canal do bot
        humans = [m for m in vc.members if not m.bot]
        guild_id = guild.id
        if not humans:
            # Canal ficou vazio — iniciar timer se ainda não existir
            if guild_id not in self._empty_timers:
                task = self.bot.loop.create_task(self._empty_channel_watcher(player))
                self._empty_timers[guild_id] = task
        else:
            # Alguém entrou — cancelar timer de canal vazio
            self._cancel_empty_timer(guild_id)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player | None = payload.player
        if not player or payload.reason == "replaced":
            return
        if player.guild:
            self._cancel_pause_timer(player.guild.id)
        mode = player.queue.mode
        # 🔁 Loop da música atual: repete a mesma faixa
        if mode == wavelink.QueueMode.loop and payload.track:
            await player.play(payload.track, volume=player.volume)
            return
        # 🔁 Loop da fila: coloca a faixa terminada de volta no final
        if mode == wavelink.QueueMode.loop_all and payload.track:
            await player.queue.put_wait(payload.track)
        if not player.queue.is_empty:
            await player.play(player.queue.get(), volume=player.volume)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player | None = payload.player
        if not player:
            return
        track = payload.track
        embed = discord.Embed(
            title="🎵 Tocando agora~",
            description=f"[{track.title}]({track.uri})" if track.uri else track.title,
            color=discord.Color.from_rgb(29, 185, 84),
        )
        embed.add_field(name="🎤 Autor", value=track.author or "Desconhecido", inline=True)
        embed.add_field(name="⏱️ Duração", value=self._fmt(track), inline=True)
        mode = player.queue.mode
        if mode == wavelink.QueueMode.loop:
            footer = "🔁 Loop da música ativo~ Espero que goste! 💙 — Lumine"
        elif mode == wavelink.QueueMode.loop_all:
            footer = "🔁 Loop da fila ativo~ Espero que goste! 💙 — Lumine"
        else:
            footer = "Espero que goste! 💙 — Lumine"
        embed.set_footer(text=footer)
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        ch = getattr(player, "reply_channel", None)
        if ch:
            await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        player: wavelink.Player | None = payload.player
        if not player:
            return
        ch = getattr(player, "reply_channel", None)
        if ch:
            await ch.send("⚠️ Essa faixa não quis cooperar... Pulando para a próxima! 💙")
        if not player.queue.is_empty:
            await player.play(player.queue.get(), volume=player.volume)

    # ---- Helpers ----

    @staticmethod
    def _fmt(track: wavelink.Playable) -> str:
        if track.is_stream:
            return "🔴 Ao vivo"
        m, s = divmod(track.length // 1000, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    @staticmethod
    def _fmt_pos(ms: int) -> str:
        """Formata milissegundos como M:SS ou H:MM:SS."""
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    @staticmethod
    def _parse_time(arg: str) -> int | None:
        """Converte SS, MM:SS ou HH:MM:SS em milissegundos."""
        parts = arg.strip().split(":")
        try:
            if len(parts) == 1:
                return int(parts[0]) * 1000
            if len(parts) == 2:
                return (int(parts[0]) * 60 + int(parts[1])) * 1000
            if len(parts) == 3:
                return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
        except ValueError:
            return None
        return None

    @staticmethod
    def _progress_bar(position_ms: int, length_ms: int, width: int = 20) -> str:
        """Monta a barra de progresso visual da música."""
        if length_ms <= 0:
            return "─" * width
        ratio = min(position_ms / length_ms, 1.0)
        filled = int(ratio * (width - 1))
        return "━" * filled + "●" + "─" * (width - filled - 1)

    async def _get_player(self, ctx: commands.Context) -> wavelink.Player | None:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Ei~ 💙 Você precisa estar em um canal de voz primeiro!")
            return None
        try:
            wavelink.Pool.get_node()
        except Exception:
            await ctx.send("⏳ Ainda me preparando... Tente de novo em alguns segundinhos! 🥺")
            return None
        if ctx.voice_client:
            if not isinstance(ctx.voice_client, wavelink.Player):
                await ctx.send("Já tem outra conexão de voz ativa... 😅")
                return None
            player: wavelink.Player = ctx.voice_client
            if player.channel != ctx.author.voice.channel:
                try:
                    await player.move_to(ctx.author.voice.channel)
                except wavelink.ChannelTimeoutException:
                    await ctx.send(
                        "😢 Não consegui me mover para o seu canal a tempo...\n"
                        "Tenta usar `l!stop` e me chamar de novo! 💙"
                    )
                    return None
        else:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
            except wavelink.ChannelTimeoutException:
                await ctx.send(
                    "😢 Não consegui entrar no canal de voz a tempo...\n"
                    "Isso pode ser instabilidade momentânea! Tenta de novo daqui a pouco~ 💙"
                )
                return None
        player.reply_channel = ctx.channel
        return player

    async def _confirm(self, ctx: commands.Context, question: str) -> bool:
        await ctx.send(question)

        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tempo esgotado! Não fiz nada~ 💙")
            return False
        if reply.content.strip().lower() in _SIM:
            return True
        await ctx.send("Tudo bem! Deixei tudo como estava~ 🎵✨")
        return False

    def _build_queue_embed(self, player: wavelink.Player, tracks: list, page: int, total_pages: int) -> discord.Embed:
        start = (page - 1) * _PER_PAGE
        lines = []
        if player.current:
            lines.append(f"▶️ **Tocando agora:** {player.current.title}")
            if tracks:
                lines.append("")
        for i, t in enumerate(tracks[start:start + _PER_PAGE], start=start + 1):
            lines.append(f"`{i:>3}.` {t.title}")
        embed = discord.Embed(
            title="📋 Filinha de músicas~",
            description="\n".join(lines) or "*Fila vazia — só a música atual* 🎵",
            color=discord.Color.from_rgb(114, 137, 218),
        )
        footer = f"Página {page}/{total_pages}"
        if tracks:
            footer += f"  •  {len(tracks)} música(s) na fila"
        footer += "  •  💙 Lumine"
        embed.set_footer(text=footer)
        return embed

    # ---- Comandos ----

    async def _play_playlist(self, ctx: commands.Context, player, query: str):
        """Carrega e toca uma playlist pessoal. Sintaxe: @nome | @nome @mention"""
        pl_cog = self.bot.get_cog("Playlists")
        if not pl_cog:
            await ctx.send("😢 O sistema de playlists não está disponível agora~")
            return

        # Parsing: separa @nome de possível mention
        parts = query.split()
        pl_name = parts[0][1:]  # remove o @

        # Tenta encontrar um mention do Discord nas partes restantes
        target_user = ctx.author
        if len(parts) > 1:
            mention_match = re.search(r"<@!?(\d+)>", " ".join(parts[1:]))
            if mention_match:
                uid = int(mention_match.group(1))
                target_user = ctx.guild.get_member(uid)
                if not target_user:
                    await ctx.send("😕 Não encontrei esse usuário no servidor~")
                    return

        tracks_data = pl_cog.get_playlist_tracks(target_user.id, pl_name)
        if tracks_data is None:
            owner_str = "Você" if target_user == ctx.author else f"**{target_user.display_name}**"
            await ctx.send(
                f"😕 {owner_str} não tem uma playlist chamada **{pl_name}**~\n"
                f"*Crie uma com `l!pl save {pl_name}` ou veja suas listas com `l!pl list`!*"
            )
            return
        if not tracks_data:
            await ctx.send(f"😔 A playlist **{pl_name}** está vazia~")
            return

        owner_label = "" if target_user == ctx.author else f" de **{target_user.display_name}**"
        total = len(tracks_data)

        # Frases fofas que a Lumine alterna enquanto carrega
        _LOADING_MSGS = [
            "Deixa eu pegar as músicas com carinho~ 🎀",
            "Estou embrulhando cada musiquinha com amor~ 💝",
            "Quase lá! Só mais um pouquinho~ 🌸",
            "Estou trabalhando com todo carinho pra você~ 💙",
            "Segura que as músicas estão chegando~ ✨",
            "Minha bagagem musical está ficando cheia~ 🎒🎵",
        ]

        def _make_progress_bar(done: int, total: int, width: int = 15) -> str:
            if total <= 0:
                return "─" * width
            ratio = min(done / total, 1.0)
            filled = int(ratio * (width - 1))
            return "━" * filled + "●" + "─" * (width - filled - 1)

        def _loading_text(done: int, failed_so_far: int) -> str:
            phrase = _LOADING_MSGS[(done // 3) % len(_LOADING_MSGS)]
            bar = _make_progress_bar(done, total)
            pct = int(done / total * 100) if total else 100
            line1 = f"📋 Carregando playlist **{pl_name}**{owner_label}~"
            line2 = f"`{bar}` **{pct}%** ({done}/{total})"
            line3 = f"*{phrase}*"
            if failed_so_far:
                line3 += f"\n*(⚠️ {failed_so_far} não carregaram ainda)*"
            return f"{line1}\n{line2}\n{line3}"

        status_msg = await ctx.send(_loading_text(0, 0))

        loaded, failed = 0, 0
        _UPDATE_EVERY = 3  # atualiza a mensagem a cada N músicas carregadas

        for i, track_data in enumerate(tracks_data, 1):
            uri = track_data.get("uri", "")
            if not uri:
                failed += 1
            else:
                try:
                    results = await wavelink.Playable.search(uri)
                    if results:
                        track = results[0] if not isinstance(results, wavelink.Playlist) else results.tracks[0]
                        await player.queue.put_wait(track)
                        loaded += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

            # Atualiza a mensagem a cada _UPDATE_EVERY músicas ou na última
            if i % _UPDATE_EVERY == 0 or i == total:
                try:
                    await status_msg.edit(content=_loading_text(i, failed))
                except discord.HTTPException:
                    pass

        if loaded == 0:
            await status_msg.edit(
                content=f"😢 Não consegui carregar nenhuma música da playlist **{pl_name}**~\n"
                        "*Verifique se as músicas ainda estão disponíveis! 💙*"
            )
            return

        result_msg = (
            f"✅ Playlist **{pl_name}**{owner_label} carregada com todo amor! 💙✨\n"
            f"**{loaded}** música(s) adicionadas à filinha~"
        )
        if failed:
            result_msg += f"\n*(⚠️ {failed} música(s) não puderam ser carregadas)*"

        if not player.playing:
            await player.play(player.queue.get(), volume=player.volume)
        await status_msg.edit(content=result_msg)

    @commands.command(name="play", aliases=["p", "tocar"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Toca uma música, playlist ou link. Ex: l!play lofi hip hop | l!play @minhaplaylist"""
        query = query.strip()
        if not query:
            await ctx.send("Hm~ Me diz o nome ou o link da música! 🎶")
            return

        # Modo playlist pessoal: query começa com @
        if query.startswith("@"):
            player = await self._get_player(ctx)
            if not player:
                return
            await self._play_playlist(ctx, player, query)
            return

        player = await self._get_player(ctx)
        if not player:
            return
        is_spotify = bool(_SPOTIFY_RE.match(query))
        if is_spotify:
            await ctx.send(
                "🟢 Suporte a Spotify está **temporariamente desativado**~ 💙\n"
                "*O Spotify agora exige conta Premium no dono do app pra usar a Web API.*\n"
                "Me passa o nome da música ou um link do YouTube e eu toco com gosto! 🎵"
            )
            return
        async with ctx.typing():
            try:
                results = (
                    await wavelink.Playable.search(query)
                    if _URL_RE.match(query)
                    else await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTubeMusic)
                )
            except Exception as exc:
                await ctx.send(f"😢 Não consegui encontrar isso... `{exc}`")
                return
        if not results:
            await ctx.send("😞 Não encontrei nada... Tenta com outro nome?")
            return
        if isinstance(results, wavelink.Playlist):
            added = await player.queue.put_wait(results)
            msg = f"📋 Adicionei **{added}** músicas da playlist **{results.name or 'playlist'}** na filinha! 🎵"
        else:
            track = results[0]
            await player.queue.put_wait(track)
            msg = f"📋 **{track.title}** adicionado na posição **#{len(player.queue)}**! 💙"
        if not player.playing:
            await player.play(player.queue.get(), volume=50)
            return
        await ctx.send(msg)

    @commands.command(name="skip", aliases=["sk", "pular"])
    async def skip(self, ctx: commands.Context):
        """Pula a música atual."""
        player: wavelink.Player | None = ctx.voice_client
        if not player or not player.current:
            await ctx.send("Não tem nada tocando agora~ 🎵")
            return
        title = player.current.title
        await player.skip(force=True)
        await ctx.send(f"⏭️ Pulei **{title}**! 🎶")

    @commands.command(name="jump", aliases=["j"])
    async def jump(self, ctx: commands.Context, amount: int):
        """Pula N músicas da fila. Ex: l!jump 5"""
        player: wavelink.Player | None = ctx.voice_client
        if not player:
            await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
            return
        if amount <= 0:
            await ctx.send("O número precisa ser maior que zero! 😅")
            return
        queue_size = len(player.queue)
        if amount >= queue_size:
            q = queue_size
            msg = (
                f"🤔 Você quer pular **{amount}** música(s), mas a fila {'está vazia' if q == 0 else f'só tem **{q}**'}!\n"
                f"A filinha ficará completamente vazia. Tem certeza? Responda **sim** ou **não** (30s). 💙"
            )
            if not await self._confirm(ctx, msg):
                return
            player.queue.reset()
            await player.stop()
            await ctx.send("✨ Pulei tudo e limpei a filinha! Me manda novas músicas quando quiser~ 🎶")
            return
        for _ in range(amount):
            if player.queue.is_empty:
                break
            player.queue.get()
        await player.skip(force=True)
        remaining = len(player.queue)
        await ctx.send(
            f"⏩ Pulei **{amount}** música(s)! {'Ainda tem **' + str(remaining) + '** na filinha~ 🎵' if remaining else 'Filinha vazia agora. 💙'}"
        )

    @commands.command(name="remove", aliases=["rm", "del"])
    async def remove(self, ctx: commands.Context, *, arg: str):
        """Remove música(s) da fila. l!rm $10 remove a #10; l!rm 10 remove as próximas 10."""
        player: wavelink.Player | None = ctx.voice_client
        if not player:
            await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
            return
        if player.queue.is_empty:
            await ctx.send("A filinha já está vazia~ ✨")
            return

        arg = arg.strip()

        # Modo $N — remove a faixa específica pelo número
        if arg.startswith("$"):
            try:
                index = int(arg[1:]) - 1
            except ValueError:
                await ctx.send("Usa `l!rm $10` para remover a 10ª música da fila! 🎵")
                return
            tracks = list(player.queue)
            if index < 0 or index >= len(tracks):
                await ctx.send(
                    f"😕 Não encontrei a música **#{index + 1}** na fila... A fila tem **{len(tracks)}** música(s)!"
                )
                return
            removed = tracks.pop(index)
            player.queue.reset()
            for t in tracks:
                player.queue.put(t)
            await ctx.send(f"🗑️ Removi **{removed.title}** da filinha~ 💙")
            return

        # Modo N — remove as próximas N faixas
        try:
            amount = int(arg)
        except ValueError:
            await ctx.send("Não entendi... Usa `l!rm 5` (remove as próximas 5) ou `l!rm $5` (remove a #5). 🎵")
            return

        if amount <= 0:
            await ctx.send("O número precisa ser maior que zero! 😅")
            return

        queue_size = len(player.queue)
        if amount >= queue_size:
            msg = (
                f"🤔 Você quer remover **{amount}** música(s), mas a fila só tem **{queue_size}**!\n"
                f"Isso vai esvaziar a filinha. Tem certeza? Responda **sim** ou **não** (30s). 💙\n"
                f"*Dica: o `l!clear` faz isso mais rápido na próxima! ✨*"
            )
            if not await self._confirm(ctx, msg):
                return
            player.queue.reset()
            await ctx.send(
                f"🧹 Pronto, limpei toda a filinha! 💙\n"
                f"*Da próxima vez, `l!clear` resolve isso numa tacada só~ ✨*"
            )
            return

        removed_count = 0
        for _ in range(amount):
            if player.queue.is_empty:
                break
            player.queue.get()
            removed_count += 1

        await ctx.send(
            f"🗑️ Removi as **{removed_count}** próximas música(s) da filinha~ 💙 "
            f"Ainda tem **{len(player.queue)}** esperando!"
        )

    @commands.command(name="clear", aliases=["limpar", "c"])
    async def clear(self, ctx: commands.Context):
        """Limpa toda a fila sem parar a música atual."""
        player: wavelink.Player | None = ctx.voice_client
        if not player:
            await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
            return
        if player.queue.is_empty:
            await ctx.send("A filinha já está vazia~ ✨")
            return
        count = len(player.queue)
        player.queue.reset()
        await ctx.send(f"🧹 Limpei **{count}** música(s) da filinha! A que está tocando continua~ 🎵💙")

    @commands.command(name="shuffle", aliases=["embaralhar", "sh"])
    async def shuffle(self, ctx: commands.Context):
        """Embaralha aleatoriamente a fila."""
        player: wavelink.Player | None = ctx.voice_client
        if not player:
            await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
            return
        if len(player.queue) < 2:
            await ctx.send("Precisa de pelo menos 2 músicas na fila para embaralhar! 😄")
            return
        tracks = list(player.queue)
        random.shuffle(tracks)
        player.queue.reset()
        for t in tracks:
            player.queue.put(t)
        await ctx.send(f"🔀 Embaralhei **{len(tracks)}** músicas! Vai ser uma surpresa~ ✨💙")

    @commands.command(name="stop", aliases=["parar", "leave"])
    async def stop(self, ctx: commands.Context):
        """Para a música e desconecta do canal de voz."""
        player: wavelink.Player | None = ctx.voice_client
        if not player:
            await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
            return
        guild_id = player.guild.id
        self._cancel_all_timers(guild_id)
        player.queue.reset()
        await player.disconnect()
        await ctx.send("⏹️ Parei tudo e saí do canal! Foi um prazer~ 💙✨")

    @commands.command(name="pause", aliases=["pausar"])
    async def pause(self, ctx: commands.Context):
        """Pausa a música atual."""
        player: wavelink.Player | None = ctx.voice_client
        if not player or not player.current:
            await ctx.send("Não tem nada tocando agora~ 🎵")
            return
        if player.paused:
            await ctx.send("Já estou pausada! Use `l!resume` para continuar. 💙")
            return
        await player.pause(True)
        await ctx.send("⏸️ Pausei! Me avisa quando quiser continuar~ 🎵")
        # Registrar quem pausou e iniciar o monitor de pause
        guild_id = player.guild.id
        self._cancel_pause_timer(guild_id)  # Cancela qualquer timer anterior
        self._pause_who[guild_id] = ctx.author.id
        task = self.bot.loop.create_task(self._pause_watcher(player, ctx.author.id))
        self._pause_timers[guild_id] = task

    @commands.command(name="resume", aliases=["retomar"])
    async def resume(self, ctx: commands.Context):
        """Retoma a música pausada."""
        player: wavelink.Player | None = ctx.voice_client
        if not player or not player.current:
            await ctx.send("Não tem nada tocando agora~ 🎵")
            return
        if not player.paused:
            await ctx.send("Já estou tocando! 🎶")
            return
        await player.pause(False)
        # Cancelar o monitor de pause ao retomar
        self._cancel_pause_timer(player.guild.id)
        await ctx.send("▶️ Continuando~ 🎵✨")

    @commands.command(name="queue", aliases=["q", "fila"])
    async def queue(self, ctx: commands.Context, page: int = 1):
        """Mostra a fila com paginação por botões."""
        player: wavelink.Player | None = ctx.voice_client
        if not player or (not player.current and player.queue.is_empty):
            await ctx.send("A filinha está vazia... Me manda uma música! 🎶")
            return
        tracks = list(player.queue)
        total = max(1, (len(tracks) + _PER_PAGE - 1) // _PER_PAGE) if tracks else 1
        page = max(1, min(page, total))
        embed = self._build_queue_embed(player, tracks, page, total)
        if total > 1:
            view = QueueView(self, player, ctx.author, page)
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np", "tocando"])
    async def nowplaying(self, ctx: commands.Context):
        """Mostra a música tocando agora com barra de progresso."""
        player: wavelink.Player | None = ctx.voice_client
        if not player or not player.current:
            await ctx.send("Não estou tocando nada agora~ 🎵")
            return
        track = player.current
        embed = discord.Embed(
            title="🎵 Tocando agora~",
            description=f"[{track.title}]({track.uri})" if track.uri else track.title,
            color=0x1DB954,
        )
        embed.add_field(name="🎤 Autor", value=track.author or "Desconhecido", inline=True)
        embed.add_field(name="⏱️ Duração", value=self._fmt(track), inline=True)
        embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
        if not track.is_stream:
            pos_ms = player.position
            bar = self._progress_bar(pos_ms, track.length)
            pos_fmt = self._fmt_pos(pos_ms)
            total_fmt = self._fmt(track)
            embed.add_field(
                name="⏳ Progresso",
                value=f"`{pos_fmt}` {bar} `{total_fmt}`",
                inline=False,
            )
        mode = player.queue.mode
        if mode == wavelink.QueueMode.loop:
            footer = "🔁 Loop da música ativo • Curtindo? 💙 — Lumine"
        elif mode == wavelink.QueueMode.loop_all:
            footer = "🔁 Loop da fila ativo • Curtindo? 💙 — Lumine"
        else:
            footer = "Curtindo a música? 💙 — Lumine"
        embed.set_footer(text=footer)
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        await ctx.send(embed=embed)

    @commands.command(name="loop", aliases=["lp"])
    async def loop(self, ctx: commands.Context):
        """Ativa/desativa o loop da música atual. Ex: l!loop"""
        player: wavelink.Player | None = ctx.voice_client
        if not player or not player.current:
            await ctx.send("Não estou tocando nada agora~ 🎵")
            return
        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            await ctx.send("🔁 Loop desativado! Vou continuar a filinha normalmente~ 💙")
        else:
            player.queue.mode = wavelink.QueueMode.loop
            await ctx.send(
                f"🔁 Agora **{player.current.title}** vai ficar em loop! 💙✨\n"
                "*Me diz quando você quiser parar, tá? Use `l!loop` de novo~*"
            )

    @commands.command(name="seek", aliases=["ir"])
    async def seek(self, ctx: commands.Context, *, time_str: str):
        """Vai para um tempo específico da música. Ex: l!seek 1:30 | l!seek 90"""
        player: wavelink.Player | None = ctx.voice_client
        if not player or not player.current:
            await ctx.send("Não estou tocando nada agora~ 🎵")
            return
        track = player.current
        if track.is_stream:
            await ctx.send(
                "😅 Não dá pra avançar em transmissões ao vivo~\n"
                "*Streams são como a vida: só vão pra frente!* 💙"
            )
            return
        ms = self._parse_time(time_str)
        if ms is None:
            await ctx.send(
                "😕 Não entendi o tempo... Usa assim:\n"
                "`l!seek 1:30` — vai pro minuto 1:30\n"
                "`l!seek 90` — vai pros 90 segundos~ 💙"
            )
            return
        if ms < 0 or ms >= track.length:
            await ctx.send(
                f"😅 Esse tempo não existe nessa música! Ela vai de `0:00` até `{self._fmt(track)}`~ 🎵"
            )
            return
        await player.seek(ms)
        pos_fmt = self._fmt_pos(ms)
        await ctx.send(f"⏩ Prontinho! Fui para **{pos_fmt}** em **{track.title}**~ 💙✨")

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx: commands.Context, value: int | None = None):
        """Mostra ou altera o volume (0–150). Ex: l!volume 70"""
        player: wavelink.Player | None = ctx.voice_client
        if not player:
            await ctx.send("Não estou em nenhum canal de voz agora~ 💙")
            return
        if value is None:
            await ctx.send(f"🔊 Volume atual: **{player.volume}%**~ 💙")
            return
        value = max(0, min(value, 150))
        await player.set_volume(value)
        if value == 0:
            await ctx.send("🔇 Silêncio total~ 🤫")
        elif value > 100:
            await ctx.send(f"🔊 Volume em **{value}%**! Cuidado com os ouvidos~ 💙😄")
        else:
            await ctx.send(f"🔊 Volume ajustado para **{value}%**~ ✨")

    def help_meta(self) -> dict:
        """Metadados pro l!help (cardápio + busca por categoria)."""
        return {
            "key": "musica",
            "aliases": ("music", "música", "song", "fila", "queue"),
            "icon": "🎵",
            "category": "Música & Fila",
            "blurb": "Posso tocar suas músicas favoritas pra você~ 🎶",
            "intro": "Vamos colocar uma musiquinha pra alegrar o ambiente? 🎶💙",
        }

    def help_field(self) -> tuple[str, str]:
        """Retorna o campo de ajuda desta cog para o l!help."""
        name = "🎵 __Comandos de Música__"
        value = (
            "`l!play` / `l!p` `<nome ou link>` — Toca ou adiciona à fila 🎶\n"
            "↳ Aceita nome da música, link do YouTube ou playlist do YouTube\n"
            "`l!play @nome` — Toca sua playlist favorita 💙\n"
            "`l!play @nome @Usuario` — Toca a playlist de outra pessoa 🌟\n"
            "`l!skip` / `l!sk` — Pula a música atual ⏭️\n"
            "`l!jump` / `l!j` `<N>` — Pula N músicas da fila\n"
            "`l!pause` — Pausa ⏸️  |  `l!resume` — Retoma ▶️\n"
            "`l!stop` / `l!parar` — Para tudo e saio ⏹️\n"
            "`l!queue` / `l!q` `[pág]` — Fila (botões ⬅️ ➡️)\n"
            "`l!remove` / `l!rm` `$N` ou `N` — Remove música(s)\n"
            "`l!clear` — Limpa a fila 🧹  |  `l!shuffle` — Embaralha 🔀\n"
            "`l!nowplaying` / `l!np` — Música atual com progresso ⏳🎵\n"
            "`l!loop` / `l!lp` — Loop da música atual 🔁\n"
            "`l!seek` / `l!ir` `<tempo>` — Vai para um tempo (ex: `1:30`) ⏩\n"
            "`l!volume` / `l!vol` `[0-150]` — Volume 🔊"
        )
        return name, value


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
