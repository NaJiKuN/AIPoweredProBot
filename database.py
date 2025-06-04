# -*- coding: utf-8 -*-
import sqlite3
import datetime
import json
from config import DATABASE_NAME, ADMIN_IDS

# --- Database Initialization ---
def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Users Table
    cursor.execute(
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_admin INTEGER DEFAULT 0, 
        preferred_model TEXT,
        conversation_context TEXT, -- Store context as JSON or TEXT
        free_requests_left INTEGER DEFAULT 0,
        free_requests_expiry DATE,
        premium_expiry DATE,
        premium_daily_limit INTEGER DEFAULT 0, -- Max daily requests for premium
        premium_requests_today INTEGER DEFAULT 0, -- Requests made today for premium
        last_premium_reset DATE, -- Last date daily premium limit was reset
        wallet_balance REAL DEFAULT 0.0, -- User's wallet balance in coins/stars
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    )

    # Admins Table (Simplified, main check via config + user table flag)
    # We primarily use the is_admin flag in the users table, 
    # but this table can store additional admin info if needed later.
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS admins (
    #     user_id INTEGER PRIMARY KEY,
    #     added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # )
    # """)

    # API Keys Table
    cursor.execute(
    CREATE TABLE IF NOT EXISTS api_keys (
        key_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL UNIQUE, -- e.g., 'GPT-4o mini', 'Midjourney'
        api_key TEXT NOT NULL,
        is_active INTEGER DEFAULT 1, -- 1 for active, 0 for inactive
        added_by INTEGER, -- Admin user_id who added the key
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    )

    # User Packages Table (Tracks purchased one-time packages)
    cursor.execute(
    CREATE TABLE IF NOT EXISTS user_packages (
        package_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        package_type TEXT NOT NULL, -- e.g., 'CHATGPT_PLUS_50', 'MIDJOURNEY_100'
        requests_total INTEGER NOT NULL,
        requests_left INTEGER NOT NULL,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expiry_date DATE, -- Optional: if packages expire
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    )

    # Usage Stats Table (Optional, for detailed tracking)
    cursor.execute(
    CREATE TABLE IF NOT EXISTS usage_stats (
        usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        model_used TEXT NOT NULL,
        request_type TEXT NOT NULL, -- 'text', 'image', 'video', 'audio', 'search', 'file'
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cost INTEGER DEFAULT 1, -- How many 'requests' this action cost
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    )

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized successfully.")

# --- Helper Function ---
def _execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    Executes a given SQL query.
    
    Args:
        query (str): The SQL query to execute.
        params (tuple): Parameters for the SQL query.
        fetchone (bool): If True, fetches one row.
        fetchall (bool): If True, fetches all rows.
        commit (bool): If True, commits the transaction.

    Returns:
        Result of fetchone/fetchall or None.
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Consider logging the error
        return None
    finally:
        conn.close()

# --- User Management ---
def add_or_update_user(user_id, username, first_name, last_name):
    """Adds a new user or updates existing user's info. Sets admin flag if ID is in config."""
    is_admin = 1 if user_id in ADMIN_IDS else 0
    query = 
    INSERT INTO users (user_id, username, first_name, last_name, is_admin, preferred_model)
    VALUES (?, ?, ?, ?, ?, ?) 
    ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name,
        last_name=excluded.last_name,
        is_admin=excluded.is_admin
    
    # Set a default preferred model, e.g., from config
    from config import DEFAULT_MODEL
    _execute_query(query, (user_id, username, first_name, last_name, is_admin, DEFAULT_MODEL), commit=True)

def get_user(user_id):
    """Retrieves user data."""
    query = "SELECT * FROM users WHERE user_id = ?"
    return _execute_query(query, (user_id,), fetchone=True)

def is_user_admin(user_id):
    """Checks if a user has admin privileges."""
    user_data = get_user(user_id)
    return user_data and user_data[4] == 1 # Index 4 is is_admin

def get_all_user_ids():
    """Retrieves all user IDs."""
    query = "SELECT user_id FROM users"
    rows = _execute_query(query, fetchall=True)
    return [row[0] for row in rows] if rows else []

def update_user_context(user_id, context):
    """Updates the conversation context for a user."""
    context_str = json.dumps(context) if context is not None else None
    query = "UPDATE users SET conversation_context = ? WHERE user_id = ?"
    _execute_query(query, (context_str, user_id), commit=True)

def get_user_context(user_id):
    """Retrieves the conversation context for a user."""
    query = "SELECT conversation_context FROM users WHERE user_id = ?"
    result = _execute_query(query, (user_id,), fetchone=True)
    if result and result[0]:
        try:
            return json.loads(result[0])
        except json.JSONDecodeError:
            return None # Or handle corrupted context
    return None

def set_preferred_model(user_id, model_name):
    """Sets the user's preferred AI model."""
    query = "UPDATE users SET preferred_model = ? WHERE user_id = ?"
    _execute_query(query, (model_name, user_id), commit=True)

def get_preferred_model(user_id):
    """Gets the user's preferred AI model."""
    query = "SELECT preferred_model FROM users WHERE user_id = ?"
    result = _execute_query(query, (user_id,), fetchone=True)
    return result[0] if result else None

# --- Admin Management ---
def add_admin(user_id):
    """Grants admin privileges to a user."""
    query = "UPDATE users SET is_admin = 1 WHERE user_id = ?"
    _execute_query(query, (user_id,), commit=True)
    # Also add to config.ADMIN_IDS if managing dynamically? Or rely solely on DB?
    # For now, relies on DB flag.

def remove_admin(user_id):
    """Revokes admin privileges from a user."""
    # Prevent removing the initial admin(s) defined in config for safety?
    # if str(user_id) in INITIAL_ADMIN_IDS:
    #     print(f"Cannot remove initial admin {user_id} via command.")
    #     return False
    query = "UPDATE users SET is_admin = 0 WHERE user_id = ?"
    _execute_query(query, (user_id,), commit=True)
    return True

def get_admin_ids():
    """Gets all admin user IDs from the database."""
    query = "SELECT user_id FROM users WHERE is_admin = 1"
    rows = _execute_query(query, fetchall=True)
    return [row[0] for row in rows] if rows else []

# --- API Key Management ---
def add_api_key(service_name, api_key, added_by):
    """Adds a new API key."""
    query = "INSERT INTO api_keys (service_name, api_key, added_by) VALUES (?, ?, ?)"
    _execute_query(query, (service_name, api_key, added_by), commit=True)

def get_api_key(service_name):
    """Retrieves an active API key by service name."""
    query = "SELECT api_key FROM api_keys WHERE service_name = ? AND is_active = 1"
    result = _execute_query(query, (service_name,), fetchone=True)
    return result[0] if result else None

def get_all_api_keys():
    """Retrieves all API keys (active and inactive)."""
    query = "SELECT key_id, service_name, api_key, is_active, added_by, added_at FROM api_keys"
    return _execute_query(query, fetchall=True)

def update_api_key(key_id, new_api_key=None, new_service_name=None, is_active=None):
    """Updates an existing API key."""
    updates = []
    params = []
    if new_api_key is not None:
        updates.append("api_key = ?")
        params.append(new_api_key)
    if new_service_name is not None:
        updates.append("service_name = ?")
        params.append(new_service_name)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if is_active else 0)
    
    if not updates:
        return False # Nothing to update
        
    query = f"UPDATE api_keys SET {', '.join(updates)} WHERE key_id = ?"
    params.append(key_id)
    _execute_query(query, tuple(params), commit=True)
    return True

def remove_api_key(key_id):
    """Removes an API key by its ID."""
    query = "DELETE FROM api_keys WHERE key_id = ?"
    _execute_query(query, (key_id,), commit=True)

def get_active_service_names():
    """Gets the names of all services with active API keys."""
    query = "SELECT service_name FROM api_keys WHERE is_active = 1"
    rows = _execute_query(query, fetchall=True)
    return [row[0] for row in rows] if rows else []

# --- Subscription & Package Management ---

def grant_free_trial(user_id, requests=50, duration_days=7):
    """Grants the initial free trial."""
    expiry_date = datetime.date.today() + datetime.timedelta(days=duration_days)
    query = "UPDATE users SET free_requests_left = ?, free_requests_expiry = ? WHERE user_id = ?"
    _execute_query(query, (requests, expiry_date, user_id), commit=True)

def grant_premium(user_id, duration_days=30, daily_limit=100):
    """Grants premium subscription."""
    expiry_date = datetime.date.today() + datetime.timedelta(days=duration_days)
    query = "UPDATE users SET premium_expiry = ?, premium_daily_limit = ?, premium_requests_today = 0, last_premium_reset = ? WHERE user_id = ?"
    _execute_query(query, (expiry_date, daily_limit, datetime.date.today(), user_id), commit=True)

def add_package(user_id, package_type, requests_total):
    """Adds a purchased package to the user."""
    # Check if user already has an active package of the same type? Or allow stacking?
    # Current implementation allows stacking.
    query = "INSERT INTO user_packages (user_id, package_type, requests_total, requests_left) VALUES (?, ?, ?, ?)"
    _execute_query(query, (user_id, package_type, requests_total, requests_total), commit=True)

def get_user_subscription_status(user_id):
    """Checks the user's current subscription status and remaining requests."""
    user_data = get_user(user_id)
    if not user_data:
        return None

    status = {
        'user_id': user_id,
        'is_admin': user_data[4] == 1,
        'free_requests_left': 0,
        'free_requests_expiry': None,
        'is_premium': False,
        'premium_expiry': None,
        'premium_daily_limit': 0,
        'premium_requests_today': 0,
        'premium_requests_left_today': 0,
        'packages': []
    }

    today = datetime.date.today()

    # Check free trial
    free_expiry_str = user_data[8] # free_requests_expiry
    if free_expiry_str:
        free_expiry_datetime = datetime.datetime.strptime(free_expiry_str, '%Y-%m-%d')
        free_expiry_date = free_expiry_datetime.date()
        if free_expiry_date >= today:
            status['free_requests_left'] = user_data[7] # free_requests_left
            status['free_requests_expiry'] = free_expiry_date
        else:
             # Expired free trial - reset requests to 0 if not already done
             if user_data[7] > 0:
                 _execute_query("UPDATE users SET free_requests_left = 0 WHERE user_id = ?", (user_id,), commit=True)

    # Check premium
    premium_expiry_str = user_data[9] # premium_expiry
    if premium_expiry_str        premium_expiry_datetime = datetime.datetime.strptime(premium_expiry_str, %Y-%m-%d)
        premium_expiry_date = premium_expiry_datetime.date()
        if premium_expiry_date >= today:
            status['is_premium'] = True
            status['premium_expiry'] = premium_expiry_date
            status['premium_daily_limit'] = user_data[10]
            
            # Reset daily premium count if needed
            last_reset_str = user_data[12] # last_premium_reset
            if last_reset_str:
                last_reset_date = datetime.datetime.strptime(last_reset_str, '%Y-%m-%d').date()
                if last_reset_date < today:
                    _execute_query("UPDATE users SET premium_requests_today = 0, last_premium_reset = ? WHERE user_id = ?", (today, user_id), commit=True)
                    status['premium_requests_today'] = 0
                else:
                    status['premium_requests_today'] = user_data[11]
            else: # First time premium or reset date missing
                 _execute_query("UPDATE users SET premium_requests_today = 0, last_premium_reset = ? WHERE user_id = ?", (today, user_id), commit=True)
                 status['premium_requests_today'] = 0
                 
            status['premium_requests_left_today'] = max(0, status['premium_daily_limit'] - status['premium_requests_today'])
        else:
            # Expired premium - reset relevant fields if not already done
            if user_data[10] > 0: # Check if premium_daily_limit was set
                 _execute_query("UPDATE users SET premium_expiry = NULL, premium_daily_limit = 0, premium_requests_today = 0, last_premium_reset = NULL WHERE user_id = ?", (user_id,), commit=True)

    # Get active packages
    package_query = "SELECT package_id, package_type, requests_left, requests_total, purchase_date FROM user_packages WHERE user_id = ? AND requests_left > 0"
    # Add expiry check if packages expire: AND (expiry_date IS NULL OR expiry_date >= ?) 
    packages = _execute_query(package_query, (user_id,), fetchall=True)
    if packages:
        status['packages'] = [
            {'id': p[0], 'type': p[1], 'left': p[2], 'total': p[3], 'purchased': p[4]}
            for p in packages
        ]

    return status

# --- Usage Tracking ---
def log_usage(user_id, model_used, request_type, cost=1):
    """Logs a usage event."""
    query = "INSERT INTO usage_stats (user_id, model_used, request_type, cost) VALUES (?, ?, ?, ?)"
    _execute_query(query, (user_id, model_used, request_type, cost), commit=True)

def consume_request(user_id, model_name, request_type='text', cost=1):
    """Decrements the request count for the user based on their plan.
    Returns True if the request was successfully consumed, False otherwise.
    Handles Free, Premium, and Packages in order of priority.
    """
    status = get_user_subscription_status(user_id)
    if not status:
        return False # User not found

    # 1. Check Free Trial
    if status['free_requests_left'] >= cost:
        new_count = status['free_requests_left'] - cost
        query = "UPDATE users SET free_requests_left = ? WHERE user_id = ?"
        _execute_query(query, (new_count, user_id), commit=True)
        log_usage(user_id, model_name, request_type, cost)
        return True

    # 2. Check Premium Daily Limit
    if status['is_premium'] and status['premium_requests_left_today'] >= cost:
        new_count = status['premium_requests_today'] + cost
        query = "UPDATE users SET premium_requests_today = ? WHERE user_id = ?"
        _execute_query(query, (new_count, user_id), commit=True)
        log_usage(user_id, model_name, request_type, cost)
        return True

    # 3. Check Packages (Find a suitable package)
    # Determine package type based on model/request_type (this needs refinement)
    package_type_prefix = None
    if model_name.startswith('Claude'): package_type_prefix = 'CLAUDE'
    elif model_name.startswith('GPT-4') or model_name.startswith('OpenAI') or model_name == 'DALL-E 3': package_type_prefix = 'CHATGPT_PLUS'
    elif model_name in ['Midjourney V7', 'Flux']: package_type_prefix = 'MIDJOURNEY_FLUX'
    elif model_name in ['Kling 2.0', 'Pika AI']: package_type_prefix = 'VIDEO'
    elif model_name.startswith('Suno'): package_type_prefix = 'SUNO'
    # Add more mappings as needed

    if package_type_prefix:
        for package in status['packages']:
            if package['type'].startswith(package_type_prefix) and package['left'] >= cost:
                new_count = package['left'] - cost
                query = "UPDATE user_packages SET requests_left = ? WHERE package_id = ?"
                _execute_query(query, (new_count, package['id']), commit=True)
                log_usage(user_id, model_name, request_type, cost)
                return True
                
    # 4. Check Combo package (treat as premium for text, specific counts for others - complex logic needed here)
    # TODO: Implement Combo package logic if applicable after premium/standard packages fail.
    # This might involve checking specific counters associated with the combo plan.

    return False # No available requests

def get_usage_stats(user_id=None):
    """Retrieves usage statistics, optionally filtered by user."""
    if user_id:
        query = "SELECT model_used, request_type, COUNT(*) as count, SUM(cost) as total_cost FROM usage_stats WHERE user_id = ? GROUP BY model_used, request_type"
        return _execute_query(query, (user_id,), fetchall=True)
    else:
        query = "SELECT user_id, model_used, request_type, COUNT(*) as count, SUM(cost) as total_cost FROM usage_stats GROUP BY user_id, model_used, request_type"
        return _execute_query(query, fetchall=True)

# --- Initial Setup ---
if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Adding initial admins from config...")
    # Ensure initial admins from config are marked in the DB
    # This requires adding them as users first if they aren't already
    # For simplicity, we assume admins will use the bot and be added via add_or_update_user
    # We just ensure their flag is set correctly here.
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    for admin_id in ADMIN_IDS:
        # Check if user exists, if not, they need to /start the bot first.
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (admin_id,))
    conn.commit()
    conn.close()
    print("Database setup check complete.")




# --- Wallet Management ---
def get_wallet_balance(user_id):
    """Retrieves the user's wallet balance."""
    query = "SELECT wallet_balance FROM users WHERE user_id = ?"
    result = _execute_query(query, (user_id,), fetchone=True)
    # Ensure the column exists and result is not None before accessing index 0
    if result is not None and len(result) > 0:
        return result[0] if result[0] is not None else 0.0
    return 0.0 # Default to 0.0 if user not found or balance is NULL

def add_wallet_balance(user_id, amount):
    """Adds a specified amount to the user's wallet balance."""
    if amount <= 0:
        print("Amount to add must be positive.")
        return False
    query = "UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?"
    _execute_query(query, (amount, user_id), commit=True)
    return True

def deduct_wallet_balance(user_id, amount):
    """Deducts a specified amount from the user's wallet balance if sufficient funds exist."""
    if amount <= 0:
        print("Amount to deduct must be positive.")
        return False
    current_balance = get_wallet_balance(user_id)
    if current_balance >= amount:
        query = "UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ?"
        _execute_query(query, (amount, user_id), commit=True)
        return True
    else:
        print(f"Insufficient balance for user {user_id}. Required: {amount}, Available: {current_balance}")
        return False
