# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database as db # Assuming database.py is in the same directory or accessible

# --- Constants for Callback Data ---
# Using prefixes to categorize callbacks
CB_PREFIX_PREMIUM = "prem:"
CB_PREFIX_PACKAGE = "pkg:"
CB_PREFIX_MODEL = "model:"
CB_PREFIX_ADMIN = "admin:"
CB_PREFIX_ACTION = "act:"

# --- Helper Function --- 
def get_active_models():
    """Gets a set of service names that have active API keys."""
    # This function assumes service names in the DB match the model names used in buttons/logic
    # e.g., 'GPT-4o mini', 'Midjourney', 'Claude 4 Sonnet + Thinking'
    return set(db.get_active_service_names())

# --- Main Menu / Start Keyboard ---
def create_start_keyboard():
    """Creates the keyboard shown with the /start command."""
    keyboard = [
        [InlineKeyboardButton("⭐ الاشتراك المميز (/premium)", callback_data=CB_PREFIX_ACTION + "show_premium")],
        [InlineKeyboardButton("⚙️ الإعدادات (/settings)", callback_data=CB_PREFIX_ACTION + "show_settings")],
        [InlineKeyboardButton("👤 حسابي (/account)", callback_data=CB_PREFIX_ACTION + "show_account")],
        [InlineKeyboardButton("❓ المساعدة (/help)", callback_data=CB_PREFIX_ACTION + "show_help")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Premium Subscription / Package Selection Keyboard ---
def create_premium_keyboard():
    """Creates the keyboard for the /premium command, showing available options."""
    active_models = get_active_models()
    keyboard = []
    keyboard.append([InlineKeyboardButton("اختر خدمة للشراء:", callback_data="no_action")]) # Non-clickable title

    # Button 1: Premium Monthly
    # Requires at least one of the included models to be active
    premium_models = {"GPT-4.1 mini", "GPT-4o mini", "DeepSeek-V3", "Gemini 2.5 Flash", "Perplexity", "GPT-4o Images", "Midjourney", "Flux"}
    if any(model in active_models for model in premium_models):
        keyboard.append([InlineKeyboardButton("💎 الاشتراك المميز | شهري (170 ⭐)", callback_data=CB_PREFIX_PREMIUM + "premium_monthly")])

    # Button 2: Premium X2 Monthly
    # Requires the same models as Premium Monthly
    if any(model in active_models for model in premium_models):
        keyboard.append([InlineKeyboardButton("💎💎 الاشتراك المميز X2 | شهري (320 ⭐)", callback_data=CB_PREFIX_PREMIUM + "premium_x2_monthly")])

    # Button 3: ChatGPT Plus Packages
    # Requires at least one of the specific OpenAI models to be active
    chatgpt_models = {"OpenAI o3", "OpenAI o4-mini", "GPT-4.5", "GPT-4.1", "GPT-4o", "DALL-E 3"}
    if any(model in active_models for model in chatgpt_models):
        keyboard.append([InlineKeyboardButton("💬 CHATGPT PLUS | حزم", callback_data=CB_PREFIX_ACTION + "show_chatgpt_packages")])

    # Button 4: Claude Packages
    # Requires Claude model to be active
    claude_models = {"Claude 4 Sonnet + Thinking"}
    if any(model in active_models for model in claude_models):
        keyboard.append([InlineKeyboardButton("☁️ CLAUDE | حزم", callback_data=CB_PREFIX_ACTION + "show_claude_packages")])

    # Button 5: Midjourney & Flux Packages
    # Requires Midjourney or Flux to be active
    mj_flux_models = {"Midjourney V7", "Flux"}
    if any(model in active_models for model in mj_flux_models):
        keyboard.append([InlineKeyboardButton("🖼️ MIDJOURNEY & FLUX | حزم", callback_data=CB_PREFIX_ACTION + "show_mjflux_packages")])

    # Button 6: Video Packages
    # Requires Kling or Pika to be active
    video_models = {"Kling 2.0", "Pika AI"}
    if any(model in active_models for model in video_models):
         # IMPORTANT: Check if video generation is enabled for the user/instance
         # For now, assuming it might be available if keys are present
         # Add a check here later if needed based on user permissions or system capability
        keyboard.append([InlineKeyboardButton("🎬 فيديو | حزم", callback_data=CB_PREFIX_ACTION + "show_video_packages")])

    # Button 7: Suno Packages
    # Requires Suno to be active
    suno_models = {"Suno V4.5"}
    if any(model in active_models for model in suno_models):
        keyboard.append([InlineKeyboardButton("🎸 أغاني SUNO | حزم", callback_data=CB_PREFIX_ACTION + "show_suno_packages")])

    # Button 8: Combo Monthly
    # Requires models from Premium, ChatGPT Plus, and Midjourney/Flux
    combo_req_premium = any(model in active_models for model in premium_models)
    combo_req_chatgpt = any(model in active_models for model in chatgpt_models)
    combo_req_mjflux = any(model in active_models for model in mj_flux_models)
    if combo_req_premium and combo_req_chatgpt and combo_req_mjflux:
        keyboard.append([InlineKeyboardButton("🔥 كومبو | شهري (580 ⭐)", callback_data=CB_PREFIX_PREMIUM + "combo_monthly")])

    # Add a back button if needed, e.g., back to main menu
    # keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=CB_PREFIX_ACTION + "main_menu")])

    # If no premium options are available at all
    if len(keyboard) <= 1: # Only the title row
        keyboard.append([InlineKeyboardButton("لا توجد اشتراكات متاحة حالياً.", callback_data="no_action")])

    return InlineKeyboardMarkup(keyboard)

# --- Package Size Selection Keyboards ---
def create_package_selection_keyboard(package_type):
    """Creates a keyboard to select the size for a specific package type."""
    keyboard = []
    options = []
    prefix = CB_PREFIX_PACKAGE + package_type + ":"

    if package_type == "chatgpt":
        keyboard.append([InlineKeyboardButton("اختر عدد طلبات ChatGPT Plus:", callback_data="no_action")])
        options = [
            ("50 طلب", "50", "175"),
            ("100 طلب", "100", "320"),
            ("200 طلب", "200", "620"),
            ("500 طلب", "500", "1550"),
        ]
    elif package_type == "claude":
        keyboard.append([InlineKeyboardButton("اختر عدد طلبات Claude:", callback_data="no_action")])
        options = [
            ("100 طلب", "100", "175"),
            ("200 طلب", "200", "320"),
            ("500 طلب", "500", "720"),
            ("1000 طلب", "1000", "1200"),
        ]
    elif package_type == "mjflux":
        keyboard.append([InlineKeyboardButton("اختر عدد طلبات صور Midjourney & Flux:", callback_data="no_action")])
        options = [
            ("50 صورة", "50", "175"),
            ("100 صورة", "100", "320"),
            ("200 صورة", "200", "620"),
            ("500 صورة", "500", "1400"),
        ]
    elif package_type == "video":
        keyboard.append([InlineKeyboardButton("اختر عدد طلبات إنشاء الفيديو:", callback_data="no_action")])
        options = [
            ("10 إنشاء", "10", "375"),
            ("20 إنشاء", "20", "730"),
            ("50 إنشاء", "50", "1750"),
        ]
    elif package_type == "suno":
        keyboard.append([InlineKeyboardButton("اختر عدد طلبات إنشاء الأغاني:", callback_data="no_action")])
        options = [
            ("20 إنشاء", "20", "175"),
            ("50 إنشاء", "50", "425"),
            ("100 إنشاء", "100", "780"),
        ]
    else:
        return None # Unknown package type

    for text, req_count, price in options:
        button_text = f"حزمة {text} بسعر: {price} ⭐"
        callback_d = prefix + req_count # e.g., pkg:chatgpt:100
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_d)])

    keyboard.append([InlineKeyboardButton("🔙 رجوع إلى الاشتراكات", callback_data=CB_PREFIX_ACTION + "show_premium")])
    return InlineKeyboardMarkup(keyboard)

