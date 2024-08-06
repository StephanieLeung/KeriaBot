import asyncio

import discord
from discord.ext import commands
from discord.ui import Button, View
import random
from cookie import local_get_info, local_update_cookie

suits = ["spades", "hearts", "diamonds", "clubs"]


def make_cards(cards):
    cards.clear()
    for i in range(4):
        suit = suits[i]
        for j in range(13):
            if j == 0:
                cards.append(Card(suit, "A"))
            elif j == 10:
                cards.append(Card(suit, "J"))
            elif j == 11:
                cards.append(Card(suit, "Q"))
            elif j == 12:
                cards.append(Card(suit, "K"))
            else:
                cards.append(Card(suit, j+1))
    random.shuffle(cards)
    return cards


def deal_cards(cards, num, hand=None):
    if hand is None:
        hand = []
    for i in range(num):
        card = random.choice(cards)
        cards.remove(card)
        hand.append(card)
    return hand


def calc_score(hand):
    hand_values = []
    for card in hand:
        hand_values.append(card.get_value())

    for i in range(len(hand_values)):
        if hand_values[i] == 0:
            if sum(hand_values) + 11 > 21:
                hand_values.pop(i)
                hand_values.insert(i, 1)
            else:
                hand_values.pop(i)
                hand_values.insert(i, 11)
    return sum(hand_values)


class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def __str__(self):
        return f":{self.suit}: {self.value}"

    def get_value(self):
        try:
            value = int(self.value)
            return value
        except ValueError:
            if self.value == "A":
                return 0
            else:
                return 10


def handle_dealer(cards, dealer_hand, loop=False):
    dscore = calc_score(dealer_hand)
    if dscore < 16:
        if loop:
            return handle_dealer(cards, deal_cards(cards, 1, dealer_hand))
        else:
            return deal_cards(cards, 1, dealer_hand)
    else:
        return dealer_hand


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
    elif dscore == 21 or dscore > pscore:
        if dscore == 21:
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
    for i in range(len(players)):
        pscore.append(calc_score(hands[i]))

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


