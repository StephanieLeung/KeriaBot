import asyncio

import random
from discord.ext import commands

from helpers.cookieFuncs import *


symbols = [":gem:", ":cherries:", ":hearts:", ":diamonds:", ":pudding:", ":kiwi:", ":tangerine:",
           ":watermelon:", ":rice_ball:", ":apple:", ":banana:", ":coin:", ":skull:", ":bubble_tea:", ":fire:",
           ":hibiscus:", ":ramen:", ":dango:", ":ice_cream:", ":blossom:"]


def get_random_symbol():
    random.shuffle(symbols)
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
    @commands.cooldown(1, 2, commands.BucketType.user)
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
        cookies = get_cookies(ctx.guild.id, ctx.author.id)
        if bet > cookies:
            await ctx.send(f"You don't have enough cookies to make this bet. ({cookies})", ephemeral=True)
            return

        edit_list = ["<a:slots:1270506170070863914>", "<a:slots_1:1270508755397902456>", "<a:slots_2:1270508773861232763>"]
        slot_result = [first_symbol, second_symbol, third_symbol]
        message = await ctx.send("<a:slots:1270506170070863914> <a:slots_1:1270508755397902456> <a:slots_2:1270508773861232763>")

        for i in range(3):
            await asyncio.sleep(0.6)
            edit_list[i] = slot_result[i]
            await message.edit(content=f"{edit_list[0]} {edit_list[1]} {edit_list[2]}")

        if first_symbol == second_symbol == third_symbol:
            if first_symbol == ":gem:":
                add = bet * 5000
                update_cookies(ctx.guild.id, ctx.author.id, add)
                update_msg = f"Jackpot! You earned **{bet * 5000}** cookies."
            else:
                add = bet * 1000
                update_cookies(ctx.guild.id, ctx.author.id, add)
                update_msg = f"Congratulations! You earned **{bet * 1000}** cookies."
        elif first_symbol == second_symbol or second_symbol == third_symbol or first_symbol == third_symbol:
            add = bet * 20
            update_cookies(ctx.guild.id, ctx.author.id, add)
            update_msg = f"Two out of three! You earned **{bet * 20}** cookies."
        else:
            add = -bet
            update_cookies(ctx.guild.id, ctx.author.id, add)
            update_msg = "No winnings..."
        await ctx.send(f"{ctx.author.mention}. " + update_msg + f" You now have **{get_cookies(ctx.guild.id, ctx.author.id)}** cookies in "
                       f"your bank.")

    @slots.error
    async def slots_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a bet number.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a valid number.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is on cooldown. Please wait **%.2f** seconds before retrying."
                           % error.retry_after, ephemeral=True)
        raise error


async def setup(bot):
    await bot.add_cog(Slots(bot))
