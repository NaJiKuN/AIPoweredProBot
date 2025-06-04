import sqlite3
import os
from datetime import datetime, timedelta
from config import DB_PATH, DEFAULT_API_KEYS, ADMIN_IDS

def init_db():
    """تهيئة قاعدة البيانات والجداول"""
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
        current_model TEXT DEFAULT 'GPT-4.1 mini',
        context_enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول الاشتراكات
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_type TEXT,
        start_date TIMESTAMP,
        end_date TIMESTAMP,
        remaining_requests INTEGER,
        image_credits INTEGER DEFAULT 0,
        video_credits INTEGER DEFAULT 0,
        music_credits INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    
    # جدول مفاتيح API
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        service_name TEXT PRIMARY KEY,
        api_key TEXT,
        added_by INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول المسؤولين
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )''')
    
    # جدول محادثة السياق
    c.execute('''CREATE TABLE IF NOT EXISTS context (
        user_id INTEGER,
        model TEXT,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # إضافة المسؤولين الافتراضيين
    for admin_id in ADMIN_IDS:
        c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
    
    # إضافة مفاتيح API الافتراضية
    for service, key in DEFAULT_API_KEYS.items():
        c.execute("INSERT OR IGNORE INTO api_keys (service_name, api_key, added_by) VALUES (?, ?, ?)",
                  (service, key, ADMIN_IDS[0]))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """الحصول على اتصال بقاعدة البيانات"""
    return sqlite3.connect(DB_PATH)

def get_user(user_id):
    """استرجاع بيانات المستخدم"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name, last_name, language='ar'):
    """إنشاء مستخدم جديد"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # إنشاء المستخدم
    c.execute(
        "INSERT INTO users (user_id, username, first_name, last_name, language) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, first_name, last_name, language)
    )
    
    # منح الاشتراك المجاني
    end_date = datetime.now() + timedelta(days=7)
    c.execute(
        "INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, remaining_requests) VALUES (?, ?, ?, ?, ?)",
        (user_id, 'free', datetime.now(), end_date, 50)
    )
    
    conn.commit()
    conn.close()

def update_user_model(user_id, model_name):
    """تحديث النموذج المفضل للمستخدم"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET current_model = ? WHERE user_id = ?",
        (model_name, user_id)
    )
    conn.commit()
    conn.close()

# يمكن إضافة المزيد من الدوال حسب الحاجة
