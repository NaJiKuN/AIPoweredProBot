from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database as db

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("حسابي /account", callback_data="account")],
        [InlineKeyboardButton("الاشتراك المميز /premium", callback_data="premium")],
        [InlineKeyboardButton("إنشاء الصور /photo", callback_data="photo")],
        [InlineKeyboardButton("توليد الفيديو /video", callback_data="video")],
        [InlineKeyboardButton("توليد الأغاني /suno", callback_data="suno")],
        [InlineKeyboardButton("البحث على الإنترنت /s", callback_data="search")],
        [InlineKeyboardButton("الإعدادات /settings", callback_data="settings")]
    ])

def buy_balance_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("100 عملة = 110 نجمة", callback_data="buy_balance_100")],
        [InlineKeyboardButton("200 عملة = 220 نجمة", callback_data="buy_balance_200")],
        [InlineKeyboardButton("350 عملة = 360 نجمة", callback_data="buy_balance_350")],
        [InlineKeyboardButton("500 عملة = 510 نجمة", callback_data="buy_balance_500")],
        [InlineKeyboardButton("1000 عملة = 1000 نجمة", callback_data="buy_balance_1000")]
    ])

def premium_packages_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الاشتراك المميز | شهري", callback_data="premium_monthly")],
        [InlineKeyboardButton("الاشتراك المميز X2 | شهري", callback_data="premium_x2")],
        [InlineKeyboardButton("CHATGPT PLUS | حزم", callback_data="chatgpt_packages")],
        [InlineKeyboardButton("CLAUDE | حزم", callback_data="claude_packages")],
        [InlineKeyboardButton("MIDJOURNEY & FLUX | حزم", callback_data="midjourney_packages")],
        [InlineKeyboardButton("فيديو | حزم", callback_data="video_packages")],
        [InlineKeyboardButton("أغاني SUNO | حزم", callback_data="suno_packages")],
        [InlineKeyboardButton("كومبو | شهري 🔥", callback_data="combo_package")]
    ])

def models_keyboard(user_id):
    active_models = db.get_active_models()
    selected_model = db.get_selected_model(user_id)
    
    buttons = []
    for model in active_models:
        prefix = "✅ " if model == selected_model else ""
        buttons.append([InlineKeyboardButton(f"{prefix}{model}", callback_data=f"select_model_{model}")])
    
    buttons.append([InlineKeyboardButton("رجوع", callback_data="back_to_settings")])
    return InlineKeyboardMarkup(buttons)

# ... (لوحات مفاتيح أخرى)
