import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='bot.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscription TEXT,
                requests_left INTEGER,
                subscription_end DATE,
                preferred_model TEXT,
                invite_code TEXT,
                invites_count INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                model_name TEXT PRIMARY KEY,
                api_key TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                package_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                price INTEGER,
                requests INTEGER,
                duration TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package_id INTEGER,
                purchase_date DATE
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username):
        self.cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    def update_user_subscription(self, user_id, subscription, requests_left, subscription_end):
        self.cursor.execute('UPDATE users SET subscription = ?, requests_left = ?, subscription_end = ? WHERE user_id = ?', (subscription, requests_left, subscription_end, user_id))
        self.conn.commit()

    def update_preferred_model(self, user_id, model):
        self.cursor.execute('UPDATE users SET preferred_model = ? WHERE user_id = ?', (model, user_id))
        self.conn.commit()

    def update_requests_left(self, user_id, requests_left):
        self.cursor.execute('UPDATE users SET requests_left = ? WHERE user_id = ?', (requests_left, user_id))
        self.conn.commit()

    def update_invite_code(self, user_id, invite_code):
        self.cursor.execute('UPDATE users SET invite_code = ? WHERE user_id = ?', (invite_code, user_id))
        self.conn.commit()

    def update_invites_count(self, user_id, count):
        self.cursor.execute('UPDATE users SET invites_count = ? WHERE user_id = ?', (count, user_id))
        self.conn.commit()

    def add_admin(self, admin_id):
        self.cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (admin_id,))
        self.conn.commit()

    def is_admin(self, user_id):
        self.cursor.execute('SELECT * FROM admins WHERE admin_id = ?', (user_id,))
        return self.cursor.fetchone() is not None

    def add_api_key(self, model_name, api_key):
        self.cursor.execute('INSERT OR REPLACE INTO api_keys (model_name, api_key) VALUES (?, ?)', (model_name, api_key))
        self.conn.commit()

    def get_api_key(self, model_name):
        self.cursor.execute('SELECT api_key FROM api_keys WHERE model_name = ?', (model_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def remove_api_key(self, model_name):
        self.cursor.execute('DELETE FROM api_keys WHERE model_name = ?', (model_name,))
        self.conn.commit()

    def add_package(self, name, description, price, requests, duration):
        self.cursor.execute('INSERT INTO packages (name, description, price, requests, duration) VALUES (?, ?, ?, ?, ?)', (name, description, price, requests, duration))
        self.conn.commit()

    def get_packages(self):
        self.cursor.execute('SELECT * FROM packages')
        return self.cursor.fetchall()

    def get_package(self, package_id):
        self.cursor.execute('SELECT * FROM packages WHERE package_id = ?', (package_id,))
        return self.cursor.fetchone()

    def add_purchase(self, user_id, package_id):
        self.cursor.execute('INSERT INTO purchases (user_id, package_id, purchase_date) VALUES (?, ?, ?)', (user_id, package_id, datetime.now()))
        self.conn.commit()

    def has_purchased_this_month(self, user_id, package_id):
        current_month = datetime.now().strftime('%Y-%m')
        self.cursor.execute('SELECT * FROM purchases WHERE user_id = ? AND package_id = ? AND strftime("%Y-%m", purchase_date) = ?', (user_id, package_id, current_month))
        return self.cursor.fetchone() is not None

    def get_all_users(self):
        self.cursor.execute('SELECT user_id FROM users')
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()