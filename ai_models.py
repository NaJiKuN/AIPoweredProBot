#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف التعامل مع نماذج الذكاء الاصطناعي
يحتوي على وظائف للتعامل مع واجهات برمجة التطبيقات (APIs) للنماذج المختلفة
"""

import logging
import os
import json
import requests
import openai
import anthropic
import google.generativeai as genai
from PIL import Image
from io import BytesIO

from database import Database
from config import OPENAI_API_KEY_DEFAULT, ANTHROPIC_API_KEY_DEFAULT, GEMINI_API_KEY_DEFAULT

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء اتصال بقاعدة البيانات
db = Database()

class AIModelHandler:
    """فئة للتعامل مع نماذج الذكاء الاصطناعي المختلفة"""
    
    def __init__(self):
        """تهيئة المعالج"""
        # الحصول على مفاتيح API من قاعدة البيانات
        self.api_keys = db.get_all_api_keys()
        
        # تعيين مفاتيح API الافتراضية إذا لم تكن موجودة في قاعدة البيانات
        if "OpenAI" not in self.api_keys and OPENAI_API_KEY_DEFAULT:
            self.api_keys["OpenAI"] = OPENAI_API_KEY_DEFAULT
        
        if "Claude" not in self.api_keys and ANTHROPIC_API_KEY_DEFAULT:
            self.api_keys["Claude"] = ANTHROPIC_API_KEY_DEFAULT
        
        if "Gemini" not in self.api_keys and GEMINI_API_KEY_DEFAULT:
            self.api_keys["Gemini"] = GEMINI_API_KEY_DEFAULT
    
    def refresh_api_keys(self):
        """تحديث مفاتيح API من قاعدة البيانات"""
        self.api_keys = db.get_all_api_keys()
    
    async def generate_text(self, model, prompt, user_id=None, context=None, instructions=None, image_path=None):
        """إنشاء نص باستخدام نموذج الذكاء الاصطناعي المحدد"""
        try:
            # تحديث مفاتيح API
            self.refresh_api_keys()
            
            # التعامل مع نماذج OpenAI
            if "gpt" in model.lower() or "openai" in model.lower() or "o3" in model.lower() or "o4" in model.lower():
                return await self._generate_openai_text(model, prompt, user_id, context, instructions, image_path)
            
            # التعامل مع نماذج Claude
            elif "claude" in model.lower():
                return await self._generate_claude_text(model, prompt, user_id, context, instructions, image_path)
            
            # التعامل مع نماذج Gemini
            elif "gemini" in model.lower():
                return await self._generate_gemini_text(model, prompt, user_id, context, instructions, image_path)
            
            # التعامل مع نماذج DeepSeek
            elif "deepseek" in model.lower():
                return await self._generate_deepseek_text(model, prompt, user_id, context, instructions)
            
            # التعامل مع نماذج Perplexity
            elif "perplexity" in model.lower():
                return await self._generate_perplexity_text(model, prompt, user_id)
            
            else:
                return "النموذج غير مدعوم حالياً."
        
        except Exception as e:
            logger.error(f"Error generating text with {model}: {e}")
            return f"حدث خطأ أثناء إنشاء النص: {str(e)}"
    
    async def _generate_openai_text(self, model, prompt, user_id=None, context=None, instructions=None, image_path=None):
        """إنشاء نص باستخدام نماذج OpenAI"""
        try:
            # التحقق من وجود مفتاح API
            if "OpenAI" not in self.api_keys:
                return "مفتاح API لـ OpenAI غير متوفر."
            
            # تعيين مفتاح API
            openai.api_key = self.api_keys["OpenAI"]
            
            # تحديد النموذج المناسب
            model_name = "gpt-4o" # افتراضي
            if "gpt-4.5" in model.lower():
                model_name = "gpt-4-turbo"
            elif "gpt-4.1" in model.lower() and "mini" not in model.lower():
                model_name = "gpt-4"
            elif "gpt-4o" in model.lower() and "mini" not in model.lower():
                model_name = "gpt-4o"
            elif "o3" in model.lower():
                model_name = "gpt-4o"
            elif "o4-mini" in model.lower() or "gpt-4.1 mini" in model.lower() or "gpt-4o mini" in model.lower():
                model_name = "gpt-4o-mini"
            
            # إعداد الرسائل
            messages = []
            
            # إضافة التعليمات إذا كانت متوفرة
            if instructions:
                messages.append({"role": "system", "content": instructions})
            else:
                messages.append({"role": "system", "content": "أنت مساعد ذكي ومفيد."})
            
            # إضافة السياق إذا كان متوفراً
            if context:
                for msg in context:
                    messages.append(msg)
            
            # إضافة الصورة إذا كانت متوفرة
            if image_path and os.path.exists(image_path):
                # قراءة الصورة وتحويلها إلى base64
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                
                # إضافة الصورة إلى الرسالة
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data.encode('base64').decode('utf-8')}"
                            }
                        }
                    ]
                })
            else:
                # إضافة النص فقط
                messages.append({"role": "user", "content": prompt})
            
            # إنشاء الاستجابة
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                max_tokens=4000
            )
            
            # استخراج النص من الاستجابة
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error with OpenAI: {e}")
            return f"حدث خطأ أثناء التواصل مع OpenAI: {str(e)}"
    
    async def _generate_claude_text(self, model, prompt, user_id=None, context=None, instructions=None, image_path=None):
        """إنشاء نص باستخدام نماذج Claude"""
        try:
            # التحقق من وجود مفتاح API
            if "Claude" not in self.api_keys:
                return "مفتاح API لـ Claude غير متوفر."
            
            # تهيئة عميل Claude
            client = anthropic.Anthropic(api_key=self.api_keys["Claude"])
            
            # تحديد النموذج المناسب
            model_name = "claude-3-sonnet-20240229" # افتراضي
            if "thinking" in model.lower():
                model_name = "claude-3-sonnet-20240229"
                # في الواقع، وضع التفكير هو نفس النموذج ولكن مع إعدادات مختلفة
            
            # إعداد الرسائل
            messages = []
            
            # إضافة التعليمات إذا كانت متوفرة
            system_prompt = "أنت مساعد ذكي ومفيد."
            if instructions:
                system_prompt = instructions
            
            # إضافة الصورة إذا كانت متوفرة
            if image_path and os.path.exists(image_path):
                # قراءة الصورة
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                
                # إنشاء الاستجابة مع الصورة
                response = client.messages.create(
                    model=model_name,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data.encode('base64').decode('utf-8')}}
                            ]
                        }
                    ]
                )
            else:
                # إنشاء الاستجابة بدون صورة
                response = client.messages.create(
                    model=model_name,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
            
            # استخراج النص من الاستجابة
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Error with Claude: {e}")
            return f"حدث خطأ أثناء التواصل مع Claude: {str(e)}"
    
    async def _generate_gemini_text(self, model, prompt, user_id=None, context=None, instructions=None, image_path=None):
        """إنشاء نص باستخدام نماذج Gemini"""
        try:
            # التحقق من وجود مفتاح API
            if "Gemini" not in self.api_keys:
                return "مفتاح API لـ Gemini غير متوفر."
            
            # تهيئة Gemini
            genai.configure(api_key=self.api_keys["Gemini"])
            
            # تحديد النموذج المناسب
            model_name = "gemini-1.5-flash" # افتراضي
            
            # إعداد النموذج
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4000,
            }
            
            # إنشاء النموذج
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            
            # إعداد الرسائل
            messages = []
            
            # إضافة التعليمات إذا كانت متوفرة
            if instructions:
                messages.append({"role": "user", "parts": [instructions]})
                messages.append({"role": "model", "parts": ["سأتبع هذه التعليمات."]})
            
            # إضافة السياق إذا كان متوفراً
            if context:
                for msg in context:
                    role = "user" if msg["role"] == "user" else "model"
                    messages.append({"role": role, "parts": [msg["content"]]})
            
            # إضافة الصورة إذا كانت متوفرة
            if image_path and os.path.exists(image_path):
                # قراءة الصورة
                image = Image.open(image_path)
                
                # إنشاء الاستجابة مع الصورة
                response = model.generate_content([prompt, image])
            else:
                # إضافة النص الحالي
                messages.append({"role": "user", "parts": [prompt]})
                
                # إنشاء الاستجابة
                chat = model.start_chat(history=messages)
                response = chat.send_message(prompt)
            
            # استخراج النص من الاستجابة
            return response.text
        
        except Exception as e:
            logger.error(f"Error with Gemini: {e}")
            return f"حدث خطأ أثناء التواصل مع Gemini: {str(e)}"
    
    async def _generate_deepseek_text(self, model, prompt, user_id=None, context=None, instructions=None):
        """إنشاء نص باستخدام نماذج DeepSeek"""
        try:
            # التحقق من وجود مفتاح API
            if "DeepSeek" not in self.api_keys:
                return "مفتاح API لـ DeepSeek غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ DeepSeek
            # لإنشاء نص حقيقي
            
            return f"هذا نص تجريبي من نموذج DeepSeek استجابةً لـ: {prompt}"
        
        except Exception as e:
            logger.error(f"Error with DeepSeek: {e}")
            return f"حدث خطأ أثناء التواصل مع DeepSeek: {str(e)}"
    
    async def _generate_perplexity_text(self, model, prompt, user_id=None):
        """إنشاء نص باستخدام نماذج Perplexity"""
        try:
            # التحقق من وجود مفتاح API
            if "Perplexity" not in self.api_keys:
                return "مفتاح API لـ Perplexity غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Perplexity
            # لإنشاء نص حقيقي
            
            return f"هذا نص تجريبي من نموذج Perplexity استجابةً لـ: {prompt}"
        
        except Exception as e:
            logger.error(f"Error with Perplexity: {e}")
            return f"حدث خطأ أثناء التواصل مع Perplexity: {str(e)}"
    
    async def generate_image(self, model, prompt, user_id=None, reference_image=None):
        """إنشاء صورة باستخدام نموذج الذكاء الاصطناعي المحدد"""
        try:
            # تحديث مفاتيح API
            self.refresh_api_keys()
            
            # التعامل مع نماذج DALL•E
            if "dall" in model.lower():
                return await self._generate_dalle_image(prompt, user_id)
            
            # التعامل مع نماذج Midjourney
            elif "midjourney" in model.lower():
                return await self._generate_midjourney_image(prompt, user_id, reference_image)
            
            # التعامل مع نماذج Flux
            elif "flux" in model.lower():
                return await self._generate_flux_image(prompt, user_id, reference_image)
            
            else:
                return None, "النموذج غير مدعوم حالياً."
        
        except Exception as e:
            logger.error(f"Error generating image with {model}: {e}")
            return None, f"حدث خطأ أثناء إنشاء الصورة: {str(e)}"
    
    async def _generate_dalle_image(self, prompt, user_id=None):
        """إنشاء صورة باستخدام نماذج DALL•E"""
        try:
            # التحقق من وجود مفتاح API
            if "OpenAI" not in self.api_keys:
                return None, "مفتاح API لـ OpenAI غير متوفر."
            
            # تعيين مفتاح API
            openai.api_key = self.api_keys["OpenAI"]
            
            # إنشاء الصورة
            response = openai.Image.create(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            # استخراج URL الصورة
            image_url = response.data[0].url
            
            # تنزيل الصورة
            image_response = requests.get(image_url)
            image_data = BytesIO(image_response.content)
            
            return image_data, None
        
        except Exception as e:
            logger.error(f"Error with DALL•E: {e}")
            return None, f"حدث خطأ أثناء التواصل مع DALL•E: {str(e)}"
    
    async def _generate_midjourney_image(self, prompt, user_id=None, reference_image=None):
        """إنشاء صورة باستخدام نماذج Midjourney"""
        try:
            # التحقق من وجود مفتاح API
            if "Midjourney" not in self.api_keys:
                return None, "مفتاح API لـ Midjourney غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Midjourney
            # لإنشاء صورة حقيقية
            
            # في هذا المثال، نعيد صورة تجريبية
            return None, "هذه وظيفة تجريبية. في التطبيق الفعلي، سيتم إنشاء صورة باستخدام Midjourney."
        
        except Exception as e:
            logger.error(f"Error with Midjourney: {e}")
            return None, f"حدث خطأ أثناء التواصل مع Midjourney: {str(e)}"
    
    async def _generate_flux_image(self, prompt, user_id=None, reference_image=None):
        """إنشاء صورة باستخدام نماذج Flux"""
        try:
            # التحقق من وجود مفتاح API
            if "Flux" not in self.api_keys:
                return None, "مفتاح API لـ Flux غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Flux
            # لإنشاء صورة حقيقية
            
            # في هذا المثال، نعيد صورة تجريبية
            return None, "هذه وظيفة تجريبية. في التطبيق الفعلي، سيتم إنشاء صورة باستخدام Flux."
        
        except Exception as e:
            logger.error(f"Error with Flux: {e}")
            return None, f"حدث خطأ أثناء التواصل مع Flux: {str(e)}"
    
    async def generate_video(self, model, prompt, user_id=None, reference_image=None):
        """إنشاء فيديو باستخدام نموذج الذكاء الاصطناعي المحدد"""
        try:
            # تحديث مفاتيح API
            self.refresh_api_keys()
            
            # التعامل مع نماذج Kling
            if "kling" in model.lower():
                return await self._generate_kling_video(prompt, user_id, reference_image)
            
            # التعامل مع نماذج Pika
            elif "pika" in model.lower():
                return await self._generate_pika_video(prompt, user_id, reference_image)
            
            else:
                return None, "النموذج غير مدعوم حالياً."
        
        except Exception as e:
            logger.error(f"Error generating video with {model}: {e}")
            return None, f"حدث خطأ أثناء إنشاء الفيديو: {str(e)}"
    
    async def _generate_kling_video(self, prompt, user_id=None, reference_image=None):
        """إنشاء فيديو باستخدام نماذج Kling"""
        try:
            # التحقق من وجود مفتاح API
            if "Kling" not in self.api_keys:
                return None, "مفتاح API لـ Kling غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Kling
            # لإنشاء فيديو حقيقي
            
            # في هذا المثال، نعيد فيديو تجريبي
            return None, "هذه وظيفة تجريبية. في التطبيق الفعلي، سيتم إنشاء فيديو باستخدام Kling."
        
        except Exception as e:
            logger.error(f"Error with Kling: {e}")
            return None, f"حدث خطأ أثناء التواصل مع Kling: {str(e)}"
    
    async def _generate_pika_video(self, prompt, user_id=None, reference_image=None):
        """إنشاء فيديو باستخدام نماذج Pika"""
        try:
            # التحقق من وجود مفتاح API
            if "Pika" not in self.api_keys:
                return None, "مفتاح API لـ Pika غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Pika
            # لإنشاء فيديو حقيقي
            
            # في هذا المثال، نعيد فيديو تجريبي
            return None, "هذه وظيفة تجريبية. في التطبيق الفعلي، سيتم إنشاء فيديو باستخدام Pika."
        
        except Exception as e:
            logger.error(f"Error with Pika: {e}")
            return None, f"حدث خطأ أثناء التواصل مع Pika: {str(e)}"
    
    async def generate_music(self, model, prompt, genre, user_id=None):
        """إنشاء موسيقى باستخدام نموذج الذكاء الاصطناعي المحدد"""
        try:
            # تحديث مفاتيح API
            self.refresh_api_keys()
            
            # التعامل مع نماذج Suno
            if "suno" in model.lower():
                return await self._generate_suno_music(prompt, genre, user_id)
            
            else:
                return None, "النموذج غير مدعوم حالياً."
        
        except Exception as e:
            logger.error(f"Error generating music with {model}: {e}")
            return None, f"حدث خطأ أثناء إنشاء الموسيقى: {str(e)}"
    
    async def _generate_suno_music(self, prompt, genre, user_id=None):
        """إنشاء موسيقى باستخدام نماذج Suno"""
        try:
            # التحقق من وجود مفتاح API
            if "Suno" not in self.api_keys:
                return None, "مفتاح API لـ Suno غير متوفر."
            
            # هذه دالة تجريبية، في التطبيق الفعلي يجب استخدام API الخاص بـ Suno
            # لإنشاء موسيقى حقيقية
            
            # في هذا المثال، نعيد موسيقى تجريبية
            return None, "هذه وظيفة تجريبية. في التطبيق الفعلي، سيتم إنشاء موسيقى باستخدام Suno."
        
        except Exception as e:
            logger.error(f"Error with Suno: {e}")
            return None, f"حدث خطأ أثناء التواصل مع Suno: {str(e)}"

# إنشاء كائن من الفئة للاستخدام في أجزاء أخرى من التطبيق
ai_handler = AIModelHandler()
