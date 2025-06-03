# -*- coding: utf-8 -*-
import datetime
from functools import wraps
import database as db
import keyboards # Import keyboards to use callback prefixes
from telegram import Update
from telegram.ext import ContextTypes

# --- Decorators for Access Control ---
def admin_required(func):
    """Decorator to restrict access to admin users only."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not db.is_user_admin(user_id):
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمسؤولين فقط.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def user_registered(func):
    """Decorator to ensure the user exists in the database. Adds/updates user if not."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
             # Cannot proceed without user info (e.g., in channel posts without sender)
             print("Warning: Could not get user info from update.")
             return
             
        user_id = user.id
        # Add or update user info on every interaction
        db.add_or_update_user(user_id, user.username, user.first_name, user.last_name)
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- Subscription and Usage Check ---
async def check_and_consume_request(user_id: int, model_name: str, request_type: str = 'text', cost: int = 1, context: ContextTypes.DEFAULT_TYPE = None, update: Update = None) -> bool:
    """Checks if the user has enough requests and consumes them if possible.
    Sends a message to the user if they don't have enough requests.
    Returns True if the request can proceed, False otherwise.
    """
    # Admins have unlimited access
    if db.is_user_admin(user_id):
        db.log_usage(user_id, model_name, request_type, cost) # Log admin usage too
        return True

    can_consume = db.consume_request(user_id, model_name, request_type, cost)

    if not can_consume:
        if update and context:
            status = db.get_user_subscription_status(user_id)
            message = "⚠️ لقد استهلكت رصيدك المتاح لهذا اليوم أو لهذه الحزمة.\n"
            message += " يمكنك الحصول على المزيد من الطلبات عبر /premium."
            # Provide more specific info based on status if needed
            await update.effective_message.reply_text(message)
        return False
    return True

# --- Formatting Helpers ---
def format_account_status(user_id: int) -> str:
    """Formats the user's account status into a readable string."""
    status = db.get_user_subscription_status(user_id)
    if not status:
        return "لم يتم العثور على معلومات حسابك. يرجى المحاولة مرة أخرى أو استخدام /start."

    lines = [f"👤 **حساب المستخدم:** {user_id}"]

    if status["is_admin"]:
        lines.append("👑 **الحالة:** مسؤول (وصول غير محدود)")
    else:
        lines.append("**الاشتراك الحالي:**")
        is_subscribed = False
        today = datetime.date.today()

        # Premium Status
        if status["is_premium"]:
            is_subscribed = True
            expiry = status["premium_expiry"]
            days_left = (expiry - today).days
            lines.append(f"  💎 **مميز:** نشط حتى {expiry} ({days_left} يوم متبقي)")
            lines.append(f"     - الحد اليومي: {status["premium_daily_limit"]} طلب")
            lines.append(f"     - المتبقي اليوم: {status["premium_requests_left_today"]} طلب")

        # Free Trial Status
        if status["free_requests_left"] > 0 and status["free_requests_expiry"]:
            is_subscribed = True
            expiry = status["free_requests_expiry"]
            days_left = (expiry - today).days
            lines.append(f"  🎁 **مجاني:** {status["free_requests_left"]} طلب متبقي (ينتهي في {expiry}, {days_left} يوم متبقي)")

        # Package Status
        if status["packages"]:
            is_subscribed = True
            lines.append("  📦 **الحزم النشطة:**")
            for pkg in status["packages"]:
                # Make package type more readable
                pkg_name = pkg["type"].replace("_", " ").title()
                lines.append(f"     - {pkg_name}: {pkg["left"]}/{pkg["total"]} طلبات متبقية")

        if not is_subscribed:
            lines.append("  - لا يوجد اشتراك نشط حالياً.")
            lines.append("  - يمكنك الحصول على 50 طلبًا مجانيًا لمدة أسبوع بالضغط على زر 'مجاني' أو استكشاف خيارات /premium.") # TODO: Add free button logic

    # Preferred Model
    preferred_model = db.get_preferred_model(user_id)
    lines.append(f"\n🧠 **النموذج المفضل:** {preferred_model or 'غير محدد (استخدم /model)'}")

    return "\n".join(lines)

def format_api_key_list(keys):
    """Formats the list of API keys for admin display."""
    if not keys:
        return "لا توجد مفاتيح API مضافة حالياً."
    
    lines = ["🔑 **قائمة مفاتيح API:**\n"] 
    for key_id, service_name, api_key, is_active, added_by, added_at in keys:
        status = "🟢 نشط" if is_active else "🔴 غير نشط"
        mask = api_key[:4] + "..." + api_key[-4:] if api_key and len(api_key) > 8 else "[مفتاح غير صالح]"
        added_at_str = added_at.split('.')[0] if added_at else 'N/A' # Format timestamp
        lines.append(f"- `{key_id}`: **{service_name}** ({mask}) - {status}")
        # lines.append(f"    *أضيف بواسطة:* {added_by} *في:* {added_at_str}")
    return "\n".join(lines)

# --- Callback Data Parsing ---
def parse_callback_data(data: str):
    """Parses callback data string into prefix and value."""
    parts = data.split(":", 1)
    if len(parts) == 2:
        return parts[0] + ":", parts[1]
    return None, data # No prefix or malformed

# Add more utility functions as needed, e.g., for cleaning text, handling errors, etc.

