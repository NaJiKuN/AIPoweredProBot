import openai
from config import DEFAULT_API_KEYS

# تهيئة عميل OpenAI
openai.api_key = DEFAULT_API_KEYS.get("GPT-4.1 mini")

async def handle_ai_request(user_id, prompt):
    """معالجة طلبات الذكاء الاصطناعي"""
    try:
        # الحصول على النموذج المفضل للمستخدم
        # (سيتم استكمال هذا الجزء في الإصدار النهائي)
        model = "gpt-4"
        
        # إرسال الطلب إلى OpenAI
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ حدث خطأ أثناء معالجة طلبك: {str(e)}"

# يمكن إضافة دوال إضافية للنماذج الأخرى
