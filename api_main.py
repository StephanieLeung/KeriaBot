from fastapi import FastAPI
from discord import FFmpegPCMAudio
import yt_dlp
import urllib.request
import re

app = FastAPI()


@app.get('/')
async def read_root():
    return {"Hello": "World"}


@app.get("/music/{search}")
async def search_youtube(search: str):
    search = search.replace(" ", "+")
    search_url = "https://www.youtube.com/results?search_query=music+" + search
    html = urllib.request.urlopen(search_url)
    vid_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    play_url = "https://www.youtube.com/watch?v=" + vid_id[0]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(play_url, download=False)
        # link = info['url']
        # source = FFmpegPCMAudio(link, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        #                         options="-vn")
        # title = info['title']
    return info
