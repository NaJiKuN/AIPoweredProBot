# -*- coding: utf-8 -*-
import logging
import asyncio
import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# Import configuration, database, keyboards, utilities, and handlers
import config
import database as db
import keyboards
import utils
# Assuming ai_handlers.py for AI logic, create if needed
from handlers import general_handlers, user_handlers, admin_handlers, ai_handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Conversation Handler States (Imported from admin_handlers for clarity) ---
# API Key Management
(SELECT_SERVICE, ENTER_KEY, CONFIRM_KEY, SELECT_KEY_TO_EDIT, EDIT_KEY_OPTIONS, ENTER_NEW_KEY_VALUE, ENTER_NEW_SERVICE_NAME) = range(7)
# Broadcast Management
(ENTER_BROADCAST_MESSAGE, CONFIRM_BROADCAST) = range(admin_handlers.CONFIRM_KEY + 1, admin_handlers.CONFIRM_KEY + 3)
# Admin Management
(ENTER_ADMIN_ID_TO_ADD,) = range(admin_handlers.CONFIRM_BROADCAST + 1 , admin_handlers.CONFIRM_BROADCAST + 2)
(ENTER_ADMIN_ID_TO_REMOVE,) = range(admin_handlers.ENTER_ADMIN_ID_TO_ADD + 1, admin_handlers.ENTER_ADMIN_ID_TO_ADD + 2)
# Edit Key Value / Service Name (Reusing states for simplicity, ensure distinct entry points)
(EDIT_KEY_VALUE_ENTRY, EDIT_SERVICE_NAME_ENTRY) = range(admin_handlers.ENTER_ADMIN_ID_TO_REMOVE + 1, admin_handlers.ENTER_ADMIN_ID_TO_REMOVE + 3)

# --- Pricing (Ideally move to config or a dedicated pricing module) ---
PRICES = {
    # Premium Subscriptions (in wallet currency ⭐)
    "premium_monthly": 170,
    "premium_x2_monthly": 320,
    "combo_monthly": 580,
    # Packages (in wallet currency ⭐)
    "chatgpt": {50: 175, 100: 320, 200: 620, 500: 1550},
    "claude": {100: 175, 200: 320, 500: 720, 1000: 1200},
    "mjflux": {50: 175, 100: 320, 200: 620, 500: 1400},
    "video": {10: 375, 20: 730, 50: 1750},
    "suno": {20: 175, 50: 425, 100: 780},
}

