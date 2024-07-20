from fastapi import FastAPI
import yt_dlp
import urllib.request
from urllib.parse import quote
import re

app = FastAPI()

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


def extract_data(url):
    html = urllib.request.urlopen(url)
    vid_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    play_url = "https://www.youtube.com/watch?v=" + vid_id[0]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(play_url, download=False)
    return info


@app.get('/')
async def read_root():
    return {"Hello": "World"}


@app.get("/music/{search}")
async def search_youtube(search: str):
    search = search.replace(" ", "+")
    search_url = "https://www.youtube.com/results?search_query=music+" + quote(search)
    return extract_data(search_url)


@app.get("/music-id/{search}")
async def search_youtube(search: str):
    play_url = "https://www.youtube.com/watch?v=" + search

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(play_url, download=False)
    return info


@app.get("/youtube/{search}")
async def search_youtube(search: str):
    search = search.replace(" ", "+")
    search_url = "https://www.youtube.com/results?search_query=" + quote(search)
    return extract_data(search_url)
