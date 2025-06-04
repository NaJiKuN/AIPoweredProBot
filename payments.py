import requests
import time
from config import PLISIO_SECRET

def create_plisio_invoice(amount, currency, user_id):
    """إنشاء فاتورة Plisio"""
    url = "https://plisio.net/api/v1/invoices/new"
    params = {
        "api_key": PLISIO_SECRET,
        "order_name": f"شحن محفظة - {user_id}",
        "order_number": f"WALLET_{user_id}_{int(time.time())}",
        "source_amount": amount,
        "source_currency": currency,
        "currency": "USD",  # أو أي عملة
        "callback_url": "https://yourdomain.com/plisio_callback",
        "success_url": "https://t.me/YourBot?start=payment_success",
        "email": "user@example.com"  # يمكن الحصول عليه من المستخدم
    }
    response = requests.get(url, params=params)
    return response.json()

def handle_plisio_callback(data):
    """معالجة رد Plisio"""
    # التحقق من صحة الطلب
    if not verify_plisio_signature(data):
        return False
    
    # تحديث رصيد المستخدم
    user_id = data['order_number'].split('_')[1]
    amount = data['source_amount']
    update_wallet_balance(user_id, amount)
    
    return True

def verify_plisio_signature(data):
    """التحقق من توقيع Plisio"""
    # (سيتم تنفيذ المنطق الكامل في الإصدار النهائي)
    return True

def update_wallet_balance(user_id, amount):
    """تحديث رصيد المحفظة"""
    # (سيتم تنفيذ المنطق الكامل في الإصدار النهائي)
    pass
