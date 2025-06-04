#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة المستخدمين
يحتوي على الوظائف الخاصة بإدارة المستخدمين وحساباتهم
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from config import FREE_SUBSCRIPTION

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /account لعرض معلومات حساب المستخدم"""
    user_id = str(update.effective_user.id)
    
    # الحصول على بيانات المستخدم
    user = db.get_user(user_id)
    if not user:
        # إذا لم يكن المستخدم مسجلاً، نقوم بتسجيله
        await register_user(update)
        user = db.get_user(user_id)
    
    # الحصول على بيانات المحفظة والاشتراك وأرصدة الطلبات
    wallet = db.get_wallet(user_id)
    subscription = db.get_subscription(user_id)
    request_balance = db.get_request_balance(user_id)
    
    # تحديد نوع الاشتراك
    subscription_type = subscription['subscription_type'] if subscription else 'مجاني'
    
    # إنشاء نص معلومات الحساب
    account_text = f"""الاشتراك: {subscription_type} ✔️
النموذج الحالي: {user['preferred_model']} /model

الرصيد المتوفر: {wallet['balance']} ⭐

📊 الاستخدام

الطلبات الأسبوعية: {request_balance['weekly_requests_used']}/{request_balance['weekly_requests']}
 └ GPT-4.1 mini | GPT-4o mini
 └ DeepSeek-V3
 └ Gemini 2.5 Flash
 └ بحث الويب مع Perplexity
 └ GPT-4o Images

📝 حزمة ChatGPT: {request_balance['chatgpt_requests_used']}/{request_balance['chatgpt_requests']}
 └ OpenAI o3 | o4-mini
 └ GPT-4.5 | GPT-4.1 | GPT-4o
 └ صور DALL•E 3
 └ التعرف على الصور

📝 حزمة Claude: {request_balance['claude_requests_used']}/{request_balance['claude_requests']}
 └ Claude 4 Sonnet + Thinking
 └ التعرف على الصور
 └ التعرف على الملفات

🌅 حزمة الصور: {request_balance['image_requests_used']}/{request_balance['image_requests']}
 └ Midjourney | Flux
 └ تبديل الوجوه

🎬 حزمة الفيديو: {request_balance['video_requests_used']}/{request_balance['video_requests']}
 └ Kling AI | Pika AI
 └ تحويل النص إلى فيديو، الصورة إلى فيديو

🎸 أغاني Suno: {request_balance['suno_requests_used']}/{request_balance['suno_requests']}

