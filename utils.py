# -*- coding: utf-8 -*-
"""وحدة الأدوات المساعدة والديكورات للبوت"""

import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from db_handler import is_admin

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\")
logger = logging.getLogger(__name__)

def admin_required(func):
    """ديكور للتحقق من أن المستخدم الذي استدعى الأمر هو مسؤول مسجل."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        logger.debug(f"التحقق من صلاحيات المسؤول للمستخدم: {user_id} للأمر: {func.__name__}")
        if not is_admin(user_id):
            logger.warning(f"المستخدم {user_id} حاول تنفيذ أمر المسؤول ", {func.__name__} دون صلاحيات.")
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمسؤولين فقط.")
            return
        logger.debug(f"المستخدم {user_id} لديه صلاحيات المسؤول. تنفيذ الأمر: {func.__name__}")
        return await func(update, context, *args, **kwargs)
    return wrapped

# يمكنك إضافة المزيد من الدوال المساعدة هنا إذا لزم الأمر
# مثلاً، دالة لتنسيق قوائم الـ API أو المسؤولين
def format_api_list(api_keys):
    """تنسيق قائمة مفاتيح API لعرضها للمستخدم."""
    if not api_keys:
        return "لا توجد مفاتيح API مضافة حالياً."
    message = "قائمة مفاتيح API المتاحة:\n\n"
    for key_info in api_keys:
        message += f"- الاسم: `{key_info[\'name\']}` (النوع: `{key_info[\'type\']}`)\n"
    return message

def format_admin_list(admin_ids):
    """تنسيق قائمة المسؤولين لعرضها."""
    if not admin_ids:
        # نظرياً، يجب أن يكون هناك دائماً المسؤول الأولي على الأقل
        return "لا يوجد مسؤولون مسجلون (هذه حالة غير متوقعة!)."
    message = "قائمة المسؤولين الحاليين:\n\n"
    for admin_id in admin_ids:
        message += f"- `{admin_id}`\n"
    return message

