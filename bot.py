#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام مدعوم بالذكاء الاصطناعي
يدعم نماذج ChatGPT و Gemini وغيرها من نماذج الذكاء الاصطناعي
مع إمكانية إضافة مسؤولين وإدارة مفاتيح API
"""

import os
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

# استيراد الوحدات المخصصة
from config.config import TOKEN, BOT_PATH, DB_FOLDER
from utils.database import ensure_db_exists
from handlers.command_handlers import (
    start_command, help_command, model_command, clear_command,
    chat_command, admin_command, keys_command, broadcast_command,
    stats_command
)
from handlers.message_handlers import (
    button_callback, admin_add_handler, key_add_name_handler,
    key_add_value_handler, message_handler, cancel_handler,
    ADMIN_ADD, ADMIN_REMOVE, KEY_ADD_NAME, KEY_ADD_VALUE, KEY_REMOVE
)

# إعداد نظام التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=f"{BOT_PATH}/bot.log"
)
logger = logging.getLogger(__name__)

async def setup_commands(application: Application) -> None:
    """
    إعداد قائمة الأوامر التي تظهر في قائمة البوت
    
    Args:
        application (Application): تطبيق البوت
    """
    commands = [
        BotCommand("start", "بدء استخدام البوت"),
        BotCommand("help", "عرض المساعدة"),
        BotCommand("chat", "بدء محادثة جديدة"),
        BotCommand("model", "اختيار نموذج الذكاء الاصطناعي"),
        BotCommand("clear", "مسح المحادثة الحالية"),
        BotCommand("admin", "إدارة المسؤولين (للمسؤولين فقط)"),
        BotCommand("keys", "إدارة مفاتيح API (للمسؤولين فقط)"),
        BotCommand("broadcast", "إرسال رسالة لجميع المستخدمين (للمسؤولين فقط)"),
        BotCommand("stats", "عرض إحصائيات البوت (للمسؤولين فقط)")
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("تم إعداد قائمة الأوامر بنجاح")

def main() -> None:
    """
    الدالة الرئيسية لتشغيل البوت
    """
    # التأكد من وجود المجلدات والملفات اللازمة
    if not os.path.exists(BOT_PATH):
        os.makedirs(BOT_PATH)
    
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
    
    # التأكد من وجود قاعدة البيانات
    ensure_db_exists()
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("model", model_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("chat", chat_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("keys", keys_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # إضافة معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # إضافة معالجات المحادثة
    admin_conv_handler = ConversationHandler(
        entry_points=[],  # سيتم استدعاؤه من خلال معالج الأزرار
        states={
            ADMIN_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_handler)],
            ADMIN_REMOVE: [CallbackQueryHandler(button_callback)]
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)]
    )
    application.add_handler(admin_conv_handler)
    
    keys_conv_handler = ConversationHandler(
        entry_points=[],  # سيتم استدعاؤه من خلال معالج الأزرار
        states={
            KEY_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, key_add_name_handler)],
            KEY_ADD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, key_add_value_handler)],
            KEY_REMOVE: [CallbackQueryHandler(button_callback)]
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)]
    )
    application.add_handler(keys_conv_handler)
    
    # إضافة معالج الرسائل العادية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # إعداد قائمة الأوامر
    application.post_init = setup_commands
    
    # بدء تشغيل البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
