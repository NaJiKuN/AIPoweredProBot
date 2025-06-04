#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف الاختبار
يحتوي على وظائف اختبار مختلف أجزاء البوت
"""

import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import sqlite3
import json
from datetime import datetime, timedelta

# إضافة المسار الحالي إلى مسارات البحث
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد الوحدات المراد اختبارها
from database import Database
from config import (
    TOKEN, ADMIN_ID, PLISIO_SECRET_KEY, DATABASE_PATH,
    PREMIUM_SUBSCRIPTION, PREMIUM_X2_SUBSCRIPTION, CHATGPT_PACKAGES,
    CLAUDE_PACKAGES, IMAGE_PACKAGES, VIDEO_PACKAGES, SUNO_PACKAGES, COMBO_PACKAGE
)
from languages import get_text, load_translations, TRANSLATIONS, SUPPORTED_LANGUAGES

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TestDatabase(unittest.TestCase):
    """اختبارات قاعدة البيانات"""
    
    def setUp(self):
        """إعداد بيئة الاختبار"""
        # استخدام قاعدة بيانات مؤقتة للاختبار
        self.test_db_path = ":memory:"
        self.db = Database(self.test_db_path)
        
        # إنشاء جداول قاعدة البيانات
        self.db.create_tables()
    
    def test_add_user(self):
        """اختبار إضافة مستخدم جديد"""
        user_id = "123456789"
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        language_code = "ar"
        
        # إضافة مستخدم جديد
        self.db.add_user(user_id, username, first_name, last_name, language_code)
        
        # التحقق من إضافة المستخدم
        user = self.db.get_user(user_id)
        
        self.assertIsNotNone(user)
        self.assertEqual(user["user_id"], user_id)
        self.assertEqual(user["username"], username)
        self.assertEqual(user["first_name"], first_name)
        self.assertEqual(user["last_name"], last_name)
        self.assertEqual(user["language_code"], language_code)
    
    def test_update_user_language(self):
        """اختبار تحديث لغة المستخدم"""
        user_id = "123456789"
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        language_code = "ar"
        
        # إضافة مستخدم جديد
        self.db.add_user(user_id, username, first_name, last_name, language_code)
        
        # تحديث لغة المستخدم
        new_language_code = "en"
        self.db.update_user_language(user_id, new_language_code)
        
        # التحقق من تحديث اللغة
        user = self.db.get_user(user_id)
        
        self.assertEqual(user["language_code"], new_language_code)
    
    def test_add_wallet(self):
        """اختبار إضافة محفظة للمستخدم"""
        user_id = "123456789"
        
        # إضافة محفظة
        self.db.add_wallet(user_id)
        
        # التحقق من إضافة المحفظة
        wallet = self.db.get_wallet(user_id)
        
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet["user_id"], user_id)
        self.assertEqual(wallet["balance"], 0)
    
    def test_update_wallet_balance(self):
        """اختبار تحديث رصيد المحفظة"""
        user_id = "123456789"
        
        # إضافة محفظة
        self.db.add_wallet(user_id)
        
        # تحديث رصيد المحفظة
        amount = 100
        self.db.update_wallet_balance(user_id, amount)
        
        # التحقق من تحديث الرصيد
        wallet = self.db.get_wallet(user_id)
        
        self.assertEqual(wallet["balance"], amount)
        
        # تحديث الرصيد مرة أخرى
        amount2 = 50
        self.db.update_wallet_balance(user_id, amount2)
        
        # التحقق من تحديث الرصيد
        wallet = self.db.get_wallet(user_id)
        
        self.assertEqual(wallet["balance"], amount + amount2)
    
    def test_add_api_key(self):
        """اختبار إضافة مفتاح API"""
        model_name = "GPT-4"
        api_key = "test_api_key"
        added_by = "admin"
        
        # إضافة مفتاح API
        self.db.add_api_key(model_name, api_key, added_by)
        
        # الحصول على جميع مفاتيح API
        api_keys = self.db.get_all_api_keys()
        
        self.assertIn(model_name, api_keys)
        self.assertEqual(api_keys[model_name], api_key)
    
    def test_remove_api_key(self):
        """اختبار إزالة مفتاح API"""
        model_name = "GPT-4"
        api_key = "test_api_key"
        added_by = "admin"
        
        # إضافة مفتاح API
        self.db.add_api_key(model_name, api_key, added_by)
        
        # إزالة مفتاح API
        self.db.remove_api_key(model_name)
        
        # الحصول على جميع مفاتيح API
        api_keys = self.db.get_all_api_keys()
        
        self.assertNotIn(model_name, api_keys)
    
    def test_update_subscription(self):
        """اختبار تحديث اشتراك المستخدم"""
        user_id = "123456789"
        subscription_type = "premium"
        duration_days = 30
        
        # تحديث اشتراك المستخدم
        self.db.update_subscription(user_id, subscription_type, duration_days)
        
        # الحصول على اشتراك المستخدم
        subscription = self.db.get_subscription(user_id)
        
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription["user_id"], user_id)
        self.assertEqual(subscription["subscription_type"], subscription_type)
        
        # التحقق من تاريخ انتهاء الاشتراك
        end_date = datetime.strptime(subscription["end_date"], '%Y-%m-%d %H:%M:%S')
        expected_end_date = datetime.now() + timedelta(days=duration_days)
        
        # التحقق من أن الفرق بين التاريخين أقل من دقيقة واحدة
        self.assertLess((expected_end_date - end_date).total_seconds(), 60)
    
    def test_update_request_balance(self):
        """اختبار تحديث رصيد الطلبات"""
        user_id = "123456789"
        request_type = "chatgpt"
        requests = 100
        
        # تحديث رصيد الطلبات
        self.db.update_request_balance(user_id, request_type, requests)
        
        # الحصول على رصيد الطلبات
        request_balance = self.db.get_request_balance(user_id)
        
        self.assertIsNotNone(request_balance)
        self.assertEqual(request_balance["user_id"], user_id)
        self.assertEqual(request_balance["chatgpt_requests"], requests)
    
    def test_use_request(self):
        """اختبار استخدام طلب"""
        user_id = "123456789"
        request_type = "chatgpt"
        requests = 100
        
        # تحديث رصيد الطلبات
        self.db.update_request_balance(user_id, request_type, requests)
        
        # استخدام طلب
        self.db.use_request(user_id, request_type)
        
        # الحصول على رصيد الطلبات
        request_balance = self.db.get_request_balance(user_id)
        
        self.assertEqual(request_balance["chatgpt_requests_used"], 1)
    
    def test_add_admin(self):
        """اختبار إضافة مسؤول"""
        admin_id = "987654321"
        added_by = ADMIN_ID
        
        # إضافة مسؤول
        self.db.add_admin(admin_id, added_by)
        
        # التحقق من إضافة المسؤول
        is_admin = self.db.is_admin(admin_id)
        
        self.assertTrue(is_admin)
    
    def test_remove_admin(self):
        """اختبار إزالة مسؤول"""
        admin_id = "987654321"
        added_by = ADMIN_ID
        
        # إضافة مسؤول
        self.db.add_admin(admin_id, added_by)
        
        # إزالة المسؤول
        self.db.remove_admin(admin_id)
        
        # التحقق من إزالة المسؤول
        is_admin = self.db.is_admin(admin_id)
        
        self.assertFalse(is_admin)
    
    def test_update_user_model_preference(self):
        """اختبار تحديث النموذج المفضل للمستخدم"""
        user_id = "123456789"
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        language_code = "ar"
        
        # إضافة مستخدم جديد
        self.db.add_user(user_id, username, first_name, last_name, language_code)
        
        # تحديث النموذج المفضل
        model = "GPT-4"
        self.db.update_user_model_preference(user_id, model)
        
        # التحقق من تحديث النموذج المفضل
        user = self.db.get_user(user_id)
        
        self.assertEqual(user["preferred_model"], model)
    
    def test_update_user_instructions(self):
        """اختبار تحديث التعليمات المخصصة للمستخدم"""
        user_id = "123456789"
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        language_code = "ar"
        
        # إضافة مستخدم جديد
        self.db.add_user(user_id, username, first_name, last_name, language_code)
        
        # تحديث التعليمات المخصصة
        instructions = "تعليمات اختبار"
        enabled = 1
        self.db.update_user_instructions(user_id, instructions, enabled)
        
        # التحقق من تحديث التعليمات المخصصة
        user = self.db.get_user(user_id)
        
        self.assertEqual(user["custom_instructions"], instructions)
        self.assertEqual(user["instructions_enabled"], enabled)
    
    def test_update_context_setting(self):
        """اختبار تحديث إعداد حفظ السياق"""
        user_id = "123456789"
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        language_code = "ar"
        
        # إضافة مستخدم جديد
        self.db.add_user(user_id, username, first_name, last_name, language_code)
        
        # تحديث إعداد حفظ السياق
        enabled = 0
        self.db.update_context_setting(user_id, enabled)
        
        # التحقق من تحديث إعداد حفظ السياق
        user = self.db.get_user(user_id)
        
        self.assertEqual(user["context_enabled"], enabled)
    
    def test_update_user_voice_settings(self):
        """اختبار تحديث إعدادات الصوت للمستخدم"""
        user_id = "123456789"
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        language_code = "ar"
        
        # إضافة مستخدم جديد
        self.db.add_user(user_id, username, first_name, last_name, language_code)
        
        # تحديث إعدادات الصوت
        enabled = 1
        voice = "nova"
        self.db.update_user_voice_settings(user_id, enabled, voice)
        
        # التحقق من تحديث إعدادات الصوت
        user = self.db.get_user(user_id)
        
        self.assertEqual(user["voice_enabled"], enabled)
        self.assertEqual(user["preferred_voice"], voice)

class TestLanguages(unittest.TestCase):
    """اختبارات نظام اللغات"""
    
    def test_get_text(self):
        """اختبار الحصول على النص المترجم"""
        # اختبار النص العربي
        ar_text = get_text("welcome", "ar")
        self.assertIsNotNone(ar_text)
        self.assertIn("مرحبًا", ar_text)
        
        # اختبار النص الإنجليزي
        en_text = get_text("welcome", "en")
        self.assertIsNotNone(en_text)
        self.assertIn("Hello", en_text)
        
        # اختبار النص مع معلمات
        balance_text = get_text("insufficient_balance", "ar", price=100, item="اشتراك", balance=50)
        self.assertIn("100", balance_text)
        self.assertIn("اشتراك", balance_text)
        self.assertIn("50", balance_text)
    
    def test_fallback_language(self):
        """اختبار اللغة الاحتياطية"""
        # اختبار لغة غير مدعومة
        text = get_text("welcome", "fr")
        self.assertIsNotNone(text)
        self.assertIn("مرحبًا", text)  # يجب أن يعود إلى العربية
        
        # اختبار مفتاح غير موجود
        text = get_text("non_existent_key", "ar")
        self.assertEqual(text, "non_existent_key")  # يجب أن يعود المفتاح نفسه

def run_tests():
    """تشغيل الاختبارات"""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    run_tests()
