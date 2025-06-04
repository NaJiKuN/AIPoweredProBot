#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة مفاتيح API
يحتوي على الوظائف الخاصة بإدارة مفاتيح API للنماذج المختلفة
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from admin import is_admin

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

async def admin_manage_api_keys_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إدارة مفاتيح API"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # الحصول على جميع مفاتيح API
    api_keys = db.get_all_api_keys()
    
    # إنشاء نص بقائمة مفاتيح API
    api_keys_text = "قائمة مفاتيح API الحالية:\n\n"
    
    if api_keys:
        for model, key in api_keys.items():
            # إخفاء جزء من المفتاح للأمان
            masked_key = key[:8] + "..." + key[-8:] if len(key) > 16 else "***"
            api_keys_text += f"• {model}: {masked_key}\n"
    else:
        api_keys_text += "لا توجد مفاتيح API مسجلة حالياً."
    
    # إنشاء لوحة مفاتيح لإدارة مفاتيح API
    keyboard = [
        [InlineKeyboardButton("إضافة مفتاح API ➕", callback_data="api_add_key")],
        [InlineKeyboardButton("إزالة مفتاح API ➖", callback_data="api_remove_key")],
        [InlineKeyboardButton("تعديل مفتاح API 🔄", callback_data="api_edit_key")],
        [InlineKeyboardButton("العودة للوحة التحكم 🔙", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(api_keys_text, reply_markup=reply_markup)

async def api_add_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إضافة مفتاح API جديد"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'add_api_key_name'
    
    await query.edit_message_text(
        "يرجى إرسال اسم النموذج الذي تريد إضافة مفتاح API له.\n"
        "مثال: ChatGPT, GPT-4, Claude, Gemini, Midjourney, Flux, etc.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="api_cancel")]])
    )

async def api_remove_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إزالة مفتاح API"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # الحصول على جميع مفاتيح API
    api_keys = db.get_all_api_keys()
    
    if not api_keys:
        await query.edit_message_text(
            "لا توجد مفاتيح API مسجلة حالياً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")]])
        )
        return
    
    # إنشاء لوحة مفاتيح لإزالة مفاتيح API
    keyboard = []
    for model in api_keys.keys():
        keyboard.append([InlineKeyboardButton(f"إزالة {model}", callback_data=f"api_remove_{model}")])
    
    keyboard.append([InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر مفتاح API الذي تريد إزالته:", reply_markup=reply_markup)

async def api_edit_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تعديل مفتاح API"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # الحصول على جميع مفاتيح API
    api_keys = db.get_all_api_keys()
    
    if not api_keys:
        await query.edit_message_text(
            "لا توجد مفاتيح API مسجلة حالياً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")]])
        )
        return
    
    # إنشاء لوحة مفاتيح لتعديل مفاتيح API
    keyboard = []
    for model in api_keys.keys():
        keyboard.append([InlineKeyboardButton(f"تعديل {model}", callback_data=f"api_edit_{model}")])
    
    keyboard.append([InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر مفتاح API الذي تريد تعديله:", reply_markup=reply_markup)

async def api_process_remove_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إزالة مفتاح API محدد"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # استخراج اسم النموذج المراد إزالة مفتاحه
    model_name = query.data.split('_')[-1]
    
    # إزالة مفتاح API
    db.remove_api_key(model_name)
    logger.info(f"تمت إزالة مفتاح API للنموذج {model_name} بواسطة {user_id}")
    
    await query.edit_message_text(
        f"تمت إزالة مفتاح API للنموذج {model_name} بنجاح.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")]])
    )

async def api_process_edit_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة تعديل مفتاح API محدد"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        await query.edit_message_text("عذراً، هذا الإجراء متاح فقط للمسؤولين.")
        return
    
    # استخراج اسم النموذج المراد تعديل مفتاحه
    model_name = query.data.split('_')[-1]
    
    # حفظ الحالة في سياق المحادثة
    context.user_data['admin_action'] = 'edit_api_key'
    context.user_data['api_model_name'] = model_name
    
    await query.edit_message_text(
        f"يرجى إرسال مفتاح API الجديد للنموذج {model_name}.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="api_cancel")]])
    )

