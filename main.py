import discord
import asyncio
import Music
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

load_dotenv()

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="b.", intents=intents)
intents.message_content = True


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})\n--------')

@bot.tree.command(name="sync")
async def sync(interaction: discord.Integration):
    await interaction.response.send_message("Synced!")
    await bot.tree.sync()


async def setup():
    await bot.add_cog(Music.music(bot))

asyncio.run(setup())

bot.run(os.getenv("DISCORD_TOKEN"))
