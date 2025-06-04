import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from config import TOKEN, ADMIN_ID, ADMINS
import database as db
import keyboards as kb
import ai_models
import payment
import strings
import utils

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # إنشاء مستخدم جديد إذا لم يكن موجوداً
    if not db.get_user(user_id):
        db.create_user(user_id, user.username, user.first_name, user.last_name)
        # منح التجربة المجانية
        db.give_free_trial(user_id)
    
    # إرسال رسالة الترحيب
    await update.message.reply_text(
        strings.START_MESSAGE,
        reply_markup=kb.main_menu_keyboard()
    )

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user_account_data(user_id)
    packages = db.get_user_packages(user_id)
    
    # بناء نص الحساب
    account_text = strings.format_account_message(user_data, packages)
    
    # إرسال الرسالة مع أزرار الشراء
    await update.message.reply_text(
        account_text,
        reply_markup=kb.buy_balance_keyboard()
    )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        strings.PREMIUM_MESSAGE,
        reply_markup=kb.premium_packages_keyboard()
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        strings.SETTINGS_INTRO,
        reply_markup=kb.settings_main_keyboard()
    )

async def delete_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.delete_user_context(user_id)
    await update.message.reply_text(strings.CONTEXT_DELETED_MESSAGE)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # معالجة أنواع مختلفة من الأزرار
    if data.startswith('buy_balance_'):
        amount = int(data.split('_')[2])
        await payment.initiate_payment(update, context, amount)
    
    elif data.startswith('select_model_'):
        model_name = data.split('_')[2]
        db.update_user(user_id, selected_model=model_name)
        await query.edit_message_text(
            f"✅ تم اختيار نموذج {model_name}",
            reply_markup=kb.models_keyboard(user_id)
        )
    
    # ... (معالجة أنواع أخرى من الأزرار)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    
    # الحصول على النموذج المختار
    selected_model = db.get_selected_model(user_id)
    
    # الحصول على السياق إذا كان مفعلاً
    context_history = db.get_conversation_context(user_id, selected_model) if db.is_context_enabled(user_id) else []
    
    # إرسال الطلب إلى نموذج الذكاء الاصطناعي
    response = await ai_models.generate_response(
        model=selected_model,
        prompt=message,
        context=context_history
    )
    
    # حفظ السياق الجديد
    db.save_conversation_context(user_id, selected_model, context_history + [message, response])
    
    # إرسال الرد
    await update.message.reply_text(response)

def main() -> None:
    # إنشاء الجداول في قاعدة البيانات
    db.create_tables()
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # تسجيل معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("account", account))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("deletecontext", delete_context))
    # ... (أوامر أخرى)
    
    # معالجة الضغط على الأزرار
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # معالجة الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # بدء تشغيل البوت
    application.run_polling()

if __name__ == "__main__":
    main()
