from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from database import Database
from models import AIModels
from subscriptions import Subscriptions
from admin import Admin
from utils import generate_invite_code, get_invite_count, save_context, load_context, clear_context

TOKEN = "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g"
ADMIN_ID = 764559466

db = Database()
ai_models = AIModels(db)
subscriptions = Subscriptions(db)
admin = Admin(db)

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    db.add_user(user_id, username)
    if not db.get_user(user_id)[6]:  # إذا لم يكن لديه كود دعوة
        invite_code = generate_invite_code(user_id)
        db.update_invite_code(user_id, invite_code)
    update.message.reply_text(
        "مرحبًا! يتيح لك الروبوت الوصول إلى أفضل أدوات الذكاء الاصطناعي لإنشاء النصوص والصور والفيديوهات والموسيقى.\n\n"
        "جرب نماذج متقدمة: OpenAI o3، o4-mini، GPT-4.5، Claude 4، /Midjourney، Flux، /Kling، Pika، /Suno، Grok والمزيد.\n\n"
        "مجانًا: GPT-4.1 mini، DeepSeek، Gemini 2.5، GPT Images، وبحث الويب Perplexity.\n\n"
        "كيفية الاستخدام:\n\n"
        "📝 النص: فقط اطرح سؤالك في الدردشة (اختر نموذج الذكاء الاصطناعي باستخدام /model).\n"
        "🔎 البحث: انقر على /s للبحث الذكي على الويب.\n"
        "🌅 الصور: انقر على /photo لبدء إنشاء الصور أو تحريرها.\n"
        "🎬 الفيديو: انقر على /video لبدء إنشاء مقطع الفيديو الخاص بك (متاح في /premium).\n"
        "🎸 الموسيقى: انقر على /chirp، واختر نوعًا موسيقيًا، وأضف كلمات الأغنية (متاح في /Suno)."
    )

def account(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = db.get_user(user_id)
    if user:
        update.message.reply_text(
            f"حسابك:\n"
            f"اسم المستخدم: {user[1]}\n"
            f"الاشتراك: {user[2]}\n"
            f"الطلبات المتبقية: {user[3]}\n"
            f"نهاية الاشتراك: {user[4]}\n"
            f"كود الدعوة: {user[6]}\n"
            f"عدد المدعوين: {user[7]}"
        )
    else:
        update.message.reply_text("لم يتم العثور على حسابك.")

def premium(update: Update, context: CallbackContext):
    packages = subscriptions.get_premium_packages()
    keyboard = []
    for package in packages:
        keyboard.append([InlineKeyboardButton(f"{package[1]} - {package[3]} ⭐", callback_data=f'purchase_{package[0]}')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر خدمة للشراء:", reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    if data.startswith('purchase_'):
        package_id = int(data.split('_')[1])
        user_id = query.from_user.id
        result = subscriptions.purchase_package(user_id, package_id)
        query.edit_message_text(text=result)

def delete_context(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    clear_context(user_id)
    update.message.reply_text("تم حذف سياق المحادثة.")

def settings(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    models = ai_models.get_available_models()
    keyboard = [[InlineKeyboardButton(model, callback_data=f'set_model_{model}')] for model in models]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر نموذج الذكاء الاصطناعي المفضل:", reply_markup=reply_markup)

def set_model_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    model = query.data.split('_')[2]
    user_id = query.from_user.id
    db.update_preferred_model(user_id, model)
    query.edit_message_text(text=f"تم تعيين {model} كنموذج مفضل.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📝 إنشاء النص\n"
        "لإنشاء نص، اكتب طلبك في الدردشة. يمكن للمستخدمين الذين لديهم اشتراك /premium أيضًا إرسال رسائل صوتية.\n"
        "/s – بحث الويب مع Perplexity\n"
        "/settings – إعدادات روبوت الدردشة\n"
        "/model – التبديل بين نماذج الذكاء الاصطناعي\n\n"
        "💬 استخدام السياق\n"
        "يحتفظ الروبوت بالسياق افتراضيًا، مما يربط استفسارك الحالي بآخر رد له. هذا يسمح بالحوار وطرح أسئلة متابعة. لبدء موضوع جديد بدون سياق، استخدم أمر /deletecontext.\n\n"
        "📄 التعرف على الملفات\n"
        "عند استخدام نموذج Claude، يمكنك العمل مع المستندات. قم بتحميل ملف بتنسيق docx، pdf، xlsx، xls، csv، pptx، txt واطرح أسئلة حول المستند. يستهلك كل طلب 3 عمليات إنشاء من Claude.\n\n"
        "🌅 إنشاء الصور\n"
        "ينشئ الروبوت صورًا باستخدام أحدث نماذج Midjourney وChatGPT وFlux. ابدأ بأمر وأضف توجيهك:\n"
        "/wow – بدء وضع صور GPT-4o\n"
        "/flux – استخدام Flux\n"
        "/dalle – استخدام DALL•E 3\n"
        "/imagine – استخدام Midjourney\n"
        "└ دليل (https://teletype.in/@gpt4telegrambot/midjourney) لإتقان Midjourney\n\n"
        "🎸 إنشاء الأغاني\n"
        "ينشئ الروبوت أغاني باستخدام Suno.\n"
        "/chirp – إنشاء أغنية؛ سيطلب منك الروبوت اختيار نوع موسيقي وإدخال كلمات الأغنية\n"
        "/Suno – دليل لإنشاء الأغاني\n\n"
        "⚙️ أوامر أخرى\n"
        "/start – وصف الروبوت\n"
        "/account – ملفك الشخصي والرصيد\n"
        "/premium – اختيار وشراء اشتراك مميز لـ ChatGPT وClaude وGemini وDALL•E 3 وMidjourney وFlux وSuno\n"
        "/privacy – شروط الاستخدام وسياسة الخصوصية\n\n"
        "لأي استفسارات، يمكنك أيضًا مراسلة المسؤول @NaJiMaS"
    )

def message_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = db.get_user(user_id)
    if not user or user[3] <= 0:
        update.message.reply_text("ليس لديك طلبات متبقية. اشترك باستخدام /premium أو اختر الاشتراك المجاني.")
        return
    text = update.message.text
    preferred_model = user[5] or "GPT-4.1 mini"
    context_text = load_context(user_id)
    full_prompt = f"{context_text}\n{text}" if context_text else text
    response = ai_models.generate_text(preferred_model, full_prompt)
    save_context(user_id, full_prompt + "\n" + response)
    db.update_requests_left(user_id, user[3] - 1)
    update.message.reply_text(response)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("account", account))
    dp.add_handler(CommandHandler("premium", premium))
    dp.add_handler(CommandHandler("deletecontext", delete_context))
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(button_callback, pattern='purchase_'))
    dp.add_handler(CallbackQueryHandler(set_model_callback, pattern='set_model_'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    # إضافة معالجات أوامر المسؤول من admin.py
    dp.add_handler(CommandHandler("add_admin", admin.add_admin))
    dp.add_handler(CommandHandler("add_api_key", admin.add_api_key))
    dp.add_handler(CommandHandler("remove_api_key", admin.remove_api_key))
    dp.add_handler(CommandHandler("add_package", admin.add_package))
    dp.add_handler(CommandHandler("broadcast", admin.broadcast))
    dp.add_handler(CommandHandler("stats", admin.stats))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()