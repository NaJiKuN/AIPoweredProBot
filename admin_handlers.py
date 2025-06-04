# -*- coding: utf-8 -*-
"""Handlers for admin-specific commands."""

import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode

import keyboards
import utils
import database as db

# Conversation states for adding/editing API keys
(SELECT_SERVICE, ENTER_KEY, CONFIRM_KEY, SELECT_KEY_TO_EDIT, EDIT_KEY_OPTIONS, ENTER_NEW_KEY_VALUE, ENTER_NEW_SERVICE_NAME) = range(7)
# Conversation states for broadcasting
(ENTER_BROADCAST_MESSAGE, CONFIRM_BROADCAST) = range(2)
# Conversation states for adding admin
(ENTER_ADMIN_ID_TO_ADD,) = range(1)
# Conversation states for removing admin
(ENTER_ADMIN_ID_TO_REMOVE,) = range(1)

# --- Admin Main Menu --- 
@utils.user_registered
@utils.admin_required
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the main admin menu."""
    reply_markup = keyboards.create_admin_keyboard()
    await update.message.reply_text("⚙️ لوحة تحكم المسؤول:", reply_markup=reply_markup)

# --- Manage Admins --- 
@utils.user_registered
@utils.admin_required
async def manage_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the process of managing admins (view, add, remove)."""
    admin_ids = db.get_admin_ids()
    admin_list = "\n".join([f"- `{admin_id}`" for admin_id in admin_ids])
    if not admin_list:
        admin_list = "لا يوجد مسؤولون حالياً (باستثناء المسؤولين الأوليين في الإعدادات)."
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مسؤول", callback_data=f"{keyboards.CB_PREFIX_ADMIN}add_admin_start")],
        [InlineKeyboardButton("➖ إزالة مسؤول", callback_data=f"{keyboards.CB_PREFIX_ADMIN}remove_admin_start")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"{keyboards.CB_PREFIX_ADMIN}main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"👥 **إدارة المسؤولين:**\n\n**المسؤولون الحاليون في قاعدة البيانات:**\n{admin_list}\n\nاختر إجراءً:", 
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    return ConversationHandler.END # End this specific interaction, wait for button press

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user ID of the admin to add."""
    await update.callback_query.edit_message_text("يرجى إرسال معرف المستخدم (User ID) للمسؤول الجديد الذي ترغب بإضافته.")
    return ENTER_ADMIN_ID_TO_ADD

async def add_admin_receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the user ID and adds the admin."""
    try:
        admin_id_to_add = int(update.message.text.strip())
        # Check if user exists? Optional, but good practice.
        user_data = db.get_user(admin_id_to_add)
        if not user_data:
             await update.message.reply_text(f"⚠️ لم يتم العثور على مستخدم بالمعرف {admin_id_to_add}. يجب أن يبدأ المستخدم البوت أولاً (/start).")
             # Go back to admin menu or ask again?
             await admin_command(update, context) # Go back to main admin menu
             return ConversationHandler.END
             
        db.add_admin(admin_id_to_add)
        await update.message.reply_text(f"✅ تم إضافة المستخدم {admin_id_to_add} كمسؤول بنجاح.")
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صالح. يرجى إرسال رقم صحيح.")
        # Ask again
        await update.message.reply_text("يرجى إرسال معرف المستخدم (User ID) للمسؤول الجديد الذي ترغب بإضافته.")
        return ENTER_ADMIN_ID_TO_ADD
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء إضافة المسؤول: {e}")
        
    # Go back to admin menu after completion/error
    await admin_command(update, context)
    return ConversationHandler.END

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user ID of the admin to remove."""
    await update.callback_query.edit_message_text("يرجى إرسال معرف المستخدم (User ID) للمسؤول الذي ترغب بإزالته.")
    return ENTER_ADMIN_ID_TO_REMOVE

async def remove_admin_receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the user ID and removes the admin."""
    try:
        admin_id_to_remove = int(update.message.text.strip())
        # Prevent removing self? Or initial admins?
        if admin_id_to_remove == update.effective_user.id:
            await update.message.reply_text("❌ لا يمكنك إزالة نفسك كمسؤول.")
        elif str(admin_id_to_remove) in context.bot_data.get("initial_admins", []): # Assuming initial admins are stored in bot_data
             await update.message.reply_text(f"❌ لا يمكن إزالة المسؤول الأولي {admin_id_to_remove} عبر هذا الأمر.")
        else:
            success = db.remove_admin(admin_id_to_remove)
            if success:
                await update.message.reply_text(f"✅ تم إزالة الامتيازات الإدارية من المستخدم {admin_id_to_remove} بنجاح.")
            else:
                 # This case might not be reachable if remove_admin always returns True now
                 await update.message.reply_text(f"⚠️ لم يتم العثور على مسؤول بالمعرف {admin_id_to_remove} أو لا يمكن إزالته.")
                 
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صالح. يرجى إرسال رقم صحيح.")
        await update.message.reply_text("يرجى إرسال معرف المستخدم (User ID) للمسؤول الذي ترغب بإزالته.")
        return ENTER_ADMIN_ID_TO_REMOVE
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء إزالة المسؤول: {e}")

    # Go back to admin menu
    await admin_command(update, context)
    return ConversationHandler.END

# --- Manage API Keys --- 
@utils.user_registered
@utils.admin_required
async def manage_keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the API key management keyboard."""
    reply_markup = keyboards.create_api_key_management_keyboard()
    key_list_text = utils.format_api_key_list(db.get_all_api_keys())
    
    # Check if called from button or command
    if update.callback_query:
        await update.callback_query.edit_message_text(key_list_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
         await update.message.reply_text(key_list_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def add_key_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new API key. Asks for service name."""
    await update.callback_query.edit_message_text(
        "يرجى إرسال **اسم الخدمة** لهذا المفتاح (مثال: `GPT-4o mini`, `Midjourney`, `Claude 4 Sonnet + Thinking`).\n" 
        "**مهم:** يجب أن يتطابق الاسم مع الأسماء المستخدمة في إعدادات البوت ولوحة المفاتيح.",
        parse_mode=ParseMode.MARKDOWN
    )
    return SELECT_SERVICE

async def receive_service_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the service name and asks for the API key."""
    service_name = update.message.text.strip()
    if not service_name:
        await update.message.reply_text("اسم الخدمة لا يمكن أن يكون فارغاً. يرجى المحاولة مرة أخرى.")
        return SELECT_SERVICE
        
    context.user_data["new_key_service_name"] = service_name
    await update.message.reply_text(f"تم تحديد اسم الخدمة: `{service_name}`. الآن يرجى إرسال مفتاح API (API Key) الخاص بهذه الخدمة.", parse_mode=ParseMode.MARKDOWN)
    return ENTER_KEY

async def receive_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the API key and asks for confirmation."""
    api_key = update.message.text.strip()
    if not api_key:
        await update.message.reply_text("مفتاح API لا يمكن أن يكون فارغاً. يرجى المحاولة مرة أخرى.")
        return ENTER_KEY
        
    context.user_data["new_key_api_key"] = api_key
    service_name = context.user_data["new_key_service_name"]
    
    keyboard = [
        [InlineKeyboardButton("✅ تأكيد الإضافة", callback_data=f"{keyboards.CB_PREFIX_ADMIN}confirm_add_key")],
        [InlineKeyboardButton("❌ إلغاء", callback_data=f"{keyboards.CB_PREFIX_ADMIN}cancel_add_key")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**تأكيد إضافة المفتاح:**\n\n**الخدمة:** `{service_name}`\n**المفتاح:** `{api_key[:4]}...{api_key[-4:]}`\n\nهل تريد إضافة هذا المفتاح؟",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    return CONFIRM_KEY

async def confirm_add_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and adds the API key to the database."""
    service_name = context.user_data.pop("new_key_service_name", None)
    api_key = context.user_data.pop("new_key_api_key", None)
    admin_id = update.effective_user.id

    if not service_name or not api_key:
        await update.callback_query.edit_message_text("حدث خطأ: لم يتم العثور على معلومات المفتاح. يرجى البدء من جديد.")
        await manage_keys_command(update, context) # Show key list again
        return ConversationHandler.END

    try:
        db.add_api_key(service_name, api_key, admin_id)
        await update.callback_query.edit_message_text(f"✅ تم إضافة مفتاح API لخدمة `{service_name}` بنجاح.")
    except db.sqlite3.IntegrityError: # Handles UNIQUE constraint violation for service_name
         await update.callback_query.edit_message_text(f"⚠️ خطأ: خدمة باسم `{service_name}` موجودة بالفعل. يمكنك تعديل المفتاح الحالي بدلاً من إضافته.")
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ حدث خطأ أثناء إضافة المفتاح: {e}")

    # Clean up context
    context.user_data.pop("new_key_service_name", None)
    context.user_data.pop("new_key_api_key", None)
    
    # Show updated key list
    await manage_keys_command(update, context)
    return ConversationHandler.END

async def cancel_add_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the process of adding an API key."""
    context.user_data.pop("new_key_service_name", None)
    context.user_data.pop("new_key_api_key", None)
    await update.callback_query.edit_message_text("تم إلغاء عملية إضافة المفتاح.")
    await manage_keys_command(update, context) # Show key list again
    return ConversationHandler.END

# --- TODO: Implement Edit/Remove Key Logic using ConversationHandler similar to add --- 
# Placeholder for key details/edit/remove actions triggered from manage_keys_command keyboard
async def key_details_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     query = update.callback_query
     await query.answer() 
     _, key_id_str = utils.parse_callback_data(query.data)
     key_id = int(key_id_str)
     
     # Fetch key details from DB using key_id
     key_data = db._execute_query("SELECT key_id, service_name, api_key, is_active FROM api_keys WHERE key_id = ?", (key_id,), fetchone=True)
     
     if not key_data:
         await query.edit_message_text("لم يتم العثور على المفتاح المحدد.")
         return ConversationHandler.END
         
     k_id, service, key_val, is_active = key_data
     status = "🟢 نشط" if is_active else "🔴 غير نشط"
     mask = key_val[:4] + "..." + key_val[-4:] if key_val and len(key_val) > 8 else "[مفتاح غير صالح]"
     
     context.user_data["edit_key_id"] = k_id # Store ID for actions
     
     keyboard = [
         [InlineKeyboardButton("✏️ تعديل المفتاح", callback_data=f"{keyboards.CB_PREFIX_ADMIN}edit_key_value:{k_id}")],
         [InlineKeyboardButton("✏️ تعديل اسم الخدمة", callback_data=f"{keyboards.CB_PREFIX_ADMIN}edit_key_service:{k_id}")],
         [InlineKeyboardButton(f"تغيير الحالة إلى {'🔴 غير نشط' if is_active else '🟢 نشط'}", callback_data=f"{keyboards.CB_PREFIX_ADMIN}toggle_key_status:{k_id}")],
         [InlineKeyboardButton("🗑️ حذف المفتاح", callback_data=f"{keyboards.CB_PREFIX_ADMIN}delete_key_confirm:{k_id}")],
         [InlineKeyboardButton("🔙 رجوع لقائمة المفاتيح", callback_data=f"{keyboards.CB_PREFIX_ADMIN}manage_keys")]
     ]
     reply_markup = InlineKeyboardMarkup(keyboard)
     
     await query.edit_message_text(
         f"**تفاصيل المفتاح (ID: {k_id}):**\n\n**الخدمة:** {service}\n**المفتاح:** {mask}\n**الحالة:** {status}\n\nاختر إجراءً:",
         reply_markup=reply_markup,
         parse_mode=ParseMode.MARKDOWN
     )
     return EDIT_KEY_OPTIONS # State to handle button presses for edit/delete

# --- TODO: Handlers for edit_key_value, edit_key_service, toggle_key_status, delete_key_confirm --- 
# These would follow a similar pattern to the add_key conversation

# --- Broadcast --- 
@utils.user_registered
@utils.admin_required
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the broadcast conversation."""
    # Check if called from button or command
    if update.callback_query:
         await update.callback_query.answer()
         origin_message = update.callback_query.message
    else:
         origin_message = update.message
         
    await origin_message.reply_text("يرجى إرسال الرسالة التي ترغب بإرسالها لجميع المستخدمين.")
    return ENTER_BROADCAST_MESSAGE

async def broadcast_receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the broadcast message and asks for confirmation."""
    message_to_broadcast = update.message.text_html # Use HTML for formatting options
    context.user_data["broadcast_message"] = message_to_broadcast
    user_count = len(db.get_all_user_ids())
    
    keyboard = [
        [InlineKeyboardButton("✅ تأكيد الإرسال", callback_data=f"{keyboards.CB_PREFIX_ADMIN}confirm_broadcast")],
        [InlineKeyboardButton("❌ إلغاء", callback_data=f"{keyboards.CB_PREFIX_ADMIN}cancel_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**تأكيد الإرسال:**\n\n**الرسالة:**\n{message_to_broadcast}\n\nسيتم إرسال هذه الرسالة إلى **{user_count}** مستخدم. هل أنت متأكد؟",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return CONFIRM_BROADCAST

async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and sends the broadcast message."""
    message_text = context.user_data.pop("broadcast_message", None)
    query = update.callback_query
    await query.answer()

    if not message_text:
        await query.edit_message_text("حدث خطأ: لم يتم العثور على رسالة البث.")
        return ConversationHandler.END

    user_ids = db.get_all_user_ids()
    await query.edit_message_text(f"بدء إرسال الرسالة إلى {len(user_ids)} مستخدم...", reply_markup=None)
    
    sent_count = 0
    failed_count = 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_text, parse_mode=ParseMode.HTML)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send broadcast to {user_id}: {e}")
            failed_count += 1
        await asyncio.sleep(0.1) # Avoid hitting rate limits

    await query.message.reply_text(f"✅ اكتمل البث!\nتم الإرسال بنجاح إلى: {sent_count} مستخدم.\nفشل الإرسال إلى: {failed_count} مستخدم.")
    return ConversationHandler.END

async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the broadcast."""
    context.user_data.pop("broadcast_message", None)
    await update.callback_query.edit_message_text("تم إلغاء عملية البث.")
    return ConversationHandler.END

# --- View Stats --- 
@utils.user_registered
@utils.admin_required
async def view_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays usage statistics."""
    # Basic stats for now
    total_users = len(db.get_all_user_ids())
    admin_users = len(db.get_admin_ids())
    active_keys = len(db.get_active_service_names())
    all_keys_data = db.get_all_api_keys()
    total_keys = len(all_keys_data) if all_keys_data else 0
    
    # More detailed stats can be added by querying usage_stats table
    # e.g., total requests today, requests per model, etc.
    
    stats_text = (
        f"📊 **إحصائيات البوت:**\n\n"
        f"- إجمالي المستخدمين: {total_users}\n"
        f"- عدد المسؤولين: {admin_users}\n"
        f"- إجمالي مفاتيح API: {total_keys}\n"
        f"- مفاتيح API النشطة: {active_keys}\n"
        # Add more stats here
    )
    
    # Check if called from button or command
    if update.callback_query:
         await update.callback_query.answer()
         await update.callback_query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    else:
         await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

# --- Conversation Handlers Setup (to be added in bot.py) --- 
# Example structure (won't run here)
# add_key_conv = ConversationHandler(...)
# broadcast_conv = ConversationHandler(...)
# add_admin_conv = ConversationHandler(...)
# remove_admin_conv = ConversationHandler(...)
# edit_key_conv = ConversationHandler(...) 

