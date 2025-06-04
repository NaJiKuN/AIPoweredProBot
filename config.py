TOKEN = "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g"
ADMIN_IDS = [764559466]  # يمكن إضافة المزيد من المسؤولين
PLISIO_SECRET = "Z468hRlbDPX7nIUdi2OYVsfAkTa9XUQNCwmxxAbyG9YVdCW4_tH6xPuVcaq8vPnO"

# مفاتيح APIs الافتراضية
DEFAULT_API_KEYS = {
    "Gemini 2.5flash": "AIzaSyADLvBIJUxbvha5Vhjc_QqO3t5JDtVKrzQ",
    "GPT-4.1 mini": "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"
}

# النماذج المدعومة
SUPPORTED_MODELS = [
    "GPT-4.1 mini", "GPT-4", "GPT-4o mini", "GPT-4o", 
    "Claude", "Gemini2.5", "DeepSeek-V3", "Perplexity", 
    "Midjourney", "Flux"
]

# خطط الاشتراك
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "مجاني",
        "requests": 50,
        "duration_days": 7,
        "price": 0,
        "models": ["GPT-4.1 mini", "DeepSeek-V3", "Gemini2.5", "Perplexity", "GPT-4o Images"]
    },
    "premium": {
        "name": "الاشتراك المميز",
        "requests": 100,  # يوميًا
        "duration_days": 30,
        "price": 170,
        "models": SUPPORTED_MODELS  # كل النماذج
    },
    # يمكن إضافة المزيد من الخطط هنا
}

# أسعار شراء العملات
WALLET_TOP_UP_OPTIONS = {
    100: 110,
    200: 220,
    350: 360,
    500: 510,
    1000: 1000
}
