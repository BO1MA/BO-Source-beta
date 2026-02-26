import sqlite3
from src.economy.items import get_item_rarity

DB_PATH = '/tmp/economy.db'

# List an item for sale or auction
def list_item_for_sale(seller_id: int, item_name: str, price: int, is_auction: bool = False):
    rarity = get_item_rarity(item_name)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO marketplace (seller_id, item_name, item_rarity, price, is_auction, top_bidder, top_bid)
                 VALUES (?, ?, ?, ?, ?, NULL, NULL)''', (seller_id, item_name, rarity, price, int(is_auction)))
    conn.commit()
    conn.close()

# Get all items for sale/auction
def get_market_items():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, seller_id, item_name, item_rarity, price, is_auction, top_bidder, top_bid FROM marketplace')
    items = c.fetchall()
    conn.close()
    return items

# Place a bid on an auction item
def place_bid(item_id: int, bidder_id: int, bid: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE marketplace SET top_bidder=?, top_bid=? WHERE id=?', (bidder_id, bid, item_id))
    conn.commit()
    conn.close()

# Buy an item (direct sale)
def buy_item(item_id: int, buyer_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT seller_id, item_name FROM marketplace WHERE id=?', (item_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    seller_id, item_name = row
    # Remove from marketplace
    c.execute('DELETE FROM marketplace WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return seller_id, item_name

# Add a function to modify an existing item in the marketplace
def modify_item(item_id, new_price):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM marketplace WHERE id = ?", (item_id,))
    item = c.fetchone()
    if not item:
        conn.close()
        return "❌ السلعة غير موجودة في السوق."

    c.execute("UPDATE marketplace SET price = ? WHERE id = ?", (new_price, item_id))
    conn.commit()
    conn.close()
    return f"✅ تم تعديل سعر السلعة بنجاح إلى {new_price} نقطة."
