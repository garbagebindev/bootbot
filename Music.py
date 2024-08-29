import asyncio
import random
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp as youtube_dl
from collections import deque



ytdl_format_options = {
    "quiet": True,
    "simulate": True,
    "forceurl": True,
    'format': 'bestaudio/best',
}

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -filter:a "volume=0.25"',
                  }

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
queues = {}


class music(commands.Cog, name="music"):

    def __init__(self, bot):
        self.bot = bot
        self.gifs = [
            "https://tenor.com/view/dashspider-dash-geometrydash-geometry-dash-colon-gif-6183807318430948778",
            "https://media.discordapp.net/attachments/1193274419284561931/1205099972698308638/pou.gif?ex=66c714cf&is=66c5c34f&hm=53f151686f818a57069b6987209070c0bae70bb7fab8bcd1238a862c729a17bf&",
            "https://media.discordapp.net/attachments/744329506827010152/1181678153446461511/attachment.gif?ex=66c6e84a&is=66c596ca&hm=b3c1986ae8a248a09553fc5875dfd842e4f8e2da61dc827947fb4d606c995974&",
            "https://media.discordapp.net/attachments/1073842702346616886/1197757147526742118/1473EA6E-8A49-4638-B6A5-8FD7953A8EBB.gif?ex=66c6bc45&is=66c56ac5&hm=4df8224e14a772a49f31b2fc3519d84e45c2e9a6a55712cd26031d9d6b44e507&",
            "https://cdn.discordapp.com/attachments/422448194476048403/914011443513401374/you_be_like-1.gif?ex=66c6bffd&is=66c56e7d&hm=c76af145424b38f1af195c3e6c55bf04730e3d2022ef28260ca144e339652806&",
            "https://media.discordapp.net/attachments/900617920126783502/1008389949223079956/attachment.gif?ex=66c752d2&is=66c60152&hm=168544adef33480982147e957565ee81a451133e9f671f9d9051918495373232&",
            "https://media.discordapp.net/attachments/745707366133006348/965773091600990208/sendo.gif?ex=66c73108&is=66c5df88&hm=56faf9a8b192e60449f080f5a6f7f376784ccc90bbe5e0ed75bb7ad84d03232a&",
            "https://tenor.com/view/lil-nas-x-pregnant-discord-gif-24975919",
            "https://media.discordapp.net/attachments/897319839251693618/996873887121948702/attachment-1-1.gif?ex=66c6f4e7&is=66c5a367&hm=4c523ecec803c3543b54fccfa219d6dc2b955de7b9852834d774548e5bfd3461&"
        ]


    @app_commands.command(name='join')
    async def join(self, interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message(f'{self.error()}')
            return
        channel = interaction.user.voice.channel
        await interaction.response.send_message(f'Connected to "{channel}"')
        await channel.connect()

    @app_commands.command(name="disconnect")
    async def dc(self, interaction: discord.Interaction):
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("Disconnected")
        else:
            await interaction.response.send_message(self.error())

    async def play_next(self, interaction: discord.Interaction):
        if queues[interaction.guild.id]:
            query = queues[interaction.guild.id].popleft()
            await self.play_song(interaction, query)


    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
            else:
                await interaction.response.send_message(self.error())
                return
        elif interaction.guild.voice_client.is_playing:
            interaction.guild.voice_client.stop()

        await self.play_song(interaction, query)


    async def play_song(self, interaction: discord.Interaction, query: str):
        loop = asyncio.get_event_loop()
        if query.startswith("https://www.youtube.com"):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f'ytsearch:{query}', download=False))

        if 'entries' in data:
            data = data['entries'][0]
        song = data['url']
        title = data['title']
        player = discord.FFmpegOpusAudio(song, **ffmpeg_options)
        interaction.guild.voice_client.play(
            player,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(interaction), self.bot.loop
            ),
        )
        await interaction.followup.send(f'Now playing: **{title}**')

    @app_commands.command(name='pause')
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client.is_playing:
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("Paused")

    @app_commands.command(name='resume')
    async def resume(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client.is_playing:
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("Resumed")

    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):
        interaction.guild.voice_client.stop()
        if interaction.guild.id in queues:
            del queues[interaction.guild.id]
        await interaction.response.send_message("Stopped")

    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client.is_playing:
            interaction.guild.voice_client.stop()

    @app_commands.command(name='queue')
    async def queue(self, interaction: discord.Interaction, query: str):
        if interaction.guild.id not in queues:
            queues[interaction.guild.id] = deque()
        queues[interaction.guild.id].append(query)
        await interaction.response.send_message(f"Added '{query}' to queue")

    @app_commands.command(name='clear')
    async def clear_queue(self, interaction: discord.Interaction):
        if interaction.guild.id in queues:
            queues[interaction.guild.id].clear()
            await interaction.response.send_message("Queue cleared")
        else:
            await interaction.response.send_message(self.error())

    @app_commands.command(name='view')
    async def view_queue(self, interaction: discord.Interaction):
        s = ""
        i = 0
        if interaction.guild.id in queues:
            for x in queues[interaction.guild.id]:
                if i == 5: break
                i += 1
                s += x + '\n'
            else:
                await interaction.response.send_message(embed=discord.Embed(title="Queue:", description=s))
                return
            await interaction.response.send_message(embed=discord.Embed(title="Queue(Top 5):", description=s))
        else:
            await interaction.response.send_message(self.error())


    def error(self):
        return self.gifs[random.randint(0, len(self.gifs) - 1)]

async def setup(bot) -> None:
    await bot.add_cog(music(bot))