import discord
from discord.ext import commands
import random
from helpers.cookieFuncs import *
from helpers.dbFuncs import update_from_local


def daily_random():
    rare = 0.40
    large = 0.10
    random.seed()
    if random.random() < large:
        return random.randint(500, 1000)
    elif random.random() < rare:
        return random.randint(200, 500)
    else:
        return random.randint(100, 200)


class Cookie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="update", hidden=True)
    async def update(self, ctx):
        await update_from_local()
        await ctx.send("Updated!")

    @commands.hybrid_command(name="daily", with_app_command=True, description="Daily claim for cookies.")
    async def daily_command(self, ctx):
        """
        Daily claim for cookies
        :param ctx:
        :return: None
        """
        await self.daily(ctx)
        
    async def daily(self, ctx):
        now = datetime.datetime.now()
        info = local_get_info(ctx.guild.id, ctx.author.id)
        saved_time = info['datetime']
        cookies = info['cookies']
        if saved_time is not None:
            saved_time = datetime.datetime.strptime(saved_time, '%Y-%m-%d %H:%M:%S.%f')
        if saved_time is None or now - saved_time >= datetime.timedelta(hours=20):
            add = daily_random()
            cookies += add
            await ctx.send(f"**+{add}** cookies added to your bank. You currently have **{cookies}** cookies total.")
            local_update_cookie(ctx.guild.id, ctx.author.id, cookies, True)
        else:
            time_left = (saved_time + datetime.timedelta(hours=20)) - now
            total_minute, second = divmod(time_left.seconds, 60)
            hour, minute = divmod(total_minute, 60)
            await ctx.send(f"Daily is not available yet. The next daily is in **{hour}h {minute}** min.")

    @commands.hybrid_command(name="top", with_app_command=True)
    async def top_command(self, ctx):
        """
        Shows the top 10 players with the most cookies
        :param ctx:
        :return: None
        """
        await self.top(ctx)

    async def top(self, ctx):
        info = local_get_all_info(ctx.guild.id)

        users = info['users']
        cookies = info['cookies']
        top = list(zip(*sorted(zip(cookies, users), reverse=True)))
        users = list(top[1])[:10]
        cookies = list(top[0])[:10]
        embed = discord.Embed(title="Leaderboard", description="Top users in the server with cookies!")
        str = ""
        for i in range(len(users)):
            str += f"**{i+1}.** <@{users[i]}>  -  **{cookies[i]}** cookies\n"

        embed.add_field(name="Top 10", value=str, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Cookie(bot))
