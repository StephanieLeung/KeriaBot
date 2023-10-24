import asyncio
import glob
import os

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import youtube_dl


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.message.author.voice.channel
            voice = await channel.connect()
            source = FFmpegPCMAudio("Animal Crossing  Nabi Bobet Tau.mp3")
            # testing on one mp3 file
            player = voice.play(source)
            await ctx.send("Playing Nabi Bobet Tau :3")
        else:
            await ctx.send("You must be connected to a voice channel for me to join")

    @commands.command()
    async def dc(self, ctx):
        if ctx.voice_client:
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel")


async def setup(bot):
    await bot.add_cog(Music(bot))
