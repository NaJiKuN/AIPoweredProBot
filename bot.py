# -*- coding: utf-8 -*-
"""الملف الرئيسي لتشغيل بوت تليجرام المدعوم بالذكاء الاصطناعي"""

import logging
import subprocess
import sys
import shlex
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from telegram.constants import ParseMode

# استيراد الوحدات والإعدادات المحلية
import config
import db_handler
import ai_handler
from utils import admin_required, format_api_list, format_admin_list

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # تقليل تسجيلات مكتبة httpx
logger = logging.getLogger(__name__)

# تعريف حالات المحادثة (إذا احتجنا إليها لاحقاً)
# SELECT_API, GET_PROMPT = range(2)

# --- معالجات أوامر المستخدمين العاديين ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة ترحيب عند إرسال المستخدم لأمر /start"""
    user = update.effective_user
    logger.info(f"المستخدم {user.id} ({user.username}) بدأ البوت.")
    welcome_message = (
        f"أهلاً بك يا {user.mention_html()} في بوت الذكاء الاصطناعي!\n\n"
        "يمكنك استخدامي للتحدث مع نماذج الذكاء الاصطناعي المختلفة.\n"
        "استخدم الأوامر التالية:\n"
        "/help - لعرض قائمة المساعدة والأوامر المتاحة\n"
        "/list_apis - لعرض قائمة نماذج الذكاء الاصطناعي المتاحة\n"
        "/ask `اسم_النموذج` `سؤالك` - لطرح سؤال على نموذج محدد\n\n"
        "مثال: `/ask gemini ما هي عاصمة فرنسا؟`"
    )
    await update.message.reply_html(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة المساعدة عند إرسال المستخدم لأمر /help"""
    user_id = update.effective_user.id
    logger.info(f"المستخدم {user_id} طلب المساعدة.")
    
    # رسالة المساعدة الأساسية
    help_text = (
        "*الأوامر المتاحة للمستخدمين:*\n"
        "/start - بدء استخدام البوت\n"
        "/help - عرض هذه الرسالة\n"
        "/list_apis - عرض قائمة نماذج الذكاء الاصطناعي المتاحة\n"
        "/ask `اسم_النموذج` `سؤالك` - طرح سؤال على نموذج محدد\n"
        "    *مثال:* `/ask chatgpt اكتب قصة قصيرة`\n\n"
    )

    # إضافة أوامر المسؤولين إذا كان المستخدم مسؤولاً
    if db_handler.is_admin(user_id):
        help_text += (
            "*الأوامر المتاحة للمسؤولين:*\n"
            "/add_admin `user_id` - إضافة مسؤول جديد\n"
            "/remove_admin `user_id` - إزالة مسؤول\n"
            "/list_admins - عرض قائمة المسؤولين\n"
            "/add_api `name` `key` `type` - إضافة أو تحديث مفتاح API (النوع: gemini أو chatgpt)\n"
            "/remove_api `name` - إزالة مفتاح API\n"
            "/update_bot - تحديث البوت من GitHub وإعادة تشغيله (يتطلب إعداد systemd)\n"
        )

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def list_apis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة بنماذج الذكاء الاصطناعي المتاحة"""
    logger.info(f"المستخدم {update.effective_user.id} طلب قائمة الـ APIs.")
    api_keys = db_handler.list_api_keys()
    message = format_api_list(api_keys)
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة أمر /ask لطرح سؤال على نموذج محدد"""
    user_id = update.effective_user.id
    args = context.args
    logger.info(f"المستخدم {user_id} استخدم أمر /ask بالوسائط: {args}")

    if len(args) < 2:
        await update.message.reply_text(
            "الرجاء استخدام التنسيق الصحيح: `/ask اسم_النموذج سؤالك`\n"
            "مثال: `/ask gemini ما هي عاصمة فرنسا؟`\n"
            "استخدم /list_apis لمعرفة الأسماء المتاحة."
        )
        return

    api_name = args[0]
    prompt = " ".join(args[1:])

    # التحقق من وجود الـ API المطلوب
    available_apis = [key_info["name"] for key_info in db_handler.list_api_keys()]
    if api_name not in available_apis:
        await update.message.reply_text(
            f"عذراً، لم يتم العثور على نموذج بالاسم `{api_name}`.\n"
            f"النماذج المتاحة حالياً: {', '.join(available_apis) if available_apis else 'لا يوجد'}.\n"
            "استخدم /list_apis للتأكد من الاسم.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # إرسال رسالة انتظار
    thinking_message = await update.message.reply_text(f"جارٍ التفكير باستخدام {api_name}... 🤔")

    # استدعاء دالة الذكاء الاصطناعي
    response = ai_handler.get_ai_response(api_name, prompt)

    # تعديل رسالة الانتظار بالرد أو رسالة الخطأ
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=thinking_message.message_id,
        text=response
    )
    logger.info(f"تم إرسال الرد للمستخدم {user_id} من {api_name}.")

# --- معالجات أوامر المسؤولين ---

@admin_required
async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إضافة مسؤول جديد (للمسؤولين فقط)"""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("الاستخدام: `/add_admin user_id`")
        return

    try:
        new_admin_id = int(context.args[0])
        success, message = db_handler.add_admin(new_admin_id)
        await update.message.reply_text(message)
    except ValueError:
        await update.message.reply_text("خطأ: معرف المستخدم يجب أن يكون رقماً.")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في add_admin_command: {e}")
        await update.message.reply_text(f"حدث خطأ غير متوقع: {e}")

@admin_required
async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إزالة مسؤول (للمسؤولين فقط)"""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("الاستخدام: `/remove_admin user_id`")
        return

    try:
        admin_to_remove = int(context.args[0])
        success, message = db_handler.remove_admin(admin_to_remove)
        await update.message.reply_text(message)
    except ValueError:
        await update.message.reply_text("خطأ: معرف المستخدم يجب أن يكون رقماً.")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في remove_admin_command: {e}")
        await update.message.reply_text(f"حدث خطأ غير متوقع: {e}")

@admin_required
async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة المسؤولين (للمسؤولين فقط)"""
    admin_ids = db_handler.list_admins()
    message = format_admin_list(admin_ids)
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

@admin_required
async def add_api_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إضافة أو تحديث مفتاح API (للمسؤولين فقط)"""
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("الاستخدام: `/add_api name key type` (النوع: gemini أو chatgpt)")
        return

    name, key, api_type = args
    api_type = api_type.lower()

    if api_type not in ["gemini", "chatgpt"]:
        await update.message.reply_text("خطأ: النوع يجب أن يكون `gemini` أو `chatgpt`.")
        return

    success, message = db_handler.add_api_key(name, key, api_type)
    await update.message.reply_text(message)

@admin_required
async def remove_api_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إزالة مفتاح API (للمسؤولين فقط)"""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("الاستخدام: `/remove_api name`")
        return

    name = context.args[0]
    success, message = db_handler.remove_api_key(name)
    await update.message.reply_text(message)

@admin_required
async def update_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تحديث البوت من GitHub وإعادة تشغيله (للمسؤولين فقط)"""
    user_id = update.effective_user.id
    logger.info(f"المسؤول {user_id} طلب تحديث البوت.")
    await update.message.reply_text("⏳ جارٍ تحديث البوت من GitHub وإعادة تشغيله...")

    script_path = os.path.join(config.PROJECT_PATH, "update.sh")
    if not os.path.exists(script_path):
         # محاولة إنشاء سكريبت التحديث إذا لم يكن موجوداً
        logger.warning(f"سكريبت التحديث {script_path} غير موجود. محاولة إنشائه.")
        update_script_content = f"""#!/bin/bash
cd "{config.PROJECT_PATH}" || exit 1

echo "Pulling latest changes from GitHub..."
git pull origin main # أو اسم الفرع الرئيسي لديك

echo "Installing/updating requirements..."
source venv/bin/activate
pip install -r requirements.txt

echo "Restarting bot service (using systemd)..."
sudo systemctl restart telegram_ai_bot.service # تأكد من أن اسم الخدمة صحيح

echo "Update process finished."
"""
        try:
            with open(script_path, "w") as f:
                f.write(update_script_content)
            os.chmod(script_path, 0o755) # جعل السكريبت قابلاً للتنفيذ
            logger.info(f"تم إنشاء سكريبت التحديث بنجاح: {script_path}")
            await update.message.reply_text("تم إنشاء سكريبت التحديث. يرجى التأكد من اسم الخدمة في السكريبت (`telegram_ai_bot.service`) ثم تشغيل الأمر /update_bot مرة أخرى.")
            return
        except Exception as e:
            logger.error(f"فشل إنشاء سكريبت التحديث: {e}")
            await update.message.reply_text(f"فشل إنشاء سكريبت التحديث: {e}. يرجى إنشائه يدوياً.")
            return

    try:
        # تنفيذ سكريبت التحديث
        logger.info(f"تنفيذ سكريبت التحديث: {script_path}")
        # استخدام shlex.split لتقسيم الأمر بشكل آمن
        process = subprocess.Popen(shlex.split(f"sudo bash {script_path}"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        output_message = "✅ تم الانتهاء من عملية التحديث.\n\n"
        if stdout:
            output_message += f"*المخرجات القياسية:*\n```\n{stdout[-1000:]}```\n\n" # عرض آخر 1000 حرف
        if stderr:
            output_message += f"*أخطاء قياسية:*\n```\n{stderr[-1000:]}```\n"
        if not stdout and not stderr:
             output_message += "(لا توجد مخرجات من السكريبت)"

        logger.info(f"مخرجات سكريبت التحديث:\nStdout: {stdout}\nStderr: {stderr}")
        # قد لا تصل هذه الرسالة إذا تمت إعادة تشغيل البوت بنجاح
        await update.message.reply_text(output_message, parse_mode=ParseMode.MARKDOWN)

    except FileNotFoundError:
        logger.error(f"خطأ: سكريبت التحديث {script_path} غير موجود.")
        await update.message.reply_text(f"خطأ: سكريبت التحديث {script_path} غير موجود. يرجى التأكد من المسار والإعدادات.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تنفيذ سكريبت التحديث: {e}")
        await update.message.reply_text(f"حدث خطأ أثناء تنفيذ سكريبت التحديث: {e}")

# --- معالج الأخطاء ---

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تسجيل الأخطاء التي تسببها تحديثات PTB"""
    logger.error("حدث استثناء أثناء معالجة تحديث:", exc_info=context.error)
    # يمكنك إضافة إشعار للمطور هنا إذا أردت
    # traceback.print_exception(type(context.error), context.error, context.error.__traceback__)

# --- الإعداد والتشغيل ---

if __name__ == "__main__":
    logger.info("بدء تشغيل البوت...")

    # التحقق من وجود رمز البوت
    if not config.TELEGRAM_TOKEN:
        logger.critical("خطأ فادح: رمز بوت تليجرام (TELEGRAM_TOKEN) غير موجود في الإعدادات أو متغيرات البيئة. لا يمكن تشغيل البوت.")
        sys.exit(1) # الخروج من البرنامج

    # تهيئة قاعدة البيانات (تتم أيضاً عند استيراد db_handler)
    # db_handler.initialize_database() # تأكد من أنها تعمل بشكل صحيح
    logger.info("تم التحقق من تهيئة قاعدة البيانات.")

    # إنشاء كائن التطبيق
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # تسجيل معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list_apis", list_apis_command))
    application.add_handler(CommandHandler("ask", ask_command))

    # تسجيل معالجات أوامر المسؤولين
    application.add_handler(CommandHandler("add_admin", add_admin_command))
    application.add_handler(CommandHandler("remove_admin", remove_admin_command))
    application.add_handler(CommandHandler("list_admins", list_admins_command))
    application.add_handler(CommandHandler("add_api", add_api_command))
    application.add_handler(CommandHandler("remove_api", remove_api_command))
    application.add_handler(CommandHandler("update_bot", update_bot_command))

    # تسجيل معالج الأخطاء
    application.add_error_handler(error_handler)

    # تشغيل البوت
    logger.info("البوت جاهز ويعمل...")
    application.run_polling()

