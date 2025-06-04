import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import TOKEN, ADMIN_IDS
from database import init_db, get_user, create_user, update_user_model
from keyboards import (
    start_keyboard,
    account_keyboard,
    premium_keyboard,
    settings_keyboard,
    model_selection_keyboard,
    wallet_topup_keyboard
)
from admin import setup_admin_handlers
from ai_services import handle_ai_request
from utils import send_typing_action, is_admin
from messages import (
    START_MESSAGE,
    ACCOUNT_MESSAGE,
    PREMIUM_MESSAGE,
    MIDJOURNEY_MESSAGE,
    VIDEO_MESSAGE,
    PHOTO_MESSAGE,
    SUNO_MESSAGE,
    SEARCH_MESSAGE,
    SETTINGS_MESSAGE,
    HELP_MESSAGE
)

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language=user.language_code or 'ar'
        )
    
    await update.message.reply_text(
        START_MESSAGE,
        reply_markup=start_keyboard(),
        parse_mode='Markdown'
    )

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await start(update, context)
        return
    
    message = ACCOUNT_MESSAGE.format(
        subscription="مجاني ✔️",
        model=db_user.get('current_model', 'GPT-4.1 mini'),
        balance=db_user.get('wallet_balance', 0),
        weekly_requests="50/50",
        chatgpt_package="0/0",
        claude_package="0/0",
        image_package="0/0",
        video_package="0/0",
        suno_package="0/0"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=account_keyboard(),
        parse_mode='Markdown'
    )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        PREMIUM_MESSAGE,
        reply_markup=premium_keyboard(),
        parse_mode='Markdown'
    )

async def delete_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تنفيذ حذف السياق هنا
    await update.message.reply_text("تم حذف السياق. عادةً ما يتذكر البوت سؤالك السابق وإجابته ويستخدم السياق في الرد")

async def midjourney(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MIDJOURNEY_MESSAGE,
        parse_mode='Markdown'
    )

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        VIDEO_MESSAGE,
        parse_mode='Markdown'
    )

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        PHOTO_MESSAGE,
        parse_mode='Markdown'
    )

async def suno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        SUNO_MESSAGE,
        reply_markup=suno_keyboard(),
        parse_mode='Markdown'
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        SEARCH_MESSAGE,
        reply_markup=search_keyboard(),
        parse_mode='Markdown'
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    await update.message.reply_text(
        SETTINGS_MESSAGE,
        reply_markup=settings_keyboard(db_user),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_MESSAGE,
        parse_mode='Markdown'
    )

@send_typing_action
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    # التحقق من الرصيد المتاح
    # (سيتم تنفيذ المنطق الكامل في الإصدار النهائي)
    
    # معالجة الطلب باستخدام الذكاء الاصطناعي
    response = await handle_ai_request(user.id, text)
    await update.message.reply_text(response)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith('model_'):
        model_name = data.split('_')[1]
        update_user_model(query.from_user.id, model_name)
        await query.edit_message_text(f"تم اختيار النموذج: {model_name} ✅")
    
    elif data == 'wallet_topup':
        await query.edit_message_text(
            "اختر كمية العملات لشرائها:",
            reply_markup=wallet_topup_keyboard()
        )
    
    # يمكن إضافة المزيد من معالجات الأزرار هنا

def main():
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("account", account))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(CommandHandler("deletecontext", delete_context))
    application.add_handler(CommandHandler("midjourney", midjourney))
    application.add_handler(CommandHandler("video", video))
    application.add_handler(CommandHandler("photo", photo))
    application.add_handler(CommandHandler("suno", suno))
    application.add_handler(CommandHandler("s", search))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("help", help_command))
    
    # إضافة معالجات المسؤول
    setup_admin_handlers(application)
    
    # معالجة استعلامات الزر
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # معالجة الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()
