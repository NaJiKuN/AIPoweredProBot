import requests

class AIModels:
    def __init__(self, db):
        self.db = db

    def get_available_models(self):
        models = []
        for model in ["ChatGPT", "GPT-4.1 mini", "GPT-4", "GPT-4o mini", "GPT-4o", "Claude", "Gemini2.5", "DeepSeek-V3", "Perplexity", "Midjourney", "Flux"]:
            if self.db.get_api_key(model):
                models.append(model)
        return models

    def generate_text(self, model_name, prompt):
        api_key = self.db.get_api_key(model_name)
        if not api_key:
            return "المفتاح غير متوفر لهذا النموذج."

        # هنا نموذج مبسط لاستدعاء API، يجب تعديله حسب كل نموذج فعليًا
        if model_name == "Gemini2.5":
            response = requests.post('https://api.gemini.com/v1/generate', headers={'Authorization': f'Bearer {api_key}'}, json={'prompt': prompt})
            return response.json().get('text', 'خطأ في الاستجابة')
        elif model_name == "GPT-4.1 mini":
            response = requests.post('https://api.openai.com/v1/completions', headers={'Authorization': f'Bearer {api_key}'}, json={'model': 'gpt-4.1-mini', 'prompt': prompt})
            return response.json().get('choices', [{}])[0].get('text', 'خطأ في الاستجابة')
        # يجب إضافة باقي النماذج مع APIs الفعلية
        return "النموذج غير مدعوم حاليًا."