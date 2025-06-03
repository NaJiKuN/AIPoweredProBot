from telegram import Update
from telegram.ext import CallbackContext

class Admin:
    def __init__(self, db):
        self.db = db
        self.db.add_admin(764559466)  # إضافة المسؤول الافتراضي

    def add_admin(self, update: Update, context: CallbackContext):
        if not self.db.is_admin(update.message.from_user.id):
            update.message.reply_text("غير مسموح.")
            return
        admin_id = int(context.args[0])
        self.db.add_admin(admin_id)
        update.message.reply_text(f"تمت إضافة المسؤول {admin_id}.")

    def add_api_key(self, update: Update, context: CallbackContext):
        if not self.db.is_admin(update.message.from_user.id):
            update.message.reply_text("غير مسموح.")
            return
        model_name = context.args[0]
        api_key = context.args[1]
        self.db.add_api_key(model_name, api_key)
        update.message.reply_text(f"تمت إضافة مفتاح API للنموذج {model_name}.")

    def remove_api_key(self, update: Update, context: CallbackContext):
        if not self.db.is_admin(update.message.from_user.id):
            update.message.reply_text("غير مسموح.")
            return
        model_name = context.args[0]
        self.db.remove_api_key(model_name)
        update.message.reply_text(f"تمت إزالة مفتاح API للنموذج {model_name}.")

    def add_package(self, update: Update, context: CallbackContext):
        if not self.db.is_admin(update.message.from_user.id):
            update.message.reply_text("غير مسموح.")
            return
        name = context.args[0]
        description = context.args[1]
        price = int(context.args[2])
        requests = int(context.args[3])
        duration = context.args[4]
        self.db.add_package(name, description, price, requests, duration)
        update.message.reply_text(f"تمت إضافة الحزمة {name}.")

    def broadcast(self, update: Update, context: CallbackContext):
        if not self.db.is_admin(update.message.from_user.id):
            update.message.reply_text("غير مسموح.")
            return
        message = " ".join(context.args)
        users = self.db.get_all_users()
        for user in users:
            context.bot.send_message(chat_id=user[0], text=message)
        update.message.reply_text("تم إرسال الرسالة لجميع المستخدمين.")

    def stats(self, update: Update, context: CallbackContext):
        if not self.db.is_admin(update.message.from_user.id):
            update.message.reply_text("غير مسموح.")
            return
        self.cursor.execute('SELECT COUNT(*) FROM users')
        total_users = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT COUNT(*) FROM purchases')
        total_purchases = self.cursor.fetchone()[0]
        update.message.reply_text(f"إحصائيات البوت:\nعدد المستخدمين: {total_users}\nعدد المشتريات: {total_purchases}")