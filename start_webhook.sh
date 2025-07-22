#!/bin/bash

# Start script for Anuj Bot Webhook Server
# For Render deployment

echo "🚀 Starting Anuj Bot Webhook Server..."

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install system dependencies if needed
echo "📦 Installing system dependencies..."
apt-get update -qq && apt-get install -y -qq tesseract-ocr tesseract-ocr-hin libgl1-mesa-glx libglib2.0-0 2>/dev/null || echo "System dependencies already installed or not available"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p files logs static pdfs images documents audio video other

# Set permissions
chmod +x start_webhook.sh

# Start the webhook server
echo "🌐 Starting webhook server..."
python webhook_server.py

