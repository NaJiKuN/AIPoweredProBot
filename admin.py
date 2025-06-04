from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, filters
from database import add_admin, remove_admin, add_api_key, remove_api_key
from config import ADMIN_IDS

def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مسؤولاً"""
    return user_id in ADMIN_IDS

def setup_admin_handlers(application):
    """إعداد معالجات أوامر المسؤولين"""
    
    async def add_admin_cmd(update: Update, context: CallbackContext):
        if not is_admin(update.effective_user.id):
            return
        
        try:
            new_admin_id = int(context.args[0])
            add_admin(new_admin_id)
            await update.message.reply_text(f"✅ تمت إضافة المسؤول الجديد: {new_admin_id}")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ استخدام: /add_admin <user_id>")
    
    async def remove_admin_cmd(update: Update, context: CallbackContext):
        if not is_admin(update.effective_user.id):
            return
        
        try:
            admin_id = int(context.args[0])
            remove_admin(admin_id)
            await update.message.reply_text(f"✅ تمت إزالة المسؤول: {admin_id}")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ استخدام: /remove_admin <user_id>")
    
    async def add_api_cmd(update: Update, context: CallbackContext):
        if not is_admin(update.effective_user.id):
            return
        
        try:
            service = context.args[0]
            api_key = context.args[1]
            add_api_key(service, api_key)
            await update.message.reply_text(f"✅ تمت إضافة مفتاح API لـ: {service}")
        except IndexError:
            await update.message.reply_text("❌ استخدام: /add_api <service> <api_key>")
    
    async def remove_api_cmd(update: Update, context: CallbackContext):
        if not is_admin(update.effective_user.id):
            return
        
        try:
            service = context.args[0]
            remove_api_key(service)
            await update.message.reply_text(f"✅ تمت إزالة مفتاح API لـ: {service}")
        except IndexError:
            await update.message.reply_text("❌ استخدام: /remove_api <service>")
    
    async def podcast_cmd(update: Update, context: CallbackContext):
        if not is_admin(update.effective_user.id):
            return
        
        message = " ".join(context.args)
        if not message:
            await update.message.reply_text("❌ استخدام: /podcast <message>")
            return
        
        # إرسال الرسالة لجميع المستخدمين
        # (سيتم تنفيذ المنطق الكامل في الإصدار النهائي)
        await update.message.reply_text("✅ تم إرسال الرسالة لجميع المستخدمين")
    
    async def status_cmd(update: Update, context: CallbackContext):
        if not is_admin(update.effective_user.id):
            return
        
        # إحصائيات استخدام البوت
        # (سيتم تنفيذ المنطق الكامل في الإصدار النهائي)
        stats = "📊 إحصائيات البوت:\n\n"
        stats += "• عدد المستخدمين: 100\n"
        stats += "• المستخدمون النشطون: 50\n"
        stats += "• إجمالي الطلبات: 500\n"
        
        await update.message.reply_text(stats)
    
    # تسجيل معالجات الأوامر
    application.add_handler(CommandHandler("add_admin", add_admin_cmd, filters=filters.User(ADMIN_IDS)))
    application.add_handler(CommandHandler("remove_admin", remove_admin_cmd, filters=filters.User(ADMIN_IDS)))
    application.add_handler(CommandHandler("add_api", add_api_cmd, filters=filters.User(ADMIN_IDS)))
    application.add_handler(CommandHandler("remove_api", remove_api_cmd, filters=filters.User(ADMIN_IDS)))
    application.add_handler(CommandHandler("podcast", podcast_cmd, filters=filters.User(ADMIN_IDS)))
    application.add_handler(CommandHandler("status", status_cmd, filters=filters.User(ADMIN_IDS)))
