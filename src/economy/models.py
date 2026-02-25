import sqlite3
from typing import Optional, List, Tuple

DB_PATH = '/tmp/economy.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        bank_balance INTEGER DEFAULT 100,
        is_cheater BOOLEAN DEFAULT 0,
        is_banned BOOLEAN DEFAULT 0,
        has_account BOOLEAN DEFAULT 0,
        last_daily TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER,
        item_name TEXT,
        item_rarity TEXT,
        PRIMARY KEY (user_id, item_name)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS marketplace (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER,
        item_name TEXT,
        item_rarity TEXT,
        price INTEGER,
        is_auction BOOLEAN DEFAULT 0,
        top_bidder INTEGER,
        top_bid INTEGER
    )''')
    conn.commit()
    conn.close()

# User/account helpers
def get_user(user_id: int) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(zip([d[0] for d in c.description], row))
    return None

def create_account(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, has_account) VALUES (?, 1)', (user_id,))
    conn.commit()
    conn.close()

def update_balance(user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET bank_balance = bank_balance + ? WHERE user_id=?', (amount, user_id))
    conn.commit()
    conn.close()

def set_cheater(user_id: int, cheater: bool):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET is_cheater=? WHERE user_id=?', (int(cheater), user_id))
    conn.commit()
    conn.close()

def set_banned(user_id: int, banned: bool):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET is_banned=? WHERE user_id=?', (int(banned), user_id))
    conn.commit()
    conn.close()

def seize_assets(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE inventory SET user_id=0 WHERE user_id=?', (user_id,))
    c.execute('UPDATE users SET bank_balance=0, is_cheater=1 WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()
