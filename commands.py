#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف الأوامر والردود
يحتوي على وظائف معالجة الأوامر والردود التفاعلية
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from languages import get_text
from api_keys import get_available_models
from subscriptions import check_subscription_status, get_subscription_info, use_request

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

async def midjourney_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /midjourney"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص Midjourney
    midjourney_text = get_text("midjourney_intro", lang_code) + "\n\n" + \
                     get_text("midjourney_example", lang_code) + "\n\n" + \
                     get_text("midjourney_details", lang_code)
    
    # إنشاء زر شراء حزمة Midjourney
    keyboard = [[InlineKeyboardButton(get_text("buy_midjourney_button", lang_code), callback_data="image_packages")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(midjourney_text, reply_markup=reply_markup)

async def video_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /video"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # التحقق من توفر رصيد للفيديو
    has_video_access = await check_video_access(user_id)
    
    if not has_video_access:
        # إذا لم يكن لديه وصول للفيديو، نعرض رسالة الترقية
        await update.message.reply_text(
            get_text("video_generation_not_available", lang_code),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text("premium_button", lang_code), callback_data="premium")]])
        )
        return
    
    # نص الفيديو
    video_text = get_text("video_intro", lang_code) + "\n\n" + \
                get_text("video_models_details", lang_code)
    
    # إنشاء أزرار خدمات الفيديو
    keyboard = [
        [InlineKeyboardButton("🐰 Pika 2.2", callback_data="video_pika"), InlineKeyboardButton("🐼 Kling AI", callback_data="video_kling")],
        [InlineKeyboardButton("🧩 Pikaddition", callback_data="video_pikaddition"), InlineKeyboardButton("💫 Pika Effects", callback_data="video_effects")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(video_text, reply_markup=reply_markup)

async def check_video_access(user_id):
    """التحقق من إمكانية الوصول إلى خدمات الفيديو"""
    # الحصول على معلومات الاشتراك
    subscription_info = await get_subscription_info(user_id)
    
    # التحقق من وجود رصيد للفيديو
    if subscription_info['video_requests'] > subscription_info['video_requests_used']:
        return True
    
    # التحقق من نوع الاشتراك
    subscription_type = await check_subscription_status(user_id)
    if subscription_type in ['premium', 'premium_x2', 'combo']:
        return True
    
    return False

async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /photo"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # التحقق مما إذا كان المستخدم قد وافق على الشروط من قبل
    if 'photo_agreed' not in context.user_data:
        # عرض شروط الاستخدام
        photo_text = get_text("photo_intro", lang_code) + "\n\n" + \
                    get_text("photo_rules", lang_code)
        
        # إنشاء زر الموافقة
        keyboard = [[InlineKeyboardButton(get_text("agree_button", lang_code), callback_data="photo_agree")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(photo_text, reply_markup=reply_markup)
    else:
        # إذا كان المستخدم قد وافق بالفعل، نعرض قائمة الخدمات
        await show_photo_services(update, context)

async def photo_agree_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع الموافقة على شروط الصور"""
    query = update.callback_query
    await query.answer()
    
    # تسجيل موافقة المستخدم
    context.user_data['photo_agreed'] = True
    
    # عرض قائمة خدمات الصور
    await show_photo_services(update, context)

async def show_photo_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة خدمات الصور"""
    user_id = str(update.effective_user.id) if update.effective_user else str(update.callback_query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص خدمات الصور
    photo_services_text = get_text("photo_service_selection", lang_code) + "\n\n" + \
                         get_text("photo_service_details", lang_code)
    
    # إنشاء أزرار خدمات الصور
    keyboard = [
        [InlineKeyboardButton("🌠 صور GPT-4o", callback_data="photo_gpt4o")],
        [InlineKeyboardButton("🌅 Midjourney", callback_data="photo_midjourney")],
        [InlineKeyboardButton("🔺Flux", callback_data="photo_flux")],
        [InlineKeyboardButton("🖼️DALL•E 3", callback_data="photo_dalle")],
        [InlineKeyboardButton("🖋 محرر Gemini", callback_data="photo_gemini")],
        [InlineKeyboardButton("📸 الصور الرمزية الرقمية", callback_data="photo_avatars")],
        [InlineKeyboardButton("🎭 تبديل الوجه", callback_data="photo_faceswap")],
        [InlineKeyboardButton(get_text("close_button", lang_code), callback_data="photo_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # إرسال الرسالة أو تحديث الرسالة الحالية
    if hasattr(update, 'message'):
        await update.message.reply_text(photo_services_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(photo_services_text, reply_markup=reply_markup)

async def suno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /suno"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # التحقق من توفر رصيد لـ Suno
    request_balance = db.get_request_balance(user_id)
    has_suno_access = request_balance and request_balance['suno_requests'] > request_balance['suno_requests_used']
    
    # نص Suno
    suno_text = get_text("suno_intro", lang_code) + "\n\n" + \
               get_text("suno_details", lang_code)
    
    # إنشاء أزرار Suno
    keyboard = []
    if has_suno_access:
        keyboard.append([InlineKeyboardButton(get_text("buy_suno_button", lang_code), callback_data="suno_packages")])
        keyboard.append([InlineKeyboardButton(get_text("start_suno_button", lang_code), callback_data="suno_start")])
    else:
        keyboard.append([InlineKeyboardButton(get_text("buy_suno_button", lang_code), callback_data="suno_packages")])
        # إذا لم يكن لديه وصول، نعرض رسالة
        await update.message.reply_text(get_text("suno_no_requests", lang_code))
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(suno_text, reply_markup=reply_markup)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /s للبحث"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص البحث
    search_text = get_text("search_intro", lang_code) + "\n\n" + \
                 get_text("search_prompt", lang_code)
    
    # الحصول على النماذج المتاحة للبحث
    available_models = await get_available_models(user_id)
    search_models = [model for model in available_models if "perplexity" in model.lower()]
    
    # إضافة نموذج البحث الافتراضي إذا لم يكن هناك نماذج متاحة
    if not search_models:
        search_models = ["Perplexity"]
    
    # إنشاء أزرار نماذج البحث
    keyboard = []
    for model in search_models:
        # إضافة علامة ✅ للنموذج المفضل
        model_text_display = f"{model} ✅" if model == user.get('preferred_model') else model
        keyboard.append([InlineKeyboardButton(model_text_display, callback_data=f"search_model_{model}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # حفظ حالة البحث في سياق المحادثة
    context.user_data['search_mode'] = True
    
    await update.message.reply_text(search_text, reply_markup=reply_markup)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /settings"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص الإعدادات
    settings_text = get_text("settings_intro", lang_code)
    
    # إنشاء أزرار الإعدادات
    context_status = "✅" if user.get('context_enabled', 1) else "❌"
    keyboard = [
        [InlineKeyboardButton(get_text("select_model_button", lang_code), callback_data="settings_model")],
        [InlineKeyboardButton(get_text("set_instructions_button", lang_code), callback_data="settings_instructions")],
        [InlineKeyboardButton(get_text("context_toggle_button", lang_code, status=context_status), callback_data="settings_context")],
        [InlineKeyboardButton(get_text("voice_responses_button", lang_code), callback_data="settings_voice")],
        [InlineKeyboardButton(get_text("language_button", lang_code), callback_data="settings_language")],
        [InlineKeyboardButton(get_text("close_button", lang_code), callback_data="settings_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(settings_text, reply_markup=reply_markup)

async def settings_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إعدادات اللغة"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص اختيار اللغة
    language_text = get_text("select_language", lang_code)
    
    # إنشاء أزرار اللغات
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es")],
        [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")],
        [InlineKeyboardButton("Português 🇧🇷", callback_data="lang_pt")],
        [InlineKeyboardButton(get_text("back_button", lang_code), callback_data="settings_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(language_text, reply_markup=reply_markup)

async def language_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار اللغة"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # استخراج اللغة المختارة
    lang_code = query.data.split('_')[-1]
    
    # تحديث لغة المستخدم
    db.update_user_language(user_id, lang_code)
    
    # الحصول على المستخدم بعد التحديث
    user = db.get_user(user_id)
    
    # رسالة تأكيد تغيير اللغة
    language_names = {
        "ar": "العربية",
        "en": "English",
        "ru": "Русский",
        "es": "Español",
        "fr": "Français",
        "pt": "Português"
    }
    
    language_name = language_names.get(lang_code, lang_code)
    
    await query.edit_message_text(
        get_text("language_set", lang_code, language=language_name),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text("back_button", lang_code), callback_data="settings_back")]])
    )

async def settings_context_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تبديل إعداد حفظ السياق"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # تبديل حالة حفظ السياق
    current_status = user.get('context_enabled', 1)
    new_status = 0 if current_status else 1
    
    # تحديث إعداد حفظ السياق
    db.update_context_setting(user_id, new_status)
    
    # إعادة عرض قائمة الإعدادات
    await settings_command(update, context)

async def settings_instructions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إعدادات التعليمات"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص التعليمات
    instructions_text = get_text("set_instructions_prompt", lang_code) + "\n\n" + \
                       get_text("custom_instructions_example", lang_code)
    
    # إنشاء أزرار التعليمات
    instructions_status = "✅" if user.get('instructions_enabled', 0) else "❌"
    keyboard = [
        [InlineKeyboardButton(get_text("set_instructions_button", lang_code), callback_data="instructions_set")],
        [InlineKeyboardButton(get_text("instructions_toggle_button", lang_code, status=instructions_status), callback_data="instructions_toggle")],
        [InlineKeyboardButton(get_text("back_button", lang_code), callback_data="settings_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instructions_text, reply_markup=reply_markup)

async def instructions_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تعيين التعليمات"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['user_action'] = 'set_instructions'
    
    await query.edit_message_text(
        get_text("set_instructions_input_prompt", lang_code),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text("cancel_button", lang_code), callback_data="settings_back")]])
    )

async def instructions_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تبديل تفعيل التعليمات"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # تبديل حالة تفعيل التعليمات
    current_status = user.get('instructions_enabled', 0)
    new_status = 0 if current_status else 1
    
    # تحديث إعداد التعليمات
    db.update_user_instructions(user_id, user.get('custom_instructions', ''), new_status)
    
    # إعادة عرض قائمة إعدادات التعليمات
    await settings_instructions_callback(update, context)

async def settings_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إعدادات الردود الصوتية"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص إعدادات الصوت
    voice_text = get_text("voice_settings_prompt", lang_code) + "\n\n" + \
                get_text("female_voices", lang_code) + "\n" + \
                get_text("male_voices", lang_code)
    
    # إنشاء أزرار الأصوات
    keyboard = []
    
    # الأصوات الأنثوية
    female_voices = ["nova", "shimmer"]
    for voice in female_voices:
        voice_text_display = f"{voice} ✅" if voice == user.get('preferred_voice') else voice
        keyboard.append([InlineKeyboardButton(voice_text_display, callback_data=f"voice_select_{voice}")])
    
    # الأصوات الذكورية
    male_voices = ["alloy", "echo", "fable", "onyx"]
    for voice in male_voices:
        voice_text_display = f"{voice} ✅" if voice == user.get('preferred_voice') else voice
        keyboard.append([InlineKeyboardButton(voice_text_display, callback_data=f"voice_select_{voice}")])
    
    # أزرار إضافية
    voice_status = "✅" if user.get('voice_enabled', 0) else "❌"
    keyboard.append([InlineKeyboardButton(get_text("voice_toggle_button", lang_code, status=voice_status), callback_data="voice_toggle")])
    keyboard.append([InlineKeyboardButton(get_text("listen_voices_button", lang_code), callback_data="voice_listen")])
    keyboard.append([InlineKeyboardButton(get_text("back_button", lang_code), callback_data="settings_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(voice_text, reply_markup=reply_markup)

async def voice_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار الصوت"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # استخراج الصوت المختار
    voice = query.data.split('_')[-1]
    
    # تحديث إعدادات الصوت
    db.update_user_voice_settings(user_id, user.get('voice_enabled', 0), voice)
    
    await query.edit_message_text(
        get_text("voice_set", lang_code, voice=voice),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text("back_button", lang_code), callback_data="settings_voice")]])
    )

async def voice_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تبديل تفعيل الردود الصوتية"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # تبديل حالة تفعيل الردود الصوتية
    current_status = user.get('voice_enabled', 0)
    new_status = 0 if current_status else 1
    
    # تحديث إعدادات الصوت
    db.update_user_voice_settings(user_id, new_status)
    
    # إعادة عرض قائمة إعدادات الصوت
    await settings_voice_callback(update, context)

async def settings_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة إلى قائمة الإعدادات الرئيسية"""
    query = update.callback_query
    await query.answer()
    
    # إعادة عرض قائمة الإعدادات
    await settings_command(update, context)

async def settings_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إغلاق قائمة الإعدادات"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    await query.edit_message_text(get_text("action_cancelled", lang_code))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /help"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص المساعدة
    help_text = get_text("help_command_text", lang_code)
    
    await update.message.reply_text(help_text)

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع أمر /privacy"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # نص سياسة الخصوصية
    privacy_text = get_text("privacy_command_text", lang_code)
    
    await update.message.reply_text(privacy_text)

async def process_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل المستخدم العادية"""
    user_id = str(update.effective_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # التحقق من الإجراء الحالي
    if 'user_action' in context.user_data:
        action = context.user_data['user_action']
        
        if action == 'set_instructions':
            # تعيين التعليمات المخصصة
            instructions = update.message.text.strip()
            
            # تحديث التعليمات المخصصة
            db.update_user_instructions(user_id, instructions, 1)
            
            # إعادة تعيين الحالة
            del context.user_data['user_action']
            
            await update.message.reply_text(
                get_text("instructions_set", lang_code),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text("back_button", lang_code), callback_data="settings_instructions")]])
            )
            return
    
    # التحقق من وضع البحث
    if context.user_data.get('search_mode'):
        # معالجة استعلام البحث
        query_text = update.message.text.strip()
        
        # إرسال رسالة انتظار
        await update.message.reply_text(get_text("search_waiting", lang_code))
        
        # هنا يتم معالجة البحث واستدعاء API البحث
        # ...
        
        # إعادة تعيين وضع البحث
        context.user_data['search_mode'] = False
        
        # إنشاء أزرار نتائج البحث
        keyboard = [
            [InlineKeyboardButton(get_text("search_sources_button", lang_code), callback_data="search_sources")],
            [InlineKeyboardButton(get_text("search_videos_button", lang_code), callback_data="search_videos")],
            [InlineKeyboardButton(get_text("search_related_button", lang_code), callback_data="search_related")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # هنا يتم إرسال نتائج البحث
        await update.message.reply_text(
            f"نتائج البحث لـ '{query_text}':\n\n"
            "هذه نتائج بحث تجريبية. في التطبيق الفعلي، سيتم استدعاء API البحث وعرض النتائج الحقيقية.",
            reply_markup=reply_markup
        )
        return
    
    # معالجة الرسائل العادية (استعلامات الذكاء الاصطناعي)
    message_text = update.message.text.strip()
    
    # الحصول على النموذج المفضل للمستخدم
    preferred_model = user.get('preferred_model', 'GPT-4.1 mini')
    
    # التحقق من توفر رصيد للطلب
    request_type = 'weekly'  # افتراضي للنماذج المجانية
    
    # تحديد نوع الطلب بناءً على النموذج
    if preferred_model in ["OpenAI o3", "o4-mini", "GPT-4.5", "GPT-4.1", "GPT-4o", "DALL•E 3"]:
        request_type = 'chatgpt'
    elif preferred_model in ["Claude 4 Sonnet", "Claude 4 Thinking"]:
        request_type = 'claude'
    
    # التحقق من توفر رصيد للطلب
    if not await use_request(user_id, request_type):
        # إذا لم يكن هناك رصيد كافٍ
        await update.message.reply_text(
            f"عذراً، ليس لديك رصيد كافٍ لاستخدام نموذج {preferred_model}. يرجى اختيار نموذج آخر أو شراء المزيد من الطلبات.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text("premium_button", lang_code), callback_data="premium")]])
        )
        return
    
    # إرسال رسالة انتظار
    await update.message.reply_text(get_text("search_waiting", lang_code))
    
    # هنا يتم معالجة الاستعلام واستدعاء API الذكاء الاصطناعي
    # ...
    
    # هنا يتم إرسال رد الذكاء الاصطناعي
    await update.message.reply_text(
        f"رد تجريبي من نموذج {preferred_model}:\n\n"
        f"سؤالك: {message_text}\n\n"
        "هذا رد تجريبي. في التطبيق الفعلي، سيتم استدعاء API الذكاء الاصطناعي وعرض الرد الحقيقي."
    )

# تسجيل معالجات الأوامر والردود
def register_command_handlers(application):
    """تسجيل معالجات الأوامر والردود"""
    # معالجات الأوامر
    application.add_handler(CommandHandler("midjourney", midjourney_command))
    application.add_handler(CommandHandler("video", video_command))
    application.add_handler(CommandHandler("photo", photo_command))
    application.add_handler(CommandHandler("suno", suno_command))
    application.add_handler(CommandHandler("s", search_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("privacy", privacy_command))
    
    # معالجات الاستجابة للأزرار
    application.add_handler(CallbackQueryHandler(photo_agree_callback, pattern="^photo_agree$"))
    application.add_handler(CallbackQueryHandler(settings_language_callback, pattern="^settings_language$"))
    application.add_handler(CallbackQueryHandler(language_select_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(settings_context_callback, pattern="^settings_context$"))
    application.add_handler(CallbackQueryHandler(settings_instructions_callback, pattern="^settings_instructions$"))
    application.add_handler(CallbackQueryHandler(instructions_set_callback, pattern="^instructions_set$"))
    application.add_handler(CallbackQueryHandler(instructions_toggle_callback, pattern="^instructions_toggle$"))
    application.add_handler(CallbackQueryHandler(settings_voice_callback, pattern="^settings_voice$"))
    application.add_handler(CallbackQueryHandler(voice_select_callback, pattern="^voice_select_"))
    application.add_handler(CallbackQueryHandler(voice_toggle_callback, pattern="^voice_toggle$"))
    application.add_handler(CallbackQueryHandler(settings_back_callback, pattern="^settings_back$"))
    application.add_handler(CallbackQueryHandler(settings_close_callback, pattern="^settings_close$"))
