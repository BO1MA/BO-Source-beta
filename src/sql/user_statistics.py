import sqlite3
from datetime import datetime

# Initialize SQLite connection
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_statistics (
            user_id INTEGER PRIMARY KEY,
            messages_sent INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            last_active TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_message(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_statistics (user_id, messages_sent, last_active)
        VALUES (?, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            messages_sent = messages_sent + 1,
            last_active = ?
    """, (user_id, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()

def get_user_statistics(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_statistics WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result