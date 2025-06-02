"""
الملف الرئيسي للبوت
يقوم بتجميع جميع الوحدات وتشغيل البوت
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

# استيراد الوحدات
from modules.users import users_router, check_subscription_expiry
from modules.admins import admins_router, MAIN_ADMIN_ID
from modules.api_keys import api_keys_router
from modules.subscriptions import subscriptions_router
from modules.models import models_router
from modules.notifications import notifications_router
from modules.stats import stats_router
from modules.commands import commands_router

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

# الحصول على رمز البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN", "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g")

# إنشاء قاعدة البيانات إذا لم تكن موجودة
def setup_database():
    """إنشاء قاعدة البيانات وجداولها إذا لم تكن موجودة"""
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

# تعريف الأوامر
async def set_commands(bot: Bot):
    """تعريف أوامر البوت"""
    commands = [
        BotCommand(command="start", description="حول هذا البوت"),
        BotCommand(command="account", description="حسابي"),
        BotCommand(command="premium", description="الاشتراك المميز"),
        BotCommand(command="deletecontext", description="حذف السياق"),
        BotCommand(command="midjourney", description="Midjourney"),
        BotCommand(command="video", description="توليد الفيديو"),
        BotCommand(command="photo", description="إنشاء الصور"),
        BotCommand(command="suno", description="توليد الأغاني"),
        BotCommand(command="s", description="البحث على الإنترنت"),
        BotCommand(command="settings", description="إعدادات البوت و نماذج AI"),
        BotCommand(command="help", description="قائمة الأوامر"),
        BotCommand(command="privacy", description="شروط الخدمة"),
        BotCommand(command="model", description="اختيار النموذج المفضل")
    ]
    
    await bot.set_my_commands(commands)

# مهمة دورية للتحقق من انتهاء صلاحية الاشتراكات
async def check_subscriptions():
    """مهمة دورية للتحقق من انتهاء صلاحية الاشتراكات"""
    while True:
        await check_subscription_expiry()
        # التحقق كل 24 ساعة
        await asyncio.sleep(24 * 60 * 60)

# الدالة الرئيسية
async def main():
    """الدالة الرئيسية لتشغيل البوت"""
    # إعداد قاعدة البيانات
    setup_database()
    
    # إنشاء كائن البوت والمرسل
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # تسجيل الراوترات
    dp.include_router(commands_router)
    dp.include_router(users_router)
    dp.include_router(admins_router)
    dp.include_router(api_keys_router)
    dp.include_router(subscriptions_router)
    dp.include_router(models_router)
    dp.include_router(notifications_router)
    dp.include_router(stats_router)
    
    # تعيين أوامر البوت
    await set_commands(bot)
    
    # بدء المهام الدورية
    asyncio.create_task(check_subscriptions())
    
    # بدء البوت
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
