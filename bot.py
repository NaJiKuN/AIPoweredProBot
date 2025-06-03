# -*- coding: utf-8 -*-
"""Main entry point for the AI Powered Pro Telegram Bot."""

import logging
import sys
import os

# Add project root to sys.path FIRST to ensure correct imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, Filters, CallbackContext

from config import TOKEN, INITIAL_ADMIN_ID
from database.models import init_db, get_db, Admin
from database.seed import seed_initial_data

# Import handler registration functions
from handlers.admin import manage_admins, manage_apis, broadcast, stats
from handlers.user import start, help, account, premium, settings, model, context, ai_interactions
# Import other handlers like payments, specific AI commands (photo, video, etc.) when developed

# Setup logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # Reduce httpx noise
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Post-initialization tasks, like seeding the database."""
    logger.info("Running post-initialization tasks...")
    try:
        init_db() # Ensure tables are created
        seed_initial_data() # Seed plans and initial admin
        logger.info("Database initialized and seeded.")
    except Exception as e:
        logger.error(f"Error during post-initialization: {e}", exc_info=True)

async def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    # Optionally notify admin about critical errors
    # if isinstance(context.error, SomeCriticalError):
    #     await context.bot.send_message(chat_id=INITIAL_ADMIN_ID, text=f"Critical Error: {context.error}")

def main() -> None:
    """Start the bot."""
    logger.info("Starting bot...")

    # Create the Application and pass it your bot\`s token.
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Register Handlers
    # Admin Handlers
    manage_admins.register_handlers(application)
    manage_apis.register_handlers(application)
    broadcast.register_handlers(application)
    stats.register_handlers(application)

    # User Handlers
    start.register_handlers(application)
    help.register_handlers(application)
    account.register_handlers(application)
    premium.register_handlers(application) # Includes callbacks
    settings.register_handlers(application) # Includes model command and callbacks
    context.register_handlers(application)
    ai_interactions.register_handlers(application) # Handles text messages

    # Register other handlers here (e.g., for /photo, /video, /suno commands)
    # Example placeholder:
    # application.add_handler(CommandHandler("photo", photo_command))
    # application.add_handler(CommandHandler("video", video_command))
    # application.add_handler(CommandHandler("suno", suno_command))
    # application.add_handler(CommandHandler("s", search_command))
    # application.add_handler(CommandHandler("privacy", privacy_command))
    # application.add_handler(CommandHandler("empty", empty_command))
    # application.add_handler(MessageHandler(Filters.VOICE, handle_voice_message)) # For premium users
    # application.add_handler(MessageHandler(Filters.Document.ALL, handle_document)) # For Claude

    # Error Handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot polling started.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