async def api_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء الإجراء الحالي"""
    query = update.callback_query
    await query.answer()
    
    # إعادة تعيين الحالة
    if 'admin_action' in context.user_data:
        del context.user_data['admin_action']
    
    if 'api_model_name' in context.user_data:
        del context.user_data['api_model_name']
    
    await query.edit_message_text(
        "تم إلغاء الإجراء.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")]])
    )

async def api_process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل في وضع إدارة مفاتيح API"""
    user_id = str(update.effective_user.id)
    
    # التحقق من صلاحيات المسؤول
    if not await is_admin(user_id):
        return
    
    # التحقق من الإجراء الحالي
    if 'admin_action' in context.user_data:
        action = context.user_data['admin_action']
        
        if action == 'add_api_key_name':
            # حفظ اسم النموذج
            model_name = update.message.text.strip()
            context.user_data['api_model_name'] = model_name
            context.user_data['admin_action'] = 'add_api_key_value'
            
            await update.message.reply_text(
                f"تم تسجيل اسم النموذج: {model_name}\n"
                "يرجى إرسال مفتاح API الخاص بهذا النموذج.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء ❌", callback_data="api_cancel")]])
            )
        
        elif action == 'add_api_key_value':
            # إضافة مفتاح API جديد
            api_key = update.message.text.strip()
            model_name = context.user_data['api_model_name']
            
            # إضافة المفتاح إلى قاعدة البيانات
            db.add_api_key(model_name, api_key, user_id)
            logger.info(f"تمت إضافة مفتاح API جديد للنموذج {model_name} بواسطة {user_id}")
            
            # إعادة تعيين الحالة
            del context.user_data['admin_action']
            del context.user_data['api_model_name']
            
            await update.message.reply_text(
                f"تمت إضافة مفتاح API للنموذج {model_name} بنجاح.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")]])
            )
        
        elif action == 'edit_api_key':
            # تعديل مفتاح API
            api_key = update.message.text.strip()
            model_name = context.user_data['api_model_name']
            
            # تحديث المفتاح في قاعدة البيانات
            db.add_api_key(model_name, api_key, user_id)
            logger.info(f"تم تعديل مفتاح API للنموذج {model_name} بواسطة {user_id}")
            
            # إعادة تعيين الحالة
            del context.user_data['admin_action']
            del context.user_data['api_model_name']
            
            await update.message.reply_text(
                f"تم تعديل مفتاح API للنموذج {model_name} بنجاح.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="admin_manage_api_keys")]])
            )

async def get_available_models(user_id):
    """الحصول على النماذج المتاحة للمستخدم بناءً على مفاتيح API المتوفرة والاشتراك"""
    # الحصول على بيانات المستخدم والاشتراك
    user = db.get_user(user_id)
    subscription = db.get_subscription(user_id)
    request_balance = db.get_request_balance(user_id)
    
    # الحصول على جميع مفاتيح API النشطة
    api_keys = db.get_all_api_keys()
    
    # قائمة النماذج المتاحة
    available_models = []
    
    # إضافة النماذج المجانية
    free_models = ["GPT-4.1 mini", "GPT-4o mini", "DeepSeek-V3", "Gemini2.5", "Perplexity"]
    for model in free_models:
        if model.lower() in [m.lower() for m in api_keys.keys()]:
            available_models.append(model)
    
    # إضافة النماذج المدفوعة حسب الاشتراك
    if subscription and subscription['subscription_type'] in ['premium', 'premium_x2', 'combo']:
        # النماذج المتاحة في الاشتراك المميز
        premium_models = ["GPT-4o Images"]
        for model in premium_models:
            if model.lower() in [m.lower() for m in api_keys.keys()]:
                available_models.append(model)
    
    # إضافة النماذج المدفوعة حسب الحزم
    if request_balance['chatgpt_requests'] > request_balance['chatgpt_requests_used']:
        chatgpt_models = ["OpenAI o3", "o4-mini", "GPT-4.5", "GPT-4.1", "GPT-4o", "DALL•E 3"]
        for model in chatgpt_models:
            if model.lower() in [m.lower() for m in api_keys.keys()]:
                available_models.append(model)
    
    if request_balance['claude_requests'] > request_balance['claude_requests_used']:
        claude_models = ["Claude 4 Sonnet", "Claude 4 Thinking"]
        for model in claude_models:
            if model.lower() in [m.lower() for m in api_keys.keys()]:
                available_models.append(model)
    
    if request_balance['image_requests'] > request_balance['image_requests_used']:
        image_models = ["Midjourney", "Flux"]
        for model in image_models:
            if model.lower() in [m.lower() for m in api_keys.keys()]:
                available_models.append(model)
    
    if request_balance['video_requests'] > request_balance['video_requests_used']:
        video_models = ["Kling AI", "Pika AI"]
        for model in video_models:
            if model.lower() in [m.lower() for m in api_keys.keys()]:
                available_models.append(model)
    
    if request_balance['suno_requests'] > request_balance['suno_requests_used']:
        suno_models = ["Suno"]
        for model in suno_models:
            if model.lower() in [m.lower() for m in api_keys.keys()]:
                available_models.append(model)
    
    return available_models

