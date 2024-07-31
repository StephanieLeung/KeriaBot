import json

import aiohttp
import discord
from discord.ext import commands
import datetime
import random

import requests

main_url = "https://keriabot.onrender.com/"
test_url = "http://localhost:8000/"


async def get_info(guild_id, user_id):
    url = test_url + f"user/{guild_id}/{user_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                info = await r.json()
        await session.close()
    return info


async def update_cookie(guild_id, user_id, cookie, daily=False):
    url = test_url + f"user/update"
    data = {"guild_id": guild_id, "user_id": user_id, "cookies": cookie, "daily": daily}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as r:
            pass
        await session.close()


def daily_random():
    normal = 0.60
    rare = 0.40
    large = 0.10
    if random.random() < large:
        return random.randint(500, 1000)
    elif random.random() < rare:
        return random.randint(200, 500)
    elif random.random() < normal:
        return random.randint(100, 200)


class Cookie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="daily", with_app_command=True, description="Daily claim for cookies.")
    async def daily_command(self, ctx):
        message = await ctx.send("Getting your cookies...")
        await self.daily(ctx, message)

    async def daily(self, ctx, message):
        now = datetime.datetime.now()
        info = await get_info(ctx.guild.id, ctx.author.id)
        saved_time = info['datetime']
        cookies = info['cookies']
        if saved_time is not None:
            saved_time = datetime.datetime.strptime(saved_time, '%Y-%m-%d %H:%M:%S.%f')
        if saved_time is None or now - saved_time >= datetime.timedelta(hours=20):
            add = daily_random()
            cookies += add
            await message.edit(content=f"**+{add}** cookies added to your bank. You currently have **{cookies}** cookies total.")
            await update_cookie(ctx.guild.id, ctx.author.id, cookies, True)
        else:
            time_left = (saved_time + datetime.timedelta(hours=20)) - now
            total_minute, second = divmod(time_left.seconds, 60)
            hour, minute = divmod(total_minute, 60)
            await message.edit(content=f"Daily is not available yet. The next daily is in **{hour}h {minute}** min.")

    @commands.hybrid_command(name="top", with_app_command=True)
    async def top_command(self, ctx):
        message = await ctx.send("Calculating...")
        await self.top(ctx, message)

    async def top(self, ctx, message):
        url = test_url + f"guild/allusers/{ctx.guild.id}"
        data = requests.get(url)
        if data.ok:
            info = json.loads(data.content)
        else:
            raise Exception()

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
        await message.edit(content="", embed=embed)


async def setup(bot):
    await bot.add_cog(Cookie(bot))
