import asyncio
import random
from threading import Thread

import aiohttp
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, FFmpegOpusAudio
import spotipy
from discord.ui import View, Button
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

from exceptions.NoSongFound import NoSongFoundError

bot_voice = {}
main_url = "https://keriabot.onrender.com/"
# test_url = "http://localhost:8000/"
test_url = "http://host.docker.internal:8000/"

disc_gif = ("https://media0.giphy.com/media/LwBTamVefKJxmYwDba/giphy.gif?cid"
            "=6c09b952g0ljvqtoads16f77bd3hpv1cwibrnm3b3pmzyifz&rid=giphy.gif&ct=s")
stop_thread = {"done": False}

load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)


class MusicObj:
    def __init__(self, url, title):
        self.url = url
        self.title = title

    def make_audio_source(self):
        if self.url == "../KeriaBot/Animal Crossing  Nabi Bobet Tau.mp3":
            source = FFmpegPCMAudio(self.url)
        else:
            source = FFmpegOpusAudio(self.url,
                                     before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss "
                                                    "00:00:00.00",
                                     options="-vn")
        return source


class BotVoiceHandler:
    def __init__(self, channel):
        self.now_playing = None
        self.voice = None
        self.channel = channel
        self.songs = []
        self.loop = False
        self.loop_all = False

    def queue(self, song: MusicObj):
        self.songs.append(song)

    def remove_song(self, index):
        return self.songs.pop(index)

    def dequeue(self):
        if self.songs:
            song = self.songs.pop(0)
            self.now_playing = song
            return song
        else:
            self.now_playing = None
            return None

    def clear_queue(self):
        self.songs = []

    def shuffle_queue(self):
        random.shuffle(self.songs)

    def set_loop_all(self):
        self.loop_all = not self.loop_all
        self.loop = False

    def set_loop(self):
        self.loop = not self.loop
        self.loop_all = False


async def search_youtube(search):
    search = parse_search(search)
    if "http" in search and "youtube" in search and "playlist" in search:
        search = search.partition("=")[2]
        url = test_url + f"music-playlist/{search}"
    elif "http" in search and "youtube" in search:
        search = search.partition("=")[2]
        url = test_url + f"music-id/{search}"
    else:
        url = test_url + f"music/{search}"

    try:
        return await get_song_info(url)
    except NoSongFoundError as e:
        raise e


async def no_search_youtube(search):
    search = parse_search(search)
    url = test_url + f"youtube/{search}"
    try:
        return await get_song_info(url)
    except NoSongFoundError as e:
        raise e


def parse_search(search):
    if "http" in search and "spotify" in search:
        track = sp.track(search)
        return track['name'] + track['artists'][0]['name']
    else:
        return search


