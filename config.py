import os

# إعدادات أساسية
TOKEN = "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g"
ADMIN_ID = 764559466
PLISIO_SECRET_KEY = "Z468hRlbDPX7nIUdi2OYVsfAkTa9XUQNCwmxxAbyG9YVdCW4_tH6xPuVcaq8vPnO"

# مسارات الملفات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'bot_data.db')

# قائمة المسؤولين
ADMINS = [ADMIN_ID]

# نماذج الذكاء الاصطناعي الافتراضية
DEFAULT_MODELS = {
    "ChatGPT": "",
    "GPT-4.1 mini": "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",
    "GPT-4": "",
    "GPT-4o mini": "",
    "GPT-4o": "",
    "Claude": "",
    "Gemini2.5": "AIzaSyADLvBIJUxbvha5Vhjc_QqO3t5JDtVKrzQ",
    "DeepSeek-V3": "",
    "Perplexity": "",
    "Midjourney": "",
    "Flux": ""
}