def display_bjack_hand(player, player_hand, dealer):
    embed = discord.Embed(title="Blackjack", description="Press the hit button to get another card, pass to end your "
                                                         "turn.")
    embed.add_field(name=player,
                    value=" ".join(str(x) for x in player_hand) + f"\n**Score**: {calc_score(player_hand)}")
    embed.add_field(name="Dealer", value=str(dealer[0]) + f"`   `\n**Score**: {calc_score([dealer[0]])}")
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
        cards = []
        cards = make_cards(cards)
        player_hand = deal_cards(cards, 2)
        dealer_hand = deal_cards(cards, 2)
        if bet == 0:
            return await ctx.send("You need to bet more than 0 cookies.", ephemeral=True)
        else:
            info = local_get_info(ctx.guild.id, ctx.author.id)
            if info['cookies'] < bet:
                return await ctx.send(f"You don't have enough cookies. (**{info['cookies']}**)")
        await self.handle_ongoing_bjack(ctx, bet, cards, player_hand, dealer_hand, info['cookies'])

    @bjack.error
    async def bjack_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Incorrect arguments entered. Please enter a bet number.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a number as bet.")
        else:
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
            return str(reaction) == "✅"

        async def add_user():
            start = False
            while not start:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=10)
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
            cards = make_cards([])
            hands = []
            last = []
            for player in players:
                hands.append(deal_cards(cards, 2))
                last.append(False)
            dealer = deal_cards(cards, 2)
            await self.handle_ongoing_mbjack(ctx, make_cards([]), players, hands, dealer, last)

    async def handle_ongoing_mbjack(self, ctx, cards, players, player_hands, dealer, last):
        pscores = []
        embed = discord.Embed(title="Blackjack", description="Click the start button to start playing!")

        for i in range(len(players)):
            pscore = calc_score(player_hands[i])
            pscores.append(pscore)

        start_view = View()
        start_button = Button(label="Start", style=discord.ButtonStyle.blurple)
        start_view.add_item(start_button)
        game_view = View()
        hit_button = Button(label="Hit", style=discord.ButtonStyle.green)
        pass_button = Button(label="Pass", style=discord.ButtonStyle.grey)
        game_view.add_item(hit_button)
        game_view.add_item(pass_button)

        def check(last):
            if all(x is True for x in last):
                return True
            return False

        async def finish():
            start_button.callback = None
            hit_button.callback = None
            pass_button.callback = None
            await self.after_mbjack(ctx, players, player_hands, pscores, dealer)

        async def hit_button_callback(interaction: discord.Interaction):
            i = players.index(interaction.user)
            player_hands[i] = deal_cards(cards, 1, player_hands[i])
            new_score = calc_score(player_hands[i])
            pscores[i] = new_score
            embed = display_bjack_hand(players[i].global_name, player_hands[i], dealer)
            if new_score >= 21:
                last[i] = True
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await ctx.send(content=f"{players[i].mention} is finished.")
                if check(last):
                    await finish()
                return
            await interaction.response.send_message(embed=embed, view=game_view, ephemeral=True)

        async def pass_button_callback(interaction: discord.Interaction):
            i = players.index(interaction.user)
            last[i] = True

            await interaction.response.send_message(content=f"{players[i].mention} is finished.")
            if check(last):
                await finish()

        hit_button.callback = hit_button_callback
        pass_button.callback = pass_button_callback

        async def start_button_callback(interaction: discord.Interaction):
            if interaction.user not in players:
                await interaction.response.send_message(content=f"You are not part of this game.", ephemeral=True)
                return
            i = players.index(interaction.user)
            embed = display_bjack_hand(players[i].global_name, player_hands[i], dealer)
            if calc_score(player_hands[i]) == 21:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await ctx.send(content=f"{players[i].mention} is finished.")
                last[i] = True
                return
            await interaction.response.send_message(embed=embed, view=game_view, ephemeral=True)

        start_button.callback = start_button_callback

        dealer = handle_dealer(cards, dealer, loop=True)
        await ctx.send(embed=embed, view=start_view)

    async def after_mbjack(self, ctx, players, player_hands, pscore, dealer):
        await ctx.send("All players are ready.")
        dscore = calc_score(dealer)
        embed = discord.Embed(title="Blackjack", description="Displaying final scores for all players and dealer.")
        for i in range(len(players)):
            embed.add_field(name=players[i].global_name, value=" ".join(str(x) for x in player_hands[i]) + f"\n**Score**: {pscore[i]}", inline=False)
        embed.add_field(name="Dealer", value=" ".join(str(x) for x in dealer) + f"\n**Score**: {dscore}")
        await ctx.send(embed=embed)
        await handle_mbjack_scores(ctx, players, player_hands, dscore)
        return

    async def handle_ongoing_bjack(self, ctx, bet, cards, player, dealer, cookies, last=False):
        pscore = calc_score(player)

        embed = discord.Embed(title="Blackjack", description="Type h/hit to get another card, p/pass to end your turn.")
        embed.add_field(name=ctx.author.global_name, value=" ".join(str(x) for x in player) + f"\n**Score**: {pscore}")
        embed.add_field(name="Dealer", value=str(dealer[0]) + f"`   `\n**Score**: {calc_score([dealer[0]])}")
        message = await ctx.send(embed=embed)

        if pscore >= 21 or last:
            dealer = handle_dealer(cards, dealer, loop=True)
            dscore = calc_score(dealer)

            embed.remove_field(1)
            embed.add_field(name="Dealer", value=" ".join(str(x) for x in dealer) + f"\n**Score**: {dscore}")
            await message.edit(embed=embed)
            return await handle_bjack_scores(ctx, bet, pscore, dscore, cookies)

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
                last = False
                if content == "exit":
                    await ctx.send("Exited Blackjack game. No cookies have been taken.")
                    return
                elif content == "h" or content == "hit":
                    player = deal_cards(cards, 1, player)
                else:
                    last = True
                dealer = handle_dealer(cards, dealer)
                await self.handle_ongoing_bjack(ctx, bet, cards, player, dealer, cookies, last)
                not_sent = False


async def setup(bot):
    await bot.add_cog(Blackjack(bot))

