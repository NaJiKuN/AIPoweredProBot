# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# توكن بوت تليجرام
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# معرفات المسؤولين (قائمة من السلاسل النصية)
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(',')

# مفاتيح API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# يمكنك إضافة المزيد من مفاتيح API هنا عند الحاجة
# مثال:
# CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# إعدادات قاعدة البيانات (مثال باستخدام SQLite)
DATABASE_NAME = "bot_database.db"

# رسائل البوت
START_MESSAGE = """
مرحبًا! يتيح لك الروبوت الوصول إلى أفضل أدوات الذكاء الاصطناعي لإنشاء النصوص والصور والفيديوهات والموسيقى.

جرب نماذج متقدمة: OpenAI o3، o4-mini، GPT-4.5، Claude 4، /Midjourney، Flux، /Kling، Pika، /Suno، Grok والمزيد.

مجانًا: GPT-4.1 mini، DeepSeek، Gemini 2.5، GPT Images، وبحث الويب Perplexity.

كيفية الاستخدام:

📝 النص: فقط اطرح سؤالك في الدردشة (اختر نموذج الذكاء الاصطناعي باستخدام /model).

🔎 البحث: انقر على /s للبحث الذكي على الويب.

🌅 الصور: انقر على /photo لبدء إنشاء الصور أو تحريرها.

🎬 الفيديو: انقر على /video لبدء إنشاء مقطع الفيديو الخاص بك (متاح في /premium).

🎸 الموسيقى: انقر على /chirp، واختر نوعًا موسيقيًا، وأضف كلمات الأغنية (متاح في /Suno).
"""

HELP_MESSAGE = """
📝 إنشاء النص
لإنشاء نص، اكتب طلبك في الدردشة. يمكن للمستخدمين الذين لديهم اشتراك /premium أيضًا إرسال رسائل صوتية.
/s – بحث الويب مع Perplexity
/settings – إعدادات روبوت الدردشة
/model – التبديل بين نماذج الذكاء الاصطناعي

💬 استخدام السياق
يحتفظ الروبوت بالسياق افتراضيًا، مما يربط استفسارك الحالي بآخر رد له. هذا يسمح بالحوار وطرح أسئلة متابعة. لبدء موضوع جديد بدون سياق، استخدم أمر /deletecontext.

📄 التعرف على الملفات
عند استخدام نموذج Claude، يمكنك العمل مع المستندات. قم بتحميل ملف بتنسيق docx، pdf، xlsx، xls، csv، pptx، txt واطرح أسئلة حول المستند. يستهلك كل طلب 3 عمليات إنشاء من Claude.

🌅 إنشاء الصور
ينشئ الروبوت صورًا باستخدام أحدث نماذج Midjourney وChatGPT وFlux. ابدأ بأمر وأضف توجيهك:
/wow – بدء وضع صور GPT-4o
/flux – استخدام Flux
/dalle – استخدام DALL•E 3
/imagine – استخدام Midjourney
└ دليل (https://teletype.in/@gpt4telegrambot/midjourney) لإتقان Midjourney

🎸 إنشاء الأغاني
ينشئ الروبوت أغاني باستخدام Suno.
/chirp – إنشاء أغنية؛ سيطلب منك الروبوت اختيار نوع موسيقي وإدخال كلمات الأغنية
/Suno – دليل لإنشاء الأغاني

⚙️ أوامر أخرى
/start – وصف الروبوت
/account – ملفك الشخصي والرصيد
/premium – اختيار وشراء اشتراك مميز لـ ChatGPT وClaude وGemini وDALL•E 3 وMidjourney وFlux وSuno
/privacy – شروط الاستخدام وسياسة الخصوصية

لأي استفسارات، يمكنك أيضًا مراسلة المسؤول @NaJiMaS
"""

# التحقق من وجود التوكن الأساسي
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("لم يتم العثور على توكن بوت تليجرام. يرجى تعيينه في ملف .env")


