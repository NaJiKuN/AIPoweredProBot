# -*- coding: utf-8 -*-
"""Handlers for general bot commands like /start, /help, /privacy."""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import keyboards
import utils
import database as db # To grant free trial on first start

@utils.user_registered # Ensure user is in DB
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and the main menu keyboard when /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Check if it's the user's first time starting (or if they need a free trial refresh)
    # Simple check: See if they have an entry but no free requests/expiry set
    # More robust check might involve a dedicated 'first_start' flag or checking creation date
    user_data = db.get_user(user_id)
    # Grant free trial if user exists but has no free requests set and no expiry
    # Or if free requests are 0 and expiry is in the past or null
    grant_trial = False
    if user_data:
        free_left = user_data[7]
        free_expiry_str = user_data[8]
        if free_left is None or free_left <= 0:
             if free_expiry_str is None:
                 grant_trial = True
             else:
                 try:
                     free_expiry_date = datetime.datetime.strptime(free_expiry_str, 
%Y-%m-%d").date()
                     if free_expiry_date < datetime.date.today():
                          grant_trial = True # Grant again if expired
                 except ValueError:
                      grant_trial = True # Grant if expiry date is invalid

    if grant_trial:
        db.grant_free_trial(user_id) # Grant default 50 requests for 7 days
        await update.message.reply_text("🎁 لقد حصلت على 50 طلبًا مجانيًا لمدة أسبوع!")

    welcome_message = (
        "مرحبًا! يتيح لك الروبوت الوصول إلى أفضل أدوات الذكاء الاصطناعي لإنشاء النصوص والصور والفيديوهات والموسيقى.\n\n"
        "جرب نماذج متقدمة: OpenAI o3، o4-mini، GPT-4.5، Claude 4، /Midjourney، Flux، /Kling، Pika، /Suno، Grok والمزيد.\n\n"
        "**مجانًا:** GPT-4.1 mini، DeepSeek، Gemini 2.5، GPT Images، وبحث الويب Perplexity.\n\n"
        "**كيفية الاستخدام:**\n"
        "📝 **النص:** فقط اطرح سؤالك في الدردشة (اختر نموذج الذكاء الاصطناعي باستخدام /model).\n"
        "🔎 **البحث:** انقر على /s للبحث الذكي على الويب.\n"
        "🌅 **الصور:** انقر على /photo لبدء إنشاء الصور أو تحريرها.\n"
        "🎬 **الفيديو:** انقر على /video لبدء إنشاء مقطع الفيديو الخاص بك (متاح في /premium).\n"
        "🎸 **الموسيقى:** انقر على /chirp، واختر نوعًا موسيقيًا، وأضف كلمات الأغنية (متاح في /Suno)."
    )
    
    # Use the keyboard created in keyboards.py
    reply_markup = keyboards.create_start_keyboard()
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

@utils.user_registered
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the help message detailing bot commands and features."""
    help_text = (
        "**مساعدة المستخدم**\n\n"
        "📝 **إنشاء النص**\n"
        "لإنشاء نص، اكتب طلبك في الدردشة. يمكن للمستخدمين الذين لديهم اشتراك /premium أيضًا إرسال رسائل صوتية.\n"
        "/s – بحث الويب مع Perplexity\n"
        "/settings – إعدادات روبوت الدردشة\n"
        "/model – التبديل بين نماذج الذكاء الاصطناعي\n\n"
        "💬 **استخدام السياق**\n"
        "يحتفظ الروبوت بالسياق افتراضيًا، مما يربط استفسارك الحالي بآخر رد له. هذا يسمح بالحوار وطرح أسئلة متابعة. لبدء موضوع جديد بدون سياق، استخدم أمر /deletecontext.\n\n"
        "📄 **التعرف على الملفات**\n"
        "عند استخدام نموذج Claude، يمكنك العمل مع المستندات. قم بتحميل ملف بتنسيق docx، pdf، xlsx، xls، csv، pptx، txt واطرح أسئلة حول المستند. يستهلك كل طلب 3 عمليات إنشاء من Claude.\n\n"
        "🌅 **إنشاء الصور**\n"
        "ينشئ الروبوت صورًا باستخدام أحدث نماذج Midjourney وChatGPT وFlux. ابدأ بأمر وأضف توجيهك:\n"
        "/wow – بدء وضع صور GPT-4o\n"
        "/flux – استخدام Flux\n"
        "/dalle – استخدام DALL•E 3\n"
        "/imagine – استخدام Midjourney\n"
        "└ دليل (https://teletype.in/@gpt4telegrambot/midjourney) لإتقان Midjourney\n\n"
        "🎸 **إنشاء الأغاني**\n"
        "ينشئ الروبوت أغاني باستخدام Suno.\n"
        "/chirp – إنشاء أغنية؛ سيطلب منك الروبوت اختيار نوع موسيقي وإدخال كلمات الأغنية\n"
        "/Suno – دليل لإنشاء الأغاني\n\n"
        "⚙️ **أوامر أخرى**\n"
        "/start – وصف الروبوت\n"
        "/account – ملفك الشخصي والرصيد\n"
        "/premium – اختيار وشراء اشتراك مميز لـ ChatGPT وClaude وGemini وDALL•E 3 وMidjourney وFlux وSuno\n"
        "/privacy – شروط الاستخدام وسياسة الخصوصية\n\n"
        "لأي استفسارات، يمكنك أيضًا مراسلة المسؤول @NaJiMaS"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@utils.user_registered
async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the privacy policy or terms of service."""
    # Replace with your actual privacy policy text
    privacy_text = (
        "**شروط الخدمة وسياسة الخصوصية**\n\n"
        "1. **جمع البيانات:** نقوم بجمع معرف المستخدم الخاص بك على تيليجرام لتوفير وظائف البوت وتتبع الاستخدام.\n"
        "2. **استخدام البيانات:** تُستخدم بياناتك فقط لتشغيل البوت، وإدارة الاشتراكات، وتقديم الدعم.\n"
        "3. **مفاتيح API:** يتم تخزين مفاتيح API التي يضيفها المسؤولون بشكل آمن ولا تتم مشاركتها.\n"
        "4. **سياق المحادثة:** يتم تخزين سياق المحادثة مؤقتًا لتحسين التفاعل وقد يتم حذفه دوريًا أو يدويًا باستخدام /deletecontext.\n"
        "5. **الخدمات الخارجية:** عند استخدام نماذج الذكاء الاصطناعي، قد تتم مشاركة استفساراتك (بدون معلومات شخصية) مع موفري النماذج هؤلاء وفقًا لسياسات الخصوصية الخاصة بهم.\n"
        "6. **التغييرات:** قد نقوم بتحديث هذه السياسة. سيتم إخطار المستخدمين بالتغييرات الهامة.\n\n"
        "باستخدام هذا البوت، فإنك توافق على هذه الشروط."
    )
    await update.message.reply_text(privacy_text, parse_mode=ParseMode.MARKDOWN)

@utils.user_registered
async def empty_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an empty message or a placeholder to clear the keyboard or screen."""
    # This command might be used to remove an inline keyboard if it's persistent
    # Or just send a minimal confirmation.
    await update.message.reply_text(".", reply_markup=None) # Send a dot or similar minimal response


