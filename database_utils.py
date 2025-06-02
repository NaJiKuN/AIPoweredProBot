# -*- coding: utf-8 -*-
import sqlite3
import logging
from datetime import datetime, timedelta
from config import DATABASE_NAME, ADMIN_IDS

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # للوصول إلى الأعمدة بالأسماء
    return conn

# --- دوال إدارة المستخدمين --- #

def add_or_update_user(user_id, username, first_name, last_name):
    """إضافة مستخدم جديد أو تحديث بيانات مستخدم موجود."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if user is None:
            # مستخدم جديد، احصل على تفاصيل الخطة المجانية
            cursor.execute("SELECT request_limit, limit_period FROM subscriptions WHERE plan_name = 'free'")
            free_plan = cursor.fetchone()
            requests_remaining = free_plan['request_limit'] if free_plan else 50 # قيمة افتراضية إذا لم توجد الخطة
            limit_period = free_plan['limit_period'] if free_plan else 'weekly'
            
            # تحديد تاريخ انتهاء الصلاحية الأسبوعي للخطة المجانية (مثال)
            expiry_date = datetime.now() + timedelta(weeks=1) if limit_period == 'weekly' else None
            
            cursor.execute("INSERT INTO users (user_id, username, first_name, last_name, requests_remaining, subscription_expiry) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, username, first_name, last_name, requests_remaining, expiry_date))
            logger.info(f"مستخدم جديد أضيف: {user_id} ({username})")
        else:
            # تحديث بيانات المستخدم إذا تغيرت
            cursor.execute("UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE user_id = ?",
                           (username, first_name, last_name, user_id))
            # لا تقم بتحديث الاشتراك أو عدد الطلبات هنا، سيتم التعامل معها بشكل منفصل
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند إضافة/تحديث المستخدم {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user(user_id):
    """الحصول على بيانات المستخدم."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_context(user_id, context):
    """تحديث سياق محادثة المستخدم."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET context = ? WHERE user_id = ?", (context, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند تحديث سياق المستخدم {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_user_context(user_id):
    """حذف سياق محادثة المستخدم."""
    update_user_context(user_id, None)

def get_user_context(user_id):
    """الحصول على سياق محادثة المستخدم."""
    user = get_user(user_id)
    return user['context'] if user else None

def update_selected_model(user_id, model_name):
    """تحديث النموذج المختار للمستخدم."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET selected_model = ? WHERE user_id = ?", (model_name, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند تحديث النموذج المختار للمستخدم {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_selected_model(user_id):
    """الحصول على النموذج المختار للمستخدم."""
    user = get_user(user_id)
    return user['selected_model'] if user else 'GPT-4o mini' # قيمة افتراضية

# --- دوال إدارة المسؤولين --- #

def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مسؤولاً."""
    # التحقق من قائمة المسؤولين في ملف الإعدادات أولاً
    if str(user_id) in ADMIN_IDS:
        return True
    # التحقق من قاعدة البيانات (إذا تمت إضافة مسؤولين ديناميكيًا)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    is_admin_db = cursor.fetchone() is not None
    conn.close()
    return is_admin_db

def add_admin(user_id):
    """إضافة مسؤول جديد."""
    if is_admin(user_id):
        return False # المسؤول موجود بالفعل
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        logger.info(f"تمت إضافة المسؤول: {user_id}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"المسؤول {user_id} موجود بالفعل في قاعدة البيانات.")
        return False # قد يكون موجودًا بالفعل
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند إضافة المسؤول {user_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_admin(user_id):
    """إزالة مسؤول."""
    # لا تسمح بإزالة المسؤولين من ملف الإعدادات عبر البوت
    if str(user_id) in ADMIN_IDS:
        logger.warning(f"محاولة إزالة مسؤول محدد في ملف الإعدادات: {user_id}")
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        if deleted:
            logger.info(f"تمت إزالة المسؤول: {user_id}")
        return deleted
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند إزالة المسؤول {user_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_all_admins():
    """الحصول على قائمة بجميع معرفات المسؤولين (من قاعدة البيانات)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins_db = [row['user_id'] for row in cursor.fetchall()]
    conn.close()
    # دمج المسؤولين من ملف الإعدادات وقاعدة البيانات
    all_admin_ids = set(int(admin_id) for admin_id in ADMIN_IDS if admin_id.isdigit()) # تحويل إلى أرقام صحيحة
    all_admin_ids.update(admins_db)
    return list(all_admin_ids)

# --- دوال إدارة مفاتيح API --- #

def add_api_key(service_name, api_key, display_name):
    """إضافة أو تحديث مفتاح API لخدمة معينة."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO api_keys (service_name, api_key, display_name) VALUES (?, ?, ?)",
                       (service_name, api_key, display_name))
        conn.commit()
        logger.info(f"تمت إضافة/تحديث مفتاح API للخدمة: {service_name}")
        return True
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند إضافة/تحديث مفتاح API للخدمة {service_name}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_api_key(service_name):
    """إزالة مفتاح API لخدمة معينة."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM api_keys WHERE service_name = ?", (service_name,))
        deleted = cursor.rowcount > 0
        conn.commit()
        if deleted:
            logger.info(f"تمت إزالة مفتاح API للخدمة: {service_name}")
        return deleted
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند إزالة مفتاح API للخدمة {service_name}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_api_key(service_name):
    """الحصول على مفتاح API لخدمة معينة."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT api_key FROM api_keys WHERE service_name = ?", (service_name,))
    result = cursor.fetchone()
    conn.close()
    return result['api_key'] if result else None

def get_all_api_keys():
    """الحصول على قائمة بجميع مفاتيح API المسجلة."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT service_name, display_name FROM api_keys")
    keys = cursor.fetchall()
    conn.close()
    return keys

