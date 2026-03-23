import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import os
from pathlib import Path
import yt_dlp
import random

# ===== TOKEN =====
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN não encontrado!")

# ===== INTENTS =====
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ===== CONFIG =====
FFMPEG_PATH = "C:/Users/Ezequiel da gaby/Downloads/ffmpeg/ffmpeg/bin/ffmpeg.exe"

YTDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0'
}

queue = []
loop_mode = False
current_song = None

# ===== BOTÕES =====
class MusicControls(View):
    def __init__(self, vc):
        super().__init__(timeout=None)
        self.vc = vc

    @discord.ui.button(label="⏸️", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("⏸️ Pausado", ephemeral=True)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: Button):
        if self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("▶️ Voltou", ephemeral=True)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: Button):
        self.vc.stop()
        await interaction.response.send_message("⏭️ Pulando...", ephemeral=True)

# ===== TOCAR =====
async def play_next(ctx):
    global current_song

    if queue:
        url = queue.pop(0)
        current_song = url

        if loop_mode:
            queue.insert(0, url)

        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)

                if 'entries' in info:
                    info = info['entries'][0]

                audio_url = info['url']
                title = info.get('title', 'Desconhecido')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')

        except Exception as e:
            await ctx.send("❌ Não consegui tocar essa música, tentando próxima...")
            await play_next(ctx)
            return

        source = discord.FFmpegPCMAudio(
            audio_url,
            executable="ffmpeg"
        )

        vc = ctx.voice_client
        vc.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))

        mins, secs = divmod(duration, 60)

        embed = discord.Embed(
            title="🎶 Tocando Agora",
            description=f"**{title}**",
            color=discord.Color.purple()
        )

        embed.add_field(name="⏱️ Duração", value=f"{mins}:{secs:02d}")
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        view = MusicControls(vc)

        await ctx.send(embed=embed, view=view)

# ===== EVENT =====
@bot.event
async def on_ready():
    print(f"🔥 Bot lendário online: {bot.user}")

# ===== PLAY =====
@bot.command()
async def play(ctx, *, search):
    if not ctx.author.voice:
        await ctx.send("Entra no voice primeiro!")
        return

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    if "http" not in search:
        search = f"ytsearch:{search}"

    queue.append(search)

    await ctx.send(f"➕ Adicionado: {search}")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

# ===== SKIP =====
@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Pulando...")

# ===== PARAR =====
@bot.command()
async def parar(ctx):
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Sai do canal")

# ===== LOOP =====
@bot.command()
async def loop(ctx):
    global loop_mode
    loop_mode = not loop_mode
    await ctx.send(f"🔁 Loop {'ativado' if loop_mode else 'desativado'}")

# ===== VOLUME =====
@bot.command()
async def volume(ctx, vol: int):
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source)
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"🔊 Volume: {vol}%")

# ===== FILA =====
@bot.command()
async def fila(ctx):
    if queue:
        embed = discord.Embed(title="📜 Fila", color=discord.Color.blue())
        for i, music in enumerate(queue[:10], start=1):
            embed.add_field(name=f"{i}.", value=music, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Fila vazia!")

# ===== MONSTERI 🥤 =====
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    if "alexia abrir lata" in content:
        if not message.author.voice:
            await message.channel.send("Entra no voice primeiro!")
            return

        if not message.guild.voice_client:
            await message.author.voice.channel.connect()

        monster_songs = [
            "ytsearch:phonk pesado",
            "ytsearch:trap brasileiro",
            "ytsearch:funk mandela",
        ]

        queue.clear()
        queue.append(random.choice(monster_songs))

        ctx = await bot.get_context(message)

        await message.channel.send("🥤 *PSSSHHHH* Alexia abriu a Monster 😈")

        if not message.guild.voice_client.is_playing():
            await play_next(ctx)

    await bot.process_commands(message)

# ===== RUN =====
bot.run(TOKEN)