import sqlite3
import random
import os
from datetime import datetime, timedelta
import tempfile

# Switch to an in-memory SQLite database for serverless environments
DB_PATH = ":memory:"

# Ensure the database file exists or can be created
if DB_PATH != ":memory:" and not os.path.exists(DB_PATH):
    open(DB_PATH, 'a').close()

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    bank_balance INTEGER DEFAULT 0,
                    has_account BOOLEAN DEFAULT FALSE,
                    is_cheater BOOLEAN DEFAULT FALSE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    last_daily TEXT DEFAULT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    item_rarity TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')
    conn.commit()
    conn.close()

# Check if the user has a bank account
def has_bank_account(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT has_account FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0]

# Open a bank account
def open_bank_account(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, has_account, bank_balance) VALUES (?, TRUE, 100)", (user_id,))
    conn.commit()
    conn.close()
    return "✅ تم فتح حساب بنكي بنجاح! رصيدك الابتدائي هو 100 نقطة."

# Get the user's bank balance
def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT bank_balance FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# Update the user's bank balance
def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# Handle daily rewards
def claim_daily(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result and result[0]:
        last_daily = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_daily < timedelta(days=1):
            conn.close()
            return "❌ لقد حصلت على هديتك اليومية بالفعل. حاول مرة أخرى غدًا."

    gift = random.randint(50, 200)
    c.execute("UPDATE users SET bank_balance = bank_balance + ?, last_daily = ? WHERE user_id = ?", 
              (gift, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    conn.close()
    return f"💰 لقد حصلت على {gift} نقطة كهديتك اليومية!"

# Transfer points between users
def transfer_points(from_user, to_user, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT bank_balance FROM users WHERE user_id = ?", (from_user,))
    result = c.fetchone()
    if not result or result[0] < amount:
        conn.close()
        return "❌ رصيدك لا يكفي لإتمام عملية التحويل."

    c.execute("UPDATE users SET bank_balance = bank_balance - ? WHERE user_id = ?", (amount, from_user))
    c.execute("INSERT OR IGNORE INTO users (user_id, bank_balance) VALUES (?, 0)", (to_user,))
    c.execute("UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?", (amount, to_user))
    conn.commit()
    conn.close()
    return f"✅ تم تحويل {amount} نقطة بنجاح إلى المستخدم {to_user}."

# Initialize the database
init_db()