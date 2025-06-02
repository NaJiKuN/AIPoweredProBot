# -*- coding: utf-8 -*-
"""وحدة التعامل مع قاعدة بيانات SQLite للبوت"""

import sqlite3
import os
import logging
from config import DATABASE_NAME, INITIAL_ADMIN_ID, INITIAL_API_KEYS

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """إنشاء وإرجاع اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # لإرجاع النتائج ككائنات شبيهة بالقاموس
    return conn

def initialize_database():
    """تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة"""
    db_exists = os.path.exists(DATABASE_NAME)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # إنشاء جدول المسؤولين
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
        """)
        logger.info("تم التحقق من/إنشاء جدول 'admins'.")

        # إنشاء جدول مفاتيح API
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            name TEXT PRIMARY KEY,
            key TEXT NOT NULL,
            type TEXT NOT NULL
        )
        """)
        logger.info("تم التحقق من/إنشاء جدول 'api_keys'.")

        # إذا كانت قاعدة البيانات جديدة، قم بإضافة المسؤول الأولي والمفاتيح الأولية
        if not db_exists:
            logger.info(f"قاعدة بيانات جديدة تم إنشاؤها. إضافة المسؤول الأولي: {INITIAL_ADMIN_ID}")
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (INITIAL_ADMIN_ID,))

            logger.info("إضافة مفاتيح API الأولية...")
            for name, data in INITIAL_API_KEYS.items():
                if data.get('key'): # تأكد من وجود المفتاح قبل إضافته
                    cursor.execute("INSERT OR IGNORE INTO api_keys (name, key, type) VALUES (?, ?, ?)",
                                     (name, data['key'], data['type']))
                    logger.info(f"تمت إضافة مفتاح API الأولي: {name} (النوع: {data['type']})")
                else:
                    logger.warning(f"لم يتم العثور على مفتاح API لـ {name} في الإعدادات أو متغيرات البيئة. تم تخطي الإضافة.")

        conn.commit()
        logger.info("تمت تهيئة قاعدة البيانات بنجاح.")

    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء تهيئة قاعدة البيانات: {e}")
        conn.rollback() # التراجع عن التغييرات في حالة حدوث خطأ
    finally:
        conn.close()

# --- دوال إدارة المسؤولين ---

def is_admin(user_id):
    """التحقق مما إذا كان معرف المستخدم ينتمي لمسؤول"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_admin(user_id):
    """إضافة مسؤول جديد"""
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"معرف المستخدم غير صالح للإضافة كمسؤول: {user_id}")
            return False, "معرف المستخدم يجب أن يكون رقماً صحيحاً."

    if is_admin(user_id):
        logger.warning(f"المستخدم {user_id} هو مسؤول بالفعل.")
        return False, "هذا المستخدم هو مسؤول بالفعل."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        logger.info(f"تمت إضافة المسؤول الجديد: {user_id}")
        return True, f"تمت إضافة المستخدم {user_id} كمسؤول بنجاح."
    except sqlite3.IntegrityError:
        # هذا لا يجب أن يحدث بسبب التحقق is_admin أعلاه، لكنه احتياطي
        logger.warning(f"المستخدم {user_id} موجود بالفعل في قاعدة بيانات المسؤولين (خطأ تكامل).")
        return False, "هذا المستخدم هو مسؤول بالفعل (خطأ تكامل)."
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء إضافة المسؤول {user_id}: {e}")
        conn.rollback()
        return False, f"حدث خطأ في قاعدة البيانات أثناء إضافة المسؤول: {e}"
    finally:
        conn.close()