async def get_song_info(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                info = await r.json()
            else:
                raise NoSongFoundError()
        await session.close()
    try:
        videos = info['entries']
        video = "https://www.youtube.com/watch?v=" + videos[0]['id']
        info, placeholder = await search_youtube(video)
        return [info[0], info[1]], videos[1:]
    except KeyError:
        return [info['url'], info['title']], []


def check_same_voice_channel(ctx):
    if ctx.voice_client and ctx.author.voice:
        return ctx.voice_client.channel.id == ctx.author.voice.channel.id
    else:
        return False


async def handle_playlist_videos(videos, bot_queue_callback, ctx):
    for video in videos:
        if stop_thread['done']:
            return
        search = "https://www.youtube.com/watch?v=" + video['id']
        await bot_queue_callback(ctx, search_youtube, search)


def display_queue(bot_voice: BotVoiceHandler, page: int):
    queue = bot_voice.songs
    embed = discord.Embed(title="Queue")
    embed.add_field(name="Now Playing", value=bot_voice.now_playing.title)
    queue_str = ""
    if len(queue) > 0:
        for i in range(min(len(queue) - (5 * (page - 1)), 5)):
            queue_str += f"{i + ((page - 1) * 5) + 1}. {queue[i].title}\n"
        embed.add_field(name="Upcoming Songs", value=queue_str, inline=False)

    if bot_voice.loop:
        embed.set_footer(text="Looping song.", icon_url=disc_gif)
    elif bot_voice.loop_all:
        embed.set_footer(text="Looping queue.", icon_url=disc_gif)
    else:
        embed.set_footer(text="Playing queue.", icon_url=disc_gif)
    return embed


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="nabi")
    async def nabi(self, ctx):
        """
        Queues Nabi Bobet Tau directly if user is in voice channel
        :param ctx: context
        :return:
        """
        if ctx.author.voice:
            guild_id = ctx.message.guild.id
            bot_handler = BotVoiceHandler(ctx.channel)

            if not ctx.voice_client:
                if guild_id not in bot_voice:
                    bot_voice[guild_id] = bot_handler
                bot_handler.voice = await ctx.message.author.voice.channel.connect()
            title = "Nabi Bobet Tau"
            bot_handler.queue(MusicObj("../KeriaBot/Animal Crossing  Nabi Bobet Tau.mp3", "Nabi Bobet Tau"))
            # testing on one mp3 file
            if ctx.voice_client.is_playing():
                pass
                await ctx.send("Added `" + title + "` to queue.")
            else:
                bot_handler.dequeue()
                await self.start_playing(ctx)
        else:
            await ctx.send("You must be connected a voice channel for me to join")

    @commands.hybrid_command(name="disconnect", aliases=['dc'])
    async def disconnect(self, ctx):
        """
        Disconnects from the voice channel
        :param ctx: context
        :return:
        """
        if ctx.voice_client:
            await ctx.guild.voice_client.disconnect()
            stop_thread['done'] = True
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is None and member == self.bot.user:
            if member.guild.voice_client is not None:
                member.guild.voice_client.cleanup()
            del bot_voice[member.guild.id]

    @commands.hybrid_command(aliases=['p'])
    async def play(self, ctx, *, search):
        """
        Plays song given a word search or YouTube/Spotify URL
        :param ctx: context
        :param search: Search terms/YouTube URL/Spotify URL
        :return:
        """
        await self.play_search(ctx, search_youtube, search)

    @commands.hybrid_command(name="nonmusicplay", aliases=['nmp'])
    async def nmp(self, ctx, *, search):
        """
        Searches YouTube without specifically looking for music
        :param ctx: context
        :param search: Search terms
        :return:
        """
        await self.play_search(ctx, no_search_youtube, search)

    async def play_search(self, ctx, search_type, search):
        guild_id = ctx.message.guild.id

        if not ctx.author.voice:
            await ctx.send("You must be connected to a voice channel.", ephemeral=True)
            return

        if guild_id in bot_voice:
            bot_handler = bot_voice[guild_id]
        else:
            bot_handler = BotVoiceHandler(ctx.channel)
            bot_voice[guild_id] = bot_handler

        if not ctx.voice_client:
            voice = await ctx.message.author.voice.channel.connect()
            bot_handler.voice = voice

        await ctx.defer()
        song = await self.queue_song(ctx, search_type, search)
        if ctx.voice_client.is_playing():
            pass
            await ctx.send("Added `" + song.title + "` to queue.")
        else:
            bot_handler.dequeue()
            await self.start_playing(ctx)

    @commands.hybrid_command(name="queue", aliases=['q'])
    async def queue(self, ctx):
        """
        Displays song queue and loop state if there is one.
        :param ctx: context
        :return: None
        """
        page = [1]
        id = ctx.message.guild.id

        async def next_button_callback(interaction: discord.Interaction):
            page[0] += 1
            embed = display_queue(bot_voice[interaction.guild_id], page=page[0])
            queue = bot_voice[interaction.guild_id].songs
            if len(queue) - ((page[0] - 1) * 5) <= 5:
                next_button.disabled = True
            back_button.disabled = False
            await interaction.response.edit_message(embed=embed, view=queue_view)

        async def back_button_callback(interaction: discord.Interaction):
            page[0] -= 1
            embed = display_queue(bot_voice[interaction.guild_id], page=page[0])
            if page[0] == 1:
                back_button.disabled = True
            next_button.disabled = False
            await interaction.response.edit_message(embed=embed, view=queue_view)

        try:
            queue = bot_voice[id].songs
            if queue or bot_voice[id].now_playing is not None:
                embed = display_queue(bot_voice[id], page=page[0])
                queue_view = View()
                next_button = Button(label="Next", style=discord.ButtonStyle.blurple)
                back_button = Button(label="Back", style=discord.ButtonStyle.grey)
                queue_view.add_item(back_button)
                queue_view.add_item(next_button)
                back_button.disabled = True
                next_button.disabled = True

                if len(queue) > 5:
                    next_button.disabled = False

                next_button.callback = next_button_callback
                back_button.callback = back_button_callback
                await ctx.send(embed=embed, view=queue_view)
        except KeyError:
            await ctx.send("I'm not playing any songs right now.")

    @commands.hybrid_command(name="clear", aliases=['qc'])
    async def clear(self, ctx):
        """
        Clears the song queue.
        :param ctx: context
        :return: None
        """
        id = ctx.message.guild.id
        if id in bot_voice and bot_voice[id] and check_same_voice_channel(ctx):
            bot_voice[id].clear_queue()
        await ctx.send("Queue cleared.")

    @commands.hybrid_command(name="skip")
    async def skip(self, ctx):
        """
        Skips the song currently playing
        :param ctx: context
        :return: None
        """
        id = ctx.message.guild.id
        if check_same_voice_channel(ctx):
            bot_voice[id].voice.pause()
            await ctx.send("Skipping to next song.")
            await self.check_queue(ctx, ctx.message.guild.id)
        else:
            await ctx.send("You have to be connected to a voice channel to use this command.", ephemeral=True)

    @commands.hybrid_command(name="pause")
    async def pause(self, ctx):
        """
        Pauses the song currently playing
        :param ctx: context
        :return: None
        """
        id = ctx.message.guild.id
        if check_same_voice_channel(ctx):
            bot_voice[id].voice.pause()
            await ctx.send("Paused.")
        else:
            await ctx.send("You have to be connected to a voice channel to use this command.", ephemeral=True)

    @commands.hybrid_command(name="resume")
    async def resume(self, ctx):
        """
        Resumes current song
        :param ctx:
        :return:
        """
        id = ctx.message.guild.id
        if check_same_voice_channel(ctx):
            bot_voice[id].voice.resume()
            await ctx.send("Resuming...")
        else:
            await ctx.send("You have to be connected to a voice channel to use this command.", ephemeral=True)

    @commands.hybrid_command(name="loop", aliases=['lp'])
    @discord.app_commands.choices(type=[discord.app_commands.Choice(name="queue", value="all")])
    async def loop(self, ctx, type: str = None):
        """
        Disables/Enables queue looping
        :param ctx:
        :param type: No input to loop track or 'all' to loop queue
        :return:
        """
        id = ctx.message.guild.id
        bot_handler = bot_voice[id]
        if check_same_voice_channel(ctx):
            if type == "all":
                bot_handler.set_loop_all()
                if not bot_handler.loop_all:
                    await ctx.send("Ending playlist loop.")
                else:
                    await ctx.send("Looping all songs in queue.")
            else:
                bot_handler.set_loop()
                if not bot_handler.loop:
                    await ctx.send("Stopping loop.")
                    return
                await ctx.send(f"Now looping `{bot_handler.now_playing.title}`.")
        else:
            await ctx.send("You have to be connected to a voice channel to use this command.", ephemeral=True)

    @commands.hybrid_command(name="remove", aliases=['qremove', 'qr'])
    async def remove(self, ctx, num: int):
        """
        Removes a song given the number in queue
        :param ctx:
        :param num: Number of song in queue to remove
        :return: None
        """
        guild_id = ctx.message.guild.id
        bot_handler = bot_voice[guild_id]
        if 1 <= num <= len(bot_handler.songs):
            song = bot_handler.remove_song(num)
            await ctx.send(f"`{song.title}` has been removed from queue.")
        else:
            await ctx.send("Please input a valid number from queue.", ephemeral=True)

    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please input a number.")

    @commands.hybrid_command(name="shuffle")
    async def shuffle(self, ctx):
        """
        Shuffles queue
        :param ctx: context
        :return: None
        """
        id = ctx.message.guild.id
        bot_handler = bot_voice[id]
        if len(bot_handler.songs) > 1:
            bot_handler.shuffle_queue()
            await ctx.send("Queue has been shuffled.")
            await self.bot.invoke("queue")
        else:
            await ctx.send("Not enough songs for me to shuffle.")

    async def start_playing(self, ctx):
        id = ctx.message.guild.id
        song = bot_voice[id].now_playing
        source = song.make_audio_source()
        await ctx.send(f'Now playing `{song.title}`')
        bot_voice[id].voice.play(source,
                                 after=lambda e=None: asyncio.run_coroutine_threadsafe(self.after_playing(ctx, e),
                                                                                         self.bot.loop))

    async def after_playing(self, ctx, error):
        id = ctx.message.guild.id
        if error:
            bot_voice[id].channel.send("Sorry, something happened. Try again later.", ephemeral=True)
            raise error
        else:
            id = ctx.message.guild.id
            if id in bot_voice and bot_voice[id]:
                await self.check_queue(ctx, ctx.message.guild.id)

    async def queue_song(self, ctx, search_type, search):
        try:
            info, videos = await search_type(search)
        except NoSongFoundError:
            return
        url = info[0]
        title = info[1]
        guild_id = ctx.message.guild.id
        if videos:
            stop_thread['done'] = False
            p = Thread(target=asyncio.run, args=(handle_playlist_videos(videos, self.queue_song, ctx),))
            p.start()
        song = MusicObj(url, title)
        bot_voice[guild_id].queue(song)
        return song

    async def check_queue(self, ctx, id):
        bot_handler = bot_voice[id]
        if bot_handler.loop:
            song = bot_handler.now_playing
        else:
            if bot_handler.loop_all:
                bot_handler.queue(bot_handler.now_playing)
            song = bot_handler.dequeue()

        if song is not None:
            source = song.make_audio_source()
            bot_handler.voice.play(source,
                                   after=lambda e=None: asyncio.run_coroutine_threadsafe(self.after_playing(ctx, e),
                                                                                         self.bot.loop))
            await bot_handler.channel.send(f'Now playing `{song.title}`')


async def setup(bot):
    await bot.add_cog(Music(bot))
