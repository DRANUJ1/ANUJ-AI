# 🚀 Anuj Bot - Deployment Guide

## ✅ Successfully Tested and Working!

This bot has been successfully deployed and tested. All core features are working including:
- ✅ MongoDB integration
- ✅ Telegram bot connectivity
- ✅ Image OCR processing (Tesseract)
- ✅ PDF processing
- ✅ OpenAI integration
- ✅ User memory system
- ✅ File management

## 🔧 Quick Deployment Steps

### 1. Environment Setup
```bash
# Extract the bot files
unzip anuj_bot_working.zip
cd anuj_bot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your credentials:
# - BOT_TOKEN (from @BotFather)
# - OPENAI_API_KEY (from OpenAI)
# - DATABASE_PATH (MongoDB connection string)
```

### 3. System Dependencies (Ubuntu/Debian)
```bash
# Install Tesseract OCR
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-hin

# Install OpenCV dependencies
sudo apt install libgl1-mesa-glx libglib2.0-0
```

### 4. Run the Bot
```bash
# Simple run
python bot.py

# Or use the startup script
chmod +x start.sh
./start.sh
```

## 🌐 Render Deployment

### Method 1: Direct Repository Deploy
1. Upload this code to your GitHub repository
2. Connect Render to your GitHub repo
3. Set environment variables in Render dashboard
4. Deploy as a Web Service

### Method 2: Docker Deploy
```dockerfile
# Use the included Dockerfile
docker build -t anuj-bot .
docker run -d --env-file .env anuj-bot
```

### Environment Variables for Render
```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
DATABASE_PATH=your_mongodb_connection_string
ADMIN_USER_IDS=your_telegram_user_id
```

## 📋 Features Status

### ✅ Working Features
- **Telegram Integration**: Full bot functionality
- **MongoDB Database**: User data, conversations, files
- **Image Processing**: OCR with Tesseract
- **PDF Processing**: Text extraction and quiz generation
- **AI Integration**: OpenAI GPT for responses
- **User Memory**: Individual conversation history
- **File Management**: Upload, categorize, retrieve
- **Context Understanding**: Natural language processing

### 🔄 Optional Features (Heavy Dependencies)
- **EasyOCR**: Advanced OCR (requires PyTorch ~2GB)
- **Matplotlib**: Data visualization
- **Sympy**: Advanced math processing

To enable optional features:
```bash
pip install easyocr matplotlib sympy
```

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   ```bash
   pip install -r requirements.txt
   ```

2. **Tesseract not found**
   ```bash
   # Ubuntu/Debian
   sudo apt install tesseract-ocr
   
   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **MongoDB Connection Issues**
   - Check your connection string format
   - Ensure MongoDB Atlas allows connections from your IP
   - Verify credentials are correct

4. **Bot Token Issues**
   - Get token from @BotFather on Telegram
   - Ensure token is correctly set in .env file
   - Check bot is not already running elsewhere

### Logs and Debugging
```bash
# Check logs
tail -f logs/anuj_bot.log

# Test specific components
python -c "from database.mongodb_manager import DatabaseManager; print('DB OK')"
python -c "from utils.image_solver import ImageSolver; print('Image Solver OK')"
```

## 📊 Performance Notes

- **Memory Usage**: ~200-500MB (without EasyOCR)
- **Memory Usage**: ~2-3GB (with EasyOCR/PyTorch)
- **Startup Time**: ~10-30 seconds
- **Response Time**: 1-5 seconds per message

## 🔒 Security

- Keep your `.env` file secure
- Use environment variables for sensitive data
- Regular MongoDB backups recommended
- Monitor bot usage and logs

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Verify all environment variables
3. Ensure system dependencies are installed
4. Test MongoDB connection separately

---

**Bot Status: ✅ FULLY FUNCTIONAL**
**Last Tested**: July 21, 2025
**Deployment Ready**: ✅ YES

