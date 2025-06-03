# -*- coding: utf-8 -*-
"""نقطة الدخول الرئيسية لتشغيل بوت التليجرام AI"""

import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)

# استيراد الإعدادات
import config

# استيراد وحدات المعالجة
from handlers import start, help, account, premium, settings, admin, ai_models, image_gen, video_gen, audio_gen, web_search, context, other_commands

# استيراد الأدوات المساعدة
from utils import database_helper, keyboards, message_templates, subscription_manager, api_helper

# إعداد تسجيل الأحداث (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """أوامر يتم تنفيذها بعد تهيئة البوت وقبل بدء التشغيل."""
    await application.bot.set_my_commands([
        ("start", "🚀 حول هذا البوت"),
        ("account", "👤 حسابي"),
        ("premium", "⭐ الاشتراك المميز"),
        ("model", "🧠 اختيار نموذج الذكاء الاصطناعي"),
        ("settings", "⚙️ إعدادات البوت ونماذج AI"),
        ("deletecontext", "🧹 حذف السياق"),
        ("s", "🔍 البحث على الإنترنت"),
        ("photo", "🖼️ إنشاء الصور"),
        ("video", "🎬 توليد الفيديو"),
        ("suno", "🎵 توليد الأغاني"),
        ("midjourney", "🎨 Midjourney"),
        ("help", "❓ قائمة الأوامر"),
        ("privacy", "🔒 شروط الخدمة"),
        ("empty", "🚫 إبقاء القائمة فارغة"),
    ])
    logger.info("Bot commands set successfully.")

async def main() -> None:
    """الدالة الرئيسية لتشغيل البوت."""
    logger.info("Starting bot...")

    # تهيئة قاعدة البيانات
    try:
        await database_helper.initialize_database()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # إنشاء كائن التطبيق
    application = Application.builder().token(config.TOKEN).post_init(post_init).build()

    # تسجيل معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", help.help_command))
    application.add_handler(CommandHandler("account", account.account_command))
    application.add_handler(CommandHandler("premium", premium.premium_command))
    application.add_handler(CommandHandler("settings", settings.settings_command))
    application.add_handler(CommandHandler("privacy", other_commands.privacy_command))
    application.add_handler(CommandHandler("empty", other_commands.empty_command))

    # أوامر الذكاء الاصطناعي
    application.add_handler(CommandHandler("model", ai_models.select_model_command))
    application.add_handler(CommandHandler("deletecontext", context.delete_context_command))
    application.add_handler(CommandHandler("s", web_search.search_command))
    application.add_handler(CommandHandler("photo", image_gen.photo_command))
    application.add_handler(CommandHandler("wow", image_gen.wow_command))
    application.add_handler(CommandHandler("flux", image_gen.flux_command))
    application.add_handler(CommandHandler("dalle", image_gen.dalle_command))
    application.add_handler(CommandHandler("imagine", image_gen.imagine_command))
    application.add_handler(CommandHandler("midjourney", image_gen.imagine_command))
    application.add_handler(CommandHandler("video", video_gen.video_command))
    application.add_handler(CommandHandler("suno", audio_gen.suno_command))
    application.add_handler(CommandHandler("chirp", audio_gen.chirp_command))

    # أوامر المسؤول
    admin_handler_group = CommandHandler("admin", admin.admin_panel_command, filters=filters.User(user_id=config.ADMIN_IDS))
    application.add_handler(admin_handler_group)

    # معالج الرسائل النصية العادية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_models.handle_text_message))

    # معالج ردود الأزرار
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))

    # معالج الأخطاء
    application.add_error_handler(error_handler)

    # بدء تشغيل البوت
    logger.info("Running bot...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج مؤقت لجميع ردود الأزرار."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    logger.info(f"Received callback query from {user_id} with data: {data}")

    if data.startswith("premium_"):
        await premium.handle_premium_callback(update, context)
    elif data.startswith("settings_"):
        await settings.handle_settings_callback(update, context)
    elif data.startswith("admin_"):
        if user_id in config.ADMIN_IDS:
            await admin.handle_admin_callback(update, context)
        else:
            await query.edit_message_text(text="ليس لديك صلاحية الوصول لهذه الوظيفة.")
    elif data.startswith("model_"):
        await ai_models.handle_model_callback(update, context)
    else:
        await query.edit_message_text(text=f"تم استلام الرد: {data} (المعالج قيد التطوير)")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يسجل الأخطاء التي تسببها التحديثات."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

if __name__ == "__main__":
    asyncio.run(main())
