import discord
import random
from discord.ext import commands

from helpers.cookieFuncs import *


def get_word(words):
    return random.choice(words)


def all_words(filename):
    with open(filename, "r") as f:
        words = f.read().splitlines()
    return words


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.words = all_words("wordle.txt")
        self.valid_words = all_words("valid_words.txt")

    @commands.hybrid_command(name="wordle", with_app_command=True, description="Classic Wordle Game.")
    async def wordle_command(self, ctx):
        word = get_word(self.words).lower()
        lines = []
        for i in range(6):
            lines.append(["⬛", "⬛", "⬛", "⬛", "⬛"])

        word = list(word)
        await self.handle_ongoing_wordle(ctx, word, lines)

    async def handle_ongoing_wordle(self, ctx, word, lines):
        embed = discord.Embed(title="Wordle", description="You have 6 tries to guess the word!")
        print_lines = []
        used_alphabet = []

        for i in range(6):
            print_lines.append("".join(lines[i]))

        embed.add_field(name="Tries", value="\n".join(print_lines), inline=False)
        embed.add_field(name="Already used", value=", ".join(used_alphabet), inline=False)

        msg = await ctx.send(embed=embed)
        await ctx.send("Type your guess in the chat.")

        guesses = ["", "", "", "", "", ""]
        cookie = 0
        guess = 0
        win = False

        def check(m):
            return m.author == ctx.author and m.channel.id == ctx.channel.id

        while guess < 6:
            message = await self.bot.wait_for("message", check=check)
            content = message.content.lower()
            if len(content) != 5:
                await ctx.send("Please enter a 5-letter word.")
                continue
            elif content not in self.valid_words:
                await ctx.send(f"`{content.capitalize()}` is not a valid word. Try again.", ephemeral=True)
                continue
            else:
                guesses[guess] = content
                chars = list(content)
                for i in range(5):
                    if word[i] == chars[i]:
                        lines[guess][i] = ":green_square:"
                    elif chars[i] in word:
                        lines[guess][i] = ":yellow_square:"
                    else:
                        if chars[i].upper() not in used_alphabet:
                            used_alphabet.append(chars[i].upper())

                guess += 1
                embed.remove_field(0)
                embed.remove_field(0)
                print_lines = []
                used_alphabet.sort()
                for i in range(6):
                    print_lines.append("".join(lines[i]) + f" - {guesses[i]}")
                embed.add_field(name="Tries", value="\n".join(print_lines), inline=False)
                embed.add_field(name="Already Used", value=", ".join(used_alphabet), inline=False)
                await msg.edit(embed=embed)
                if content == "".join(word):
                    win = True
                    break

        embed.set_footer(text=f"Game ended. Guesses: {guess}/6")
        await msg.edit(embed=embed)
        await ctx.send(f"The word was `{"".join(word).capitalize()}`.")
        if win:
            cookie += 70 - (guess * 10)

        if cookie != 0:
            cookies = get_cookies(ctx.guild.id, ctx.author.id)
            cookies += cookie
            await ctx.send(f"Congrats! You earned **{cookie}** cookies. You now have **{cookies}** cookies in your bank.")
            local_update_cookie(ctx.guild.id, ctx.author.id, cookies + cookie)


async def setup(bot):
    await bot.add_cog(Wordle(bot))

