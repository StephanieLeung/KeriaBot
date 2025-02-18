import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord
import logging

from helpers.dbFuncs import *
from helpers.restrictUsers import restricted_users

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
OWNER = os.getenv('OWNER')

EXTENSIONS = ("simplecmd", "music", "blackjack", "cookie", "wordle", "slots", "bank", "study")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='mew ', intents=intents)

logging.basicConfig(level=logging.INFO)


@tasks.loop(hours=1)
async def update_to_db_thread():
    await update_from_local()
    logging.info("All data updated in MongoDB.")


@bot.check
def check_for_restricted(ctx):
    return not restricted_users.is_restricted(ctx.author.id)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(f"Sorry, you don't have permission to use this command right now.",
                       ephemeral=True, delete_after=20)
    else:
        return

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

    logging.info(f'{bot.user.name} has connected to Discord!')


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
        try:
            for extension in EXTENSIONS:
                await bot.reload_extension(extension)
            await ctx.send("Reloaded all extensions.")
        except:
            await ctx.send("Something went wrong. Please check the extensions.")
    else:
        await ctx.send(f"You have to be the owner of this app to run this command.")


async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    bot.run(TOKEN)
