import datetime
import os

import pymongo
import requests
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
import yt_dlp
from urllib.parse import quote
import re
from pydantic import BaseModel

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()
uri = os.getenv("MONGO_URI")


app = FastAPI()
db_client = MongoClient(uri, server_api=ServerApi('1'))
db = db_client['KeriaBot']
user_db = db['UserDB']


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


class Item(BaseModel):
    guild_id: int
    user_id: int
    cookies: int
    daily: bool | None = False
    datetime: str | None = None


def extract_data(url):
    html = requests.get(url)
    vid_id = re.search(r"watch\?v=(\S{11})", html.content.decode()).group(0)
    play_url = "https://www.youtube.com/" + vid_id

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


@app.get("/user/{guild_id}/{user_id}")
async def user_info(guild_id: int, user_id: int):
    result = user_db.find_one({"guild_id": guild_id, "user_id": user_id})
    if result is not None:
        return {"cookies": result['cookies'], "datetime": result['datetime']}
    user_db.insert_one({"guild_id": guild_id, "user_id": user_id, "cookies": 0, "datetime": None})
    return {"cookies": 0, "datetime": None}


@app.post("/user/update", status_code=202)
async def update_user(data: Item):
    guild_id, user_id, cookies, daily = data.guild_id, data.user_id, data.cookies, data.daily
    if daily:
        user_db.find_one_and_update({"guild_id": guild_id, "user_id": user_id},
                                    {"$set": {"datetime": str(datetime.datetime.now()), "cookies": cookies}},
                                    upsert=True)
    else:
        user_db.find_one_and_update({"guild_id": guild_id, "user_id": user_id}, {"$set": {"cookies": cookies}},
                                    upsert=True)


@app.get("/guild/allusers/{guild_id}")
async def get_users(guild_id: int):
    result = user_db.find({"guild_id": guild_id, "cookies": {"$gt": 0}})
    data = {'users': [], 'cookies': []}
    for document in result:
        data['users'].append(document['user_id'])
        data['cookies'].append(document['cookies'])
    return data


@app.get("/allusers")
async def get_all_data():
    result = user_db.find()
    data = []
    for document in result:
        data.append({"guild_id": document['guild_id'],
                     "user_id": document['user_id'],
                     "cookies": document['cookies'],
                     "datetime": document['datetime']})
    return {"all data": data}


@app.post("/allusers/update", status_code=202)
async def update_db(data: list[Item]):
    operations = []
    for item in data:
        operations.append(pymongo.UpdateOne(
            {"guild_id": item.guild_id, "user_id": item.user_id},
            {"$set": {"cookies": item.cookies, "datetime": item.datetime}},
            upsert=True))
    user_db.bulk_write(operations)



if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='0.0.0.0')