import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    tea_name TEXT,
    description TEXT,
    how_to_brew TEXT,
    rating INTEGER,
    price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
    
    conn.commit()
    conn.close()

def save_entry(user_id, tea_name=None, description=None, how_to_brew=None, rating=None, price=None):
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()

    c.execute('''INSERT INTO entries 
        (user_id, tea_name, description, how_to_brew, rating, price)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, tea_name, description, how_to_brew, rating, price))

    conn.commit()
    conn.close()

def get_entries(user_id):
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()
    
    c.execute('''SELECT * FROM entries WHERE user_id = ? ORDER BY created_at DESC''', (user_id,))
    entries = c.fetchall()
    
    conn.close()
    return entries

def search_by_name(user_id, name_part):
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()

    c.execute('''SELECT * FROM entries 
                 WHERE user_id = ? AND tea_name LIKE ? 
                 ORDER BY created_at DESC''',
              (user_id, f"%{name_part}%"))
    results = c.fetchall()
    conn.close()
    return results

def search_by_rating(user_id, min_rating):
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()

    c.execute('''SELECT * FROM entries 
                 WHERE user_id = ? AND rating >= ? 
                 ORDER BY rating DESC''',
              (user_id, min_rating))
    results = c.fetchall()
    conn.close()
    return results

def show_all_entries(user_id):
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()

    c.execute('''SELECT * FROM entries WHERE user_id = ? ORDER BY created_at DESC''', (user_id,))
    results = c.fetchall()
    
    conn.close()
    return results

def get_entries_paginated(user_id: int, limit: int, offset: int) -> list[tuple]:
    with sqlite3.connect('teapot.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM entries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )
        return cursor.fetchall()

def count_entries(user_id: int):
    conn = sqlite3.connect('teapot.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM entries WHERE user_id = ?", (user_id,))
    total = c.fetchone()[0]
    conn.close()
    return total

def delete_entry(entry_id: int):
    conn = sqlite3.connect('teapot.db')
    with conn:
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))

# Add more CRUD operations later
init_db()