async def settings_model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إعدادات اختيار نموذج الذكاء الاصطناعي"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # الحصول على النماذج المتاحة للمستخدم
    available_models = await get_available_models(user_id)
    
    # الحصول على النموذج المفضل للمستخدم
    user = db.get_user(user_id)
    preferred_model = user['preferred_model']
    
    # إنشاء نص اختيار النموذج
    model_text = """هنا، يمكنك التبديل بين نماذج ChatGPT و Claude و DeepSeek و Gemini:

🍓 OpenAI o3 — نموذج متقدم لحل المشكلات المعقدة من خلال التفكير المنطقي. كل طلب يستهلك 3 جيلات.
🤖 OpenAI o4-mini — نموذج تفكير جديد للبرمجة والرياضيات والعلوم.

🌟 GPT-4.5 — أكثر نماذج GPT "إنسانية" مع التعاطف ونهج إبداعي. كل طلب يستهلك 5 إنشاءات.
🖥 GPT-4.1 — نموذج جديد من OpenAI للبرمجة والعمل مع النصوص.
🔥 GPT-4o — نموذج ذكي وسريع للعمل مع النصوص.
✔️ GPT-4.1 mini/4o mini — نماذج صغيرة اقتصادية من OpenAI للمهام اليومية.

🚀 Claude 4 Sonnet — النموذج الرئيسي من Anthropic للتفكير المنطقي والبرمجة والرياضيات.
💬️ Claude 4 Thinking — وضع من Claude Sonnet يأخذ وقتًا إضافيًا لاستكشاف أساليب متعددة قبل الرد. كل طلب يستهلك 5 جيلات.

🐼 DeepSeek-V3 (Mar'25) — نموذج نصي قوي من مطور صيني.
🐳 DeepSeek-R1 — نموذج تفكير للمهام المعقدة.

⚡️ Gemini 2.5 Flash — أفضل نموذج للتفكير متعدد الخطوات من Google.

التعرف على الصور يعمل في نماذج Claude و OpenAI o3/o4 و GPT-4.5/4o.

التعرف على الملفات (docx, pdf, xlsx, csv, pptx, txt) متاح في Claude. قم بتحميل مستند حتى 10 ميجابايت وطرح الأسئلة. كل طلب يستهلك 3 جيلات.

GPT-4.1 mini وGemini 2.5 وDeepSeek-V3 متاحة مجانًا. يمكنك شراء حق الوصول إلى نماذج أخرى في /premium"""
    
    # إنشاء أزرار النماذج المتاحة
    keyboard = []
    for model in available_models:
        # إضافة علامة ✅ للنموذج المفضل
        model_text_display = f"{model} ✅" if model == preferred_model else model
        keyboard.append([InlineKeyboardButton(model_text_display, callback_data=f"model_select_{model}")])
    
    keyboard.append([InlineKeyboardButton("العودة 🔙", callback_data="settings_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(model_text, reply_markup=reply_markup)

async def model_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار نموذج الذكاء الاصطناعي"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # استخراج النموذج المختار
    model = query.data.split('_')[-1]
    
    # تحديث النموذج المفضل للمستخدم
    db.update_user_model_preference(user_id, model)
    
    await query.edit_message_text(
        f"تم تعيين {model} كنموذج الذكاء الاصطناعي المفضل لديك.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="settings_model")]])
    )

# تسجيل معالجات الأوامر والاستجابات
def register_api_handlers(application):
    """تسجيل معالجات إدارة مفاتيح API"""
    application.add_handler(CallbackQueryHandler(admin_manage_api_keys_callback, pattern="^admin_manage_api_keys$"))
    application.add_handler(CallbackQueryHandler(api_add_key_callback, pattern="^api_add_key$"))
    application.add_handler(CallbackQueryHandler(api_remove_key_callback, pattern="^api_remove_key$"))
    application.add_handler(CallbackQueryHandler(api_edit_key_callback, pattern="^api_edit_key$"))
    application.add_handler(CallbackQueryHandler(api_process_remove_key, pattern="^api_remove_"))
    application.add_handler(CallbackQueryHandler(api_process_edit_key, pattern="^api_edit_"))
    application.add_handler(CallbackQueryHandler(api_cancel_callback, pattern="^api_cancel$"))
    application.add_handler(CallbackQueryHandler(settings_model_callback, pattern="^settings_model$"))
    application.add_handler(CallbackQueryHandler(model_select_callback, pattern="^model_select_"))