هل تحتاج إلى المزيد من الطلبات؟
تحقق من /premium للحصول على خيارات إضافية"""
    
    # إنشاء أزرار شراء العملات
    keyboard = [
        [InlineKeyboardButton("شراء 100 عملة (110 نجمة) 💰", callback_data="buy_currency_100")],
        [InlineKeyboardButton("شراء 200 عملة (220 نجمة) 💰", callback_data="buy_currency_200")],
        [InlineKeyboardButton("شراء 350 عملة (360 نجمة) 💰", callback_data="buy_currency_350")],
        [InlineKeyboardButton("شراء 500 عملة (510 نجمة) 💰", callback_data="buy_currency_500")],
        [InlineKeyboardButton("شراء 1000 عملة (1000 نجمة) 💰", callback_data="buy_currency_1000")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(account_text, reply_markup=reply_markup)

async def register_user(update: Update):
    """تسجيل المستخدم في قاعدة البيانات"""
    user = update.effective_user
    language_code = user.language_code or 'ar'
    
    # التحقق من اللغة المدعومة
    if language_code not in ['ar', 'en', 'ru', 'es', 'fr', 'pt']:
        language_code = 'ar'  # اللغة الافتراضية هي العربية
    
    is_new = db.add_user(
        str(user.id),
        user.username,
        user.first_name,
        user.last_name,
        language_code
    )
    
    return is_new

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /premium لعرض خيارات الاشتراك المميز"""
    user_id = str(update.effective_user.id)
    
    # الحصول على بيانات المستخدم
    user = db.get_user(user_id)
    if not user:
        # إذا لم يكن المستخدم مسجلاً، نقوم بتسجيله
        await register_user(update)
    
    # إنشاء أزرار أنواع الاشتراكات
    keyboard = [
        [InlineKeyboardButton("مجاني", callback_data="subscription_free")],
        [InlineKeyboardButton("مدفوع", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("أنواع الاشتراكات:", reply_markup=reply_markup)

async def subscription_free_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار الاشتراك المجاني"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # تحديث اشتراك المستخدم إلى مجاني
    db.update_subscription(user_id, 'free', FREE_SUBSCRIPTION['duration_days'])
    
    # إعادة تعيين رصيد الطلبات الأسبوعية
    db.update_request_balance(user_id, 'weekly', FREE_SUBSCRIPTION['text_requests'])
    
    free_text = """مجاني | أسبوعي
☑️ 50 طلبًا نصيًا في الاسبوع
☑️ GPT-4.1 mini | GPT-4o mini
☑️ DeepSeek-V3 | Gemini 2.5 Flash
☑️ بحث الويب مع Perplexity
☑️ GPT-4o Images"""
    
    await query.edit_message_text(
        f"تم تفعيل الاشتراك المجاني بنجاح!\n\n{free_text}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="back_to_premium")]])
    )

async def subscription_paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار الاشتراك المدفوع"""
    query = update.callback_query
    await query.answer()
    
    # إنشاء نص الاشتراكات المدفوعة
    paid_text = "اختر خدمة للشراء:"
    
    # إنشاء أزرار الاشتراكات والحزم
    keyboard = [
        [InlineKeyboardButton("الاشتراك المميز | شهري", callback_data="premium_monthly")],
        [InlineKeyboardButton("الاشتراك المميز X2 | شهري", callback_data="premium_x2_monthly")],
        [InlineKeyboardButton("CHATGPT PLUS | حزم", callback_data="chatgpt_packages")],
        [InlineKeyboardButton("CLAUDE | حزم", callback_data="claude_packages")],
        [InlineKeyboardButton("MIDJOURNEY & FLUX | حزم", callback_data="image_packages")],
        [InlineKeyboardButton("فيديو | حزم", callback_data="video_packages")],
        [InlineKeyboardButton("أغاني SUNO | حزم", callback_data="suno_packages")],
        [InlineKeyboardButton("كومبو | شهري 🔥", callback_data="combo_package")],
        [InlineKeyboardButton("العودة 🔙", callback_data="back_to_premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(paid_text, reply_markup=reply_markup)

async def premium_monthly_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار الاشتراك المميز الشهري"""
    query = update.callback_query
    await query.answer()
    
    premium_text = """الاشتراك المميز | شهري
(يستطيع استخدام النماذج GPT-4.1 mini وGPT-4o mini وDeepSeek-V3 وGemini 2.5 Flash ونموذج بحث الويب Perplexity ونموذج GPT-4o Images ونماذج الصور Midjourney وFlux)
✅ 100 طلب نصياً يوميًا
✅ GPT-4.1 mini | GPT-4o mini
✅ DeepSeek-V3 | Gemini 2.5 Flash
✅ بحث الويب مع Perplexity
✅ استفسارات وردود صوتية
🌅 GPT-4o Images
🌅 10 صور Midjourney وFlux
السعر: 170 ⭐"""
    
    # إنشاء زر الشراء
    keyboard = [
        [InlineKeyboardButton("شراء الاشتراك المميز", callback_data="buy_premium_monthly")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(premium_text, reply_markup=reply_markup)

async def premium_x2_monthly_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار الاشتراك المميز X2 الشهري"""
    query = update.callback_query
    await query.answer()
    
    premium_x2_text = """الاشتراك المميز X2 | شهري
مضاعفة جميع الحدود x2 في المميز 
السعر: 320 ⭐"""
    
    # إنشاء زر الشراء
    keyboard = [
        [InlineKeyboardButton("شراء الاشتراك المميز X2", callback_data="buy_premium_x2_monthly")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(premium_x2_text, reply_markup=reply_markup)

async def chatgpt_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار حزم ChatGPT"""
    query = update.callback_query
    await query.answer()
    
    chatgpt_text = """CHATGPT PLUS | حزم
(يستطيع استخدام نماذج OpenAI o3 وo4-mini وGPT-4.5 وGPT-4.1 وGPT-4o ونموذج DALL•E للصور)
✅ من 50 لغاية 500 طلب
✅ OpenAI o3 | o4-mini
✅ GPT-4.5 | GPT-4.1 | GPT-4o
✅ التعرف على الصور
🌅 صور DALL•E 3
اختر عدد الطلبات:"""
    
    # إنشاء أزرار الحزم
    keyboard = [
        [InlineKeyboardButton("حزمة 50 طلب: 175 ⭐", callback_data="buy_chatgpt_50")],
        [InlineKeyboardButton("حزمة 100 طلب: 320 ⭐", callback_data="buy_chatgpt_100")],
        [InlineKeyboardButton("حزمة 200 طلب: 620 ⭐", callback_data="buy_chatgpt_200")],
        [InlineKeyboardButton("حزمة 500 طلب: 1550 ⭐", callback_data="buy_chatgpt_500")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(chatgpt_text, reply_markup=reply_markup)

async def claude_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار حزم Claude"""
    query = update.callback_query
    await query.answer()
    
    claude_text = """CLAUDE | حزم
(يستطيع استخدام النموذج Claude 4 Sonnet + Thinking والتعرف على الملفات والتعرف على الصور)
✅ من 100 لغاية 1,000 طلب
✅ Claude 4 Sonnet + Thinking
✅ التعرف على الملفات
✅ التعرف على الصور
اختر عدد الطلبات:"""
    
    # إنشاء أزرار الحزم
    keyboard = [
        [InlineKeyboardButton("حزمة 100 طلب: 175 ⭐", callback_data="buy_claude_100")],
        [InlineKeyboardButton("حزمة 200 طلب: 320 ⭐", callback_data="buy_claude_200")],
        [InlineKeyboardButton("حزمة 500 طلب: 720 ⭐", callback_data="buy_claude_500")],
        [InlineKeyboardButton("حزمة 1000 طلب: 1200 ⭐", callback_data="buy_claude_1000")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(claude_text, reply_markup=reply_markup)

async def image_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار حزم الصور"""
    query = update.callback_query
    await query.answer()
    
    image_text = """MIDJOURNEY & FLUX | حزم
(يستطيع استخدام نماذج Midjourney V7 وFlux)
🌅 من 50 لغاية 500 صورة
🌅 /Midjourney V7 وFlux
✅ تبديل الوجوه
اختر عدد طلبات الصور:"""
    
    # إنشاء أزرار الحزم
    keyboard = [
        [InlineKeyboardButton("حزمة 50 طلب صورة: 175 ⭐", callback_data="buy_image_50")],
        [InlineKeyboardButton("حزمة 100 طلب صورة: 320 ⭐", callback_data="buy_image_100")],
        [InlineKeyboardButton("حزمة 200 طلب صورة: 620 ⭐", callback_data="buy_image_200")],
        [InlineKeyboardButton("حزمة 500 طلب صورة: 1400 ⭐", callback_data="buy_image_500")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(image_text, reply_markup=reply_markup)

async def video_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار حزم الفيديو"""
    query = update.callback_query
    await query.answer()
    
    video_text = """فيديو | حزم
(يستطيع استخدام نماذج Kling 2.0 وPika AI)
🎬 10 إلى 50 عملية إنشاء
🎬 /Kling 2.0 وPika AI
✅ تحويل النص إلى فيديو، الصورة إلى فيديو
✅ مؤثرات بصرية إبداعية
اختر عدد طلبات انشاء الفيديو:"""
    
    # إنشاء أزرار الحزم
    keyboard = [
        [InlineKeyboardButton("حزمة 10 طلب انشاء: 375 ⭐", callback_data="buy_video_10")],
        [InlineKeyboardButton("حزمة 20 طلب انشاء: 730 ⭐", callback_data="buy_video_20")],
        [InlineKeyboardButton("حزمة 50 طلب انشاء: 1750 ⭐", callback_data="buy_video_50")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(video_text, reply_markup=reply_markup)

async def suno_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار حزم Suno"""
    query = update.callback_query
    await query.answer()
    
    suno_text = """أغاني SUNO | حزم
(يستطيع استخدام نموذج Suno V4.5)
🎸 50 إلى 100 عملية إنشاء
🎸 نموذج الذكاء الاصطناعي /Suno V4.5
✅ استخدام كلمات أغاني من إنشائك أو من إنشاء الذكاء الاصطناعي
اختر عدد طلبات الاغاني:"""
    
    # إنشاء أزرار الحزم
    keyboard = [
        [InlineKeyboardButton("حزمة 20 طلب انشاء اغنية: 175 ⭐", callback_data="buy_suno_20")],
        [InlineKeyboardButton("حزمة 50 طلب انشاء اغنية: 425 ⭐", callback_data="buy_suno_50")],
        [InlineKeyboardButton("حزمة 100 طلب انشاء اغنية: 780 ⭐", callback_data="buy_suno_100")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(suno_text, reply_markup=reply_markup)

async def combo_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار حزمة كومبو"""
    query = update.callback_query
    await query.answer()
    
    combo_text = """كومبو | شهري 🔥
✅ 100 طلب يوميًا
✅ 100 طلب ChatGPT Plus شهريا
🌅 100 صورة Midjourney وFlux شهريا
السعر: 580 ⭐ (خصم 30%)"""
    
    # إنشاء زر الشراء
    keyboard = [
        [InlineKeyboardButton("شراء حزمة كومبو", callback_data="buy_combo")],
        [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(combo_text, reply_markup=reply_markup)

async def back_to_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة إلى قائمة الاشتراكات الرئيسية"""
    query = update.callback_query
    await query.answer()
    
    # إنشاء أزرار أنواع الاشتراكات
    keyboard = [
        [InlineKeyboardButton("مجاني", callback_data="subscription_free")],
        [InlineKeyboardButton("مدفوع", callback_data="subscription_paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("أنواع الاشتراكات:", reply_markup=reply_markup)

async def deletecontext_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /deletecontext لحذف سياق المحادثة"""
    user_id = str(update.effective_user.id)
    
    # حذف سياق المحادثة للمستخدم
    db.delete_context(user_id)
    
    await update.message.reply_text("تم حذف السياق. عادةً ما يتذكر البوت سؤالك السابق وإجابته ويستخدم السياق في الرد")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /settings لعرض إعدادات البوت"""
    user_id = str(update.effective_user.id)
    
    # الحصول على بيانات المستخدم
    user = db.get_user(user_id)
    if not user:
        # إذا لم يكن المستخدم مسجلاً، نقوم بتسجيله
        await register_user(update)
        user = db.get_user(user_id)
    
    settings_text = """في هذا القسم، يمكنك:
1. اختيار نموذج الذكاء الاصطناعي.
2. تعيين أي دور أو تعليمات مخصصة سيأخذها البوت في الاعتبار عند إعداد الردود.
3. تشغيل أو إيقاف الحفاظ على السياق. عندما يكون السياق مفعلاً، يأخذ البوت في الاعتبار رده السابق لإجراء حوار.
4. إعداد الردود الصوتية واختيار صوت GPT (متاح في /premium).
5. اختيار لغة الواجهة"""
    
    # إنشاء أزرار الإعدادات
    keyboard = [
        [InlineKeyboardButton("اختيار نموذج الذكاء الاصطناعي", callback_data="settings_model")],
        [InlineKeyboardButton("تعيين التعليمات", callback_data="settings_instructions")],
        [InlineKeyboardButton(f"الحفاظ على السياق {'✅' if user['context_enabled'] else '❌'}", callback_data="settings_context")],
        [InlineKeyboardButton("الردود الصوتية", callback_data="settings_voice")],
        [InlineKeyboardButton("اللغة", callback_data="settings_language")],
        [InlineKeyboardButton("إغلاق", callback_data="settings_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(settings_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /help لعرض المساعدة"""
    help_text = """📝 إنشاء النص
لإنشاء نص، اكتب طلبك في الدردشة. يمكن للمستخدمين الذين لديهم اشتراك /premium أيضًا إرسال رسائل صوتية.
/s – بحث الويب مع Perplexity
/settings – إعدادات روبوت الدردشة
/model – التبديل بين نماذج الذكاء الاصطناعي

💬 استخدام السياق
يحتفظ الروبوت بالسياق افتراضيًا، مما يربط استفسارك الحالي بآخر رد له. هذا يسمح بالحوار وطرح أسئلة متابعة. لبدء موضوع جديد بدون سياق، استخدم أمر /deletecontext.

📄 التعرف على الملفات
عند استخدام نموذج Claude، يمكنك العمل مع المستندات. قم بتحميل ملف بتنسيق docx، pdf، xlsx، xls، csv، pptx، txt واطرح أسئلة حول المستند. يستهلك كل طلب 3 عمليات إنشاء من Claude.

🌅 إنشاء الصور
ينشئ الروبوت صورًا باستخدام أحدث نماذج Midjourney وChatGPT وFlux. ابدأ بأمر وأضف توجيهك:
/wow – بدء وضع صور GPT-4o
/flux – استخدام Flux
/dalle – استخدام DALL•E 3
/imagine – استخدام Midjourney
└ دليل (https://teletype.in/@gpt4telegrambot/midjourney) لإتقان Midjourney

🎸 إنشاء الأغاني
ينشئ الروبوت أغاني باستخدام Suno.
/chirp – إنشاء أغنية؛ سيطلب منك الروبوت اختيار نوع موسيقي وإدخال كلمات الأغنية
/Suno – دليل لإنشاء الأغاني

⚙️ أوامر أخرى
/start – وصف الروبوت
/account – ملفك الشخصي والرصيد
/premium – اختيار وشراء اشتراك مميز لـ ChatGPT وClaude وGemini وDALL•E 3 وMidjourney وFlux وSuno
/privacy – شروط الاستخدام وسياسة الخصوصية

لأي استفسارات، يمكنك أيضًا مراسلة المسؤول @NaJiMaS"""
    
    await update.message.reply_text(help_text)

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /privacy لعرض سياسة الخصوصية"""
    privacy_text = """شروط الاستخدام وسياسة الخصوصية

1. الاستخدام المقبول
- يجب استخدام البوت بطريقة قانونية وأخلاقية.
- يحظر استخدام البوت لإنشاء محتوى غير قانوني أو ضار أو مسيء.
- يحظر استخدام البوت لانتهاك حقوق الملكية الفكرية للآخرين.

2. المحتوى المنشأ
- المستخدم مسؤول بالكامل عن المحتوى الذي ينشئه باستخدام البوت.
- لا نتحمل أي مسؤولية عن أي محتوى ينشئه المستخدمون.

3. جمع البيانات
- نجمع معلومات المستخدم الأساسية مثل معرف المستخدم واسم المستخدم واللغة المفضلة.
- نحتفظ بسجلات المحادثات لتحسين جودة الخدمة.

4. استخدام البيانات
- نستخدم البيانات المجمعة لتحسين خدماتنا وتخصيص تجربة المستخدم.
- لا نشارك بياناتك مع أطراف ثالثة إلا بموافقتك الصريحة.

5. الاشتراكات والمدفوعات
- جميع المدفوعات نهائية ولا يمكن استردادها.
- نحتفظ بالحق في تغيير أسعار الاشتراكات والحزم في أي وقت.

6. التغييرات في الشروط
- نحتفظ بالحق في تعديل هذه الشروط في أي وقت.
- سيتم إخطار المستخدمين بالتغييرات الهامة في الشروط.

باستخدام هذا البوت، فإنك توافق على الالتزام بهذه الشروط وسياسة الخصوصية."""
    
    await update.message.reply_text(privacy_text)

# تسجيل معالجات الأوامر والاستجابات
def register_user_handlers(application):
    """تسجيل معالجات أوامر المستخدم"""
    application.add_handler(CommandHandler("account", account_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("deletecontext", deletecontext_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("privacy", privacy_command))
    
    # معالجات الاستجابة للأزرار
    application.add_handler(CallbackQueryHandler(subscription_free_callback, pattern="^subscription_free$"))
    application.add_handler(CallbackQueryHandler(subscription_paid_callback, pattern="^subscription_paid$"))
    application.add_handler(CallbackQueryHandler(premium_monthly_callback, pattern="^premium_monthly$"))
    application.add_handler(CallbackQueryHandler(premium_x2_monthly_callback, pattern="^premium_x2_monthly$"))
    application.add_handler(CallbackQueryHandler(chatgpt_packages_callback, pattern="^chatgpt_packages$"))
    application.add_handler(CallbackQueryHandler(claude_packages_callback, pattern="^claude_packages$"))
    application.add_handler(CallbackQueryHandler(image_packages_callback, pattern="^image_packages$"))
    application.add_handler(CallbackQueryHandler(video_packages_callback, pattern="^video_packages$"))
    application.add_handler(CallbackQueryHandler(suno_packages_callback, pattern="^suno_packages$"))
    application.add_handler(CallbackQueryHandler(combo_package_callback, pattern="^combo_package$"))
    application.add_handler(CallbackQueryHandler(back_to_premium_callback, pattern="^back_to_premium$"))
