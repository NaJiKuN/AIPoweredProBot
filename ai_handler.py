# -*- coding: utf-8 -*-
"""وحدة التعامل مع واجهات برمجة تطبيقات الذكاء الاصطناعي (Gemini, ChatGPT)"""

import logging
import google.generativeai as genai
from openai import OpenAI
import requests

from db_handler import get_api_key_by_type, list_api_keys

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\')
logger = logging.getLogger(__name__)

# --- دوال الاستعلام عن نماذج الذكاء الاصطناعي ---

def query_gemini(api_key, prompt):
    """إرسال استعلام إلى Google Gemini API"""
    if not api_key:
        logger.error("مفتاح Gemini API غير متوفر.")
        return None, "خطأ: مفتاح Gemini API غير مكوّن في البوت."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(\'gemini-pro\')
        response = model.generate_content(prompt)
        logger.info(f"تم استلام رد من Gemini API.")
        # قد تحتاج إلى تعديل طريقة استخلاص النص حسب بنية الرد الفعلية
        if response.parts:
            return response.text, None
        else:
            # التحقق من وجود سبب للحظر أو مشكلة أخرى
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason
                logger.warning(f"تم حظر طلب Gemini: {block_reason}")
                return None, f"عذراً، تم حظر الطلب بواسطة Gemini بسبب: {block_reason}"
            else:
                logger.warning("رد Gemini فارغ أو غير متوقع.")
                return None, "عذراً، لم يتمكن Gemini من إنشاء رد. قد يكون السبب محتوى غير آمن أو مشكلة أخرى."

    except Exception as e:
        logger.error(f"حدث خطأ أثناء استدعاء Gemini API: {e}")
        # يمكنك إضافة معالجة أكثر تفصيلاً لأنواع الأخطاء المختلفة هنا
        return None, f"حدث خطأ أثناء التواصل مع Gemini: {e}"

def query_chatgpt(api_key, prompt):
    """إرسال استعلام إلى OpenAI ChatGPT API"""
    if not api_key:
        logger.error("مفتاح ChatGPT API غير متوفر.")
        return None, "خطأ: مفتاح ChatGPT API غير مكوّن في البوت."

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo", # أو gpt-4 إذا كان المفتاح يدعمه
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        logger.info("تم استلام رد من ChatGPT API.")
        response_text = completion.choices[0].message.content
        return response_text, None
    except Exception as e:
        logger.error(f"حدث خطأ أثناء استدعاء ChatGPT API: {e}")
        # يمكنك إضافة معالجة أكثر تفصيلاً لأنواع الأخطاء المختلفة هنا
        return None, f"حدث خطأ أثناء التواصل مع ChatGPT: {e}"

def get_ai_response(api_name, prompt):
    """الحصول على رد من نموذج الذكاء الاصطناعي المحدد"""
    logger.info(f"محاولة الحصول على رد من API: {api_name}")
    api_info = get_api_key(api_name) # نفترض أن db_handler.py لديه هذه الدالة

    if not api_info:
        logger.error(f"لم يتم العثور على معلومات API للاسم: {api_name}")
        return f"خطأ: لم يتم العثور على إعدادات لواجهة برمجة التطبيقات بالاسم \'{api_name}\'."

    api_key = api_info.get(\'key\')
    api_type = api_info.get(\'type\')

    if not api_key:
        logger.error(f"مفتاح API فارغ للاسم: {api_name}")
        return f"خطأ: مفتاح API لواجهة برمجة التطبيقات \'{api_name}\' غير موجود أو فارغ."

    if api_type == \'gemini\':
        response, error = query_gemini(api_key, prompt)
    elif api_type == \'chatgpt\':
        response, error = query_chatgpt(api_key, prompt)
    else:
        logger.warning(f"نوع API غير مدعوم: {api_type} للاسم: {api_name}")
        return f"خطأ: نوع واجهة برمجة التطبيقات \'{api_type}\' غير مدعوم حالياً."

    if error:
        return error # إرجاع رسالة الخطأ للمستخدم
    elif response:
        return response
    else:
        # حالة غير متوقعة
        logger.error(f"حدث خطأ غير متوقع عند معالجة الرد من {api_name}.")
        return "عذراً، حدث خطأ غير متوقع أثناء معالجة طلبك."

# استيراد get_api_key من db_handler (تأكد من وجود هذه الدالة هناك)
from db_handler import get_api_key