# --- Model Selection Keyboard (/model or /settings) ---
def create_model_selection_keyboard(user_id):
    """Creates keyboard for selecting the preferred AI model.
       Shows only models the user potentially has access to based on active keys and basic plans.
       Actual access check happens during request.
    """
    active_models = get_active_models()
    user_status = db.get_user_subscription_status(user_id)
    current_model = db.get_preferred_model(user_id)
    keyboard = []
    keyboard.append([InlineKeyboardButton("اختر نموذج الذكاء الاصطناعي المفضل:", callback_data="no_action")])

    available_models_for_user = set()

    # Free models (always potentially available if keys exist)
    free_models = {"GPT-4.1 mini", "GPT-4o mini", "DeepSeek-V3", "Gemini 2.5 Flash", "Perplexity", "GPT-4o Images"}
    available_models_for_user.update(active_models.intersection(free_models))

    # Premium models (potentially available if keys exist - actual check later)
    premium_models = {"Midjourney", "Flux"} # Add others covered by premium base
    available_models_for_user.update(active_models.intersection(premium_models))

    # Package-specific models (potentially available if keys exist)
    package_models = {
        "OpenAI o3", "OpenAI o4-mini", "GPT-4.5", "GPT-4.1", "GPT-4o", "DALL-E 3", # ChatGPT Plus
        "Claude 4 Sonnet + Thinking", # Claude
        "Midjourney V7", # MJ/Flux specific
        "Kling 2.0", "Pika AI", # Video
        "Suno V4.5" # Suno
    }
    available_models_for_user.update(active_models.intersection(package_models))

    # Sort models for consistent display
    sorted_models = sorted(list(available_models_for_user))

    for model_name in sorted_models:
        prefix = "✅ " if model_name == current_model else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{model_name}", callback_data=CB_PREFIX_MODEL + model_name)])

    if not available_models_for_user:
        keyboard.append([InlineKeyboardButton("لا توجد نماذج متاحة حالياً.", callback_data="no_action")])

    # Add back button maybe?
    # keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=CB_PREFIX_ACTION + "show_settings")])

    return InlineKeyboardMarkup(keyboard)