# --- Main Callback Query Handler ---
@utils.user_registered # Ensure user is in DB for callbacks too
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer() # Answer callback query first

    prefix, data = utils.parse_callback_data(query.data)
    user_id = query.from_user.id

    logger.info(f"Callback received: prefix=\"{prefix}\", data=\"{data}\" from user {user_id}")

    # --- Action Callbacks (act:) ---
    if prefix == keyboards.CB_PREFIX_ACTION:
        if data == "show_premium":
            premium_text = "اختر خدمة للشراء:"
            reply_markup = keyboards.create_premium_keyboard()
            if reply_markup and len(reply_markup.inline_keyboard) > 2:
                 await query.edit_message_text(text=premium_text, reply_markup=reply_markup)
            else:
                 await query.edit_message_text(text="عذراً، لا توجد اشتراكات أو حزم متاحة للشراء في الوقت الحالي.")
        elif data == "show_settings":
            # TODO: Implement full settings logic
            settings_text = "⚙️ **إعدادات البوت**\n\nاختر الإعداد الذي ترغب بتغييره:"
            reply_markup = keyboards.create_settings_keyboard(user_id) # Needs implementation in keyboards.py
            await query.edit_message_text(text=settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        elif data == "show_account":
            account_status_text = utils.format_account_status(user_id)
            reply_markup = keyboards.create_account_keyboard() # Add buy balance buttons
            await query.edit_message_text(text=account_status_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        elif data == "show_help":
            # Help text is long, send as new message
            await general_handlers.help_command(update, context) # Call the command handler
        elif data == "show_chatgpt_packages":
            reply_markup = keyboards.create_package_selection_keyboard("chatgpt", PRICES.get("chatgpt", {}))
            await query.edit_message_text(text="اختر حجم حزمة ChatGPT Plus:", reply_markup=reply_markup)
        elif data == "show_claude_packages":
            reply_markup = keyboards.create_package_selection_keyboard("claude", PRICES.get("claude", {}))
            await query.edit_message_text(text="اختر حجم حزمة Claude:", reply_markup=reply_markup)
        elif data == "show_mjflux_packages":
            reply_markup = keyboards.create_package_selection_keyboard("mjflux", PRICES.get("mjflux", {}))
            await query.edit_message_text(text="اختر حجم حزمة Midjourney & Flux:", reply_markup=reply_markup)
        elif data == "show_video_packages":
             # --- IMPORTANT VIDEO CHECK --- 
             # This check should ideally be based on user roles/permissions, not just a flag
             is_pro_member = True # Assume Pro for now to show packages, replace with actual check
             if not is_pro_member:
                 await query.message.reply_text(
                     "🎬 ميزة إنشاء الفيديو متاحة للأعضاء المميزين (Pro) فقط.\n"
                     "يرجى الترقية إلى العضوية المميزة للاستفادة من هذه الميزة."
                 )
                 return
             else:
                 reply_markup = keyboards.create_package_selection_keyboard("video", PRICES.get("video", {}))
                 await query.edit_message_text(text="اختر حجم حزمة الفيديو:", reply_markup=reply_markup)
        elif data == "show_suno_packages":
            reply_markup = keyboards.create_package_selection_keyboard("suno", PRICES.get("suno", {}))
            await query.edit_message_text(text="اختر حجم حزمة Suno:", reply_markup=reply_markup)
        elif data == "buy_balance":
            # TODO: Initiate Plisio payment process
            await query.edit_message_text("عملية شراء الرصيد عبر Plisio (نجوم تليجرام) قيد التطوير.")
        # Add other action handlers here (e.g., for settings submenus)

    # --- Model Selection Callbacks (model:) ---
    elif prefix == keyboards.CB_PREFIX_MODEL:
        model_name = data
        # Check if model exists and has an active key before setting
        active_keys = db.get_active_service_names()
        if model_name in active_keys:
            db.set_preferred_model(user_id, model_name)
            await query.edit_message_text(f"✅ تم تغيير النموذج المفضل إلى: **{model_name}**", parse_mode=ParseMode.MARKDOWN)
            # Refresh settings menu
            settings_text = "⚙️ **إعدادات البوت**\n\nاختر الإعداد الذي ترغب بتغييره:"
            reply_markup = keyboards.create_settings_keyboard(user_id)
            await query.edit_message_text(text=settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(f"⚠️ عذراً، النموذج **{model_name}** غير متاح حالياً أو لا يوجد مفتاح API نشط له.")
            # Optionally show model selection again
            # reply_markup = keyboards.create_model_selection_keyboard(user_id)
            # await query.message.reply_text("اختر نموذجاً آخر:", reply_markup=reply_markup)

    # --- Premium Purchase Callbacks (prem:) ---
    elif prefix == keyboards.CB_PREFIX_PREMIUM:
        product_id = data
        price = PRICES.get(product_id)
        product_name = ""

        if product_id == "premium_monthly":
            product_name = "الاشتراك المميز الشهري"
        elif product_id == "premium_x2_monthly":
            product_name = "الاشتراك المميز X2 الشهري"
        elif product_id == "combo_monthly":
            product_name = "الكومبو الشهري"

        if price is None or not product_name:
            await query.edit_message_text("⚠️ طلب شراء غير معروف أو غير صالح.")
            return

        # Check balance
        current_balance = db.get_wallet_balance(user_id)
        if current_balance < price:
            await query.edit_message_text(f"⚠️ رصيدك غير كافٍ ({current_balance:.2f} ⭐) لشراء **{product_name}** (السعر: {price} ⭐).\nيرجى شحن رصيدك أولاً.", parse_mode=ParseMode.MARKDOWN)
            return

        # Attempt to deduct balance
        if db.deduct_wallet_balance(user_id, price):
            # Grant subscription/package on successful deduction
            purchase_successful = False
            if product_id == "premium_monthly":
                db.grant_premium(user_id, duration_days=30, daily_limit=100)
                purchase_successful = True
            elif product_id == "premium_x2_monthly":
                db.grant_premium(user_id, duration_days=30, daily_limit=200)
                purchase_successful = True
            elif product_id == "combo_monthly":
                # Grant base premium
                db.grant_premium(user_id, duration_days=30, daily_limit=100)
                # Add package components (Define specific package types in DB/logic)
                # Example: Assuming combo includes 100 ChatGPT Plus and 100 MJ/Flux
                db.add_package(user_id, "COMBO_CHATGPT_PLUS_100", 100) # Use consistent naming
                db.add_package(user_id, "COMBO_MJFLUX_100", 100)
                purchase_successful = True

            if purchase_successful:
                await query.edit_message_text(f"✅ تم شراء وتفعيل **{product_name}** بنجاح مقابل {price} ⭐!", parse_mode=ParseMode.MARKDOWN)
                # Show updated account status
                account_status_text = utils.format_account_status(user_id)
                reply_markup = keyboards.create_account_keyboard()
                await query.message.reply_text(f"**حالة حسابك المحدثة:**\n\n{account_status_text}", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                # This case should ideally not happen if deduction succeeded but granting failed
                # Rollback deduction? Or log error.
                logger.error(f"Deduction succeeded for {user_id} buying {product_name}, but granting failed.")
                # Refund the user
                db.add_wallet_balance(user_id, price)
                await query.edit_message_text(f"⚠️ حدث خطأ أثناء تفعيل **{product_name}**. تم استرجاع المبلغ ({price} ⭐). يرجى المحاولة مرة أخرى أو الاتصال بالدعم.", parse_mode=ParseMode.MARKDOWN)
        else:
            # Deduction failed (e.g., race condition, though balance check should prevent this)
            await query.edit_message_text(f"⚠️ فشلت عملية خصم المبلغ لـ **{product_name}**. رصيدك الحالي: {db.get_wallet_balance(user_id):.2f} ⭐. يرجى المحاولة مرة أخرى.", parse_mode=ParseMode.MARKDOWN)

    # --- Package Purchase Callbacks (pkg:) ---
    elif prefix == keyboards.CB_PREFIX_PACKAGE:
        # Format: pkg:<type>:<requests>
        parts = data.split(":")
        if len(parts) == 2:
            package_type_code, requests_str = parts
            try:
                requests_count = int(requests_str)
                # Get price
                price = PRICES.get(package_type_code, {}).get(requests_count)
                
                if price is None:
                    await query.edit_message_text("⚠️ حزمة غير معروفة أو حجم غير صالح.")
                    return

                # Construct package name and DB type
                package_name = f"حزمة {package_type_code.upper()} ({requests_count} طلب)"
                db_package_type = f"{package_type_code.upper()}_{requests_count}"
                # Special cases for naming consistency
                if package_type_code == "mjflux": 
                    package_name = f"حزمة Midjourney & Flux ({requests_count} صورة)"
                    db_package_type = f"MIDJOURNEY_FLUX_{requests_count}"
                if package_type_code == "chatgpt": 
                    package_name = f"حزمة ChatGPT Plus ({requests_count} طلب)"
                    db_package_type = f"CHATGPT_PLUS_{requests_count}"
                if package_type_code == "video":
                    package_name = f"حزمة فيديو ({requests_count} إنشاء)"
                    db_package_type = f"VIDEO_{requests_count}"
                if package_type_code == "suno":
                    package_name = f"حزمة أغاني Suno ({requests_count} إنشاء)"
                    db_package_type = f"SUNO_{requests_count}"
                # ... add other mappings if DB types differ significantly

                # Check balance
                current_balance = db.get_wallet_balance(user_id)
                if current_balance < price:
                    await query.edit_message_text(f"⚠️ رصيدك غير كافٍ ({current_balance:.2f} ⭐) لشراء **{package_name}** (السعر: {price} ⭐).\nيرجى شحن رصيدك أولاً.", parse_mode=ParseMode.MARKDOWN)
                    return

                # Attempt to deduct balance
                if db.deduct_wallet_balance(user_id, price):
                    # Add package on successful deduction
                    db.add_package(user_id, db_package_type, requests_count)
                    await query.edit_message_text(f"✅ تم شراء **{package_name}** بنجاح مقابل {price} ⭐!", parse_mode=ParseMode.MARKDOWN)
                    # Show updated account status
                    account_status_text = utils.format_account_status(user_id)
                    reply_markup = keyboards.create_account_keyboard()
                    await query.message.reply_text(f"**حالة حسابك المحدثة:**\n\n{account_status_text}", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                else:
                    # Deduction failed
                    await query.edit_message_text(f"⚠️ فشلت عملية خصم المبلغ لـ **{package_name}**. رصيدك الحالي: {db.get_wallet_balance(user_id):.2f} ⭐. يرجى المحاولة مرة أخرى.", parse_mode=ParseMode.MARKDOWN)

            except ValueError:
                 await query.edit_message_text("⚠️ بيانات الحزمة غير صالحة (عدد الطلبات يجب أن يكون رقماً).")
        else:
            await query.edit_message_text("⚠️ طلب شراء حزمة غير معروف أو بتنسيق غير صحيح.")
            
    # --- Admin Callbacks (admin:) --- 
    # Route admin callbacks to their respective handlers or conversation entries
    elif prefix == keyboards.CB_PREFIX_ADMIN:
        # Simple actions handled directly
        if data == "manage_keys":
            await admin_handlers.manage_keys_command(update, context)
        elif data == "manage_admins":
            await admin_handlers.manage_admins_command(update, context)
        elif data == "view_stats":
            await admin_handlers.view_stats_command(update, context)
        elif data == "main_menu": # Go back to main admin menu
             reply_markup = keyboards.create_admin_keyboard()
             await query.edit_message_text("⚙️ لوحة تحكم المسؤول:", reply_markup=reply_markup)
        # --- Key Management Actions --- 
        elif data.startswith("key_details:"):
             # Entry point for the edit key conversation handler
             await admin_handlers.key_details_handler(update, context)
        elif data.startswith("edit_key_value:"):
             _, key_id = data.split(":")
             context.user_data["edit_key_id"] = int(key_id)
             await query.edit_message_text("يرجى إرسال قيمة مفتاح API الجديدة.")
             return EDIT_KEY_VALUE_ENTRY # Return state for ConversationHandler
        elif data.startswith("edit_key_service:"):
             _, key_id = data.split(":")
             context.user_data["edit_key_id"] = int(key_id)
             await query.edit_message_text("يرجى إرسال اسم الخدمة الجديد.")
             return EDIT_SERVICE_NAME_ENTRY # Return state for ConversationHandler
        elif data.startswith("toggle_key_status:"):
             _, key_id = data.split(":")
             key_data = db._execute_query("SELECT is_active FROM api_keys WHERE key_id = ?", (int(key_id),), fetchone=True)
             if key_data:
                 new_status = not key_data[0]
                 db.update_api_key(int(key_id), is_active=new_status)
                 status_text = 'نشط' if new_status else 'غير نشط'
                 await query.edit_message_text(f"✅ تم تغيير حالة المفتاح {key_id} إلى {status_text}.")
                 await admin_handlers.manage_keys_command(update, context) # Refresh list
             else:
                 await query.edit_message_text("لم يتم العثور على المفتاح.")
             return ConversationHandler.END # End conversation if any
        elif data.startswith("delete_key_confirm:"):
             _, key_id = data.split(":")
             # Ask for confirmation maybe?
             db.remove_api_key(int(key_id))
             await query.edit_message_text(f"🗑️ تم حذف المفتاح ID: {key_id} بنجاح.")
             await admin_handlers.manage_keys_command(update, context) # Refresh list
             return ConversationHandler.END # End conversation if any
        # --- Add Key Conversation --- 
        elif data == "add_key_start":
             # Let the ConversationHandler catch this via CallbackQueryHandler entry
             pass 
        elif data == "confirm_add_key":
             # Should be handled by ConversationHandler state CONFIRM_KEY
             pass
        elif data == "cancel_add_key":
             # Should be handled by ConversationHandler state CONFIRM_KEY
             pass
        # --- Broadcast Conversation --- 
        elif data == "broadcast":
             # Let the ConversationHandler catch this
             pass
        elif data == "confirm_broadcast":
             # Should be handled by ConversationHandler state CONFIRM_BROADCAST
             pass
        elif data == "cancel_broadcast":
             # Should be handled by ConversationHandler state CONFIRM_BROADCAST
             pass
        # --- Admin Management Conversation --- 
        elif data == "add_admin_start":
             pass # Let ConversationHandler handle this
        elif data == "remove_admin_start":
             pass # Let ConversationHandler handle this
             
    # --- Fallback for unknown callbacks ---
    else:
        logger.warning(f"Unhandled callback query prefix: {prefix} with data: {data}")
        try:
            await query.edit_message_text("حدث خطأ غير متوقع أو أن هذا الزر لم يعد صالحاً.")
        except Exception as e:
             logger.error(f"Error editing message on unhandled callback: {e}")

# --- Message Handler for AI Interaction ---
@utils.user_registered
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles regular text messages, potentially routing them to the selected AI model."""
    user_id = update.effective_user.id
    message_text = update.message.text

    # Ignore commands being processed by CommandHandlers
    if message_text.startswith("/"):
        return

    # Get user's preferred model
    preferred_model = db.get_preferred_model(user_id)
    if not preferred_model:
        await update.message.reply_text("الرجاء اختيار نموذج AI أولاً باستخدام /model أو /settings.")
        return

    # Check if the preferred model has an active API key
    active_keys = db.get_active_service_names()
    if preferred_model not in active_keys:
         await update.message.reply_text(f"عذراً، النموذج المختار ({preferred_model}) غير متاح حالياً بسبب عدم وجود مفتاح API نشط له. يرجى اختيار نموذج آخر أو مراجعة المسؤول.")
         # Show model selection keyboard?
         reply_markup = keyboards.create_model_selection_keyboard(user_id)
         await update.message.reply_text("اختر نموذجاً بديلاً:", reply_markup=reply_markup)
         return

    # Determine request type and cost (can be more complex based on model)
    request_type = "text"
    cost = 1 # Default cost, adjust based on model if needed (e.g., GPT-4.5 costs more)
    # TODO: Implement cost calculation based on model

    # Check user's balance/subscription and consume request
    if not await utils.check_and_consume_request(user_id, preferred_model, request_type, cost, context, update):
        return # Stop if user doesn't have enough requests

    # --- AI Interaction Logic --- 
    # Placeholder: Send to a hypothetical AI handler function
    await update.message.reply_text(f"⏳ جارٍ معالجة طلبك باستخدام نموذج {preferred_model}...")
    try:
        # --- Replace with actual AI API call --- 
        # Example: response = await ai_handlers.get_ai_response(user_id, preferred_model, message_text, context)
        await asyncio.sleep(2) # Simulate AI processing time
        response = f"رد من نموذج {preferred_model} على: '{message_text}' (هذا رد تجريبي)"
        # --- End Replace --- 
        
        await update.message.reply_text(response)
        # TODO: Update conversation context if enabled
        # current_context = db.get_user_context(user_id) or []
        # current_context.append({"role": "user", "content": message_text})
        # current_context.append({"role": "assistant", "content": response})
        # # Limit context size if necessary
        # db.update_user_context(user_id, current_context)

    except Exception as e:
        logger.error(f"Error processing AI request for user {user_id} with model {preferred_model}: {e}")
        await update.message.reply_text("حدث خطأ أثناء معالجة طلبك مع نموذج الذكاء الاصطناعي. يرجى المحاولة مرة أخرى لاحقاً.")
        # Optional: Refund the request cost if AI call failed?
        # utils.refund_request(user_id, model_name, request_type, cost) # Needs implementation

# --- Main Function ---
def main() -> None:
    """Start the bot."""
    # Initialize Database
    db.init_db()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.TOKEN).build()

    # Store initial admin IDs in bot_data for reference (e.g., preventing removal)
    application.bot_data["initial_admins"] = config.ADMIN_IDS

    # --- Conversation Handlers --- 
    # Add API Key Conversation
    add_key_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.add_key_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}add_key_start$")],
        states={
            admin_handlers.SELECT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_service_name)],
            admin_handlers.ENTER_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_api_key)],
            admin_handlers.CONFIRM_KEY: [
                CallbackQueryHandler(admin_handlers.confirm_add_key, pattern=f"^{keyboards.CB_PREFIX_ADMIN}confirm_add_key$"),
                CallbackQueryHandler(admin_handlers.cancel_add_key, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_add_key$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_add_key), # Allow cancelling via command
            CallbackQueryHandler(admin_handlers.cancel_add_key, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_add_key$")
            ], 
        map_to_parent={
            # Return to main admin menu or key list after completion/cancel
            ConversationHandler.END: ConversationHandler.END # Adjust if needed
        }
    )
    
    # Edit API Key Conversation (Triggered by buttons within key_details_handler)
    edit_key_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_handlers.key_details_handler, pattern=f"^{keyboards.CB_PREFIX_ADMIN}key_details:"),
            # Direct entry for editing value/name if needed, handled by button_callback_handler now
            # CallbackQueryHandler(lambda u,c: EDIT_KEY_VALUE_ENTRY, pattern=f"^{keyboards.CB_PREFIX_ADMIN}edit_key_value:"),
            # CallbackQueryHandler(lambda u,c: EDIT_SERVICE_NAME_ENTRY, pattern=f"^{keyboards.CB_PREFIX_ADMIN}edit_key_service:")
        ],
        states={
            admin_handlers.EDIT_KEY_OPTIONS: [
                 # Handles buttons pressed *after* key_details_handler shows options
                 CallbackQueryHandler(admin_handlers.manage_keys_command, pattern=f"^{keyboards.CB_PREFIX_ADMIN}manage_keys$"), # Back button
                 # The following patterns are now handled by button_callback_handler which returns the next state
                 # CallbackQueryHandler(..., pattern=f"^{keyboards.CB_PREFIX_ADMIN}edit_key_value:"),
                 # CallbackQueryHandler(..., pattern=f"^{keyboards.CB_PREFIX_ADMIN}edit_key_service:"),
                 # CallbackQueryHandler(..., pattern=f"^{keyboards.CB_PREFIX_ADMIN}toggle_key_status:"),
                 # CallbackQueryHandler(..., pattern=f"^{keyboards.CB_PREFIX_ADMIN}delete_key_confirm:"),
            ],
            EDIT_KEY_VALUE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_new_key_value)], # Needs implementation
            EDIT_SERVICE_NAME_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_new_service_name)], # Needs implementation
        },
        fallbacks=[
             CommandHandler("cancel", admin_handlers.cancel_edit_key), # Needs implementation
             CallbackQueryHandler(admin_handlers.manage_keys_command, pattern=f"^{keyboards.CB_PREFIX_ADMIN}manage_keys$") # Back button as fallback
             ],
        map_to_parent={
             ConversationHandler.END: ConversationHandler.END
        }
    )

    # Broadcast Conversation
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("podcast", admin_handlers.broadcast_start), CallbackQueryHandler(admin_handlers.broadcast_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}broadcast$")],
        states={
            admin_handlers.ENTER_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.broadcast_receive_message)],
            admin_handlers.CONFIRM_BROADCAST: [
                CallbackQueryHandler(admin_handlers.broadcast_confirm, pattern=f"^{keyboards.CB_PREFIX_ADMIN}confirm_broadcast$"),
                CallbackQueryHandler(admin_handlers.broadcast_cancel, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_broadcast$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_handlers.broadcast_cancel), CallbackQueryHandler(admin_handlers.broadcast_cancel, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_broadcast$")],
    )

    # Add Admin Conversation
    add_admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.add_admin_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}add_admin_start$")],
        states={
            admin_handlers.ENTER_ADMIN_ID_TO_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.add_admin_receive_id)],
        },
        fallbacks=[CommandHandler("cancel", admin_handlers.cancel_manage_admin)], # Needs implementation
    )

    # Remove Admin Conversation
    remove_admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.remove_admin_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}remove_admin_start$")],
        states={
            admin_handlers.ENTER_ADMIN_ID_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.remove_admin_receive_id)],
        },
        fallbacks=[CommandHandler("cancel", admin_handlers.cancel_manage_admin)], # Needs implementation
    )

    # --- Command Handlers ---
    # General Commands
    application.add_handler(CommandHandler("start", general_handlers.start_command))
    application.add_handler(CommandHandler("help", general_handlers.help_command))
    application.add_handler(CommandHandler("privacy", general_handlers.privacy_command))
    # User Commands
    application.add_handler(CommandHandler("account", user_handlers.account_command))
    application.add_handler(CommandHandler("premium", user_handlers.premium_command))
    application.add_handler(CommandHandler("deletecontext", user_handlers.delete_context_command))
    application.add_handler(CommandHandler("settings", user_handlers.settings_command))
    application.add_handler(CommandHandler("model", user_handlers.model_command))
    # TODO: Add handlers for /midjourney, /video, /photo, /suno, /s, /empty
    # Admin Commands (Entry point)
    application.add_handler(CommandHandler("admin", admin_handlers.admin_command))

    # --- Add Conversation Handlers to Application ---
    # IMPORTANT: Add conversation handlers BEFORE the general CallbackQueryHandler
    application.add_handler(add_key_conv_handler)
    # application.add_handler(edit_key_conv_handler) # Add when fully implemented
    application.add_handler(broadcast_conv_handler)
    application.add_handler(add_admin_conv_handler)
    application.add_handler(remove_admin_conv_handler)

    # --- Callback Query Handler (Handles button presses) ---
    # This should come AFTER conversation handlers that use callbacks as entry points
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    # --- Message Handler (Handles regular text messages for AI interaction) ---
    # Make sure this doesn't interfere with ConversationHandler states expecting text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    # TODO: Add handlers for voice messages, photos, documents if needed

    # Run the bot until the user presses Ctrl-C
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()

