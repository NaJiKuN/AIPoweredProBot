# -*- coding: utf-8 -*-
import sqlite3
from config import DATABASE_NAME

def init_db():
    """إنشاء جداول قاعدة البيانات إذا لم تكن موجودة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # جدول المستخدمين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        subscription_type TEXT DEFAULT 'free',
        requests_remaining INTEGER DEFAULT 50, -- للخطط المجانية الأسبوعية أو اليومية للمميزة
        subscription_expiry DATE, -- تاريخ انتهاء صلاحية الاشتراك المميز
        context TEXT, -- لحفظ سياق المحادثة
        selected_model TEXT DEFAULT 'GPT-4o mini' -- النموذج الافتراضي
    )
    ''')

    # جدول المسؤولين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
    ''')

    # جدول مفاتيح API
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        service_name TEXT PRIMARY KEY, -- اسم الخدمة (مثل 'ChatGPT', 'Gemini', 'Midjourney')
        api_key TEXT NOT NULL,
        display_name TEXT -- الاسم الذي يظهر للمستخدمين
    )
    ''')

    # جدول الاشتراكات (لتتبع تفاصيل الخطط)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        plan_name TEXT PRIMARY KEY, -- 'free', 'premium'
        request_limit INTEGER, -- حد الطلبات (يومي للمميز، أسبوعي للمجاني)
        limit_period TEXT, -- 'daily', 'weekly'
        allowed_models TEXT -- قائمة النماذج المسموح بها (مفصولة بفاصلة)
    )
    ''')

    # إضافة بيانات الاشتراكات الافتراضية إذا لم تكن موجودة
    cursor.execute("INSERT OR IGNORE INTO subscriptions (plan_name, request_limit, limit_period, allowed_models) VALUES (?, ?, ?, ?)",
                   ('free', 50, 'weekly', 'GPT-4.1 mini,GPT-4o mini,DeepSeek-V3,Gemini 2.5 Flash,Perplexity,GPT-4o Images'))
    cursor.execute("INSERT OR IGNORE INTO subscriptions (plan_name, request_limit, limit_period, allowed_models) VALUES (?, ?, ?, ?)",
                   ('premium', 100, 'daily', 'GPT-4.1 mini,GPT-4o mini,DeepSeek-V3,Gemini 2.5 Flash,Perplexity,GPT-4o Images,Midjourney,Flux,Claude,GPT-4,GPT-4o')) # أضف كل النماذج المتاحة للمميز

    conn.commit()
    conn.close()

# --- دوال مساعدة لقاعدة البيانات --- (سيتم إضافتها لاحقًا)

if __name__ == "__main__":
    print("جارٍ تهيئة قاعدة البيانات...")
    init_db()
    print("تم تهيئة قاعدة البيانات بنجاح.")


