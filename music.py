import asyncio
import glob
import json
import os

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp
import urllib.request
import requests
import re

queue = {}
title_queue = {}


def search_youtube(search):
    url = f"http://127.0.0.1:8000/music/{search}"
    data = requests.get(url)

    if data.ok:
        info = json.loads(data.content)
    else:
        raise Exception()
    link = info['url']
    title = info['title']
    source = FFmpegPCMAudio(link, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                            options="-vn")
    return source, title


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice = None
        self.now_playing = None

    @commands.command()
    async def nabi(self, ctx):
        if ctx.author.voice:
            if not ctx.voice_client:
                channel = ctx.message.author.voice.channel
                self.voice = await channel.connect()
            source = FFmpegPCMAudio("Animal Crossing  Nabi Bobet Tau.mp3")
            # testing on one mp3 file
            self.voice.play(source)
            await ctx.send("Playing Nabi Bobet Tau :3")
        else:
            await ctx.send("You must be connected to a voice channel for me to join")

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        if ctx.voice_client:
            self.voice = None
            queue.clear()
            title_queue.clear()
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel")

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, search):
        if not ctx.author.voice:
            await ctx.send("You must be connected to a voice channel.")
            return

        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            self.voice = await channel.connect()

        title = self.queue(ctx, search)
        if ctx.voice_client.is_playing():
            pass
            await ctx.send("Added `" + title + "` to queue.")
        else:
            self.start_playing(ctx)
            self.now_playing = title

    @commands.command(aliases=['queue'])
    async def q(self, ctx):
        id = ctx.message.guild.id
        if id in queue and queue[id]:
            embed = discord.Embed(title="Queue")
            embed.add_field(name="Now Playing", value=self.now_playing)
            embed.add_field(name="Upcoming Songs", value="\n\n".join(title_queue[id][1:]))
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
        self.check_queue(ctx, ctx.message.guild.id)
        await ctx.send("Skipping to next song.")

    @commands.command()
    async def pause(self, ctx):
        self.voice.pause()
        await ctx.send("Paused.")

    @commands.command()
    async def resume(self, ctx):
        self.voice.resume()
        await ctx.send("Resuming...")

    @commands.command(aliases=['qremove'])
    async def qr(self, ctx, arg):
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

    def start_playing(self, ctx):
        id = ctx.message.guild.id
        self.voice.play(queue[id][0], after=lambda e=None: self.after_playing(ctx, e))
        asyncio.run_coroutine_threadsafe(ctx.send(f'Now playing `{title_queue[id][0]}`'), self.bot.loop)

    def after_playing(self, ctx, error):
        if error:
            raise error
        else:
            id = ctx.message.guild.id
            if id in queue and queue[id]:
                self.check_queue(ctx, ctx.message.guild.id)

    def queue(self, ctx, search):
        source, title = search_youtube(search)

        guild_id = ctx.message.guild.id
        if guild_id in queue:
            queue[guild_id].append(source)
            title_queue[guild_id].append(title)
        else:
            queue[guild_id] = [source]
            title_queue[guild_id] = [title]
        return title

    def check_queue(self, ctx, id):
        queue[id].pop(0)
        title_queue[id].pop(0)
        if queue[id]:
            self.voice.play(queue[id][0], after=lambda e=None: self.after_playing(ctx, e))
            asyncio.run_coroutine_threadsafe(ctx.send(f'Now playing `{title_queue[id][0]}`'), self.bot.loop)
            self.now_playing = title_queue[id][0]


async def setup(bot):
    await bot.add_cog(Music(bot))
