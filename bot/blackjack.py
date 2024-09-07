import asyncio

import discord
from discord.ext import commands
from discord.ui import Button, View
from cookie import local_get_info, local_update_cookie

from cardgame import Deck, Player

suits = ["spades", "hearts", "diamonds", "clubs"]


def handle_dealer(cards: Deck, dealer: Player, loop=False):
    if dealer.score < 16 and len(dealer) < 5:
        if loop:
            dealer.draw_card(cards)
            return handle_dealer(cards, dealer, loop=True)
        else:
            return dealer.draw_card(cards)


async def handle_bjack_scores(ctx, bet, pscore, dscore, cookies):
    p_win = "Player wins!"
    d_win = "Dealer wins!"
    if pscore > 21:
        cookies -= bet
        await ctx.send("Bust! Player loses.")
    elif pscore == 21 or pscore > dscore:
        if pscore == 21:
            p_win = "Blackjack. " + p_win
            cookies += bet
        cookies += bet
        await ctx.send(p_win)
    elif dscore > 21:
        cookies += bet
        await ctx.send("Bust! Dealer loses.")
    elif dscore == pscore:
        await ctx.send("Tie.")
    elif dscore == 21:
        d_win = "Blackjack. " + d_win
        cookies -= bet
        await ctx.send(d_win)
    else:
        cookies -= bet
        await ctx.send(d_win)
    if cookies < 0:
        cookies = 0
    local_update_cookie(ctx.guild.id, ctx.author.id, cookies)
    await ctx.send(f"You now have **{cookies}** cookies in your bank.")
    return


async def handle_mbjack_scores(ctx, players, hands, dscore):
    pscore = []
    for i in range(len(hands)):
        pscore.append(hands[i].score)

    highest_val = 0
    index = None
    multi = []
    for i in range(len(pscore)):
        if highest_val < pscore[i] <= 21:
            highest_val = pscore[i]
            index = i

    multi.append(index)
    for i in range(len(pscore)):
        if highest_val == pscore[i] and i != index:
            multi.append(i)

    if highest_val == 0 and dscore < 21:
        await ctx.send("Dealer wins!")
    elif highest_val == 0 and dscore > 21:
        await ctx.send("Bust! Everyone loses.")
    elif highest_val == dscore:
        win = " ".join(players[x].mention for x in multi)
        await ctx.send(f"{win} tied with dealer!")
    elif highest_val < dscore <= 21:
        await ctx.send("Dealer won!")
    else:
        win = " ".join(players[x].mention for x in multi)
        await ctx.send(f"{win} won!")


