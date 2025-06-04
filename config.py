# -*- coding: utf-8 -*-
import os

# Load environment variables or use defaults
TOKEN = os.getenv("BOT_TOKEN", "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g")
# Initial admin ID, can be a list of strings or integers
INITIAL_ADMIN_IDS = ["764559466"] 

# Database configuration
DATABASE_NAME = "aipoweredprobot.db"

# Other configurations can be added here
# For example, default model, API endpoints (placeholders for now)
DEFAULT_MODEL = "GPT-4o mini"

# Convert admin IDs to integers for consistency
try:
    ADMIN_IDS = [int(admin_id) for admin_id in INITIAL_ADMIN_IDS]
except ValueError:
    print("Error: One or more ADMIN_IDs are not valid integers. Please check INITIAL_ADMIN_IDS.")
    ADMIN_IDS = [] # Or handle the error as appropriate

if not TOKEN:
    raise ValueError("Bot token not found. Please set the BOT_TOKEN environment variable or add it directly to config.py")

print("Configuration loaded.")


PLISIO_SECRET_KEY = "Z468hRlbDPX7nIUdi2OYVsfAkTa9XUQNCwmxxAbyG9YVdCW4_tH6xPuVcaq8vPnO"

