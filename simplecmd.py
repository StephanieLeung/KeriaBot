from discord.ext import commands
import discord
from random import randint


class SimpleCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if "hi" in message.clean_content or "hello" in message.clean_content:
                await message.channel.send("hello")
                await self.bot.process_commands(message)

    @commands.command()
    async def roll(self, ctx):
        embed = discord.Embed(description=randint(0, 100), color=discord.Color.pink())
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SimpleCmd(bot))
