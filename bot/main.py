import os
from dotenv import load_dotenv
from discord.ext import commands
import asyncio
from simplecmd import *
import discord

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

EXTENSIONS = ("simplecmd", "music")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='mew ', intents=intents)


@bot.event
async def setup_hook() -> None:
    for extension in EXTENSIONS:
        await bot.load_extension(extension)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.CustomActivity(name='CHKCHKBOOM'))
    print(f'{bot.user.name} has connected to Discord!')


async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    bot.run(TOKEN)


