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

# استيراد وحدات المعالجة (سيتم استكمالها لاحقاً)
from handlers import start, help, account, premium, settings, admin, ai_models, image_gen, video_gen, audio_gen, web_search, context, other_commands

# استيراد الأدوات المساعدة (سيتم استكمالها لاحقاً)
from utils import database_helper, keyboards, message_templates, subscription_manager, api_helper

# إعداد تسجيل الأحداث (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """أوامر يتم تنفيذها بعد تهيئة البوت وقبل بدء التشغيل."""
    # يمكنك هنا تعيين أوامر البوت التي تظهر في قائمة الأوامر في تليجرام
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
        ("midjourney", "🎨 Midjourney"), # كمثال، يمكن تعديلها لاحقاً
        ("help", "❓ قائمة الأوامر"),
        ("privacy", "🔒 شروط الخدمة"),
        ("empty", "🚫 إبقاء القائمة فارغة"),
        # أضف أوامر المسؤول هنا إذا أردت أن تظهر في القائمة (قد لا يكون مفضلاً)
    ])
    logger.info("Bot commands set successfully.")

async def main() -> None:
    """الدالة الرئيسية لتشغيل البوت."""
    logger.info("Starting bot...")

    # تهيئة قاعدة البيانات (سيتم إنشاء الجداول إذا لم تكن موجودة)
    # يجب التأكد من وجود الدالة initialize_database في database_helper.py
    try:
        await database_helper.initialize_database()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return # لا يمكن تشغيل البوت بدون قاعدة بيانات

    # إنشاء كائن التطبيق
    application = Application.builder().token(config.TOKEN).post_init(post_init).build()

    # --- تسجيل معالجات الأوامر والرسائل --- 
    # ملاحظة: هذه مجرد هياكل أولية، سيتم ربطها بالوظائف الفعلية في ملفات handlers

    # أوامر أساسية
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
    application.add_handler(CommandHandler("wow", image_gen.wow_command)) # كمثال لـ GPT-4o Images
    application.add_handler(CommandHandler("flux", image_gen.flux_command))
    application.add_handler(CommandHandler("dalle", image_gen.dalle_command))
    application.add_handler(CommandHandler("imagine", image_gen.imagine_command))
    application.add_handler(CommandHandler("midjourney", image_gen.imagine_command)) # ربط /midjourney بنفس معالج /imagine
    application.add_handler(CommandHandler("video", video_gen.video_command))
    application.add_handler(CommandHandler("suno", audio_gen.suno_command))
    application.add_handler(CommandHandler("chirp", audio_gen.chirp_command))

    # أوامر المسؤول (سيتم إضافة المزيد من التفاصيل لاحقاً)
    # يجب إضافة فلتر للتحقق من أن المستخدم هو مسؤول
    # application.add_handler(CommandHandler("addadmin", admin.add_admin_command, filters=filters.User(user_id=config.ADMIN_IDS)))
    # application.add_handler(CommandHandler("removeadmin", admin.remove_admin_command, filters=filters.User(user_id=config.ADMIN_IDS)))
    # ... أوامر إدارة API، الاشتراكات، الإشعارات، الإحصائيات ...
    # مثال مبدئي لمعالج أوامر المسؤولين
    admin_handler_group = CommandHandler("admin", admin.admin_panel_command, filters=filters.User(user_id=config.ADMIN_IDS))
    application.add_handler(admin_handler_group)

    # معالج الرسائل النصية العادية (للتفاعل مع نماذج AI)
    # يجب أن يكون هذا المعالج ذا أولوية منخفضة ليتم تنفيذه فقط إذا لم يتطابق أي أمر
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_models.handle_text_message))

    # معالج الرسائل الصوتية (للمشتركين المميزين)
    # application.add_handler(MessageHandler(filters.VOICE, ai_models.handle_voice_message))

    # معالج ردود الأزرار (CallbackQueryHandler)
    # application.add_handler(CallbackQueryHandler(premium.handle_subscription_callback, pattern="^subscribe_"))
    # application.add_handler(CallbackQueryHandler(settings.handle_settings_callback, pattern="^setting_"))
    # application.add_handler(CallbackQueryHandler(admin.handle_admin_callback, pattern="^admin_"))
    # ... معالجات أخرى لردود الأزرار ...
    # مثال لمعالج عام لردود الأزرار، يمكن تقسيمه لاحقاً
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))

    # معالج الأخطاء
    application.add_error_handler(error_handler)

    # بدء تشغيل البوت
    logger.info("Running bot...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج مؤقت لجميع ردود الأزرار، سيتم تقسيمه لاحقاً."""
    query = update.callback_query
    await query.answer() # مهم لإعلام تليجرام بأن الرد تم استلامه
    user_id = query.from_user.id
    data = query.data
    logger.info(f"Received callback query from {user_id} with data: {data}")

    # هنا سيتم توجيه الرد بناءً على بيانات الزر (data)
    # مثال:
    if data.startswith("premium_"):
        await premium.handle_premium_callback(update, context)
    elif data.startswith("settings_"):
        await settings.handle_settings_callback(update, context)
    elif data.startswith("admin_"):
        # التحقق من أن المستخدم مسؤول قبل استدعاء وظائف المسؤول
        if user_id in config.ADMIN_IDS:
            await admin.handle_admin_callback(update, context)
        else:
            await query.edit_message_text(text="ليس لديك صلاحية الوصول لهذه الوظيفة.")
    elif data.startswith("model_"):
        await ai_models.handle_model_callback(update, context)
    # ... إلخ لبقية أنواع الأزرار ...
    else:
        await query.edit_message_text(text=f"تم استلام الرد: {data} (المعالج قيد التطوير)")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يسجل الأخطاء التي تسببها التحديثات."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    # يمكنك هنا إرسال رسالة للمستخدم أو للمسؤول لإعلامه بالخطأ
    # if isinstance(update, Update) and update.effective_message:
    #     await update.effective_message.reply_text("حدث خطأ ما أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً.")

if __name__ == "__main__":
    # استخدام asyncio.run لتشغيل الدالة main غير المتزامنة
    asyncio.run(main())

