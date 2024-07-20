import asyncio
import json
import random

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

queue = {}
title_queue = {}
voice_state = {}
voice = None
now_playing = None
channel = None
loop = False
loop_playlist = False
main_url = "https://keriabot.onrender.com/"
test_url = "http://localhost:8000/"
disc_gif = "https://media0.giphy.com/media/LwBTamVefKJxmYwDba/giphy.gif?cid=6c09b952g0ljvqtoads16f77bd3hpv1cwibrnm3b3pmzyifz&rid=giphy.gif&ct=s"

load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)


def search_youtube(search):
    search = parse_search(search)
    if "http" in search and "youtube" in search:
        search = search.partition("=")[2]
        url = test_url + f"music-id/{search}"
    else:
        url = test_url + f"music/{search}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/111.0.0.0 Safari/537.36'}
    data = requests.get(url, headers=headers)

    if data.ok:
        info = json.loads(data.content)
    else:
        raise Exception()
    return info['url'], info['title']


def no_search_youtube(search):
    search = parse_search(search)
    url = test_url + f"youtube/{search}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/111.0.0.0 Safari/537.36'}
    data = requests.get(url, headers=headers)

    if data.ok:
        info = json.loads(data.content)
    else:
        raise Exception()
    return info['url'], info['title']


def make_audio_source(link):
    source = FFmpegPCMAudio(link,
                            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss 00:00:00.00",
                            options="-vn")
    return source


def parse_search(search):
    if "http" in search and "spotify" in search:
        track = sp.track(search)
        return track['name'] + track['artists'][0]['name']
    else:
        return search


