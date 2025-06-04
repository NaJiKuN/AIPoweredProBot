from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import SUPPORTED_MODELS, SUBSCRIPTION_PLANS, WALLET_TOP_UP_OPTIONS

def start_keyboard():
    """لوحة مفاتيح أمر /start"""
    keyboard = [
        [InlineKeyboardButton("حسابي 🪪", callback_data="account")],
        [InlineKeyboardButton("الاشتراكات 💎", callback_data="premium")],
        [InlineKeyboardButton("إنشاء صور 🖼️", callback_data="photo")],
        [InlineKeyboardButton("إنشاء فيديو 🎬", callback_data="video")],
        [InlineKeyboardButton("إنشاء أغنية 🎵", callback_data="suno")]
    ]
    return InlineKeyboardMarkup(keyboard)

def account_keyboard():
    """لوحة مفاتيح أمر /account"""
    keyboard = [
        [InlineKeyboardButton("شراء عملات المحفظة 💰", callback_data="wallet_topup")],
        [InlineKeyboardButton("الاشتراكات 💎", callback_data="premium")],
        [InlineKeyboardButton("رجوع ↩️", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def premium_keyboard():
    """لوحة مفاتيح الاشتراكات"""
    keyboard = []
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        if plan_id == "free":
            continue
        text = f"{plan['name']} - {plan['price']} ⭐"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"buy_{plan_id}")])
    
    keyboard.append([InlineKeyboardButton("رجوع ↩️", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def wallet_topup_keyboard():
    """لوحة مفاتيح شراء العملات"""
    keyboard = []
    for amount, stars in WALLET_TOP_UP_OPTIONS.items():
        text = f"{amount} عملة = {stars} نجمة"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"topup_{amount}")])
    
    keyboard.append([InlineKeyboardButton("رجوع ↩️", callback_data="account")])
    return InlineKeyboardMarkup(keyboard)

def model_selection_keyboard(current_model=None):
    """لوحة اختيار النماذج"""
    keyboard = []
    for model in SUPPORTED_MODELS:
        # التحقق من توفر النموذج (سيتم استكماله لاحقًا)
        is_available = True  # مؤقت
        if is_available:
            text = model
            if current_model == model:
                text = f"✅ {model}"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"model_{model}")])
    
    keyboard.append([InlineKeyboardButton("رجوع ↩️", callback_data="settings")])
    return InlineKeyboardMarkup(keyboard)

def suno_keyboard():
    """لوحة مفاتيح Suno"""
    keyboard = [
        [InlineKeyboardButton("شراء حزمة Suno", callback_data="buy_suno")],
        [InlineKeyboardButton("بدء الإنشاء", callback_data="start_suno")],
        [InlineKeyboardButton("رجوع ↩️", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def search_keyboard():
    """لوحة مفاتيح البحث"""
    keyboard = [
        [InlineKeyboardButton("Deep Research", callback_data="model_deepresearch")],
        [InlineKeyboardButton("Perplexity", callback_data="model_perplexity")],
        [InlineKeyboardButton("Google", callback_data="model_google")],
        [InlineKeyboardButton("رجوع ↩️", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
