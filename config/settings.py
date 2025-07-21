"""
Configuration settings for Anuj Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'anuj_assistant_bot')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY')

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/anuj_bot.db')

# File Storage Configuration
FILES_DIR = os.getenv('FILES_DIR', 'files/')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '50')) * 1024 * 1024  # 50MB default

# Channel Configuration (for file storage)
FILE_STORAGE_CHANNEL_ID = os.getenv('FILE_STORAGE_CHANNEL_ID', '')
ADMIN_USER_IDS = [int(x) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x]

# Quiz Configuration
MAX_QUIZ_QUESTIONS = int(os.getenv('MAX_QUIZ_QUESTIONS', '10'))
QUIZ_TIME_LIMIT = int(os.getenv('QUIZ_TIME_LIMIT', '300'))  # 5 minutes

# Image Processing Configuration
MAX_IMAGE_SIZE = (1920, 1080)
SOLUTION_FONT_SIZE = 24
SOLUTION_COLOR = (255, 0, 0)  # Red color for solutions

# Memory Configuration
MAX_HISTORY_MESSAGES = int(os.getenv('MAX_HISTORY_MESSAGES', '100'))
CONTEXT_WINDOW_SIZE = int(os.getenv('CONTEXT_WINDOW_SIZE', '10'))

# Bot Personality Configuration
BOT_NAME = "Anuj"
BOT_PERSONALITY = {
    'greeting_style': 'friendly_hindi_english',
    'response_style': 'helpful_enthusiastic',
    'emoji_usage': True,
    'language_mix': 'hindi_english'
}

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/anuj_bot.log')

# Create necessary directories
os.makedirs('database', exist_ok=True)
os.makedirs('files', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Validation
if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    print("⚠️  Warning: Please set your BOT_TOKEN in environment variables or .env file")

if OPENAI_API_KEY == 'YOUR_OPENAI_API_KEY':
    print("⚠️  Warning: Please set your OPENAI_API_KEY in environment variables or .env file")

