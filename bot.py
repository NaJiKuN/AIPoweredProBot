#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف البوت الرئيسي
يحتوي على نقطة البداية وإعداد البوت وتسجيل الأوامر
"""

import logging
import os
import sys
from datetime import datetime, timedelta
import asyncio
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# استيراد الوحدات الخاصة بالبوت
from config import TOKEN, ADMIN_ID, SUPPORTED_MODELS, DEFAULT_API_KEYS
from database import Database

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء قاعدة البيانات
db = Database()

# إضافة المسؤول الرئيسي
def setup_admin():
    """إعداد المسؤول الرئيسي"""
    if not db.is_admin(ADMIN_ID):
        db.add_admin(ADMIN_ID, "system")
        logger.info(f"تم إضافة المسؤول الرئيسي: {ADMIN_ID}")

# إضافة مفاتيح API الافتراضية
def setup_default_api_keys():
    """إعداد مفاتيح API الافتراضية"""
    for model, key in DEFAULT_API_KEYS.items():
        if not db.get_api_key(model):
            db.add_api_key(model, key, "system")
            logger.info(f"تم إضافة مفتاح API الافتراضي لنموذج: {model}")

# وظائف مساعدة
async def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مسؤولاً"""
    return user_id == ADMIN_ID or db.is_admin(str(user_id))

async def register_user(update: Update):
    """تسجيل المستخدم في قاعدة البيانات"""
    user = update.effective_user
    language_code = user.language_code or 'ar'
    
    # التحقق من اللغة المدعومة
    if language_code not in ['ar', 'en', 'ru', 'es', 'fr', 'pt']:
        language_code = 'ar'  # اللغة الافتراضية هي العربية
    
    is_new = db.add_user(
        str(user.id),
        user.username,
        user.first_name,
        user.last_name,
        language_code
    )
    
    return is_new

# أوامر البوت الأساسية
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /start"""
    is_new_user = await register_user(update)
    user_id = str(update.effective_user.id)
    
    # نص الترحيب
    welcome_text = """مرحبًا! يتيح لك الروبوت الوصول إلى أفضل أدوات الذكاء الاصطناعي لإنشاء النصوص والصور والفيديوهات والموسيقى.

جرب نماذج متقدمة: OpenAI o3، o4-mini، GPT-4.5، Claude 4، /Midjourney، Flux، /Kling، Pika، /Suno، Grok والمزيد.

مجانًا: GPT-4.1 mini، DeepSeek، Gemini 2.5، GPT Images، وبحث الويب Perplexity.

كيفية الاستخدام:

📝 النص: فقط اطرح سؤالك في الدردشة (اختر نموذج الذكاء الاصطناعي باستخدام /model).

🔎 البحث: انقر على /s للبحث الذكي على الويب.

🌅 الصور: انقر على /photo لبدء إنشاء الصور أو تحريرها.

🎬 الفيديو: انقر على /video لبدء إنشاء مقطع الفيديو الخاص بك (متاح في /premium).

🎸 الموسيقى: انقر على /chirp، واختر نوعًا موسيقيًا، وأضف كلمات الأغنية (متاح في /Suno)."""
    
    # إنشاء لوحة المفاتيح
    keyboard = [
        [InlineKeyboardButton("حسابي 👤", callback_data="account")],
        [InlineKeyboardButton("الاشتراك المميز 🌟", callback_data="premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    # إذا كان مستخدم جديد، نرسل رسالة ترحيب إضافية
    if is_new_user:
        logger.info(f"مستخدم جديد تم تسجيله: {user_id}")

# وظيفة تشغيل البوت
def main():
    """تشغيل البوت"""
    # إعداد المسؤول الرئيسي ومفاتيح API الافتراضية
    setup_admin()
    setup_default_api_keys()
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start_command))
    
    # بدء البوت
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
