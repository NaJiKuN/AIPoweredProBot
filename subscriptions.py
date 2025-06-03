from datetime import datetime, timedelta

class Subscriptions:
    def __init__(self, db):
        self.db = db
        self.initialize_packages()

    def initialize_packages(self):
        packages = [
            ("الاشتراك المميز | شهري", "100 طلب يوميًا + Midjourney وFlux", 170, 100, "شهري"),
            ("الاشتراك المميز X2 | شهري", "200 طلب يوميًا + Midjourney وFlux", 320, 200, "شهري"),
            ("CHATGPT PLUS | 50 طلب", "50 طلبًا", 175, 50, "حزمة"),
            ("CHATGPT PLUS | 100 طلب", "100 طلبًا", 320, 100, "حزمة"),
            ("CHATGPT PLUS | 200 طلب", "200 طلبًا", 620, 200, "حزمة"),
            ("CHATGPT PLUS | 500 طلب", "500 طلبًا", 1550, 500, "حزمة"),
            ("CLAUDE | 100 طلب", "100 طلبًا", 175, 100, "حزمة"),
            ("CLAUDE | 200 طلب", "200 طلبًا", 320, 200, "حزمة"),
            ("CLAUDE | 500 طلب", "500 طلبًا", 720, 500, "حزمة"),
            ("CLAUDE | 1000 طلب", "1000 طلبًا", 1200, 1000, "حزمة"),
            ("MIDJOURNEY & FLUX | 50 صورة", "50 صورة", 175, 50, "حزمة"),
            ("MIDJOURNEY & FLUX | 100 صورة", "100 صورة", 320, 100, "حزمة"),
            ("MIDJOURNEY & FLUX | 200 صورة", "200 صورة", 620, 200, "حزمة"),
            ("MIDJOURNEY & FLUX | 500 صورة", "500 صورة", 1400, 500, "حزمة"),
            ("فيديو | 10 طلب", "10 فيديوهات", 375, 10, "حزمة"),
            ("فيديو | 20 طلب", "20 فيديو", 730, 20, "حزمة"),
            ("فيديو | 50 طلب", "50 فيديو", 1750, 50, "حزمة"),
            ("أغاني SUNO | 20 طلب", "20 أغنية", 175, 20, "حزمة"),
            ("أغاني SUNO | 50 طلب", "50 أغنية", 425, 50, "حزمة"),
            ("أغاني SUNO | 100 طلب", "100 أغنية", 780, 100, "حزمة"),
            ("كومبو | شهري", "100 طلب يوميًا + 100 ChatGPT + 100 صورة", 580, 100, "شهري")
        ]
        for name, desc, price, requests, duration in packages:
            if not self.db.get_package_by_name(name):
                self.db.add_package(name, desc, price, requests, duration)

    def get_free_subscription(self):
        return {
            'name': 'مجاني',
            'requests': 50,
            'duration': 'أسبوع',
            'models': ['GPT-4.1 mini', 'GPT-4o mini', 'DeepSeek-V3', 'Gemini 2.5 Flash', 'Perplexity', 'GPT-4o Images']
        }

    def get_premium_packages(self):
        return self.db.get_packages()

    def apply_free_subscription(self, user_id):
        subscription = self.get_free_subscription()
        end_date = datetime.now() + timedelta(days=7)
        user = self.db.get_user(user_id)
        if user[2] == "مجاني" and user[4] > datetime.now().strftime('%Y-%m-%d'):
            return "لديك اشتراك مجاني ساري بالفعل."
        self.db.update_user_subscription(user_id, subscription['name'], subscription['requests'], end_date)
        return "تم تفعيل الاشتراك المجاني: 50 طلبًا لمدة أسبوع."

    def purchase_package(self, user_id, package_id):
        package = self.db.get_package(package_id)
        if not package:
            return "الحزمة غير موجودة."
        if self.db.has_purchased_this_month(user_id, package_id) and package[5] == "شهري":
            return "لا يمكنك شراء هذه الحزمة أكثر من مرة في الشهر."
        
        user = self.db.get_user(user_id)
        current_requests = user[3] if user else 0
        if package[5] == "شهري":
            end_date = datetime.now() + timedelta(days=30)
        else:
            end_date = None
        total_requests = current_requests + package[4]
        self.db.update_user_subscription(user_id, package[1], total_requests, end_date)
        self.db.add_purchase(user_id, package_id)
        invites_count = self.db.get_user(user_id)[7]
        discount = 0
        if invites_count >= 1000:
            discount = 0.20
        elif invites_count >= 500:
            discount = 0.10
        final_price = package[3] * (1 - discount)
        return f"تم شراء الحزمة {package[1]} بنجاح! السعر بعد الخصم: {final_price:.2f} ⭐"