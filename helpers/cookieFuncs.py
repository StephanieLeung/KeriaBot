import aiohttp
import datetime

import sqlite3

def local_get_info(guild_id, user_id):
    db = sqlite3.connect("bot.db")
    cursor = db.cursor()
    info = cursor.execute('''
        SELECT *
        FROM users
        WHERE guild_id = ? AND user_id = ?;
    ''', [guild_id, user_id]).fetchone()
    if info:
        cursor.close()
        db.close()
        return {"cookies": info[2], "datetime": info[3]}
    else:
        cursor.execute('''
            INSERT INTO users 
            VALUES (
                ?,?,?,?
            );
        ''', [guild_id, user_id, 0, None])
        db.commit()
        cursor.close()
        db.close()
        return {"cookies": 0, "datetime": None}


def local_update_cookie(guild_id, user_id, cookie, daily=False):
    db = sqlite3.connect("bot.db")
    cursor = db.cursor()
    if daily:
        date = str(datetime.datetime.now())
        cursor.execute('''
            UPDATE users
            SET cookies = ?, datetime = ?
            WHERE guild_id = ? AND user_id = ?;
        ''', [cookie, date, guild_id, user_id])
    else:
        cursor.execute('''
            UPDATE users
            SET cookies = ?
            WHERE guild_id = ? AND user_id = ?;
        ''', [cookie, guild_id, user_id])
    db.commit()
    cursor.close()
    db.close()


def local_get_all_info(guild_id):
    db = sqlite3.connect("bot.db")
    cursor = db.cursor()
    result = cursor.execute('''
        SELECT * FROM users
        WHERE guild_id = ?;
    ''', [guild_id]).fetchall()
    cursor.close()
    db.close()
    data = {"users": [], "cookies": []}
    for document in result:
        data["users"].append(document[1])
        data["cookies"].append(document[2])
    return data


def update_cookies(guild_id, author_id, add):
    cookies = get_cookies(guild_id, author_id)
    cookies += add
    local_update_cookie(guild_id, author_id, cookies)


def get_cookies(guild_id, author_id):
    info = local_get_info(guild_id, author_id)
    return info['cookies']


# async def __get_info(guild_id, user_id):
#     url = main_url + f"user/{guild_id}/{user_id}"
#
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as r:
#             if r.status == 200:
#                 info = await r.json()
#         await session.close()
#     return info
#
#
# async def __update_cookie(guild_id, user_id, cookie, daily=False):
#     url = main_url + f"user/update"
#     data = {"guild_id": guild_id, "user_id": user_id, "cookies": cookie, "daily": daily}
#
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=data) as r:
#             pass
#         await session.close()
