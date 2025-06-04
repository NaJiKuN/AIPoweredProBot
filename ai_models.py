import openai
import google.generativeai as genai
from config import DEFAULT_MODELS

# تهيئة نماذج الذكاء الاصطناعي
genai.configure(api_key=DEFAULT_MODELS['Gemini2.5'])
openai.api_key = DEFAULT_MODELS['GPT-4.1 mini']

async def generate_response(model: str, prompt: str, context: list = []):
    if model == 'Gemini2.5':
        return await generate_gemini_response(prompt, context)
    elif model.startswith('GPT'):
        return await generate_openai_response(model, prompt, context)
    # ... (نماذج أخرى)

async def generate_gemini_response(prompt: str, context: list):
    model = genai.GenerativeModel('gemini-1.5-flash')
    full_context = "\n".join(context) + "\n" + prompt if context else prompt
    response = model.generate_content(full_context)
    return response.text

async def generate_openai_response(model: str, prompt: str, context: list):
    model_map = {
        'GPT-4.1 mini': 'gpt-4-1106-preview',
        'GPT-4': 'gpt-4',
        'GPT-4o': 'gpt-4o'
    }
    
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for i, msg in enumerate(context):
        messages.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": msg
        })
    
    messages.append({"role": "user", "content": prompt})
    
    response = openai.ChatCompletion.create(
        model=model_map.get(model, 'gpt-4-turbo'),
        messages=messages
    )
    
    return response.choices[0].message['content']

# ... (وظائف للنماذج الأخرى)
