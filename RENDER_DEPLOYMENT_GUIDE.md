# Anuj Bot - Render Deployment Guide

## Overview
This guide will help you deploy the Anuj Bot as a **Web Service** on Render using webhooks.

## Prerequisites
1. Render account (free tier works)
2. GitHub repository with your bot code
3. Telegram Bot Token
4. OpenAI API Key
5. MongoDB connection string (if using MongoDB)

## Step-by-Step Deployment

### 1. Prepare Your Repository
- Upload the bot code to a GitHub repository
- Ensure all files are included, especially:
  - `webhook_server.py` (main webhook server)
  - `requirements.txt` (dependencies)
  - `start_webhook.sh` (startup script)
  - All bot modules and utilities

### 2. Create Web Service on Render

1. **Go to Render Dashboard**
   - Visit [render.com](https://render.com)
   - Sign in to your account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your bot

3. **Configure Service Settings**
   - **Name**: `anuj-bot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python webhook_server.py`

### 3. Set Environment Variables

In the Render dashboard, add these environment variables:

#### Required Variables:
```
BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
WEBHOOK_URL=https://your-app-name.onrender.com
```

#### Optional Variables (if using MongoDB):
```
DATABASE_PATH=your_mongodb_connection_string
USE_MONGODB=true
```

#### Other Optional Variables:
```
BOT_USERNAME=your_bot_username
MAX_FILE_SIZE=50
MAX_QUIZ_QUESTIONS=10
LOG_LEVEL=INFO
```

### 4. Deploy and Set Webhook

1. **Deploy the Service**
   - Click "Create Web Service"
   - Wait for deployment to complete (5-10 minutes)
   - Note your app URL: `https://your-app-name.onrender.com`

2. **Set Webhook URL**
   - Once deployed, visit: `https://your-app-name.onrender.com/set_webhook`
   - This will automatically set the webhook for your bot
   - Or manually set via API call:
     ```bash
     curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
          -d "url=https://your-app-name.onrender.com/webhook"
     ```

### 5. Verify Deployment

1. **Check Health**
   - Visit: `https://your-app-name.onrender.com/`
   - Should show: `{"status": "ok", "message": "Anuj Bot Webhook Server is running"}`

2. **Check Webhook Info**
   - Visit: `https://your-app-name.onrender.com/get_webhook_info`
   - Should show webhook is set correctly

3. **Test Bot**
   - Send `/start` to your bot on Telegram
   - Bot should respond immediately

## Important Notes

### Free Tier Limitations
- Render free tier services sleep after 15 minutes of inactivity
- First request after sleep may take 30-60 seconds to respond
- Consider upgrading to paid tier for production use

### Environment Variables Security
- Never commit sensitive keys to your repository
- Use Render's environment variables feature
- Rotate keys regularly

### Monitoring
- Check Render logs for any errors
- Monitor bot responses and performance
- Set up alerts if needed

## Troubleshooting

### Common Issues:

1. **Bot Not Responding**
   - Check if webhook is set correctly
   - Verify environment variables
   - Check Render logs for errors

2. **"No open ports detected" Error**
   - This guide fixes this by using Flask webhook server
   - Ensure `webhook_server.py` is the main entry point

3. **Image Processing Errors**
   - Tesseract is installed via system dependencies
   - Check if OpenCV works in the environment

4. **Database Connection Issues**
   - Verify MongoDB connection string
   - Check if database is accessible from Render

### Useful Endpoints:

- Health Check: `GET /`
- Set Webhook: `POST /set_webhook`
- Get Webhook Info: `GET /get_webhook_info`
- Delete Webhook: `POST /delete_webhook`

## Support

If you encounter issues:
1. Check Render logs first
2. Verify all environment variables
3. Test webhook endpoints manually
4. Check Telegram Bot API documentation

## Alternative: Background Worker

If you prefer polling instead of webhooks:
1. Change service type to "Background Worker"
2. Use `start.sh` instead of `webhook_server.py`
3. No webhook setup needed

---

**Happy Deploying! 🚀**

