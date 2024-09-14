import asyncio
import random
import discord
import gifs
from discord import app_commands
from discord.ext import commands
import yt_dlp as youtube_dl
from collections import deque

import gifs

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
        if query.startswith("https://www.youtube.com") or query.startswith("https://youtu.be/"):
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
        if interaction.guild.id not in queues or not queues[interaction.guild.id]:
            interaction.response.send_message(self.error())
        if interaction.guild.voice_client.is_playing:
            interaction.guild.voice_client.stop()

    @app_commands.command(name='queue')
    async def queue(self, interaction: discord.Interaction, query: str):
        if interaction.guild.id not in queues:
            queues[interaction.guild.id] = deque()
            await self.play_song(interaction, query)
            return
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
        return gifs.GIF.gifs[random.randint(0, len(gifs.GIF.gifs) - 1)]

async def setup(bot) -> None:
    await bot.add_cog(music(bot))