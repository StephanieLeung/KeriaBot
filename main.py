from discord.ext import commands
import asyncio
from simplecmd import *
from key import TOKEN
import discord

EXTENSIONS = ("simplecmd", "music" )
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
    print(f'{bot.user.name} has connected to Discord!')


async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    '''asyncio.run(main())'''
    bot.run(TOKEN)


