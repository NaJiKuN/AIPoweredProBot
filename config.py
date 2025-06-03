# -*- coding: utf-8 -*-
"""Configuration file for the AI Powered Pro Bot."""

import os

# Telegram Bot Token (Replace with your actual token)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8063450521:AAH4CjiHMgqEU1SZbY-9sdyr_VE2n_6Bz-g")

# Initial Admin User ID (Replace with the primary admin's Telegram ID)
# Ensure this is an integer
INITIAL_ADMIN_ID = int(os.environ.get("INITIAL_ADMIN_ID", "764559466"))

# Database URL (Using SQLite for simplicity)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///aipoweredprobot.db")

# Project Root Directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Add other configurations as needed
# For example, API keys can be loaded from environment variables or a secure vault
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyADLvBIJUxbvha5Vhjc_QqO3t5JDtVKrzQ") # Example, load securely
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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") # Example, load securely

# Default language
DEFAULT_LANGUAGE = "ar"

