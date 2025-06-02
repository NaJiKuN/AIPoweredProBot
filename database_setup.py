"""
ملف إعداد قاعدة البيانات
يقوم بإنشاء قاعدة البيانات وجداولها
"""

import sqlite3
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# الحصول على معرف المسؤول الرئيسي من المتغيرات البيئية
MAIN_ADMIN_ID = os.getenv("ADMIN_ID", "764559466")

def setup_database():
    """إنشاء قاعدة البيانات وجداولها"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        registration_date TEXT,
        subscription_type TEXT DEFAULT 'free',
        subscription_expiry TEXT,
        text_requests_left INTEGER DEFAULT 50,
        image_requests_left INTEGER DEFAULT 0,
        preferred_model TEXT DEFAULT 'gpt-4.1-mini'
    )
    ''')
    
    # جدول المسؤولين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_by INTEGER,
        added_date TEXT
    )
    ''')
    
    # جدول مفاتيح API
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        api_name TEXT PRIMARY KEY,
        api_key TEXT,
        added_by INTEGER,
        added_date TEXT,
        updated_by INTEGER,
        updated_date TEXT
    )
    ''')
    
    # جدول الحزم النشطة
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS active_packages (
        package_name TEXT PRIMARY KEY,
        activated_date TEXT
    )
    ''')
    
    # جدول حزم المستخدمين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_packages (
        user_id INTEGER,
        package_name TEXT,
        requests_left INTEGER,
        purchase_date TEXT,
        PRIMARY KEY (user_id, package_name)
    )
    ''')
    
    # جدول سياق المحادثة
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversation_context (
        user_id INTEGER PRIMARY KEY,
        context TEXT,
        created_date TEXT,
        updated_date TEXT
    )
    ''')
    
    # جدول استخدام النماذج
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS model_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        model_name TEXT,
        usage_date TEXT
    )
    ''')
    
    # جدول الإشعارات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        message_text TEXT,
        total_users INTEGER,
        sent_count INTEGER,
        failed_count INTEGER,
        sent_date TEXT
    )
    ''')
    
    # إضافة مفاتيح API الافتراضية
    cursor.execute("SELECT COUNT(*) FROM api_keys")
    if cursor.fetchone()[0] == 0:
        # إضافة مفتاح Gemini 2.5flash
        cursor.execute(
            "INSERT INTO api_keys (api_name, api_key, added_by, added_date) VALUES (?, ?, ?, datetime('now'))",
            ("gemini2.5", "AIzaSyAZdRvGnptFullhaGMp0sxM-fr1qhYq7MA", MAIN_ADMIN_ID)
        )
        
        # إضافة مفتاح GPT-4.1 mini
        cursor.execute(
            "INSERT INTO api_keys (api_name, api_key, added_by, added_date) VALUES (?, ?, ?, datetime('now'))",
            ("gpt-4.1-mini", "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", MAIN_ADMIN_ID)
        )
    
    conn.commit()
    conn.close()
    
    print("تم إنشاء قاعدة البيانات وجداولها بنجاح.")

if __name__ == "__main__":
    setup_database()