# --- Admin Keyboard --- (Example)
def create_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔑 إدارة مفاتيح API", callback_data=CB_PREFIX_ADMIN + "manage_keys")],
        [InlineKeyboardButton("👥 إدارة المسؤولين", callback_data=CB_PREFIX_ADMIN + "manage_admins")],
        [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data=CB_PREFIX_ADMIN + "view_stats")],
        [InlineKeyboardButton("📢 إرسال رسالة للجميع", callback_data=CB_PREFIX_ADMIN + "broadcast")],
        # Add more admin actions here
    ]
    return InlineKeyboardMarkup(keyboard)

# --- API Key Management Keyboard --- (Example)
def create_api_key_management_keyboard():
    keys = db.get_all_api_keys()
    keyboard = [[InlineKeyboardButton("إدارة مفاتيح API:", callback_data="no_action")]]
    if keys:
        for key_id, service_name, api_key_masked, is_active, _, _ in keys:
            status = "🟢 نشط" if is_active else "🔴 غير نشط"
            mask = api_key_masked[:4] + "..." + api_key_masked[-4:] if api_key_masked else "[لا يوجد مفتاح]"
            keyboard.append([
                InlineKeyboardButton(f"{service_name} ({mask}) - {status}", callback_data=f"{CB_PREFIX_ADMIN}key_details:{key_id}")
            ])
    keyboard.append([InlineKeyboardButton("➕ إضافة مفتاح جديد", callback_data=CB_PREFIX_ADMIN + "add_key_start")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data=CB_PREFIX_ADMIN + "main_menu")]) # Or back to admin menu
    return InlineKeyboardMarkup(keyboard)

# Add more keyboards as needed (e.g., for confirming actions, specific settings)

