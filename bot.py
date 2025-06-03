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
from handlers import general_handlers, user_handlers, admin_handlers, ai_handlers # Assuming ai_handlers.py for AI logic

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
            settings_text = "⚙️ **إعدادات البوت**\n\nيمكنك هنا تغيير بعض إعدادات البوت الخاص بك."
            reply_markup = keyboards.create_model_selection_keyboard(user_id)
            await query.edit_message_text(text=settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        elif data == "show_account":
            account_status_text = utils.format_account_status(user_id)
            # Consider adding a refresh button here?
            await query.edit_message_text(text=account_status_text, parse_mode=ParseMode.MARKDOWN)
        elif data == "show_help":
            # Help text is long, maybe just send as new message?
            await general_handlers.help_command(update, context) # Call the command handler
            # Or display a snippet and a button to view full help?
            # await query.edit_message_text(text="للحصول على المساعدة الكاملة، استخدم الأمر /help.")
        elif data == "show_chatgpt_packages":
            reply_markup = keyboards.create_package_selection_keyboard("chatgpt")
            await query.edit_message_text(text="اختر حجم حزمة ChatGPT Plus:", reply_markup=reply_markup)
        elif data == "show_claude_packages":
            reply_markup = keyboards.create_package_selection_keyboard("claude")
            await query.edit_message_text(text="اختر حجم حزمة Claude:", reply_markup=reply_markup)
        elif data == "show_mjflux_packages":
            reply_markup = keyboards.create_package_selection_keyboard("mjflux")
            await query.edit_message_text(text="اختر حجم حزمة Midjourney & Flux:", reply_markup=reply_markup)
        elif data == "show_video_packages":
             # --- IMPORTANT VIDEO CHECK --- 
             # Check if user has access to video generation (Pro member check)
             # This is a placeholder - replace with actual check if available
             is_pro_member = False # Assume not Pro by default
             if not is_pro_member:
                 await query.message.reply_text(
                     "🎬 ميزة إنشاء الفيديو متاحة للأعضاء المميزين (Pro) فقط.\n"
                     "يرجى الترقية إلى العضوية المميزة للاستفادة من هذه الميزة."
                 )
                 # Optionally, show the premium menu again
                 # premium_text = "اختر خدمة للشراء:"
                 # reply_markup = keyboards.create_premium_keyboard()
                 # await query.edit_message_text(text=premium_text, reply_markup=reply_markup)
                 return # Stop processing if not Pro
             else:
                 # Proceed if user is Pro
                 reply_markup = keyboards.create_package_selection_keyboard("video")
                 await query.edit_message_text(text="اختر حجم حزمة الفيديو:", reply_markup=reply_markup)
        elif data == "show_suno_packages":
            reply_markup = keyboards.create_package_selection_keyboard("suno")
            await query.edit_message_text(text="اختر حجم حزمة Suno:", reply_markup=reply_markup)
        # Add other action handlers here

    # --- Model Selection Callbacks (model:) ---
    elif prefix == keyboards.CB_PREFIX_MODEL:
        model_name = data
        db.set_preferred_model(user_id, model_name)
        await query.edit_message_text(f"✅ تم تغيير النموذج المفضل إلى: **{model_name}**", parse_mode=ParseMode.MARKDOWN)
        # Optionally, show the settings menu again or the main menu
        # reply_markup = keyboards.create_model_selection_keyboard(user_id)
        # await query.message.reply_text("إعدادات النموذج المحدثة:", reply_markup=reply_markup)

    # --- Premium Purchase Callbacks (prem:) ---
    elif prefix == keyboards.CB_PREFIX_PREMIUM:
        # Simulate purchase - In reality, this would involve Telegram Stars API interaction
        purchase_successful = True # Assume success for simulation
        product_name = ""
        
        if data == "premium_monthly":
            product_name = "الاشتراك المميز الشهري"
            if purchase_successful:
                db.grant_premium(user_id, duration_days=30, daily_limit=100)
        elif data == "premium_x2_monthly":
            product_name = "الاشتراك المميز X2 الشهري"
            if purchase_successful:
                db.grant_premium(user_id, duration_days=30, daily_limit=200)
        elif data == "combo_monthly":
            product_name = "الكومبو الشهري"
            if purchase_successful:
                # Grant base premium
                db.grant_premium(user_id, duration_days=30, daily_limit=100)
                # Add package components (needs specific package types)
                # Example: Assuming combo includes 100 ChatGPT Plus and 100 MJ/Flux
                db.add_package(user_id, "COMBO_CHATGPT_PLUS_100", 100)
                db.add_package(user_id, "COMBO_MJFLUX_100", 100)
        
        if purchase_successful and product_name:
            await query.edit_message_text(f"✅ تم تفعيل **{product_name}** بنجاح!", parse_mode=ParseMode.MARKDOWN)
            # Show account status after purchase
            account_status_text = utils.format_account_status(user_id)
            await query.message.reply_text(f"**حالة حسابك المحدثة:**\n\n{account_status_text}", parse_mode=ParseMode.MARKDOWN)
        elif product_name: # Purchase failed (simulation)
            await query.edit_message_text(f"⚠️ فشلت عملية شراء **{product_name}**. يرجى المحاولة مرة أخرى أو الاتصال بالدعم.", parse_mode=ParseMode.MARKDOWN)
        else:
             await query.edit_message_text("⚠️ طلب شراء غير معروف.")

    # --- Package Purchase Callbacks (pkg:) ---
    elif prefix == keyboards.CB_PREFIX_PACKAGE:
        # Format: pkg:<type>:<requests>
        parts = data.split(":")
        if len(parts) == 2:
            package_type_code, requests_str = parts
            try:
                requests_count = int(requests_str)
                # Simulate purchase
                purchase_successful = True # Assume success
                package_name = f"حزمة {package_type_code.upper()} ({requests_count} طلب)"
                
                # Construct the full package type identifier used in the DB
                db_package_type = f"{package_type_code.upper()}_{requests_count}"
                # Special cases for naming if needed
                if package_type_code == "mjflux": db_package_type = f"MIDJOURNEY_FLUX_{requests_count}"
                if package_type_code == "chatgpt": db_package_type = f"CHATGPT_PLUS_{requests_count}"
                # ... add other mappings if DB types differ significantly from button codes
                
                if purchase_successful:
                    db.add_package(user_id, db_package_type, requests_count)
                    await query.edit_message_text(f"✅ تم شراء **{package_name}** بنجاح!", parse_mode=ParseMode.MARKDOWN)
                    # Show account status
                    account_status_text = utils.format_account_status(user_id)
                    await query.message.reply_text(f"**حالة حسابك المحدثة:**\n\n{account_status_text}", parse_mode=ParseMode.MARKDOWN)
                else:
                    await query.edit_message_text(f"⚠️ فشلت عملية شراء **{package_name}**. يرجى المحاولة مرة أخرى.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                 await query.edit_message_text("⚠️ بيانات الحزمة غير صالحة.")
        else:
            await query.edit_message_text("⚠️ طلب شراء حزمة غير معروف.")
            
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
             # This now acts as an entry point for the edit key conversation handler
             # The state EDIT_KEY_OPTIONS should handle the button presses within the details view
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
                 await query.edit_message_text(f"✅ تم تغيير حالة المفتاح {key_id} إلى {"نشط" if new_status else "غير نشط"}.")
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
             # This callback now just triggers the start of the conversation
             # The actual logic is in the ConversationHandler entry point
             # We might need to adjust admin_handlers.add_key_start if it expects query
             # For now, assume it works or adjust admin_handlers later.
             # Let the ConversationHandler catch this via CallbackQueryHandler entry
             pass # Let ConversationHandler handle this
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
        logger.warning(f"Unhandled callback query prefix: {prefix}")
        await query.edit_message_text("حدث خطأ غير متوقع أو أن هذا الزر لم يعد صالحاً.")

# --- Message Handler for AI Interaction ---
@utils.user_registered
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles regular text messages, potentially routing them to the selected AI model."""
    user_id = update.effective_user.id
    message_text = update.message.text

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
    request_type = "text" # Default
    cost = 1 # Default cost
    # Example: if preferred_model == "Claude 4 Sonnet + Thinking" and context.user_data.get("has_file"): cost = 3

    # Check permissions and consume request
    can_proceed = await utils.check_and_consume_request(user_id, preferred_model, request_type, cost, context, update)

    if can_proceed:
        # Get conversation context
        conversation_context = db.get_user_context(user_id)
        if conversation_context is None: conversation_context = [] # Initialize if null

        # Add current user message to context
        conversation_context.append({"role": "user", "content": message_text})
        
        # --- Simulate AI Response --- 
        # Replace this with actual API call using preferred_model and api_key
        await update.message.reply_chat_action("typing") # Show typing indicator
        api_key = db.get_api_key(preferred_model)
        
        # Placeholder for actual API call function
        # response_text = await ai_handlers.get_ai_response(preferred_model, api_key, conversation_context)
        await asyncio.sleep(1) # Simulate delay
        response_text = f"رد محاكاة من نموذج {preferred_model}: \"{message_text}\""
        # --- End Simulation --- 
        
        if response_text:
            # Add AI response to context
            conversation_context.append({"role": "assistant", "content": response_text})
            # Limit context length if necessary (e.g., keep last N messages)
            max_context = 10 # Example limit
            if len(conversation_context) > max_context:
                conversation_context = conversation_context[-max_context:]
                
            # Save updated context
            db.update_user_context(user_id, conversation_context)
            
            await update.message.reply_text(response_text)
        else:
            await update.message.reply_text(f"عذراً، حدث خطأ أثناء معالجة طلبك مع نموذج {preferred_model}.")
            # Optionally, refund the request cost here if possible

# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    # Optionally notify admin or user about the error
    # try:
    #     if isinstance(update, Update) and update.effective_message:
    #         await update.effective_message.reply_text("عذرًا، حدث خطأ ما. لقد تم إبلاغ المسؤول.")
    # except Exception as e:
    #     logger.error(f"Error sending error message to user: {e}")

# --- Main Function --- 
def main() -> None:
    """Start the bot."""
    # Initialize Database
    db.init_db()
    # Ensure initial admins from config are marked in DB
    # (This might be better placed after Application build if bot_data is used)
    conn = db.sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    initial_admin_ids_str = [str(id) for id in config.ADMIN_IDS]
    for admin_id in config.ADMIN_IDS:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (admin_id,))
    conn.commit()
    conn.close()
    logger.info(f"Ensured initial admin IDs {config.ADMIN_IDS} have admin flag set in DB.")

    # Create the Application and pass it your bot token.
    application = Application.builder().token(config.TOKEN).build()
    
    # Store initial admins in bot_data for checks in handlers
    application.bot_data["initial_admins"] = initial_admin_ids_str

    # --- Conversation Handlers --- 
    # Add Key Conversation
    add_key_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.add_key_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}add_key_start$")],
        states={
            SELECT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_service_name)],
            ENTER_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_api_key)],
            CONFIRM_KEY: [
                CallbackQueryHandler(admin_handlers.confirm_add_key, pattern=f"^{keyboards.CB_PREFIX_ADMIN}confirm_add_key$"),
                CallbackQueryHandler(admin_handlers.cancel_add_key, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_add_key$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(admin_handlers.cancel_add_key, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_add_key$"),
            CommandHandler("cancel", admin_handlers.cancel_add_key), # Allow cancelling with /cancel
            CallbackQueryHandler(admin_handlers.manage_keys_command, pattern=f"^{keyboards.CB_PREFIX_ADMIN}manage_keys$") # Go back
            ], 
        map_to_parent={
            # Return to main admin menu or key list after completion/cancel
            ConversationHandler.END: ConversationHandler.END 
            # Or map to a specific state if part of a larger admin conversation
        }
    )
    
    # Edit Key Conversation (Simplified example - needs more states for value/service edit)
    edit_key_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.key_details_handler, pattern=f"^{keyboards.CB_PREFIX_ADMIN}key_details:")],
        states={
            EDIT_KEY_OPTIONS: [
                 # Add handlers for buttons inside key_details_handler view
                 CallbackQueryHandler(button_callback_handler) # Route button presses back to main handler
            ],
            EDIT_KEY_VALUE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_new_key_value)], # Need receive_new_key_value handler
            EDIT_SERVICE_NAME_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_new_service_name)], # Need receive_new_service_name handler
        },
        fallbacks=[
             CallbackQueryHandler(admin_handlers.manage_keys_command, pattern=f"^{keyboards.CB_PREFIX_ADMIN}manage_keys$"), # Back to list
             CommandHandler("cancel", admin_handlers.cancel_edit_key) # Need cancel_edit_key
            ]
    )

    # Broadcast Conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.broadcast_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}broadcast$")],
        states={
            ENTER_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.broadcast_receive_message)],
            CONFIRM_BROADCAST: [
                CallbackQueryHandler(admin_handlers.broadcast_confirm, pattern=f"^{keyboards.CB_PREFIX_ADMIN}confirm_broadcast$"),
                CallbackQueryHandler(admin_handlers.broadcast_cancel, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_broadcast$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(admin_handlers.broadcast_cancel, pattern=f"^{keyboards.CB_PREFIX_ADMIN}cancel_broadcast$"),
            CommandHandler("cancel", admin_handlers.broadcast_cancel)
            ]
    )
    
    # Add Admin Conversation
    add_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.add_admin_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}add_admin_start$")],
        states={
            ENTER_ADMIN_ID_TO_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.add_admin_receive_id)],
        },
        fallbacks=[CommandHandler("cancel", admin_handlers.cancel_admin_action)] # Need cancel_admin_action
    )

    # Remove Admin Conversation
    remove_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.remove_admin_start, pattern=f"^{keyboards.CB_PREFIX_ADMIN}remove_admin_start$")],
        states={
            ENTER_ADMIN_ID_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.remove_admin_receive_id)],
        },
        fallbacks=[CommandHandler("cancel", admin_handlers.cancel_admin_action)] # Need cancel_admin_action
    )
    
    # --- Command Handlers ---
    # General
    application.add_handler(CommandHandler("start", general_handlers.start_command))
    application.add_handler(CommandHandler("help", general_handlers.help_command))
    application.add_handler(CommandHandler("privacy", general_handlers.privacy_command))
    application.add_handler(CommandHandler("empty", general_handlers.empty_command))
    # User
    application.add_handler(CommandHandler("account", user_handlers.account_command))
    application.add_handler(CommandHandler("premium", user_handlers.premium_command))
    application.add_handler(CommandHandler("deletecontext", user_handlers.delete_context_command))
    application.add_handler(CommandHandler("settings", user_handlers.settings_command))
    application.add_handler(CommandHandler("model", user_handlers.model_command))
    # Admin Command Entry Point
    application.add_handler(CommandHandler("admin", admin_handlers.admin_command))
    # AI Specific Commands (Placeholders - need handlers in ai_handlers.py)
    # application.add_handler(CommandHandler("s", ai_handlers.search_command))
    # application.add_handler(CommandHandler("photo", ai_handlers.photo_command))
    # application.add_handler(CommandHandler("midjourney", ai_handlers.midjourney_command))
    # application.add_handler(CommandHandler("video", ai_handlers.video_command))
    # application.add_handler(CommandHandler("suno", ai_handlers.suno_command))
    # application.add_handler(CommandHandler("chirp", ai_handlers.suno_command)) # Alias for suno
    # application.add_handler(CommandHandler("wow", ai_handlers.gpt4o_image_command))
    # application.add_handler(CommandHandler("flux", ai_handlers.flux_command))
    # application.add_handler(CommandHandler("dalle", ai_handlers.dalle_command))
    # application.add_handler(CommandHandler("imagine", ai_handlers.midjourney_command)) # Alias

    # --- Add Conversation Handlers --- 
    # IMPORTANT: Add conversation handlers BEFORE the main CallbackQueryHandler if they share entry points
    application.add_handler(add_key_conv)
    # application.add_handler(edit_key_conv) # Add when fully implemented
    application.add_handler(broadcast_conv)
    application.add_handler(add_admin_conv)
    application.add_handler(remove_admin_conv)

    # --- Callback Query Handler (Handles button presses) ---
    # Must be added AFTER conversation handlers that use callbacks as entry points
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    # --- Message Handler (Handles text messages for AI) ---
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    # --- Error Handler ---
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == "__main__":
    main()

