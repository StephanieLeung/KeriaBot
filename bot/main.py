import datetime
import os
import sqlite3

import aiohttp
from dotenv import load_dotenv
from discord.ext import commands, tasks
from pathlib import Path
from simplecmd import *
import discord
from cookie import update_from_local

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
OWNER = os.getenv('OWNER')

EXTENSIONS = ("simplecmd", "music", "blackjack", "cookie", "wordle", "slots")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='mew ', intents=intents)


async def update_db():
    # checks if database exists
    if not (Path.cwd() / "bot.db").exists():
        db = sqlite3.connect("bot.db")
        cursor = db.cursor()
        cursor.execute('''
                CREATE TABLE users (
                    guild_id INTEGER NOT NULL, 
                    user_id INTEGER NOT NULL, 
                    cookies INTEGER , 
                    datetime TEXT, 
                    PRIMARY KEY (guild_id, user_id)
                );
            ''')
        db.commit()
    else:
        db = sqlite3.connect("bot.db")
        cursor = db.cursor()
        cursor.execute('''
            DELETE FROM users;   
        ''')
        db.commit()

    url = "http://localhost:8000/allusers"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                info = await r.json()
        await session.close()
    info = info['all data']
    for doc in info:
        cursor.execute('''
            INSERT INTO users (guild_id, user_id, cookies, datetime)
            VALUES (:guild_id, :user_id, :cookies, :datetime);
        ''', doc)
    db.commit()
    cursor.close()
    db.close()


@tasks.loop(minutes=30)
async def update_to_db_thread():
    await update_from_local()
    print("Updated MongoDB!")


@bot.event
async def setup_hook() -> None:
    for extension in EXTENSIONS:
        await bot.load_extension(extension)


@bot.event
async def on_ready():
    await update_db()
    await bot.change_presence(status=discord.Status.idle, activity=discord.CustomActivity(name='CHKCHKBOOM'))
    if not update_to_db_thread.is_running():
        update_to_db_thread.start()
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='ssync', hidden=True)
async def server_sync(ctx):
    if int(ctx.author.id) == int(OWNER):
        # bot.tree.copy_global_to(guild=ctx.guild)
        # bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send("Synced to guild.")
    else:
        await ctx.send(f"You have to be the owner of this app to run this command.")


@bot.command(name='allsync', hidden=True)
async def global_sync(ctx):
    if int(ctx.author.id) == int(OWNER):
        await bot.tree.sync()
        await ctx.send("Synced all servers.")
    else:
        await ctx.send(f"You have to be the owner of this app to run this command.")


@bot.command(name='reload', hidden=True)
async def reload(ctx):
    if int(ctx.author.id) == int(OWNER):
        for extension in EXTENSIONS:
            await bot.reload_extension(extension)
        await ctx.send("Reloaded all extensions.")
    else:
        await ctx.send(f"You have to be the owner of this app to run this command.")


async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    bot.run(TOKEN)


