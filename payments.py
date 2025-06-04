#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة المدفوعات
يحتوي على الوظائف الخاصة بإدارة المدفوعات وربط بوابة الدفع
"""

import logging
import json
import uuid
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import PLISIO_SECRET_KEY
from database import Database
from languages import get_text

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

# تعريف أسعار العملات
CURRENCY_PRICES = {
    "100": 10,   # 100 عملة مقابل 10 نجوم
    "250": 20,   # 250 عملة مقابل 20 نجوم
    "500": 35,   # 500 عملة مقابل 35 نجوم
    "1000": 60,  # 1000 عملة مقابل 60 نجوم
    "2000": 100  # 2000 عملة مقابل 100 نجوم
}

async def buy_currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع شراء العملات"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # استخراج كمية العملات المطلوبة
    amount = query.data.split('_')[-1]
    
    if amount not in CURRENCY_PRICES:
        await query.edit_message_text(get_text("error_occurred", lang_code))
        return
    
    stars_price = CURRENCY_PRICES[amount]
    
    # إنشاء معرف فريد للمعاملة
    transaction_id = str(uuid.uuid4())
    
    # حفظ معلومات المعاملة في قاعدة البيانات
    db.add_transaction(user_id, transaction_id, amount, stars_price)
    
    # إنشاء رابط الدفع
    payment_url = create_payment_url(transaction_id, stars_price, user_id)
    
    # إنشاء نص الدفع
    payment_text = get_text("payment_prompt", lang_code, amount=amount, stars=stars_price)
    
    # إنشاء أزرار الدفع
    keyboard = [
        [InlineKeyboardButton(get_text("pay_now_button", lang_code), url=payment_url)],
        [InlineKeyboardButton(get_text("update_status_button", lang_code), callback_data=f"check_payment_{transaction_id}")],
        [InlineKeyboardButton(get_text("cancel_button", lang_code), callback_data="cancel_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(payment_text, reply_markup=reply_markup)

def create_payment_url(transaction_id, stars_price, user_id):
    """إنشاء رابط الدفع باستخدام Plisio"""
    # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Plisio
    # لإنشاء رابط دفع حقيقي
    
    # في هذا المثال، نفترض أن سعر النجمة الواحدة هو 0.1 دولار
    amount_usd = stars_price * 0.1
    
    # بناء رابط الدفع
    payment_url = f"https://plisio.net/pay?amount={amount_usd}&currency=USD&order_id={transaction_id}&user_id={user_id}&secret_key={PLISIO_SECRET_KEY}"
    
    return payment_url

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من حالة الدفع"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    # استخراج معرف المعاملة
    transaction_id = query.data.split('_')[-1]
    
    # الحصول على معلومات المعاملة من قاعدة البيانات
    transaction = db.get_transaction(transaction_id)
    
    if not transaction:
        await query.edit_message_text(get_text("error_occurred", lang_code))
        return
    
    # التحقق من حالة الدفع
    payment_status = check_payment_status(transaction_id)
    
    if payment_status == "completed":
        # تحديث حالة المعاملة في قاعدة البيانات
        db.update_transaction_status(transaction_id, "completed")
        
        # إضافة العملات إلى محفظة المستخدم
        amount = int(transaction["amount"])
        db.update_wallet_balance(user_id, amount)
        
        # إرسال رسالة نجاح الدفع
        await query.edit_message_text(
            get_text("payment_success_message", lang_code, amount=amount),
            reply_markup=None
        )
    elif payment_status == "pending":
        await query.edit_message_text(
            get_text("payment_pending_message", lang_code),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text("update_status_button", lang_code), callback_data=f"check_payment_{transaction_id}")],
                [InlineKeyboardButton(get_text("cancel_button", lang_code), callback_data="cancel_payment")]
            ])
        )
    else:
        await query.edit_message_text(
            get_text("payment_failed_message", lang_code),
            reply_markup=None
        )

def check_payment_status(transaction_id):
    """التحقق من حالة الدفع باستخدام Plisio API"""
    # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Plisio
    # للتحقق من حالة الدفع الحقيقية
    
    # في هذا المثال، نفترض أن جميع المعاملات مكتملة للاختبار
    return "completed"
    
    # في التطبيق الفعلي، يجب استخدام شيء مثل:
    """
    try:
        response = requests.get(
            f"https://plisio.net/api/v1/operations/{transaction_id}",
            params={"secret_key": PLISIO_SECRET_KEY}
        )
        data = response.json()
        
        if data["status"] == "success":
            return data["data"]["status"]
        else:
            return "failed"
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        return "failed"
    """

async def cancel_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء عملية الدفع"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = db.get_user(user_id)
    lang_code = user['language_code'] if user else 'ar'
    
    await query.edit_message_text(get_text("payment_cancelled_message", lang_code))

# تسجيل معالجات المدفوعات
def register_payment_handlers(application):
    """تسجيل معالجات المدفوعات"""
    application.add_handler(CallbackQueryHandler(buy_currency_callback, pattern="^buy_currency_"))
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"))
    application.add_handler(CallbackQueryHandler(cancel_payment_callback, pattern="^cancel_payment$"))
