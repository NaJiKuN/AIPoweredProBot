#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة قاعدة البيانات
يحتوي على الوظائف الخاصة بإنشاء وإدارة قاعدة البيانات
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from config import DATABASE_FILE, FREE_SUBSCRIPTION

class Database:
    def __init__(self, db_file=DATABASE_FILE):
        """تهيئة قاعدة البيانات"""
        self.db_file = db_file
        self.conn = None
        self.create_tables()
    
    def connect(self):
        """الاتصال بقاعدة البيانات"""
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def create_tables(self):
        """إنشاء جداول قاعدة البيانات إذا لم تكن موجودة"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT DEFAULT 'ar',
            join_date TEXT,
            last_activity TEXT,
            preferred_model TEXT DEFAULT 'GPT-4.1 mini',
            context_enabled INTEGER DEFAULT 1,
            custom_instructions TEXT,
            instructions_enabled INTEGER DEFAULT 0,
            voice_enabled INTEGER DEFAULT 0,
            preferred_voice TEXT DEFAULT 'nova'
        )
        ''')
        
        # جدول المسؤولين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id TEXT PRIMARY KEY,
            added_by TEXT,
            added_date TEXT
        )
        ''')
        
        # جدول المحافظ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            user_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # جدول الاشتراكات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id TEXT PRIMARY KEY,
            subscription_type TEXT DEFAULT 'free',
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # جدول أرصدة الطلبات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_balances (
            user_id TEXT PRIMARY KEY,
            weekly_requests INTEGER DEFAULT 50,
            weekly_requests_used INTEGER DEFAULT 0,
            weekly_reset_date TEXT,
            chatgpt_requests INTEGER DEFAULT 0,
            chatgpt_requests_used INTEGER DEFAULT 0,
            claude_requests INTEGER DEFAULT 0,
            claude_requests_used INTEGER DEFAULT 0,
            image_requests INTEGER DEFAULT 0,
            image_requests_used INTEGER DEFAULT 0,
            video_requests INTEGER DEFAULT 0,
            video_requests_used INTEGER DEFAULT 0,
            suno_requests INTEGER DEFAULT 0,
            suno_requests_used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # جدول مفاتيح API
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            model_name TEXT PRIMARY KEY,
            api_key TEXT,
            is_active INTEGER DEFAULT 1,
            added_by TEXT,
            added_date TEXT
        )
        ''')
        
        # جدول سياق المحادثات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_contexts (
            user_id TEXT,
            model TEXT,
            context TEXT,
            last_updated TEXT,
            PRIMARY KEY (user_id, model),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # جدول معاملات الدفع
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id TEXT,
            amount INTEGER,
            currency_amount INTEGER,
            status TEXT,
            transaction_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, first_name, last_name, language_code='ar'):
        """إضافة مستخدم جديد"""
        conn = self.connect()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # التحقق من وجود المستخدم
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            # إضافة مستخدم جديد
            cursor.execute(
                'INSERT INTO users (user_id, username, first_name, last_name, language_code, join_date, last_activity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, username, first_name, last_name, language_code, now, now)
            )
            
            # إنشاء محفظة للمستخدم
            cursor.execute('INSERT INTO wallets (user_id) VALUES (?)', (user_id,))
            
            # إنشاء اشتراك مجاني للمستخدم
            start_date = datetime.now()
            end_date = start_date + timedelta(days=FREE_SUBSCRIPTION['duration_days'])
            
            cursor.execute(
                'INSERT INTO subscriptions (user_id, subscription_type, start_date, end_date) VALUES (?, ?, ?, ?)',
                (user_id, 'free', start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            # إنشاء رصيد طلبات للمستخدم
            weekly_reset_date = start_date + timedelta(days=7)
            cursor.execute(
                'INSERT INTO request_balances (user_id, weekly_requests, weekly_reset_date) VALUES (?, ?, ?)',
                (user_id, FREE_SUBSCRIPTION['text_requests'], weekly_reset_date.strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            conn.commit()
            conn.close()
            return True
        else:
            # تحديث آخر نشاط للمستخدم
            cursor.execute('UPDATE users SET last_activity = ? WHERE user_id = ?', (now, user_id))
            conn.commit()
            conn.close()
            return False
    
    def update_user_language(self, user_id, language_code):
        """تحديث لغة المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language_code = ? WHERE user_id = ?', (language_code, user_id))
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        """الحصول على بيانات المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def is_admin(self, user_id):
        """التحقق مما إذا كان المستخدم مسؤولاً"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
        admin = cursor.fetchone()
        conn.close()
        return bool(admin)
    
    def add_admin(self, user_id, added_by):
        """إضافة مسؤول جديد"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT OR REPLACE INTO admins (user_id, added_by, added_date) VALUES (?, ?, ?)',
                      (user_id, added_by, now))
        conn.commit()
        conn.close()
    
    def remove_admin(self, user_id):
        """إزالة مسؤول"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def get_all_admins(self):
        """الحصول على قائمة المسؤولين"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM admins')
        admins = cursor.fetchall()
        conn.close()
        return [admin['user_id'] for admin in admins]
    
    def get_wallet(self, user_id):
        """الحصول على بيانات محفظة المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM wallets WHERE user_id = ?', (user_id,))
        wallet = cursor.fetchone()
        conn.close()
        return dict(wallet) if wallet else None
    
    def update_wallet_balance(self, user_id, amount):
        """تحديث رصيد محفظة المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        if amount < 0:  # إذا كان المبلغ سالباً (عملية شراء)
            cursor.execute('UPDATE wallets SET total_spent = total_spent + ? WHERE user_id = ?', (abs(amount), user_id))
        conn.commit()
        conn.close()
    
    def get_subscription(self, user_id):
        """الحصول على بيانات اشتراك المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
        subscription = cursor.fetchone()
        conn.close()
        return dict(subscription) if subscription else None
    
    def update_subscription(self, user_id, subscription_type, duration_days):
        """تحديث اشتراك المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        cursor.execute(
            'UPDATE subscriptions SET subscription_type = ?, start_date = ?, end_date = ? WHERE user_id = ?',
            (subscription_type, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S'), user_id)
        )
        conn.commit()
        conn.close()
    
    def get_request_balance(self, user_id):
        """الحصول على أرصدة طلبات المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM request_balances WHERE user_id = ?', (user_id,))
        balance = cursor.fetchone()
        conn.close()
        return dict(balance) if balance else None
    
    def update_request_balance(self, user_id, balance_type, amount):
        """تحديث رصيد طلبات المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if balance_type == 'weekly':
            cursor.execute('UPDATE request_balances SET weekly_requests = weekly_requests + ? WHERE user_id = ?', (amount, user_id))
        elif balance_type == 'chatgpt':
            cursor.execute('UPDATE request_balances SET chatgpt_requests = chatgpt_requests + ? WHERE user_id = ?', (amount, user_id))
        elif balance_type == 'claude':
            cursor.execute('UPDATE request_balances SET claude_requests = claude_requests + ? WHERE user_id = ?', (amount, user_id))
        elif balance_type == 'image':
            cursor.execute('UPDATE request_balances SET image_requests = image_requests + ? WHERE user_id = ?', (amount, user_id))
        elif balance_type == 'video':
            cursor.execute('UPDATE request_balances SET video_requests = video_requests + ? WHERE user_id = ?', (amount, user_id))
        elif balance_type == 'suno':
            cursor.execute('UPDATE request_balances SET suno_requests = suno_requests + ? WHERE user_id = ?', (amount, user_id))
        
        conn.commit()
        conn.close()
    
    def use_request(self, user_id, request_type):
        """استخدام طلب من رصيد المستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if request_type == 'weekly':
            cursor.execute('UPDATE request_balances SET weekly_requests_used = weekly_requests_used + 1 WHERE user_id = ?', (user_id,))
        elif request_type == 'chatgpt':
            cursor.execute('UPDATE request_balances SET chatgpt_requests_used = chatgpt_requests_used + 1 WHERE user_id = ?', (user_id,))
        elif request_type == 'claude':
            cursor.execute('UPDATE request_balances SET claude_requests_used = claude_requests_used + 1 WHERE user_id = ?', (user_id,))
        elif request_type == 'image':
            cursor.execute('UPDATE request_balances SET image_requests_used = image_requests_used + 1 WHERE user_id = ?', (user_id,))
        elif request_type == 'video':
            cursor.execute('UPDATE request_balances SET video_requests_used = video_requests_used + 1 WHERE user_id = ?', (user_id,))
        elif request_type == 'suno':
            cursor.execute('UPDATE request_balances SET suno_requests_used = suno_requests_used + 1 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
    
    def check_request_availability(self, user_id, request_type):
        """التحقق من توفر رصيد للطلب"""
        balance = self.get_request_balance(user_id)
        if not balance:
            return False
        
        if request_type == 'weekly':
            return balance['weekly_requests'] > balance['weekly_requests_used']
        elif request_type == 'chatgpt':
            return balance['chatgpt_requests'] > balance['chatgpt_requests_used']
        elif request_type == 'claude':
            return balance['claude_requests'] > balance['claude_requests_used']
        elif request_type == 'image':
            return balance['image_requests'] > balance['image_requests_used']
        elif request_type == 'video':
            return balance['video_requests'] > balance['video_requests_used']
        elif request_type == 'suno':
            return balance['suno_requests'] > balance['suno_requests_used']
        
        return False
    
    def reset_weekly_requests(self):
        """إعادة تعيين الطلبات الأسبوعية للمستخدمين"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now()
        
        # الحصول على المستخدمين الذين يجب إعادة تعيين طلباتهم الأسبوعية
        cursor.execute('SELECT user_id, weekly_reset_date FROM request_balances')
        users = cursor.fetchall()
        
        for user in users:
            reset_date = datetime.strptime(user['weekly_reset_date'], '%Y-%m-%d %H:%M:%S')
            if now >= reset_date:
                # إعادة تعيين الطلبات الأسبوعية
                new_reset_date = now + timedelta(days=7)
                cursor.execute(
                    'UPDATE request_balances SET weekly_requests_used = 0, weekly_reset_date = ? WHERE user_id = ?',
                    (new_reset_date.strftime('%Y-%m-%d %H:%M:%S'), user['user_id'])
                )
        
        conn.commit()
        conn.close()
    
    def add_api_key(self, model_name, api_key, added_by):
        """إضافة مفتاح API جديد"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'INSERT OR REPLACE INTO api_keys (model_name, api_key, is_active, added_by, added_date) VALUES (?, ?, ?, ?, ?)',
            (model_name, api_key, 1, added_by, now)
        )
        conn.commit()
        conn.close()
    
    def remove_api_key(self, model_name):
        """إزالة مفتاح API"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM api_keys WHERE model_name = ?', (model_name,))
        conn.commit()
        conn.close()
    
    def toggle_api_key_status(self, model_name, is_active):
        """تبديل حالة مفتاح API"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE api_keys SET is_active = ? WHERE model_name = ?', (is_active, model_name))
        conn.commit()
        conn.close()
    
    def get_api_key(self, model_name):
        """الحصول على مفتاح API لنموذج معين"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT api_key FROM api_keys WHERE model_name = ? AND is_active = 1', (model_name,))
        key = cursor.fetchone()
        conn.close()
        return key['api_key'] if key else None
    
    def get_all_api_keys(self):
        """الحصول على جميع مفاتيح API النشطة"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT model_name, api_key FROM api_keys WHERE is_active = 1')
        keys = cursor.fetchall()
        conn.close()
        return {key['model_name']: key['api_key'] for key in keys}
    
    def save_context(self, user_id, model, context):
        """حفظ سياق المحادثة"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # تحويل السياق إلى JSON إذا لم يكن نصاً
        if not isinstance(context, str):
            context = json.dumps(context)
        
        cursor.execute(
            'INSERT OR REPLACE INTO conversation_contexts (user_id, model, context, last_updated) VALUES (?, ?, ?, ?)',
            (user_id, model, context, now)
        )
        conn.commit()
        conn.close()
    
    def get_context(self, user_id, model):
        """الحصول على سياق المحادثة"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT context FROM conversation_contexts WHERE user_id = ? AND model = ?', (user_id, model))
        context = cursor.fetchone()
        conn.close()
        
        if context:
            try:
                return json.loads(context['context'])
            except:
                return context['context']
        return None
    
    def delete_context(self, user_id, model=None):
        """حذف سياق المحادثة"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if model:
            cursor.execute('DELETE FROM conversation_contexts WHERE user_id = ? AND model = ?', (user_id, model))
        else:
            cursor.execute('DELETE FROM conversation_contexts WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
    
    def record_payment(self, transaction_id, user_id, amount, currency_amount, status='pending'):
        """تسجيل معاملة دفع"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            'INSERT INTO payment_transactions (transaction_id, user_id, amount, currency_amount, status, transaction_date) VALUES (?, ?, ?, ?, ?, ?)',
            (transaction_id, user_id, amount, currency_amount, status, now)
        )
        conn.commit()
        conn.close()
    
    def update_payment_status(self, transaction_id, status):
        """تحديث حالة معاملة الدفع"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE payment_transactions SET status = ? WHERE transaction_id = ?', (status, transaction_id))
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        conn.close()
        return [user['user_id'] for user in users]
    
    def get_user_stats(self):
        """الحصول على إحصائيات المستخدمين"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # إجمالي عدد المستخدمين
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total_users = cursor.fetchone()['total']
        
        # عدد المستخدمين النشطين في آخر 24 ساعة
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) as active FROM users WHERE last_activity > ?', (yesterday,))
        active_users = cursor.fetchone()['active']
        
        # إجمالي الإنفاق
        cursor.execute('SELECT SUM(total_spent) as total FROM wallets')
        total_spent = cursor.fetchone()['total'] or 0
        
        # إجمالي الرصيد المتاح
        cursor.execute('SELECT SUM(balance) as total FROM wallets')
        total_balance = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_spent': total_spent,
            'total_balance': total_balance
        }
    
    def update_user_model_preference(self, user_id, model):
        """تحديث النموذج المفضل للمستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET preferred_model = ? WHERE user_id = ?', (model, user_id))
        conn.commit()
        conn.close()
    
    def update_user_voice_settings(self, user_id, voice_enabled, preferred_voice=None):
        """تحديث إعدادات الصوت للمستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if preferred_voice:
            cursor.execute('UPDATE users SET voice_enabled = ?, preferred_voice = ? WHERE user_id = ?', 
                          (voice_enabled, preferred_voice, user_id))
        else:
            cursor.execute('UPDATE users SET voice_enabled = ? WHERE user_id = ?', (voice_enabled, user_id))
        
        conn.commit()
        conn.close()
    
    def update_user_instructions(self, user_id, instructions, enabled):
        """تحديث التعليمات المخصصة للمستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET custom_instructions = ?, instructions_enabled = ? WHERE user_id = ?', 
                      (instructions, enabled, user_id))
        conn.commit()
        conn.close()
    
    def update_context_setting(self, user_id, enabled):
        """تحديث إعداد حفظ السياق للمستخدم"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET context_enabled = ? WHERE user_id = ?', (enabled, user_id))
        conn.commit()
        conn.close()