def display_bjack_hand(player, player_hand: Player, dealer: Player):
    embed = discord.Embed(title="Blackjack", description="Press the hit button to get another card, pass to end your "
                                                         "turn.")
    embed.add_field(name=player,
                    value=" ".join(str(x) for x in player_hand.get_cards()) + f"\n**Score**: {player_hand.score}")
    embed.add_field(name="Dealer", value=str(dealer.first_card()) + f"`   `\n**Score**: {dealer.first_score()}")
    return embed


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="bjack")
    async def bjack(self, ctx, *, bet: int):
        """
        Classic Blackjack game with one player.
        :param ctx:
        :param bet: Amount of cookies to bet
        :return:
        """
        cards = Deck()
        cards.shuffle()
        player = Player(deck=cards, init_cards=2)
        dealer = Player(deck=cards, init_cards=2)

        if bet == 0:
            return await ctx.send("You need to bet more than 0 cookies.", ephemeral=True)
        else:
            info = local_get_info(ctx.guild.id, ctx.author.id)
            if info['cookies'] < bet:
                return await ctx.send(f"You don't have enough cookies. (**{info['cookies']}**)")
        await self.handle_ongoing_bjack(ctx, bet, cards, player, dealer, info['cookies'])

    @bjack.error
    async def bjack_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Incorrect arguments entered. Please enter a bet number.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a number as bet.")
        else:
            print(error)
            await ctx.send("Oops. Something went wrong. Try again later.")

    @commands.hybrid_command(name="multibjack", aliases=['mbjack'])
    async def multi_bjack(self, ctx):
        """
        Classic Blackjack game with max. 5 players
        :param ctx:
        :return: None
        """
        embed = discord.Embed(title="Blackjack (Max. 5 players)", description="React to the message if you want to "
                                                                              "join the game. No bets will be taken "
                                                                              "for the multiplayer version. The goal "
                                                                              "is to get as close to 21 as possible "
                                                                              "without going over.")
        value = 10
        embed.add_field(name="Timer", value=f"{value} seconds left")
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        players = []

        def check(reaction, user):
            return str(reaction) == "✅" and reaction.message == message

        async def add_user():
            start = False
            while not start:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=10)
                    if not user.bot:
                        if user not in players:
                            players.append(user)
                            await ctx.send(f"{user.mention} has been added to game.")
                        else:
                            players.remove(user)
                            await ctx.send(f"{user.mention} has been removed from the game.")

                except asyncio.TimeoutError:
                    if len(players) >= 1:
                        return True
                    else:
                        await ctx.send("Timed out waiting for someone to join. :frowning:")
                        return False
                else:
                    if len(players) == 5:
                        await ctx.send("Maximum players reached.")
                        return True

        async def timer(value):
            while value != 0:
                await asyncio.sleep(1)
                value -= 1
                embed.remove_field(0)
                if value == 0:
                    embed.add_field(name="Timer", value="Timer is up.")
                else:
                    embed.add_field(name="Timer", value=f"{value} seconds left")
                await message.edit(embed=embed)

        ret1, ret2 = await asyncio.gather(add_user(), timer(value))
        if ret1:
            await ctx.send("Starting game now...")
            cards = Deck()
            cards.shuffle()
            hands = []
            for _ in players:
                hands.append(Player(cards, 2))
            dealer = Player(cards, 2)
            await self.handle_ongoing_mbjack(ctx, cards, players, hands, dealer)

    async def handle_ongoing_mbjack(self, ctx, cards: Deck, player_names, players: list[Player], dealer: Player):
        embed = discord.Embed(title="Blackjack", description="Click the start button to start playing!")

        start_view = View()
        start_button = Button(label="Start", style=discord.ButtonStyle.blurple)
        start_view.add_item(start_button)
        game_view = View()
        hit_button = Button(label="Hit", style=discord.ButtonStyle.green)
        pass_button = Button(label="Pass", style=discord.ButtonStyle.grey)
        game_view.add_item(hit_button)
        game_view.add_item(pass_button)

        def check():
            return all(player.is_done() is True for player in players)

        async def finish():
            start_button.callback = None
            hit_button.callback = None
            pass_button.callback = None
            await self.after_mbjack(ctx, player_names, players, dealer)


        async def hit_button_callback(interaction: discord.Interaction):
            i = player_names.index(interaction.user)
            players[i].draw_card(cards)
            embed = display_bjack_hand(player_names[i].global_name, players[i], dealer)
            if players[i].score >= 21:
                players[i].done()
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await ctx.send(content=f"{player_names[i].mention} is finished.")
                if check():
                    await finish()
                return
            await interaction.response.send_message(embed=embed, view=game_view, ephemeral=True)

        async def pass_button_callback(interaction: discord.Interaction):
            i = player_names.index(interaction.user)
            players[i].done()

            await interaction.response.send_message(content=f"{player_names[i].mention} is finished.")
            if check():
                await finish()

        hit_button.callback = hit_button_callback
        pass_button.callback = pass_button_callback

        async def start_button_callback(interaction: discord.Interaction):
            if interaction.user not in player_names:
                await interaction.response.send_message(content=f"You are not part of this game.", ephemeral=True)
                return
            i = player_names.index(interaction.user)
            embed = display_bjack_hand(player_names[i].global_name, players[i], dealer)

            if players[i].score == 21:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await ctx.send(content=f"{player_names[i].mention} is finished.")
                players[i].done()
                if check():
                    await finish()
                return

            await interaction.response.send_message(embed=embed, view=game_view, ephemeral=True)

        start_button.callback = start_button_callback

        handle_dealer(cards, dealer, loop=True)
        await ctx.send(embed=embed, view=start_view)

    async def after_mbjack(self, ctx, player_names, players, dealer):
        await ctx.send("All players are ready.")
        embed = discord.Embed(title="Blackjack", description="Displaying final scores for all players and dealer.")
        for i in range(len(player_names)):
            embed.add_field(name=player_names[i].global_name,
                            value=" ".join(str(x) for x in players[i].get_cards()) +
                                  f"\n**Score**: {players[i].score}", inline=False)
        embed.add_field(name="Dealer", value=" ".join(str(x) for x in dealer.get_cards()) +
                                             f"\n**Score**: {dealer.score}")
        await ctx.send(embed=embed)
        await handle_mbjack_scores(ctx, player_names, players, dealer.score)
        return

    async def handle_ongoing_bjack(self, ctx, bet, cards: Deck, player: Player, dealer: Player, cookies):
        embed = display_bjack_hand(ctx.author.global_name, player, dealer)
        message = await ctx.send(embed=embed)

        if player.score >= 21 or player.is_done():
            handle_dealer(cards, dealer, loop=True)

            embed.remove_field(1)
            embed.add_field(name="Dealer", value=" ".join(str(x) for x in dealer.get_cards()) +
                                                 f"\n**Score**: {dealer.score}")
            await message.edit(embed=embed)
            return await handle_bjack_scores(ctx, bet, player.score, dealer.score, cookies)

        not_sent = True

        def check(m):
            return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

        while not_sent:
            message = await self.bot.wait_for("message", check=check)

            content = message.content.lower()
            if content != "h" and content != "p" and content != "hit" and content != "pass" and content != "exit":
                await ctx.send("Please enter h/hit or p/pass. Exit if you want to quit the game")
                continue
            else:
                if content == "exit":
                    await ctx.send("Exited Blackjack game. No cookies have been taken.")
                    return
                elif content == "h" or content == "hit":
                    player.draw_card(cards)
                else:
                    player.done()
                await self.handle_ongoing_bjack(ctx, bet, cards, player, dealer, cookies)
                not_sent = False


async def setup(bot):
    await bot.add_cog(Blackjack(bot))