def init_loop(id):
    voice_state[id]['loop_playlist'] = False
    voice_state[id]['loop'] = False


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nabi(self, ctx):
        """
        Queues Nabi Bobet Tau directly if user is in voice channel
        :param ctx: context
        :return:
        """
        if ctx.author.voice:
            guild_id = ctx.message.guild.id
            if guild_id not in voice_state:
                voice_state[guild_id] = {}
                init_loop(guild_id)

            if not ctx.voice_client:
                channel = ctx.message.author.voice.channel
                voice_state[guild_id]['voice'] = await channel.connect()
            source = FFmpegPCMAudio("Animal Crossing  Nabi Bobet Tau.mp3")
            title = "Nabi Bobet Tau"
            # testing on one mp3 file
            if guild_id in queue:
                queue[guild_id].append(source)
                title_queue[guild_id].append(title)
            else:
                queue[guild_id] = [source]
                title_queue[guild_id] = [title]
            if ctx.voice_client.is_playing():
                pass
                await ctx.send("Added `" + title + "` to queue.")
            else:
                self.start_playing(ctx)
                voice_state[guild_id]['now_playing'] = title
                voice_state[guild_id]['channel'] = ctx.channel
        else:
            await ctx.send("You must be connected a voice channel for me to join")

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """
        Disconnects from the voice channel
        :param ctx: context
        :return:
        """
        guild_id = ctx.message.guild.id

        if ctx.voice_client:
            voice_state[guild_id]['voice'] = None
            voice_state[guild_id]['channel'] = None
            queue.clear()
            title_queue.clear()
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel")

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, search):
        """
        Plays song given a word search or YouTube/Spotify URL
        :param ctx: context
        :param search: Search terms/YouTube URL/Spotify URL
        :return:
        """
        guild_id = ctx.message.guild.id

        if not ctx.author.voice:
            await ctx.send("You must be connected to a voice channel.")
            return

        if not ctx.voice_client:
            if guild_id not in voice_state:
                voice_state[guild_id] = {}
                init_loop(guild_id)
            channel = ctx.message.author.voice.channel
            voice_state[guild_id]['voice'] = await channel.connect()

        title = self.q(ctx, search)
        if ctx.voice_client.is_playing():
            pass
            await ctx.send("Added `" + title + "` to queue.")
        else:
            self.start_playing(ctx)
            voice_state[guild_id]['now_playing'] = title
            voice_state[guild_id]['channel'] = ctx.channel

    @commands.command(aliases=['np'])
    async def nop(self, ctx, *, search):
        """
        Searches YouTube without specifically looking for music
        :param ctx: context
        :param search: Search terms
        :return:
        """
        guild_id = ctx.message.guild.id

        if not ctx.author.voice:
            await ctx.send("You must be connected to a voice channel.")
            return

        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            voice_state[guild_id]['voice'] = await channel.connect()

        title = self.noqueue(ctx, search)
        if ctx.voice_client.is_playing():
            pass
            await ctx.send("Added `" + title + "` to queue.")
        else:
            self.start_playing(ctx)
            voice_state[guild_id]['now_playing'] = title
            voice_state[guild_id]['channel'] = ctx.channel

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        id = ctx.message.guild.id
        if id in queue and queue[id]:
            embed = discord.Embed(title="Queue")
            embed.add_field(name="Now Playing", value=voice_state[id]['now_playing'])
            queue_str = ""
            if len(title_queue[id]) > 1:
                for i in range(len(title_queue[id])-1):
                    queue_str += f"{i+1}. {title_queue[id][i+1]}\n"
                print(queue_str)
                embed.add_field(name="Upcoming Songs", value=queue_str, inline=False)
            if voice_state[id]['loop']:
                embed.set_footer(text="Looping song.", icon_url=disc_gif)
            elif voice_state[id]['loop_playlist']:
                embed.set_footer(text="Looping queue.", icon_url=disc_gif)
            else:
                embed.set_footer(text="Playing queue.", icon_url=disc_gif)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Queue is empty.")

    @commands.command(alises=['qc'])
    async def clear(self, ctx):
        queue.clear()
        title_queue.clear()
        await ctx.send("Queue cleared.")

    @commands.command()
    async def skip(self, ctx):
        id = ctx.message.guild.id
        voice_state[id]['voice'].pause()
        await ctx.send("Skipping to next song.")
        self.check_queue(ctx, ctx.message.guild.id)

    @commands.command()
    async def pause(self, ctx):
        id = ctx.message.guild.id
        voice_state[id]['voice'].pause()
        await ctx.send("Paused.")

    @commands.command()
    async def resume(self, ctx):
        id = ctx.message.guild.id
        voice_state[id]['voice'].resume()
        await ctx.send("Resuming...")

    @commands.command(aliases=['lp'])
    async def loop(self, ctx, arg=None):
        id = ctx.message.guild.id

        if arg == "all":
            if voice_state[id]['loop_playlist']:
                voice_state[id]['loop_playlist'] = False
                await ctx.send("Ending playlist loop.")
            else:
                voice_state[id]['loop_playlist'] = True
                voice_state[id]['loop'] = False
                await ctx.send("Looping all songs in queue.")
        elif voice_state[id]['loop'] is True:
            voice_state[id]['loop'] = False
            await ctx.send("Stopping loop.")
        else:
            voice_state[id]['loop'] = True
            voice_state[id]['loop_playlist'] = False
            await ctx.send(f"Now looping `{voice_state[id]['now_playing']}`.")

    @commands.command(aliases=['qr', 'qremove'])
    async def remove(self, ctx, arg):
        guild_id = ctx.message.guild.id
        try:
            index = int(arg)
        except ValueError:
            await ctx.send("Please input a number.")
            return
        if 1 <= index <= len(title_queue[guild_id]) - 1:
            queue[guild_id].pop(index)
            title = title_queue[guild_id].pop(index)
            await ctx.send(f"`{title}` has been removed from queue.")
        else:
            await ctx.send("Please input a valid number.")

    @commands.command()
    async def shuffle(self, ctx):
        id = ctx.message.guild.id

        if len(queue[id]) > 2:
            temp_queue = queue[id][1:]
            temp_title = title_queue[id][1:]
            temp_list = list(zip(temp_queue, temp_title))
            random.shuffle(temp_list)
            shuffled_queue, shuffled_title = zip(*temp_list)
            queue[id] = [queue[id][0]] + list(shuffled_queue)
            title_queue[id] = [title_queue[id][0]] + list(shuffled_title)
            await ctx.send("Queue has been shuffled.")
        else:
            await ctx.send("Not enough songs to shuffle.")

    def start_playing(self, ctx):
        id = ctx.message.guild.id
        source = make_audio_source(queue[id][0])
        voice_state[id]['voice'].play(source, after=lambda e=None: self.after_playing(ctx, e))
        asyncio.run_coroutine_threadsafe(ctx.send(f'Now playing `{title_queue[id][0]}`'), self.bot.loop)

    def after_playing(self, ctx, error):
        id = ctx.message.guild.id
        if error:
            voice_state[id]['channel'].send("Sorry, something happened. Try again later.")
            raise error
        else:
            id = ctx.message.guild.id
            if id in queue and queue[id]:
                self.check_queue(ctx, ctx.message.guild.id)

    def q(self, ctx, search):
        url, title = search_youtube(search)

        guild_id = ctx.message.guild.id
        if guild_id in queue:
            queue[guild_id].append(url)
            title_queue[guild_id].append(title)
        else:
            queue[guild_id] = [url]
            title_queue[guild_id] = [title]
        return title

    def noqueue(self, ctx, search):
        url, title = no_search_youtube(search)
        guild_id = ctx.message.guild.id
        if guild_id in queue:
            queue[guild_id].append(url)
            title_queue[guild_id].append(title)
        else:
            queue[guild_id] = [url]
            title_queue[guild_id] = [title]
        return title

    def check_queue(self, ctx, id):
        if not voice_state[id]['loop'] and not voice_state[id]['loop_playlist']:
            queue[id].pop(0)
            title_queue[id].pop(0)
        elif voice_state[id]['loop_playlist']:
            queue[id].append(queue[id].pop(0))
            title_queue[id].append(title_queue[id].pop(0))
        if queue[id]:
            source = make_audio_source(queue[id][0])
            voice_state[id]['voice'].play(source, after=lambda e=None: self.after_playing(ctx, e))
            asyncio.run_coroutine_threadsafe(voice_state[id]['channel'].send(f'Now playing `{title_queue[id][0]}`'), self.bot.loop)
            voice_state[id]['now_playing'] = title_queue[id][0]


async def setup(bot):
    await bot.add_cog(Music(bot))
