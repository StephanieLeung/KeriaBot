from pathlib import Path
import sqlite3
import aiohttp
from api_main import headers


main_url = "https://keria-bot-api.vercel.app/"

async def update_db():
    # checks if database exists
    if not (Path.cwd() / "bot.db").exists():
        db = sqlite3.connect("bot.db")
        cursor = db.cursor()

        cursor.execute('''
                CREATE TABLE users (
                    guild_id INTEGER NOT NULL, 
                    user_id INTEGER NOT NULL, 
                    cookies INTEGER , 
                    datetime TEXT, 
                    PRIMARY KEY (guild_id, user_id)
                );
            ''')
        cursor.execute('''
            CREATE TABLE bank (
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        loan INTEGER,
                        payment_date TEXT,
                        due INTEGER,
                        FOREIGN KEY (guild_id, user_id) REFERENCES users (guild_id, user_id)
                    );
            ''')
        db.commit()
    else:
        db = sqlite3.connect("bot.db")
        cursor = db.cursor()
        cursor.execute('''
            DELETE FROM users;   
        ''')
        cursor.execute('''
            DELETE FROM bank;   
        ''')
        db.commit()

    url = main_url + "allusers"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as r:
            if r.status == 200:
                user_info = await r.json()
        await session.close()
    user_info = user_info['all data']

    url = main_url + "allbank"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as r:
            if r.status == 200:
                bank_info = await r.json()
        await session.close()
    bank_info = bank_info['all data']

    for doc in user_info:
        cursor.execute('''
            INSERT INTO users (guild_id, user_id, cookies, datetime)
            VALUES (:guild_id, :user_id, :cookies, :datetime);
        ''', doc)
    for doc in bank_info:
        cursor.execute('''
                INSERT INTO bank (guild_id, user_id, loan, payment_date, due)
                VALUES (:guild_id, :user_id, :loan, :payment_date, :due);
            ''', doc)

    db.commit()
    cursor.close()
    db.close()


async def update_from_local():
    url = main_url + f"allusers/update"

    db = sqlite3.connect("bot.db")
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    user_data = [dict(zip(column_names, row)) for row in rows]

    cursor.execute("SELECT * FROM bank")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    bank_data = [dict(zip(column_names, row)) for row in rows]

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, json=user_data) as r:
            if r.status == 202:
                url = main_url + f"allbank/update"
                async with session.post(url, json=bank_data) as bank_r:
                    pass
        await session.close()

    cursor.close()
    db.close()

