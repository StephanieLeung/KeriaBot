import datetime
import os

import pymongo
import requests
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, Security, HTTPException, status, Response
import yt_dlp
from urllib.parse import quote
import re

from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import BaseModel

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from requests.auth import HTTPBasicAuth

load_dotenv()
uri = os.getenv("MONGO_URI")
key = os.getenv("BOT_KEY")
headers = {
    "API-Key": f"{key}",
    "Content-Type": "application/json"
}

api_key_header = APIKeyHeader(name="API-Key")


def auth_user(api_key_header: str = Security(api_key_header)):
    if key == api_key_header:
        return {"message": "Authentication successful"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key"
    )


app = FastAPI()
db_client = MongoClient(uri, server_api=ServerApi('1'))
db = db_client['KeriaBot']
user_db = db['UserDB']
bank_db = db['BankDB']
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'quiet': True,
    'ignoreerrors': True,
    'skip_download': True,
    'extract_flat': True,
    'username': 'oauth2',
    'password': '',
    'verbose': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192',
    }],
}

ydl_playlist_opts = {
    'extract_flat': True,
    'skip_download': True,
    'ignoreerrors': True,
    'quiet': True,
    'playlist_end': 15,
    'username': 'oauth2',
    'password': '',
}


class User(BaseModel):
    guild_id: int
    user_id: int
    cookies: int
    daily: bool | None = False
    datetime: str | None = None


class BankAccount(BaseModel):
    guild_id: int
    user_id: int
    loan: int
    payment_date: str | None = None
    due: int


def extract_data(url):
    html = requests.get(url)
    vid_id = re.search(r"watch\?v=(\S{11})", html.content.decode()).group(0)
    play_url = "https://www.youtube.com/" + vid_id

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(play_url, download=False)
    return info


@app.get('/')
async def read_root():
    return {"message": "Root path for Keria Bot backend. Authentication key needed for DB access."}


@app.get("/music/{search}")
async def search_youtube(search: str):
    search = search.replace(" ", "+")
    search_url = "https://www.youtube.com/results?search_query=music+" + quote(search)
    info = extract_data(search_url)
    if info is None:
        raise HTTPException(status_code=503, detail=f"No results found for {search}")
    return extract_data(search_url)


@app.get("/music-id/{search}")
async def search_youtube_id(search: str):
    play_url = "https://www.youtube.com/watch?v=" + search

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(play_url, download=False)
    if info is None:
        raise HTTPException(status_code=503, detail=f"No results found for {search}")
    return info

@app.get("/music-playlist/{search}")
async def search_youtube_playlist(search: str):
    play_url = "https://www.youtube.com/playlist?list=" + search
    with yt_dlp.YoutubeDL(ydl_playlist_opts) as ydl:
        info = ydl.extract_info(play_url, download=False)

    if info is None:
        raise HTTPException(status_code=503, detail=f"No results found for {search}")
    return info


@app.get("/youtube/{search}")
async def search_youtube(search: str):
    search = search.replace(" ", "+")
    search_url = "https://www.youtube.com/results?search_query=" + quote(search)
    return extract_data(search_url)


@app.get("/user/{guild_id}/{user_id}")
async def user_info(guild_id: int, user_id: int, auth: HTTPBasicAuth = Depends(auth_user)):
    result = user_db.find_one({"guild_id": guild_id, "user_id": user_id})
    if result is not None:
        try:
            return {"cookies": result['cookies'], "datetime": result['datetime']}
        except KeyError:
            return {"cookies": result['cookies'], "datetime": None}
    user_db.insert_one({"guild_id": guild_id, "user_id": user_id, "cookies": 0, "datetime": None})
    return {"cookies": 0, "datetime": None}


@app.post("/user/update", status_code=202)
async def update_user(data: User, auth: HTTPBasicAuth = Depends(auth_user)):
    guild_id, user_id, cookies, daily = data.guild_id, data.user_id, data.cookies, data.daily
    if daily:
        user_db.find_one_and_update({"guild_id": guild_id, "user_id": user_id},
                                    {"$set": {"datetime": str(datetime.datetime.now()), "cookies": cookies}},
                                    upsert=True)
    else:
        user_db.find_one_and_update({"guild_id": guild_id, "user_id": user_id}, {"$set": {"cookies": cookies}},
                                    upsert=True)


@app.get("/guild/allusers/{guild_id}")
async def get_users(guild_id: int, auth: HTTPBasicAuth = Depends(auth_user)):
    result = user_db.find({"guild_id": guild_id, "cookies": {"$gt": 0}})
    data = {'users': [], 'cookies': []}
    for document in result:
        data['users'].append(document['user_id'])
        data['cookies'].append(document['cookies'])
    return data


@app.get("/allusers")
async def get_all_user_data(auth: HTTPBasicAuth = Depends(auth_user)):
    result = user_db.find()
    data = []
    for document in result:
        try:
            data.append({"guild_id": document['guild_id'],
                         "user_id": document['user_id'],
                         "cookies": document['cookies'],
                         "datetime": document['datetime']})
        except KeyError:
            data.append({"guild_id": document['guild_id'],
                         "user_id": document['user_id'],
                         "cookies": document['cookies'],
                         "datetime": None})
    return {"all data": data}


@app.post("/allusers/update", status_code=202)
async def update_user_db(data: list[User], auth: HTTPBasicAuth = Depends(auth_user)):
    operations = []
    for item in data:
        operations.append(pymongo.UpdateOne(
            {"guild_id": item.guild_id, "user_id": item.user_id},
            {"$set": {"cookies": item.cookies, "datetime": item.datetime}},
            upsert=True))
    user_db.bulk_write(operations)


@app.get("/allbank")
async def get_all_bank_data(auth: HTTPBasicAuth = Depends(auth_user)):
    result = bank_db.find()
    data = []
    for document in result:
        data.append({"guild_id": document['guild_id'],
                     "user_id": document['user_id'],
                     "loan": document['loan'],
                     "payment_date": document['payment_date'],
                     "due": document['due']})
    return {"all data": data}


@app.post("/allbank/update", status_code=202)
async def update_user_db(data: list[BankAccount], auth: HTTPBasicAuth = Depends(auth_user)):
    operations = []
    for item in data:
        operations.append(pymongo.UpdateOne(
            {"guild_id": item.guild_id, "user_id": item.user_id},
            {"$set": {"loan": item.loan, "payment_date": item.payment_date, "due": item.due}},
            upsert=True))
    bank_db.bulk_write(operations)


if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='0.0.0.0')
