import sqlite3
from helpers.cookieFuncs import get_cookies
from helpers.account import Account

def get_bank_info(guild_id, user_id):
    db = sqlite3.connect("bot.db")
    cursor = db.cursor()
    info = cursor.execute('''
        SELECT 
            users.cookies, bank.loan, bank.payment_date, bank.due
        FROM bank
        JOIN users ON bank.guild_id = users.guild_id AND bank.user_id = users.user_id
        WHERE bank.guild_id = ? AND bank.user_id = ?; 
    ''', [guild_id, user_id]).fetchone()

    if info:
        cursor.close()
        db.close()
        return {"cookies": info[0], "loan": info[1], "payment_date": info[2], "due": info[3]}
    else:
        cursor.execute('''
            INSERT INTO bank 
            VALUES (
                ?,?,?,?,?
            );
        ''', [guild_id, user_id, 0, None, 0])
        db.commit()
        cursor.close()
        db.close()
        return {"cookies": get_cookies(guild_id, user_id), "loan": 0, "payment_date": None, "due": 0}


def update_bank_info(guild_id, user_id, account: Account):
    db = sqlite3.connect("bot.db")
    cursor = db.cursor()
    cursor.execute('''
        UPDATE bank
        SET loan = ?, payment_date = ?, due = ? 
        WHERE guild_id = ? AND user_id = ?;
    ''', [account.loan, account.payment_date, account.due, guild_id, user_id])
    cursor.execute('''
        UPDATE users
        SET cookies = ?
        WHERE guild_id = ? AND user_id = ?; 
    ''', [account.cookies, guild_id, user_id])
    db.commit()
    cursor.close()
    db.close()
