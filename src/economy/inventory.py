from src.economy.models import get_user
from src.economy.items import get_item_rarity, ITEMS_DATABASE
import sqlite3

DB_PATH = '/tmp/economy.db'

def add_item(user_id: int, item_name: str):
    rarity = get_item_rarity(item_name)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO inventory (user_id, item_name, item_rarity) VALUES (?, ?, ?)', (user_id, item_name, rarity))
    conn.commit()
    conn.close()

def remove_item(user_id: int, item_name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM inventory WHERE user_id=? AND item_name=?', (user_id, item_name))
    conn.commit()
    conn.close()

def get_inventory(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT item_name, item_rarity FROM inventory WHERE user_id=?', (user_id,))
    items = c.fetchall()
    conn.close()
    return items
