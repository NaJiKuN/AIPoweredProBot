#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف الإعدادات الرئيسي للبوت
يحتوي على المتغيرات الثابتة والإعدادات الأساسية
"""

# توكن البوت
TOKEN = "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g"

# معرف المسؤول الرئيسي
ADMIN_ID = "764559466"

# قائمة المسؤولين الإضافيين (يمكن تعديلها من خلال لوحة التحكم)
ADDITIONAL_ADMINS = []

# مفتاح Plisio لبوابة الدفع
PLISIO_SECRET_KEY = "Z468hRlbDPX7nIUdi2OYVsfAkTa9XUQNCwmxxAbyG9YVdCW4_tH6xPuVcaq8vPnO"

# مفاتيح API الافتراضية
DEFAULT_API_KEYS = {
    "gemini": "AIzaSyADLvBIJUxbvha5Vhjc_QqO3t5JDtVKrzQ",
    "gpt4_mini": "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"
}

# قائمة النماذج المدعومة
SUPPORTED_MODELS = [
    "ChatGPT",
    "GPT-4.1 mini",
    "GPT-4",
    "GPT-4o mini",
    "GPT-4o",
    "Claude",
    "Gemini2.5",
    "DeepSeek-V3",
    "Perplexity",
    "Midjourney",
    "Flux"
]

# إعدادات قاعدة البيانات
DATABASE_FILE = "bot_database.db"

# إعدادات الاشتراك المجاني
FREE_SUBSCRIPTION = {
    "name": "مجاني",
    "duration_days": 7,
    "text_requests": 50,
    "models": ["GPT-4.1 mini", "GPT-4o mini", "DeepSeek-V3", "Gemini2.5", "Perplexity", "GPT-4o Images"]
}

# إعدادات الاشتراكات والحزم
PREMIUM_SUBSCRIPTION = {
    "name": "الاشتراك المميز",
    "duration_days": 30,
    "price": 170,
    "daily_text_requests": 100,
    "models": ["GPT-4.1 mini", "GPT-4o mini", "DeepSeek-V3", "Gemini2.5", "Perplexity", "GPT-4o Images"],
    "image_requests": 10,
    "image_models": ["Midjourney", "Flux"]
}

PREMIUM_X2_SUBSCRIPTION = {
    "name": "الاشتراك المميز X2",
    "duration_days": 30,
    "price": 320,
    "daily_text_requests": 200,
    "models": ["GPT-4.1 mini", "GPT-4o mini", "DeepSeek-V3", "Gemini2.5", "Perplexity", "GPT-4o Images"],
    "image_requests": 20,
    "image_models": ["Midjourney", "Flux"]
}

# حزم ChatGPT
CHATGPT_PACKAGES = {
    "50": {"price": 175, "requests": 50},
    "100": {"price": 320, "requests": 100},
    "200": {"price": 620, "requests": 200},
    "500": {"price": 1550, "requests": 500}
}

# حزم Claude
CLAUDE_PACKAGES = {
    "100": {"price": 175, "requests": 100},
    "200": {"price": 320, "requests": 200},
    "500": {"price": 720, "requests": 500},
    "1000": {"price": 1200, "requests": 1000}
}

# حزم Midjourney & Flux
IMAGE_PACKAGES = {
    "50": {"price": 175, "requests": 50},
    "100": {"price": 320, "requests": 100},
    "200": {"price": 620, "requests": 200},
    "500": {"price": 1400, "requests": 500}
}

# حزم الفيديو
VIDEO_PACKAGES = {
    "10": {"price": 375, "requests": 10},
    "20": {"price": 730, "requests": 20},
    "50": {"price": 1750, "requests": 50}
}

# حزم الأغاني
SUNO_PACKAGES = {
    "20": {"price": 175, "requests": 20},
    "50": {"price": 425, "requests": 50},
    "100": {"price": 780, "requests": 100}
}

# حزمة كومبو
COMBO_PACKAGE = {
    "name": "كومبو",
    "duration_days": 30,
    "price": 580,
    "daily_text_requests": 100,
    "chatgpt_requests": 100,
    "image_requests": 100
}

# أسعار شراء العملات
CURRENCY_PRICES = {
    "100": 110,
    "200": 220,
    "350": 360,
    "500": 510,
    "1000": 1000
}

# اللغات المدعومة
SUPPORTED_LANGUAGES = ["ar", "en", "ru", "es", "fr", "pt"]

# الأصوات المدعومة للردود الصوتية
VOICE_OPTIONS = {
    "female": ["nova", "shimmer"],
    "male": ["alloy", "echo", "fable", "onyx"]
}
