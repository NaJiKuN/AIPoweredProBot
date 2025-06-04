# النصوص بالعربية (يمكن إضافة لغات أخرى)
START_MESSAGE = """مرحبًا! يتيح لك الروبوت الوصول إلى أفضل أدوات الذكاء الاصطناعي لإنشاء النصوص والصور والفيديوهات والموسيقى.

جرب نماذج متقدمة: OpenAI o3، o4-mini، GPT-4.5، Claude 4، /Midjourney، Flux، /Kling، Pika، /Suno، Grok والمزيد.

مجانًا: GPT-4.1 mini، DeepSeek، Gemini 2.5، GPT Images، وبحث الويب Perplexity.

كيفية الاستخدام:

📝 النص: فقط اطرح سؤالك في الدردشة (اختر نموذج الذكاء الاصطناعي باستخدام /model).

🔎 البحث: انقر على /s للبحث الذكي على الويب.

🌅 الصور: انقر على /photo لبدء إنشاء الصور أو تحريرها.

🎬 الفيديو: انقر على /video لبدء إنشاء مقطع الفيديو الخاص بك (متاح في /premium).

🎸 الموسيقى: انقر على /chirp، واختر نوعًا موسيقيًا، وأضف كلمات الأغنية (متاح في /Suno)."""

CONTEXT_DELETED_MESSAGE = "تم حذف السياق. عادةً ما يتذكر البوت سؤالك السابق وإجابته ويستخدم السياق في الرد"

def format_account_message(user_data, packages):
    # بناء نص الحساب بناءً على بيانات المستخدم
    return f"""[الاشتراك: {user_data['subscription_type']} ✔️
النموذج الحالي: {user_data['selected_model']} /model

الرصيد المتوفر: {user_data['wallet_balance']}

📊 الاستخدام

الطلبات الأسبوعية: {packages.get('free', 0)}/50
 └ GPT-4.1 mini | GPT-4o mini
 └ DeepSeek-V3
 └ Gemini 2.5 Flash
 └ بحث الويب مع Perplexity
 └ GPT-4o Images

📝 حزمة ChatGPT: {packages.get('chatgpt', 0)}/0
 └ OpenAI o3 | o4-mini
 └ GPT-4.5 | GPT-4.1 | GPT-4o
 └ صور DALL•E 3
 └ التعرف على الصور

📝 حزمة Claude: {packages.get('claude', 0)}/0
 └ Claude 4 Sonnet + Thinking
 └ التعرف على الصور
 └ التعرف على الملفات

🌅 حزمة الصور: {packages.get('images', 0)}/0
 └ Midjourney | Flux
 └ تبديل الوجوه

🎬 حزمة الفيديو: {packages.get('video', 0)}/0
 └ Kling AI | Pika AI
 └ تحويل النص إلى فيديو، الصورة إلى فيديو

🎸 أغاني Suno: {packages.get('suno', 0)}/0

هل تحتاج إلى المزيد من الطلبات؟
تحقق من /premium للحصول على خيارات إضافية]"""

# ... (نصوص أخرى)
