import discord
from discord.ext import commands
from discord.ui import Button, View

from exceptions.LimitReached import LimitReachedError
from exceptions.NotEnoughCookies import NotEnoughCookiesError
from helpers.bankFuncs import *


def create_account(guild_id, user_id):
    bank_info = get_bank_info(guild_id, user_id)
    return Account(bank_info['cookies'], bank_info['loan'], bank_info['payment_date'], bank_info['due'])


class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="bank")
    async def bank(self, ctx):
        """
        Displays your bank account
        :param ctx:
        :return:
        """
        account = create_account(ctx.guild.id, ctx.author.id)
        embed = discord.Embed(title="Bank", description="Displaying account balance and any loans or outstanding payments.")
        embed.add_field(name="Balance", value=f"**{str(account.cookies)}** cookies", inline=False)
        embed.add_field(name="Monthly Loans (15000 Limit)", value=f"**{str(account.loan)}** cookies", inline=False)
        if account.due > 0:
            year = account.payment_date.year
            month = account.payment_date.month
            day = account.payment_date.day
            embed.add_field(name="Payment date", value=f"{year}-{month}-{day}", inline=False)

            embed.add_field(name="Due", value=f"**{account.due}** cookies", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="loan")
    async def loan(self, ctx, amount: int):
        """
        Trys to loan amount from the bank
        :param ctx:
        :param amount:
        :return:
        """
        account = create_account(ctx.guild.id, ctx.author.id)
        try:
            account.make_loan(amount)
            update_bank_info(ctx.guild.id, ctx.author.id, account)
            await ctx.send(f"Your loan has been approved. **{amount}** cookies have been added to your balance.")
        except LimitReachedError:
            await ctx.send("The loan amount you're trying to borrow is over the limit. The limit is currently "
                           "**15000** cookies.")

    @loan.error
    async def loan_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing an argument. Please enter the amount you want to loan.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a number as the loan amount.")
        else:
            await ctx.send("Oops. Something went wrong. Try again later.")

    @commands.command(name="payment")
    async def payment(self, ctx, amount: int):
        account = create_account(ctx.guild.id, ctx.author.id)
        try:
            account.pay_due(amount)
            update_bank_info(ctx.guild.id, ctx.author.id, account)
            await ctx.send(f"Payment has been processed. You now have **{account.due}** cookies due by the payment date.")
        except NotEnoughCookiesError:
            await ctx.send("You don't have enough cookies to pay back this amount.")

    @payment.error
    async def payment_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing an argument. Please enter the amount you want to pay back.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a number as the amount to pay back.")
        else:
            await ctx.send("Oops. Something went wrong. Try again later.")


async def setup(bot):
    await bot.add_cog(Bank(bot))
