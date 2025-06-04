#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة المسؤولين
يحتوي على الوظائف الخاصة بإدارة المسؤولين والتحكم في البوت
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from config import ADMIN_ID

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

async def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مسؤولاً"""
    return str(user_id) == ADMIN_ID or db.is_admin(str(user_id))

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /admin للمسؤولين"""
    user_id = str(update.effective_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await update.message.reply_text("عذراً، هذا الأمر متاح فقط للمسؤولين.")
        return
    
    # إنشاء لوحة مفاتيح للمسؤول
    keyboard = [
        [InlineKeyboardButton("إدارة المسؤولين 👥", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("إدارة المشتركين 👤", callback_data="admin_manage_users")],
        [InlineKeyboardButton("إدارة مفاتيح API 🔑", callback_data="admin_manage_api_keys")],
        [InlineKeyboardButton("إحصائيات البوت 📊", callback_data="admin_stats")],
        [InlineKeyboardButton("إرسال رسالة للجميع 📣", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "مرحباً بك في لوحة تحكم المسؤول. يرجى اختيار الإجراء الذي تريد القيام به:",
        reply_markup=reply_markup
    )

async def admin_manage_admins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إدارة المسؤولين"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # الحصول على قائمة المسؤولين
    admins = db.get_all_admins()
    
    # إنشاء نص بقائمة المسؤولين
    admin_list_text = "قائمة المسؤولين الحاليين:\n\n"
    for admin_id in admins:
        admin_list_text += f"• {admin_id}\n"
    
    # إنشاء لوحة مفاتيح لإدارة المسؤولين
    keyboard = [
        [InlineKeyboardButton("إضافة مسؤول ➕", callback_data="admin_add_admin")],
        [InlineKeyboardButton("إزالة مسؤول ➖", callback_data="admin_remove_admin")],
        [InlineKeyboardButton("العودة للوحة التحكم 🔙", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(admin_list_text, reply_markup=reply_markup)

async def admin_add_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إضافة مسؤول جديد"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'add_admin'
    
    await query.edit_message_text(
        "يرجى إرسال معرف المستخدم الذي تريد إضافته كمسؤول.\n"
        "يمكنك إرسال معرف المستخدم مباشرة (مثل 123456789).",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="admin_cancel")]])
    )

async def admin_remove_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إزالة مسؤول"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # الحصول على قائمة المسؤولين
    admins = db.get_all_admins()
    
    # إنشاء لوحة مفاتيح لإزالة المسؤولين
    keyboard = []
    for admin_id in admins:
        # لا يمكن إزالة المسؤول الرئيسي
        if admin_id != ADMIN_ID:
            keyboard.append([InlineKeyboardButton(f"إزالة {admin_id}", callback_data=f"admin_remove_{admin_id}")])
    
    keyboard.append([InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_admins")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر المسؤول الذي تريد إزالته:", reply_markup=reply_markup)

async def admin_process_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إزالة مسؤول محدد"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # استخراج معرف المسؤول المراد إزالته
    admin_to_remove = query.data.split('_')[-1]
    
    # التحقق من أن المسؤول ليس المسؤول الرئيسي
    if admin_to_remove == ADMIN_ID:
        await query.edit_message_text("لا يمكن إزالة المسؤول الرئيسي.")
        return
    
    # إزالة المسؤول
    db.remove_admin(admin_to_remove)
    logger.info(f"تمت إزالة المسؤول {admin_to_remove} بواسطة {user_id}")
    
    await query.edit_message_text(
        f"تمت إزالة المسؤول {admin_to_remove} بنجاح.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_admins")]])
    )

async def admin_process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل في وضع المسؤول"""
    user_id = str(update.effective_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        return
    
    # التحقق من الإجراء الحالي
    if 'admin_action' in context.user_data:
        action = context.user_data['admin_action']
        
        if action == 'add_admin':
            # إضافة مسؤول جديد
            new_admin_id = update.message.text.strip()
            
            # التحقق من صحة المعرف
            if not new_admin_id.isdigit():
                await update.message.reply_text(
                    "معرف المستخدم غير صالح. يرجى إرسال معرف رقمي صحيح.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="admin_cancel")]])
                )
                return
            
            # التحقق مما إذا كان المستخدم مسؤولاً بالفعل
            if db.is_admin(new_admin_id):
                await update.message.reply_text(
                    "هذا المستخدم مسؤول بالفعل.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_admins")]])
                )
                return
            
            # إضافة المسؤول الجديد
            db.add_admin(new_admin_id, user_id)
            logger.info(f"تمت إضافة مسؤول جديد {new_admin_id} بواسطة {user_id}")
            
            # إعادة تعيين الحالة
            del context.user_data['admin_action']
            
            await update.message.reply_text(
                f"تمت إضافة المسؤول {new_admin_id} بنجاح.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_admins")]])
            )
        
        elif action == 'broadcast':
            # إرسال رسالة للجميع
            broadcast_message = update.message.text
            
            # الحصول على جميع المستخدمين
            users = db.get_all_users()
            
            # إرسال الرسالة لكل مستخدم
            success_count = 0
            fail_count = 0
            
            await update.message.reply_text(f"جاري إرسال الرسالة إلى {len(users)} مستخدم...")
            
            for user_id in users:
                try:
                    await context.bot.send_message(chat_id=user_id, text=broadcast_message)
                    success_count += 1
                except Exception as e:
                    logger.error(f"فشل إرسال الرسالة إلى المستخدم {user_id}: {e}")
                    fail_count += 1
            
            # إعادة تعيين الحالة
            del context.user_data['admin_action']
            
            await update.message.reply_text(
                f"تم إرسال الرسالة بنجاح إلى {success_count} مستخدم.\n"
                f"فشل الإرسال إلى {fail_count} مستخدم.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_back")]])
            )

async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إرسال رسالة للجميع"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'broadcast'
    
    await query.edit_message_text(
        "يرجى إرسال الرسالة التي تريد إرسالها لجميع المستخدمين.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="admin_cancel")]])
    )

async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع عرض إحصائيات البوت"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # الحصول على الإحصائيات
    stats = db.get_user_stats()
    
    stats_text = f"""📊 إحصائيات البوت:

