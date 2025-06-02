# -*- coding: utf-8 -*-
"""ملف الإعدادات الثابتة للبوت"""

import os

# رمز بوت تليجرام (يجب الحصول عليه من BotFather)
# هام: يُفضل بشدة تخزين هذا الرمز كمتغير بيئة بدلاً من وضعه مباشرة في الكود
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8063450521:AAEuWliwmyxbGPpMcNF8VZmOedht3ni0j5s")

# معرف المستخدم للمسؤول الأول (سيتم إضافته تلقائياً عند أول تشغيل إذا لم تكن قاعدة البيانات موجودة)
# يمكن للمسؤول الأول إضافة مسؤولين آخرين لاحقاً
INITIAL_ADMIN_ID = 764559466 # استبدل بالمعرف الرقمي للمسؤول

# اسم ملف قاعدة بيانات SQLite
DATABASE_NAME = "bot_database.db"

# رابط مستودع GitHub (لأمر التحديث)
GITHUB_REPO_URL = "https://github.com/NaJiKuN/AIPoweredProBot"

# مسار المشروع على الخادم (لأمر التحديث)
PROJECT_PATH = "/home/ec2-user/projects/AIPoweredProBot"

# مفاتيح API الأولية (سيتم تخزينها في قاعدة البيانات عند التهيئة الأولية)
# يمكن للمسؤولين إدارتها (إضافة/حذف/تعديل) لاحقاً عبر أوامر البوت
# هام: يُفضل بشدة تخزين المفاتيح الفعلية كمتغيرات بيئة أو في نظام إدارة أسرار آمن
INITIAL_API_KEYS = {
    "gemini": {
        "key": os.getenv("GEMINI_API_KEY", "AIzaSyAZdRvGnptFullhaGMp0sxM-fr1qhYq7MA"),
        "type": "gemini"
    },
    "chatgpt": {
        "key": os.getenv("CHATGPT_API_KEY", "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"),
        "type": "chatgpt"
    }
}

# التحقق من وجود المتغيرات الأساسية
if not TELEGRAM_TOKEN:
    raise ValueError("خطأ: لم يتم تعيين رمز بوت تليجرام (TELEGRAM_TOKEN).")

print("تم تحميل الإعدادات بنجاح.")

