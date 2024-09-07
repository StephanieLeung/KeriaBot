from bot.music import *


async def handle_playlist_videos(videos, bot_voice: Music, ctx):
    for video in videos:
        await bot_voice.queue_song(ctx, search_youtube, video['id'])