👥 إجمالي المستخدمين: {stats['total_users']}
👤 المستخدمين النشطين (24 ساعة): {stats['active_users']}
💰 إجمالي الإنفاق: {stats['total_spent']} ⭐
💵 إجمالي الرصيد المتاح: {stats['total_balance']} ⭐
"""
    
    await query.edit_message_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_back")]])
    )

async def admin_manage_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إدارة المستخدمين"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # إنشاء لوحة مفاتيح لإدارة المستخدمين
    keyboard = [
        [InlineKeyboardButton("البحث عن مستخدم 🔍", callback_data="admin_search_user")],
        [InlineKeyboardButton("تعديل رصيد محفظة 💰", callback_data="admin_edit_wallet")],
        [InlineKeyboardButton("تعديل اشتراك مستخدم 🌟", callback_data="admin_edit_subscription")],
        [InlineKeyboardButton("العودة للوحة التحكم 🔙", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر إجراء إدارة المستخدمين:", reply_markup=reply_markup)

async def admin_search_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع البحث عن مستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'search_user'
    
    await query.edit_message_text(
        "يرجى إرسال معرف المستخدم الذي تريد البحث عنه.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="admin_cancel")]])
    )

async def admin_edit_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تعديل رصيد محفظة مستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'edit_wallet_user_id'
    
    await query.edit_message_text(
        "يرجى إرسال معرف المستخدم الذي تريد تعديل رصيد محفظته.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="admin_cancel")]])
    )

async def admin_edit_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تعديل اشتراك مستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'edit_subscription_user_id'
    
    await query.edit_message_text(
        "يرجى إرسال معرف المستخدم الذي تريد تعديل اشتراكه.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="admin_cancel")]])
    )

async def admin_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء الإجراء الحالي"""
    query = update.callback_query
    await query.answer()
    
    # إعادة تعيين الحالة
    if 'admin_action' in context.user_data:
        del context.user_data['admin_action']
    
    await query.edit_message_text(
        "تم إلغاء الإجراء.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_back")]])
    )

async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة إلى لوحة تحكم المسؤول"""
    query = update.callback_query
    await query.answer()
    
    # إعادة تعيين الحالة
    if 'admin_action' in context.user_data:
        del context.user_data['admin_action']
    
    # إنشاء لوحة مفاتيح للمسؤول
    keyboard = [
        [InlineKeyboardButton("إدارة المسؤولين 👥", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("إدارة المشتركين 👤", callback_data="admin_manage_users")],
        [InlineKeyboardButton("إدارة مفاتيح API 🔑", callback_data="admin_manage_api_keys")],
        [InlineKeyboardButton("إحصائيات البوت 📊", callback_data="admin_stats")],
        [InlineKeyboardButton("إرسال رسالة للجميع 📣", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "مرحباً بك في لوحة تحكم المسؤول. يرجى اختيار الإجراء الذي تريد القيام به:",
        reply_markup=reply_markup
    )

# تسجيل معالجات الأوامر والاستجابات
def register_admin_handlers(application):
    """تسجيل معالجات أوامر المسؤول"""
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("status", admin_stats_callback))
    application.add_handler(CommandHandler("podcast", admin_broadcast_callback))
    
    # معالجات الاستجابة للأزرار
    application.add_handler(CallbackQueryHandler(admin_manage_admins_callback, pattern="^admin_manage_admins$"))
    application.add_handler(CallbackQueryHandler(admin_add_admin_callback, pattern="^admin_add_admin$"))
    application.add_handler(CallbackQueryHandler(admin_remove_admin_callback, pattern="^admin_remove_admin$"))
    application.add_handler(CallbackQueryHandler(admin_process_remove_admin, pattern="^admin_remove_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$"))
    application.add_handler(CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(admin_manage_users_callback, pattern="^admin_manage_users$"))
    application.add_handler(CallbackQueryHandler(admin_search_user_callback, pattern="^admin_search_user$"))
    application.add_handler(CallbackQueryHandler(admin_edit_wallet_callback, pattern="^admin_edit_wallet$"))
    application.add_handler(CallbackQueryHandler(admin_edit_subscription_callback, pattern="^admin_edit_subscription$"))
    application.add_handler(CallbackQueryHandler(admin_cancel_callback, pattern="^admin_cancel$"))
    application.add_handler(CallbackQueryHandler(admin_back_callback, pattern="^admin_back$"))
