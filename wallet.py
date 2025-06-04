#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة المحافظ
يحتوي على الوظائف الخاصة بإدارة محافظ المستخدمين والمدفوعات
"""

import logging
import uuid
import json
import requests
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from config import PLISIO_SECRET_KEY, CURRENCY_PRICES

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

async def buy_currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع شراء العملات"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # استخراج كمية العملات المطلوبة
    amount = query.data.split('_')[-1]
    
    # التحقق من صحة الكمية
    if amount not in CURRENCY_PRICES:
        await query.edit_message_text("حدث خطأ في اختيار الكمية. يرجى المحاولة مرة أخرى.")
        return
    
    # الحصول على سعر العملات بالنجوم
    stars_price = CURRENCY_PRICES[amount]
    
    # إنشاء معرف فريد للمعاملة
    transaction_id = str(uuid.uuid4())
    
    # تسجيل المعاملة في قاعدة البيانات
    db.record_payment(transaction_id, user_id, int(amount), stars_price, 'pending')
    
    # إنشاء رابط الدفع باستخدام Plisio
    payment_url = await create_payment_link(transaction_id, user_id, int(amount), stars_price)
    
    if payment_url:
        # إنشاء زر للدفع
        keyboard = [
            [InlineKeyboardButton("الدفع الآن 💳", url=payment_url)],
            [InlineKeyboardButton("تحديث الحالة 🔄", callback_data=f"check_payment_{transaction_id}")],
            [InlineKeyboardButton("إلغاء ❌", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"لشراء {amount} عملة مقابل {stars_price} نجمة تليجرام، يرجى النقر على زر الدفع أدناه.\n\n"
            "بعد إتمام الدفع، انقر على زر 'تحديث الحالة' للتحقق من حالة المعاملة.",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text("حدث خطأ أثناء إنشاء رابط الدفع. يرجى المحاولة مرة أخرى لاحقاً.")

async def create_payment_link(transaction_id, user_id, amount, stars_price):
    """إنشاء رابط دفع باستخدام Plisio"""
    try:
        # بيانات طلب إنشاء الفاتورة
        payload = {
            'api_key': PLISIO_SECRET_KEY,
            'order_number': transaction_id,
            'order_name': f"شراء {amount} عملة",
            'source_amount': stars_price,
            'source_currency': 'USDT',
            'currency': 'USDT',
            'callback_url': f"https://example.com/callback?transaction_id={transaction_id}&user_id={user_id}",
            'success_url': f"https://t.me/AIPoweredProBot?start=payment_success_{transaction_id}",
            'cancel_url': f"https://t.me/AIPoweredProBot?start=payment_cancel_{transaction_id}",
            'email': f"{user_id}@telegram.user",
            'language': 'ar'
        }
        
        # إرسال طلب إنشاء الفاتورة
        response = requests.post('https://plisio.net/api/v1/invoices/new', data=payload)
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']['invoice_url']
        else:
            logger.error(f"خطأ في إنشاء رابط الدفع: {data}")
            return None
    except Exception as e:
        logger.error(f"استثناء أثناء إنشاء رابط الدفع: {e}")
        return None

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من حالة الدفع"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # استخراج معرف المعاملة
    transaction_id = query.data.split('_')[-1]
    
    # التحقق من حالة الدفع
    payment_status = await check_payment_status(transaction_id)
    
    if payment_status == 'completed':
        # الحصول على تفاصيل المعاملة
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT amount FROM payment_transactions WHERE transaction_id = ?', (transaction_id,))
        transaction = cursor.fetchone()
        conn.close()
        
        if transaction:
            amount = transaction['amount']
            
            # تحديث حالة المعاملة
            db.update_payment_status(transaction_id, 'completed')
            
            # إضافة العملات إلى محفظة المستخدم
            db.update_wallet_balance(user_id, amount)
            
            await query.edit_message_text(
                f"تم إتمام الدفع بنجاح! تمت إضافة {amount} عملة إلى محفظتك.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
            )
        else:
            await query.edit_message_text("لم يتم العثور على تفاصيل المعاملة.")
    elif payment_status == 'pending':
        await query.edit_message_text(
            "لم يتم تأكيد الدفع بعد. يرجى المحاولة مرة أخرى بعد إتمام عملية الدفع.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("تحديث الحالة 🔄", callback_data=f"check_payment_{transaction_id}")],
                [InlineKeyboardButton("إلغاء ❌", callback_data="cancel_payment")]
            ])
        )
    else:
        await query.edit_message_text(
            "لم يتم العثور على المعاملة أو تم إلغاؤها.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="account")]])
        )

async def check_payment_status(transaction_id):
    """التحقق من حالة الدفع باستخدام Plisio API"""
    try:
        # بيانات طلب التحقق من حالة الفاتورة
        payload = {
            'api_key': PLISIO_SECRET_KEY,
            'order_number': transaction_id
        }
        
        # إرسال طلب التحقق من حالة الفاتورة
        response = requests.get('https://plisio.net/api/v1/invoices/info', params=payload)
        data = response.json()
        
        if data['status'] == 'success':
            invoice_status = data['data']['status']
            
            if invoice_status in ['completed', 'confirmed']:
                return 'completed'
            elif invoice_status in ['pending', 'new', 'partially_paid']:
                return 'pending'
            else:
                return 'failed'
        else:
            logger.error(f"خطأ في التحقق من حالة الدفع: {data}")
            return 'error'
    except Exception as e:
        logger.error(f"استثناء أثناء التحقق من حالة الدفع: {e}")
        return 'error'

async def cancel_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء عملية الدفع"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "تم إلغاء عملية الدفع.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="account")]])
    )

async def buy_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع شراء الاشتراكات والحزم"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # استخراج نوع الاشتراك أو الحزمة
    subscription_type = query.data.split('_')[1]
    
    # الحصول على بيانات المحفظة
    wallet = db.get_wallet(user_id)
    
    if not wallet:
        await query.edit_message_text(
            "لم يتم العثور على محفظتك. يرجى المحاولة مرة أخرى.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]])
        )
        return
    
    # تحديد السعر والإجراء المناسب حسب نوع الاشتراك أو الحزمة
    if subscription_type == 'premium':
        # الاشتراك المميز الشهري
        price = 170
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذا الاشتراك. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث اشتراك المستخدم
        db.update_subscription(user_id, 'premium', 30)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'image', 10)
        
        await query.edit_message_text(
            "تم شراء الاشتراك المميز بنجاح! يمكنك الآن الاستمتاع بجميع المزايا المتاحة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type == 'premium_x2':
        # الاشتراك المميز X2 الشهري
        price = 320
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذا الاشتراك. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث اشتراك المستخدم
        db.update_subscription(user_id, 'premium_x2', 30)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'image', 20)
        
        await query.edit_message_text(
            "تم شراء الاشتراك المميز X2 بنجاح! يمكنك الآن الاستمتاع بجميع المزايا المتاحة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type == 'combo':
        # حزمة كومبو
        price = 580
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذا الاشتراك. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث اشتراك المستخدم
        db.update_subscription(user_id, 'combo', 30)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'chatgpt', 100)
        db.update_request_balance(user_id, 'image', 100)
        
        await query.edit_message_text(
            "تم شراء حزمة كومبو بنجاح! يمكنك الآن الاستمتاع بجميع المزايا المتاحة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type.startswith('chatgpt_'):
        # حزم ChatGPT
        package_size = subscription_type.split('_')[1]
        
        # تحديد السعر وعدد الطلبات
        if package_size == '50':
            price = 175
            requests = 50
        elif package_size == '100':
            price = 320
            requests = 100
        elif package_size == '200':
            price = 620
            requests = 200
        elif package_size == '500':
            price = 1550
            requests = 500
        else:
            await query.edit_message_text(
                "حدث خطأ في اختيار الحزمة. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="chatgpt_packages")]])
            )
            return
        
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذه الحزمة. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="chatgpt_packages")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'chatgpt', requests)
        
        await query.edit_message_text(
            f"تم شراء حزمة ChatGPT بنجاح! تمت إضافة {requests} طلب إلى رصيدك.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type.startswith('claude_'):
        # حزم Claude
        package_size = subscription_type.split('_')[1]
        
        # تحديد السعر وعدد الطلبات
        if package_size == '100':
            price = 175
            requests = 100
        elif package_size == '200':
            price = 320
            requests = 200
        elif package_size == '500':
            price = 720
            requests = 500
        elif package_size == '1000':
            price = 1200
            requests = 1000
        else:
            await query.edit_message_text(
                "حدث خطأ في اختيار الحزمة. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="claude_packages")]])
            )
            return
        
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذه الحزمة. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="claude_packages")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'claude', requests)
        
        await query.edit_message_text(
            f"تم شراء حزمة Claude بنجاح! تمت إضافة {requests} طلب إلى رصيدك.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type.startswith('image_'):
        # حزم الصور
        package_size = subscription_type.split('_')[1]
        
        # تحديد السعر وعدد الطلبات
        if package_size == '50':
            price = 175
            requests = 50
        elif package_size == '100':
            price = 320
            requests = 100
        elif package_size == '200':
            price = 620
            requests = 200
        elif package_size == '500':
            price = 1400
            requests = 500
        else:
            await query.edit_message_text(
                "حدث خطأ في اختيار الحزمة. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="image_packages")]])
            )
            return
        
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذه الحزمة. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="image_packages")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'image', requests)
        
        await query.edit_message_text(
            f"تم شراء حزمة الصور بنجاح! تمت إضافة {requests} طلب إلى رصيدك.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type.startswith('video_'):
        # حزم الفيديو
        package_size = subscription_type.split('_')[1]
        
        # تحديد السعر وعدد الطلبات
        if package_size == '10':
            price = 375
            requests = 10
        elif package_size == '20':
            price = 730
            requests = 20
        elif package_size == '50':
            price = 1750
            requests = 50
        else:
            await query.edit_message_text(
                "حدث خطأ في اختيار الحزمة. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="video_packages")]])
            )
            return
        
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذه الحزمة. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="video_packages")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'video', requests)
        
        await query.edit_message_text(
            f"تم شراء حزمة الفيديو بنجاح! تمت إضافة {requests} طلب إلى رصيدك.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    elif subscription_type.startswith('suno_'):
        # حزم Suno
        package_size = subscription_type.split('_')[1]
        
        # تحديد السعر وعدد الطلبات
        if package_size == '20':
            price = 175
            requests = 20
        elif package_size == '50':
            price = 425
            requests = 50
        elif package_size == '100':
            price = 780
            requests = 100
        else:
            await query.edit_message_text(
                "حدث خطأ في اختيار الحزمة. يرجى المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="suno_packages")]])
            )
            return
        
        if wallet['balance'] < price:
            await query.edit_message_text(
                f"رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذه الحزمة. رصيدك الحالي: {wallet['balance']} عملة.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("شراء عملات 💰", callback_data="account")],
                    [InlineKeyboardButton("العودة 🔙", callback_data="suno_packages")]
                ])
            )
            return
        
        # خصم المبلغ من المحفظة
        db.update_wallet_balance(user_id, -price)
        
        # تحديث أرصدة الطلبات
        db.update_request_balance(user_id, 'suno', requests)
        
        await query.edit_message_text(
            f"تم شراء حزمة Suno بنجاح! تمت إضافة {requests} طلب إلى رصيدك.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عرض حسابي 👤", callback_data="account")]])
        )
    
    else:
        await query.edit_message_text(
            "حدث خطأ في اختيار الاشتراك أو الحزمة. يرجى المحاولة مرة أخرى.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة 🔙", callback_data="subscription_paid")]])
        )

# تسجيل معالجات الاستجابة للأزرار
def register_wallet_handlers(application):
    """تسجيل معالجات أزرار المحفظة والمدفوعات"""
    application.add_handler(CallbackQueryHandler(buy_currency_callback, pattern="^buy_currency_"))
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"))
    application.add_handler(CallbackQueryHandler(cancel_payment_callback, pattern="^cancel_payment$"))
    
    # معالجات شراء الاشتراكات والحزم
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_premium_monthly$"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_premium_x2_monthly$"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_combo$"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_chatgpt_"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_claude_"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_image_"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_video_"))
    application.add_handler(CallbackQueryHandler(buy_subscription_callback, pattern="^buy_suno_"))
