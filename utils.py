import hashlib
from collections import defaultdict

context_store = defaultdict(str)

def generate_invite_code(user_id):
    return hashlib.md5(str(user_id).encode()).hexdigest()[:8]

def get_invite_count(db, invite_code):
    users = db.get_all_users()
    count = sum(1 for user in users if db.get_user(user[0])[6] == invite_code)
    return count

def save_context(user_id, text):
    context_store[user_id] = text

def load_context(user_id):
    return context_store.get(user_id, "")

def clear_context(user_id):
    if user_id in context_store:
        del context_store[user_id]