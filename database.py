import sqlite3
import os
from config import DB_PATH

def create_tables():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'ar',
                wallet_balance INTEGER DEFAULT 0,
                free_trial_used BOOLEAN DEFAULT 0,
                subscription_type TEXT DEFAULT 'free',
                subscription_expiry DATETIME,
                selected_model TEXT,
                context_enabled BOOLEAN DEFAULT 1,
                custom_instructions TEXT,
                voice_response BOOLEAN DEFAULT 0,
                voice_style TEXT
                )''')
    
    # جدول حزم المستخدم
    c.execute('''CREATE TABLE IF NOT EXISTS user_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package_type TEXT,
                remaining_credits INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                )''')
    
    # جدول المسؤولين
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY
                )''')
    
    # جدول مفاتيح API
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                api_key TEXT,
                is_active BOOLEAN DEFAULT 1
                )''')
    
    # جدول السياق
    c.execute('''CREATE TABLE IF NOT EXISTS conversation_context (
                user_id INTEGER,
                model TEXT,
                context TEXT,
                PRIMARY KEY (user_id, model)
                )''')
    
    # جدول المعاملات
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                stars INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                )''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
              (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    set_clause = ', '.join([f"{key} = ?" for key in kwargs])
    values = list(kwargs.values()) + [user_id]
    c.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

# ... (وظائف أخرى لإدارة البيانات)
