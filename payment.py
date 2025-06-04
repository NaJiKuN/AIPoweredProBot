import requests
from config import PLISIO_SECRET_KEY
import database as db

async def initiate_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    user_id = update.effective_user.id
    stars_required = calculate_stars(amount)
    
    # إنشاء معاملة في قاعدة البيانات
    transaction_id = db.create_transaction(user_id, amount, stars_required)
    
    # إعداد بيانات الدفع
    data = {
        'api_key': PLISIO_SECRET_KEY,
        'order_number': f"TX{transaction_id}",
        'order_name': f"شحن محفظة {amount} عملة",
        'source_amount': stars_required,
        'source_currency': 'XLM',
        'callback_url': 'https://yourdomain.com/payment_callback',
        'success_url': 'https://t.me/yourbot?start=success',
        'cancel_url': 'https://t.me/yourbot?start=cancel'
    }
    
    # إرسال طلب الدفع إلى Plisio
    response = requests.post('https://plisio.net/api/v1/invoices/new', data=data)
    
    if response.status_code == 200:
        payment_url = response.json()['data']['invoice_url']
        await update.callback_query.message.reply_text(
            f"يرجى إكمال الدفع: {payment_url}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("دفع الآن", url=payment_url)]
            ])
        )
    else:
        await update.callback_query.message.reply_text("❌ حدث خطأ أثناء معالجة الدفع")

def calculate_stars(amount: int):
    # حساب النجوم المطلوبة بناء على الكمية
    rates = {
        100: 110,
        200: 220,
        350: 360,
        500: 510,
        1000: 1000
    }
    return rates.get(amount, amount * 1.1)

# ... (وظائف أخرى للدفع)
