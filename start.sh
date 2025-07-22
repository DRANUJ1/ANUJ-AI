#!/bin/bash

# Anuj Bot Startup Script
# This script starts the Anuj Telegram Bot with proper environment setup

echo "🤖 Starting Anuj Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Please copy .env.example to .env and configure your settings"
    echo "cp .env.example .env"
    echo "Then edit .env with your bot token and API keys"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p database files logs static

# Check system dependencies
echo "🔍 Checking system dependencies..."

# Check for tesseract
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract OCR not found!"
    echo "📥 Please install: sudo apt install tesseract-ocr tesseract-ocr-hin"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher required. Found: $python_version"
    exit 1
fi

echo "✅ All dependencies check passed!"

# Start the bot
echo "🚀 Starting Anuj Bot..."
echo "📊 Logs will be saved to logs/anuj_bot.log"
echo "🛑 Press Ctrl+C to stop the bot"
echo ""

# Run the bot with error handling
python3 bot.py

echo "🛑 Anuj Bot stopped."

