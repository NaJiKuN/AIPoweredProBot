# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import openai
import google.generativeai as genai

# استيراد الإعدادات وأدوات قاعدة البيانات
import config
import database_utils as db

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تهيئة البوت والديسباتشر
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

# تهيئة عملاء OpenAI و Gemini إذا كانت المفاتيح موجودة
if config.OPENAI_API_KEY:
    openai.api_key = config.OPENAI_API_KEY
    logger.info("تم تهيئة OpenAI API.")
else:
    logger.warning("لم يتم العثور على مفتاح OpenAI API في الإعدادات.")

if config.GEMINI_API_KEY:
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        logger.info("تم تهيئة Google Generative AI API.")
    except Exception as e:
        logger.error(f"خطأ في تهيئة Google Generative AI API: {e}")
else:
    logger.warning("لم يتم العثور على مفتاح Gemini API في الإعدادات.")

# --- معالجات الأوامر الأساسية --- #

@dp.message(CommandStart())
async def handle_start(message: Message):
    """معالج الأمر /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # إضافة المستخدم أو تحديث بياناته في قاعدة البيانات
    db.add_or_update_user(user_id, username, first_name, last_name)
    
    await message.answer(config.START_MESSAGE)

@dp.message(Command("help"))
async def handle_help(message: Message):
    """معالج الأمر /help"""
    user_id = message.from_user.id
    # التأكد من وجود المستخدم في قاعدة البيانات
    if not db.get_user(user_id):
        db.add_or_update_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        
    await message.answer(config.HELP_MESSAGE, disable_web_page_preview=True)

@dp.message(Command("account"))
async def handle_account(message: Message):
    """معالج الأمر /account"""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        # إضافة المستخدم إذا لم يكن موجودًا (احتياطي)
        db.add_or_update_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        user_data = db.get_user(user_id)
        if not user_data:
            await message.answer("حدث خطأ أثناء جلب بيانات حسابك. يرجى المحاولة مرة أخرى.")
            return

    subscription_type = user_data["subscription_type"]
    requests_remaining = user_data["requests_remaining"]
    expiry_date_str = user_data["subscription_expiry"]
    selected_model = user_data["selected_model"]

    # تجديد الرصيد إذا لزم الأمر قبل عرضه
    db.check_and_decrement_requests(user_id) # استدعاء للتحقق من الصلاحية والتجديد إذا لزم الأمر، لا نخصم هنا
    user_data = db.get_user(user_id) # إعادة جلب البيانات بعد التحديث المحتمل
    requests_remaining = user_data["requests_remaining"]
    subscription_type = user_data["subscription_type"]
    expiry_date_str = user_data["subscription_expiry"]

    plan_details = db.get_db_connection().cursor().execute("SELECT request_limit, limit_period FROM subscriptions WHERE plan_name = ?", (subscription_type,)).fetchone()
    limit_period_ar = {"daily": "يوميًا", "weekly": "أسبوعيًا"}.get(plan_details["limit_period"], "")
    request_limit = plan_details["request_limit"]

    expiry_info = ""
    if expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d %H:%M:%S.%f')
            expiry_info = f"\nتنتهي صلاحية الخطة الحالية في: {expiry_date.strftime('%Y-%m-%d')}"
        except ValueError:
            expiry_info = f"\nتاريخ انتهاء الصلاحية: {expiry_date_str} (تنسيق غير متوقع)"

    account_info = f"""
    👤 **حسابي**

    **معرف المستخدم:** `{user_id}`
    **نوع الاشتراك:** {subscription_type.capitalize()} ({request_limit} طلب {limit_period_ar})
    **الطلبات المتبقية:** {requests_remaining}
    **النموذج المختار:** {selected_model}
    {expiry_info}
    """
    await message.answer(account_info, parse_mode="Markdown")

@dp.message(Command("deletecontext"))
async def handle_delete_context(message: Message):
    """معالج الأمر /deletecontext"""
    user_id = message.from_user.id
    db.delete_user_context(user_id)
    await message.answer("تم حذف سياق المحادثة بنجاح. يمكنك الآن بدء موضوع جديد.")

# --- معالجات أوامر المسؤولين (مثال) --- #

@dp.message(Command("addadmin"))
async def handle_add_admin(message: Message):
    user_id = message.from_user.id
    if not db.is_admin(user_id):
        await message.reply("ليس لديك الصلاحية لاستخدام هذا الأمر.")
        return

    try:
        target_user_id = int(message.text.split()[1])
        if db.add_admin(target_user_id):
            await message.reply(f"تمت إضافة المستخدم {target_user_id} كمسؤول بنجاح.")
        else:
            await message.reply(f"فشلت إضافة المستخدم {target_user_id} كمسؤول (قد يكون مسؤولاً بالفعل أو حدث خطأ).")
    except (IndexError, ValueError):
        await message.reply("الاستخدام: /addadmin <user_id>")
    except Exception as e:
        logger.error(f"خطأ عند إضافة مسؤول: {e}")
        await message.reply("حدث خطأ غير متوقع.")

@dp.message(Command("removeadmin"))
async def handle_remove_admin(message: Message):
    user_id = message.from_user.id
    if not db.is_admin(user_id):
        await message.reply("ليس لديك الصلاحية لاستخدام هذا الأمر.")
        return

    try:
        target_user_id = int(message.text.split()[1])
        if db.remove_admin(target_user_id):
            await message.reply(f"تمت إزالة المستخدم {target_user_id} من قائمة المسؤولين بنجاح.")
        else:
            await message.reply(f"فشلت إزالة المستخدم {target_user_id} من قائمة المسؤولين (قد لا يكون مسؤولاً أو لا يمكن إزالته).")
    except (IndexError, ValueError):
        await message.reply("الاستخدام: /removeadmin <user_id>")
    except Exception as e:
        logger.error(f"خطأ عند إزالة مسؤول: {e}")
        await message.reply("حدث خطأ غير متوقع.")

# --- معالج الرسائل النصية (للتفاعل مع الذكاء الاصطناعي) --- #

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_input = message.text

    # 1. التحقق من وجود المستخدم وتحديث بياناته
    user_data = db.get_user(user_id)
    if not user_data:
        db.add_or_update_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        user_data = db.get_user(user_id)
        if not user_data:
            await message.reply("حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.")
            return

    # 2. التحقق من رصيد الطلبات
    if not db.check_and_decrement_requests(user_id):
        await message.reply("لقد استهلكت رصيدك من الطلبات لهذا اليوم/الأسبوع. يرجى الترقية إلى /premium أو الانتظار حتى يتم تجديد رصيدك.")
        return

    # 3. الحصول على النموذج المختار والسياق
    selected_model_name = db.get_selected_model(user_id)
    context = db.get_user_context(user_id) or ""

    # 4. استدعاء نموذج الذكاء الاصطناعي المناسب
    response_text = "عذرًا، حدث خطأ أثناء معالجة طلبك."
    try:
        # عرض رسالة "جارٍ الكتابة..."
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # --- منطق اختيار واستدعاء النموذج --- #
        if "GPT" in selected_model_name.upper() and config.OPENAI_API_KEY:
            model_to_use = selected_model_name
            messages = []
            if context:
                messages.append({"role": "system", "content": "You are a helpful AI assistant."})
                messages.append({"role": "user", "content": context})
            messages.append({"role": "user", "content": user_input})
            
            completion = await asyncio.to_thread(
                openai.chat.completions.create,
                model=model_to_use,
                messages=messages
            )
            response_text = completion.choices[0].message.content
            new_context = f"{context}\n\nUser: {user_input}\nAI: {response_text}".strip()
            db.update_user_context(user_id, new_context)

        elif "GEMINI" in selected_model_name.upper() and config.GEMINI_API_KEY:
            model = genai.GenerativeModel(selected_model_name)
            chat_history = []
            if context:
                pass
            response = await asyncio.to_thread(model.generate_content, user_input, generation_config=genai.types.GenerationConfig(temperature=0.7))
            response_text = response.text
            new_context = f"{context}\n\nUser: {user_input}\nAI: {response_text}".strip()
            db.update_user_context(user_id, new_context)
            
        elif "CLAUDE" in selected_model_name.upper():
            response_text = "نموذج Claude غير مدمج بعد."
        elif "DEEPSEEK" in selected_model_name.upper():
            response_text = "نموذج DeepSeek غير مدمج بعد."
        elif "PERPLEXITY" in selected_model_name.upper():
            response_text = "نموذج Perplexity غير مدمج بعد (يستخدم عادةً عبر /s)."
        else:
            response_text = f"النموذج المختار '{selected_model_name}' غير مدعوم حاليًا أو لم يتم تكوينه بشكل صحيح."

    except openai.APIError as e:
        logger.error(f"OpenAI API error for user {user_id}: {e}")
        response_text = f"حدث خطأ في واجهة OpenAI: {e}"
    except Exception as e:
        logger.error(f"Error processing text message for user {user_id} with model {selected_model_name}: {e}")
        response_text = f"عذرًا، حدث خطأ غير متوقع أثناء معالجة طلبك مع نموذج {selected_model_name}."

    # 5. إرسال الرد للمستخدم
    await message.reply(response_text)

# --- دالة التشغيل الرئيسية --- #

async def main():
    # تهيئة قاعدة البيانات عند بدء التشغيل
    logger.info("جارٍ تهيئة قاعدة البيانات...")
    db.init_db()
    logger.info("تم تهيئة قاعدة البيانات.")

    # إضافة المسؤولين من ملف الإعدادات إلى قاعدة البيانات إذا لم يكونوا موجودين
    logger.info("جارٍ التحقق من المسؤولين...")
    initial_admins = [admin_id for admin_id in config.ADMIN_IDS if admin_id.isdigit()]
    for admin_id_str in initial_admins:
        try:
            admin_id = int(admin_id_str)
            if not db.is_admin(admin_id):
                db.add_admin(admin_id)
        except ValueError:
            logger.warning(f"معرف المسؤول غير صالح في ملف الإعدادات: {admin_id_str}")
        except Exception as e:
            logger.error(f"خطأ عند إضافة المسؤول الأولي {admin_id_str}: {e}")
    logger.info(f"المسؤولون الحاليون (من الإعدادات وقاعدة البيانات): {db.get_all_admins()}")

    # إضافة مفاتيح API الأولية من ملف الإعدادات إلى قاعدة البيانات
    logger.info("جارٍ إضافة/تحديث مفاتيح API الأولية...")
    if config.OPENAI_API_KEY:
        db.add_api_key("ChatGPT", config.OPENAI_API_KEY, "ChatGPT (OpenAI)")
    if config.GEMINI_API_KEY:
        db.add_api_key("Gemini", config.GEMINI_API_KEY, "Gemini (Google)")
    logger.info("تمت معالجة مفاتيح API الأولية.")

    logger.info("بدء تشغيل البوت...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
