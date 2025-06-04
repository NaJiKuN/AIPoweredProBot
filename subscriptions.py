#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة الاشتراكات
يحتوي على الوظائف الخاصة بإدارة الاشتراكات والعروض
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from config import (
    PREMIUM_SUBSCRIPTION, PREMIUM_X2_SUBSCRIPTION, CHATGPT_PACKAGES,
    CLAUDE_PACKAGES, IMAGE_PACKAGES, VIDEO_PACKAGES, SUNO_PACKAGES, COMBO_PACKAGE
)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

async def check_subscription_status(user_id):
    """التحقق من حالة اشتراك المستخدم وتحديثها إذا لزم الأمر"""
    # الحصول على بيانات الاشتراك
    subscription = db.get_subscription(user_id)
    
    if not subscription:
        return None
    
    # التحقق من انتهاء الاشتراك
    end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d %H:%M:%S')
    
    if datetime.now() > end_date:
        # إعادة تعيين الاشتراك إلى مجاني
        db.update_subscription(user_id, 'free', 7)
        return 'free'
    
    return subscription['subscription_type']

async def check_weekly_reset(user_id):
    """التحقق من إعادة تعيين الطلبات الأسبوعية"""
    # الحصول على بيانات أرصدة الطلبات
    request_balance = db.get_request_balance(user_id)
    
    if not request_balance:
        return
    
    # التحقق من موعد إعادة التعيين
    reset_date = datetime.strptime(request_balance['weekly_reset_date'], '%Y-%m-%d %H:%M:%S')
    
    if datetime.now() > reset_date:
        # إعادة تعيين الطلبات الأسبوعية
        new_reset_date = datetime.now() + timedelta(days=7)
        
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE request_balances SET weekly_requests_used = 0, weekly_reset_date = ? WHERE user_id = ?',
            (new_reset_date.strftime('%Y-%m-%d %H:%M:%S'), user_id)
        )
        conn.commit()
        conn.close()

async def get_subscription_info(user_id):
    """الحصول على معلومات اشتراك المستخدم"""
    # التحقق من حالة الاشتراك
    subscription_type = await check_subscription_status(user_id)
    
    # التحقق من إعادة تعيين الطلبات الأسبوعية
    await check_weekly_reset(user_id)
    
    # الحصول على بيانات المستخدم والمحفظة وأرصدة الطلبات
    user = db.get_user(user_id)
    wallet = db.get_wallet(user_id)
    request_balance = db.get_request_balance(user_id)
    
    # إنشاء نص معلومات الاشتراك
    subscription_info = {
        'type': subscription_type,
        'balance': wallet['balance'] if wallet else 0,
        'weekly_requests': request_balance['weekly_requests'] if request_balance else 0,
        'weekly_requests_used': request_balance['weekly_requests_used'] if request_balance else 0,
        'chatgpt_requests': request_balance['chatgpt_requests'] if request_balance else 0,
        'chatgpt_requests_used': request_balance['chatgpt_requests_used'] if request_balance else 0,
        'claude_requests': request_balance['claude_requests'] if request_balance else 0,
        'claude_requests_used': request_balance['claude_requests_used'] if request_balance else 0,
        'image_requests': request_balance['image_requests'] if request_balance else 0,
        'image_requests_used': request_balance['image_requests_used'] if request_balance else 0,
        'video_requests': request_balance['video_requests'] if request_balance else 0,
        'video_requests_used': request_balance['video_requests_used'] if request_balance else 0,
        'suno_requests': request_balance['suno_requests'] if request_balance else 0,
        'suno_requests_used': request_balance['suno_requests_used'] if request_balance else 0,
        'preferred_model': user['preferred_model'] if user else 'GPT-4.1 mini'
    }
    
    return subscription_info

async def process_subscription_purchase(user_id, subscription_type, price, duration_days=30):
    """معالجة شراء الاشتراك"""
    # الحصول على بيانات المحفظة
    wallet = db.get_wallet(user_id)
    
    if not wallet or wallet['balance'] < price:
        return False, "رصيدك غير كافٍ لشراء هذا الاشتراك."
    
    # خصم المبلغ من المحفظة
    db.update_wallet_balance(user_id, -price)
    
    # تحديث اشتراك المستخدم
    db.update_subscription(user_id, subscription_type, duration_days)
    
    return True, "تم شراء الاشتراك بنجاح!"

async def process_package_purchase(user_id, package_type, package_size):
    """معالجة شراء حزمة"""
    # تحديد نوع الحزمة والسعر وعدد الطلبات
    if package_type == 'chatgpt':
        packages = CHATGPT_PACKAGES
    elif package_type == 'claude':
        packages = CLAUDE_PACKAGES
    elif package_type == 'image':
        packages = IMAGE_PACKAGES
    elif package_type == 'video':
        packages = VIDEO_PACKAGES
    elif package_type == 'suno':
        packages = SUNO_PACKAGES
    else:
        return False, "نوع الحزمة غير صالح."
    
    # التحقق من وجود الحزمة
    if package_size not in packages:
        return False, "حجم الحزمة غير صالح."
    
    price = packages[package_size]['price']
    requests = packages[package_size]['requests']
    
    # الحصول على بيانات المحفظة
    wallet = db.get_wallet(user_id)
    
    if not wallet or wallet['balance'] < price:
        return False, "رصيدك غير كافٍ لشراء هذه الحزمة."
    
    # خصم المبلغ من المحفظة
    db.update_wallet_balance(user_id, -price)
    
    # تحديث أرصدة الطلبات
    db.update_request_balance(user_id, package_type, requests)
    
    return True, f"تم شراء الحزمة بنجاح! تمت إضافة {requests} طلب إلى رصيدك."

async def check_request_availability(user_id, request_type):
    """التحقق من توفر رصيد للطلب"""
    # التحقق من حالة الاشتراك
    subscription_type = await check_subscription_status(user_id)
    
    # التحقق من إعادة تعيين الطلبات الأسبوعية
    await check_weekly_reset(user_id)
    
    # الحصول على بيانات أرصدة الطلبات
    request_balance = db.get_request_balance(user_id)
    
    if not request_balance:
        return False
    
    # التحقق من توفر رصيد للطلب
    if request_type == 'weekly':
        return request_balance['weekly_requests'] > request_balance['weekly_requests_used']
    elif request_type == 'chatgpt':
        return request_balance['chatgpt_requests'] > request_balance['chatgpt_requests_used']
    elif request_type == 'claude':
        return request_balance['claude_requests'] > request_balance['claude_requests_used']
    elif request_type == 'image':
        return request_balance['image_requests'] > request_balance['image_requests_used']
    elif request_type == 'video':
        return request_balance['video_requests'] > request_balance['video_requests_used']
    elif request_type == 'suno':
        return request_balance['suno_requests'] > request_balance['suno_requests_used']
    
    return False

async def use_request(user_id, request_type):
    """استخدام طلب من رصيد المستخدم"""
    # التحقق من توفر رصيد للطلب
    if not await check_request_availability(user_id, request_type):
        return False
    
    # استخدام الطلب
    db.use_request(user_id, request_type)
    return True

# تسجيل معالجات الاشتراكات
def register_subscription_handlers(application):
    """تسجيل معالجات الاشتراكات"""
    # لا يوجد معالجات خاصة هنا، حيث تم تسجيلها في ملفات أخرى
    pass
