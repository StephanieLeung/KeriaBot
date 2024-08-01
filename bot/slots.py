import asyncio

import discord
import random
from discord.ext import commands
from cookie import local_get_info, local_update_cookie

symbols = [":seven:", ":cherries:", ":hearts:", ":diamonds:", ":pudding:", ":kiwi:", ":tangerine:",
           ":watermelon:", ":rice_ball:", ":apple:", ":banana:", ":coin:", ":skull:", ":bubble_tea:", ":fire:",
           ":hibiscus:", ":ramen:", ":dango:", ":ice_cream:", ":blossom:"]


def get_random_symbol():
    return random.choice(symbols)


def next_symbol(val: int):
    if val + 1 == len(symbols): return 0
    return val + 1


def check_equal(val, symbol):
    if symbols[val] == symbol:
        return val
    return next_symbol(val)


class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        random.seed()

    @commands.hybrid_command(name="slots")
    async def slots(self, ctx, bet: int):
        """
        Simple slots machine.
        :param ctx:
        :param bet: Amount of cookies to bet
        :return:
        """
        first_symbol = get_random_symbol()
        second_symbol = get_random_symbol()
        third_symbol = get_random_symbol()
        print(first_symbol, second_symbol, third_symbol)
        title = await ctx.send("Setting up the slots...")
        info = local_get_info(ctx.guild.id, ctx.author.id)
        cookies = info['cookies']

        first = random.randint(0, 19)
        second = random.randint(0, 19)
        third = random.randint(0, 19)
        await title.edit(content="**Slots start!**")
        message = await ctx.send("****")
        while symbols[first] != first_symbol or symbols[second] != second_symbol or symbols[third] != third_symbol:
            first = check_equal(first, first_symbol)
            second = check_equal(second, second_symbol)
            third = check_equal(third, third_symbol)
            await message.edit(content=f"{symbols[first-1]} {symbols[second-1]} {symbols[third-1]}\n"
                                       f"{symbols[first]} {symbols[second]} {symbols[third]} **<<**\n"
                                       f"{symbols[next_symbol(first)]} {symbols[next_symbol(second)]} {symbols[next_symbol(third)]}")
            await asyncio.sleep(1)

        if first_symbol == second_symbol == third_symbol:
            if first_symbol == ":seven:":
                cookies += bet * 1000
                await ctx.send("Jackpot!")
            else:
                await ctx.send("Congratulations!")
                cookies += bet * 500
        elif first_symbol == second_symbol or second_symbol == third_symbol or first_symbol == third_symbol:
            await ctx.send("Two out of three!")
            cookies += bet * 100
        else:
            await ctx.send("No winnings...")
            cookies -= bet
        await ctx.send(f"{ctx.author.mention}. You now have **{cookies}** cookies in your bank.")
        local_update_cookie(ctx.guild.id, ctx.author.id, cookies)


async def setup(bot):
    await bot.add_cog(Slots(bot))
