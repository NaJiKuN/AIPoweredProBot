# -*- coding: utf-8 -*-
"""Handlers for user-specific commands like /account, /premium, /settings, /model."""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import keyboards
import utils
import database as db

@utils.user_registered
async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the user's account information and subscription status."""
    user_id = update.effective_user.id
    account_status_text = utils.format_account_status(user_id)
    # Maybe add a keyboard to refresh or go back?
    await update.message.reply_text(account_status_text, parse_mode=ParseMode.MARKDOWN)

@utils.user_registered
async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the premium subscription and package options."""
    premium_text = "اختر خدمة للشراء:"
    reply_markup = keyboards.create_premium_keyboard()
    
    # Check if the keyboard has more than just the title and the fallback message
    if reply_markup and len(reply_markup.inline_keyboard) > 2:
        await update.message.reply_text(premium_text, reply_markup=reply_markup)
    elif reply_markup and len(reply_markup.inline_keyboard) == 2: # Title + fallback message
         await update.message.reply_text("عذراً، لا توجد اشتراكات أو حزم متاحة للشراء في الوقت الحالي. يرجى مراجعة المسؤول.")
    else: # Should not happen if create_premium_keyboard is correct
         await update.message.reply_text("حدث خطأ أثناء عرض خيارات الاشتراك.")

@utils.user_registered
async def delete_context_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the conversation context for the user."""
    user_id = update.effective_user.id
    db.update_user_context(user_id, None) # Set context to None in DB
    # Clear context in bot's memory if stored there as well (depends on implementation)
    context.user_data.pop("conversation_context", None) 
    await update.message.reply_text("تم حذف سياق المحادثة بنجاح. يمكنك الآن بدء موضوع جديد.")

@utils.user_registered
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays user settings options, primarily model selection for now."""
    user_id = update.effective_user.id
    settings_text = "⚙️ **إعدادات البوت**\n\nيمكنك هنا تغيير بعض إعدادات البوت الخاص بك."
    # For now, settings mainly links to model selection
    reply_markup = keyboards.create_model_selection_keyboard(user_id)
    await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

@utils.user_registered
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the model selection keyboard directly."""
    user_id = update.effective_user.id
    model_text = "🧠 اختر نموذج الذكاء الاصطناعي الذي تفضل استخدامه:"
    reply_markup = keyboards.create_model_selection_keyboard(user_id)
    await update.message.reply_text(model_text, reply_markup=reply_markup)

# Note: CallbackQueryHandlers for button presses (like selecting a model or package)
# will be handled in a separate handler file or the main bot file.