# --- دوال إدارة الاشتراكات والطلبات --- #

def check_and_decrement_requests(user_id):
    """التحقق من رصيد الطلبات المتبقية للمستخدم وتحديثه."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT requests_remaining, subscription_type, subscription_expiry FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            logger.warning(f"المستخدم {user_id} غير موجود عند محاولة التحقق من الطلبات.")
            return False # المستخدم غير موجود

        requests_remaining = user_data['requests_remaining']
        subscription_type = user_data['subscription_type']
        expiry_date = user_data['subscription_expiry']

        # التحقق من انتهاء صلاحية الاشتراك المميز
        if subscription_type == 'premium' and expiry_date and datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S.%f') < datetime.now():
            # إعادة المستخدم إلى الخطة المجانية
            cursor.execute("SELECT request_limit, limit_period FROM subscriptions WHERE plan_name = 'free'")
            free_plan = cursor.fetchone()
            new_requests = free_plan['request_limit'] if free_plan else 50
            new_expiry = datetime.now() + timedelta(weeks=1) if free_plan and free_plan['limit_period'] == 'weekly' else None
            cursor.execute("UPDATE users SET subscription_type = 'free', requests_remaining = ?, subscription_expiry = ? WHERE user_id = ?",
                           (new_requests, new_expiry, user_id))
            conn.commit()
            logger.info(f"انتهت صلاحية الاشتراك المميز للمستخدم {user_id}. تم إعادته للخطة المجانية.")
            return False # لا يمكن إجراء الطلب الآن، يحتاج المستخدم إلى المحاولة مرة أخرى
        
        # التحقق من انتهاء صلاحية الخطة المجانية الأسبوعية (إذا كانت أسبوعية)
        if subscription_type == 'free' and expiry_date and datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S.%f') < datetime.now():
             cursor.execute("SELECT request_limit, limit_period FROM subscriptions WHERE plan_name = 'free'")
             free_plan = cursor.fetchone()
             new_requests = free_plan['request_limit'] if free_plan else 50
             new_expiry = datetime.now() + timedelta(weeks=1) if free_plan and free_plan['limit_period'] == 'weekly' else None
             cursor.execute("UPDATE users SET requests_remaining = ?, subscription_expiry = ? WHERE user_id = ?", (new_requests, new_expiry, user_id))
             requests_remaining = new_requests # تحديث الرصيد الحالي
             logger.info(f"تم تجديد رصيد الخطة المجانية الأسبوعية للمستخدم {user_id}.")

        if requests_remaining > 0:
            cursor.execute("UPDATE users SET requests_remaining = requests_remaining - 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return True # يمكن إجراء الطلب
        else:
            logger.info(f"نفذ رصيد الطلبات للمستخدم {user_id}.")
            return False # نفذ الرصيد

    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند التحقق/تحديث رصيد المستخدم {user_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- دوال أخرى --- #

def get_all_user_ids():
    """الحصول على قائمة بجميع معرفات المستخدمين."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row['user_id'] for row in cursor.fetchall()]
    conn.close()
    return user_ids

def get_bot_stats():
    """الحصول على إحصائيات استخدام البوت."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_type = 'premium'")
        premium_users = cursor.fetchone()[0]
        # يمكن إضافة إحصائيات أخرى مثل إجمالي الطلبات المنفذة إذا تم تسجيلها
        conn.close()
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "free_users": total_users - premium_users
        }
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات عند جلب الإحصائيات: {e}")
        conn.close()
        return None