def remove_admin(user_id):
    """إزالة مسؤول"""
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"معرف المستخدم غير صالح للإزالة: {user_id}")
            return False, "معرف المستخدم يجب أن يكون رقماً صحيحاً."

    if user_id == INITIAL_ADMIN_ID:
        logger.warning("محاولة إزالة المسؤول الأولي.")
        return False, "لا يمكن إزالة المسؤول الأولي."

    if not is_admin(user_id):
        logger.warning(f"محاولة إزالة مستخدم غير مسؤول: {user_id}")
        return False, "هذا المستخدم ليس مسؤولاً."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"تمت إزالة المسؤول: {user_id}")
            return True, f"تمت إزالة المسؤول {user_id} بنجاح."
        else:
            # هذا لا يجب أن يحدث بسبب التحقق is_admin أعلاه
            logger.warning(f"لم يتم العثور على المسؤول {user_id} للإزالة (ربما تم حذفه للتو؟).")
            return False, "لم يتم العثور على المسؤول في قاعدة البيانات."
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء إزالة المسؤول {user_id}: {e}")
        conn.rollback()
        return False, f"حدث خطأ في قاعدة البيانات أثناء إزالة المسؤول: {e}"
    finally:
        conn.close()

def list_admins():
    """الحصول على قائمة بجميع معرفات المسؤولين"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM admins")
        admins = [row['user_id'] for row in cursor.fetchall()]
        return admins
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء جلب قائمة المسؤولين: {e}")
        return []
    finally:
        conn.close()

# --- دوال إدارة مفاتيح API ---

def add_api_key(name, key, api_type):
    """إضافة أو تحديث مفتاح API"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # استخدام INSERT OR REPLACE لتحديث المفتاح إذا كان الاسم موجوداً بالفعل
        cursor.execute("INSERT OR REPLACE INTO api_keys (name, key, type) VALUES (?, ?, ?)",
                         (name, key, api_type.lower()))
        conn.commit()
        logger.info(f"تمت إضافة/تحديث مفتاح API: {name} (النوع: {api_type.lower()})")
        return True, f"تمت إضافة/تحديث مفتاح API '{name}' بنجاح."
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء إضافة/تحديث مفتاح API '{name}': {e}")
        conn.rollback()
        return False, f"حدث خطأ في قاعدة البيانات أثناء إضافة/تحديث المفتاح: {e}"
    finally:
        conn.close()

def remove_api_key(name):
    """إزالة مفتاح API باسمه"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM api_keys WHERE name = ?", (name,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"تمت إزالة مفتاح API: {name}")
            return True, f"تمت إزالة مفتاح API '{name}' بنجاح."
        else:
            logger.warning(f"لم يتم العثور على مفتاح API بالاسم '{name}' للإزالة.")
            return False, f"لم يتم العثور على مفتاح API بالاسم '{name}'."
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء إزالة مفتاح API '{name}': {e}")
        conn.rollback()
        return False, f"حدث خطأ في قاعدة البيانات أثناء إزالة المفتاح: {e}"
    finally:
        conn.close()

def get_api_key(name):
    """الحصول على بيانات مفتاح API باسمه"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT key, type FROM api_keys WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            return {'key': result['key'], 'type': result['type']}
        else:
            return None
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء جلب مفتاح API '{name}': {e}")
        return None
    finally:
        conn.close()

def list_api_keys():
    """الحصول على قائمة بجميع مفاتيح API (الاسم والنوع فقط)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, type FROM api_keys ORDER BY name")
        keys = [{'name': row['name'], 'type': row['type']} for row in cursor.fetchall()]
        return keys
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء جلب قائمة مفاتيح API: {e}")
        return []
    finally:
        conn.close()

def get_api_key_by_type(api_type):
    """الحصول على أول مفتاح API متاح لنوع معين"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT key FROM api_keys WHERE type = ? LIMIT 1", (api_type.lower(),))
        result = cursor.fetchone()
        if result:
            return result['key']
        else:
            logger.warning(f"لم يتم العثور على مفتاح API للنوع: {api_type.lower()}")
            return None
    except sqlite3.Error as e:
        logger.error(f"حدث خطأ أثناء جلب مفتاح API للنوع '{api_type.lower()}': {e}")
        return None
    finally:
        conn.close()

# قم بتهيئة قاعدة البيانات عند استيراد الوحدة لأول مرة
if __name__ != "__main__":
    initialize_database()

