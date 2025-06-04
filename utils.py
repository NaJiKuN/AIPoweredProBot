from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

def send_typing_action(func):
    """ديكوراتور لإظهار حالة الكتابة أثناء معالجة الأمر"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        return await func(update, context, *args, **kwargs)
    return wrapper

def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مسؤولاً"""
    return user_id in ADMIN_IDS
