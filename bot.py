# -*- coding: utf-8 -*-
"""الملف الرئيسي لتشغيل بوت تليجرام AI.

يقوم هذا الملف بتهيئة البوت، تحميل الإعدادات، تسجيل معالجات الأوامر،
وبدء تشغيل البوت للاستماع إلى الرسائل الواردة.
"""

import logging
import config # استيراد ملف الإعدادات الخاص بنا
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler # مستورد ولكن لم يستخدم مباشرة هنا، يستخدم في admin_handler
)

# استيراد المعالجات والوظائف من الوحدات الأخرى
from utils import user_manager, database # استيراد database للتحقق من المفاتيح عند البدء
from handlers import admin, user_commands

# إعداد تسجيل الأحداث (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- معالجات الأوامر الأساسية المحدثة ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة ترحيبية وتسجيل المستخدم عند إرسال أمر /start."""
    user = update.effective_user
    user_id = user.id
    logger.info(f"المستخدم {user.username} (ID: {user_id}) بدأ البوت (/start).")

    # تسجيل المستخدم إذا لم يكن موجودًا
    is_new_user = user_manager.register_user_if_not_exists(user_id, user.username, user.first_name)
    if is_new_user:
        logger.info(f"تم تسجيل مستخدم جديد: {user.username} (ID: {user_id})")
    else:
        logger.info(f"المستخدم {user.username} (ID: {user_id}) موجود بالفعل.")

    # تنسيق الرسالة الترحيبية
    # (يمكن تحسينها لاحقًا لعرض نماذج محددة متاحة بناءً على المفاتيح المفعلة)
    free_models_list = ", ".join(config.USAGE_LIMITS["free"]["allowed_models"])
    welcome_text = config.WELCOME_MESSAGE.format(
        free_models=free_models_list,
        free_limits=config.USAGE_LIMITS["free"]["text_requests_weekly"]
    )

    await update.message.reply_html(
        rf"مرحباً {user.mention_html()}!\n{welcome_text}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة المساعدة عند إرسال المستخدم لأمر /help."""
    user = update.effective_user
    logger.info(f"المستخدم {user.username} (ID: {user_id}) طلب المساعدة (/help).")
    await update.message.reply_html(config.HELP_MESSAGE)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تسجيل الأخطاء التي تحدث بسبب تحديثات Telegram."""
    logger.error("حدث خطأ غير متوقع:", exc_info=context.error)
    # يمكن إرسال رسالة للمستخدم في حالة حدوث خطأ معين
    # if isinstance(context.error, telegram.error.BadRequest):
    #     # ... التعامل مع خطأ معين
    #     pass
    # elif update and isinstance(update, Update) and update.effective_message:
    #     await update.effective_message.reply_text("عذرًا، حدث خطأ ما. يرجى المحاولة مرة أخرى.")

# --- الوظيفة الرئيسية --- #

def main() -> None:
    """بدء تشغيل البوت."""
    logger.info("بدء تهيئة البوت...")

    # التحقق من وجود مفاتيح API مفعلة عند البدء
    enabled_keys = database.get_enabled_api_keys()
    if not enabled_keys:
        logger.warning("لا توجد مفاتيح API مفعلة في ملف البيانات. قد لا تعمل وظائف الذكاء الاصطناعي.")
    else:
        logger.info(f"تم العثور على {len(enabled_keys)} مفتاح API مفعل.")

    # إنشاء كائن التطبيق وتمرير توكن البوت إليه
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # -- تسجيل معالجات الأوامر للمستخدم العادي --
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("account", user_commands.account_command))
    application.add_handler(CommandHandler("premium", user_commands.premium_command))
    application.add_handler(CommandHandler("deletecontext", user_commands.delete_context_command))
    application.add_handler(CommandHandler("privacy", user_commands.privacy_command))
    application.add_handler(CommandHandler("model", user_commands.model_command)) # قيد التطوير
    application.add_handler(CommandHandler("settings", user_commands.settings_command)) # قيد التطوير
    application.add_handler(CommandHandler("s", user_commands.search_command)) # قيد التطوير
    application.add_handler(CommandHandler("photo", user_commands.photo_command)) # قيد التطوير
    application.add_handler(CommandHandler("video", user_commands.video_command))
    application.add_handler(CommandHandler("suno", user_commands.music_command))
    application.add_handler(CommandHandler("chirp", user_commands.music_command))
    application.add_handler(CommandHandler("midjourney", user_commands.midjourney_command))
    # الأمر /empty غير ضروري عادةً، يمكن للمستخدم ببساطة عدم إرسال شيء

    # -- تسجيل معالج أوامر المسؤولين (ConversationHandler) --
    application.add_handler(admin.admin_conv_handler)

    # -- تسجيل معالج الرسائل النصية العامة (يجب أن يكون بعد CommandHandlers) --
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_commands.handle_message))

    # -- تسجيل معالج الرسائل الصوتية (إذا كان سيتم دعمها) --
    # application.add_handler(MessageHandler(filters.VOICE, user_commands.handle_voice_message)) # تحتاج لإنشاء هذه الدالة

    # -- تسجيل معالج الأخطاء --
    application.add_error_handler(error_handler)

    # بدء تشغيل البوت
    logger.info("بدء تشغيل البوت والاستماع للتحديثات...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

