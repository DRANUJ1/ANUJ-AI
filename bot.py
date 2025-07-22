#!/usr/bin/env python3
"""
Personal Assistant Bot "Anuj"
A comprehensive Telegram bot with advanced features
"""

import os
import logging
import sqlite3
import json
import asyncio
import aiohttp
import io
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from telegram.constants import ParseMode

import PyPDF2
from PIL import Image, ImageDraw, ImageFont
import openai
from openai import OpenAI

# Import custom modules
from config.settings import *
from database.db_manager import DatabaseManager
from utils.file_manager import FileManager
from utils.quiz_generator import QuizGenerator
from utils.image_solver import ImageSolver
from utils.context_manager import ContextManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AnujBot:
    def __init__(self):
        # Initialize database manager with MongoDB connection
        from config.settings import USE_MONGODB, DATABASE_PATH
        if USE_MONGODB:
            self.db_manager = DatabaseManager(DATABASE_PATH)
        else:
            self.db_manager = DatabaseManager()
        self.image_solver = ImageSolver()
        self.context_manager = ContextManager()
        self.openai_client = OpenAI()
        
        # Bot personality responses
        self.surprise_links = [
            "🎉 https://youtu.be/dQw4w9WgXcQ",
            "🌟 https://youtu.be/ZZ5LpwO-An4",
            "✨ https://youtu.be/L_jWHffIx5E",
            "🎊 https://youtu.be/fJ9rUzIMcZQ"
        ]
        
        self.best_wishes_responses = [
            "🌟 Best wishes to you too! Aur koi doubt hai? Puchte raho, main yahan hun!",
            "✨ Thank you! Koi aur question hai? Don't suffer in silence, ask away!",
            "🎉 Best wishes! Aur doubts lao, main solve kar dunga!"
        ]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Initialize user in database (async)
        await self.db_manager.add_user(user_id, user_name)
        
        welcome_message = f"""
🤖 **Namaste {user_name}! Main Anuj hun, aapka Personal Assistant!**

🌟 **Main kya kar sakta hun:**
• 📚 Notes aur files manage kar sakta hun
• 🧠 Quiz generate kar sakta hun PDF se
• 🖼️ Images me doubts solve kar sakta hun
• 💭 Context samajh kar help kar sakta hun
• 📝 Har user ka individual memory rakhta hun
• 🎯 Auto-filter ki tarah kaam karta hun

**Commands:**
/start - Bot start karne ke liye
/help - Help menu
/quiz - Quiz generate karne ke liye
/notes - Notes search karne ke liye
/memory - Apna chat history dekhne ke liye

**Bas file bhejo ya question pucho, main samajh jaunga! 😊**
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        user_id = update.effective_user.id
        help_text = f"""
🤖 **Anuj Bot Help Menu**

**📚 File Management:**
• PDF bhejo → Quiz banaunga
• Images bhejo → Doubts solve karunga
• "send me notes" bolo → Files forward karunga

**🧠 Quiz Features:**
• PDF upload karo → Auto quiz generate hoga
• Group me add karo → Quiz conduct karunga
• Multiple choice questions banaunga

**🖼️ Image Doubt Solving:**
• Math problems ki images bhejo
• Handwriting style me solution dunga
• Copy pe solve kiya hua lagega

**💭 Smart Features:**
• Context samajhta hun
• Individual memory rakhta hun
• Auto-filter ki tarah kaam karta hun
• Personal assistant ban jata hun

**Commands:**
/start - Bot start karne ke liye
/help - Help menu
/quiz - Quiz generate karne ke liye
/notes - Notes search karne ke liye
/memory - Apna chat history dekhne ke liye

**Special:**
• "Thanks" bolo to get a surprise!
• "Best wishes" bolo to get motivation!

**Don\"t suffer in silence, ask Anuj! 😊**

**Group Features:**
• Group me add karo quiz ke liye
• Members ka record rakhta hun
• Scheduled quizzes kar sakta hun

**Bas message karo, main samajh jaunga! 😊**
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
        await self.db_manager.add_message(user_id, "/help", "user")
        await self.db_manager.add_message(user_id, help_text, "bot")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages with context understanding"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        message_text = update.message.text.lower()
        
        # Store message in user history
        self.db_manager.add_message(user_id, message_text, 'user')
        
        # Context-based responses
        if any(word in message_text for word in ['thanks', 'thank you', 'dhanyawad', 'shukriya']):
            surprise_link = random.choice(self.surprise_links)
            response = f"🎉 **Welcome {user_name}!** \n\nYahan hai aapke liye ek surprise: {surprise_link}\n\n✨ Aur koi doubt hai? Puchte raho!"
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
        elif any(word in message_text for word in ['best wishes', 'best wish', 'good luck']):
            response = random.choice(self.best_wishes_responses)
            await update.message.reply_text(response)
            
        elif any(word in message_text for word in ['notes', 'send me notes', 'file chahiye', 'notes do']):
            await self.send_relevant_files(update, context, message_text)
            
        elif any(word in message_text for word in ['doubt', 'question', 'help', 'problem']):
            response = "🤔 **Doubt hai? Perfect!**\n\n📸 Image bhejo agar visual problem hai\n📝 Text me likho agar theory doubt hai\n📚 PDF bhejo agar quiz chahiye\n\n**Aur doubts pucho, suffering karte rahne se kya fayda! 😊**"
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
        else:
            # General context understanding
            await self.handle_general_query(update, context, message_text)

    async def handle_general_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Handle general queries with AI assistance"""
        user_id = update.effective_user.id
        
        # Get user context
        user_history = self.db_manager.get_user_history(user_id, limit=5)
        context_prompt = f"User history: {user_history}\nCurrent query: {query}"
        
        try:
            response = await self.get_ai_response(context_prompt)
            await update.message.reply_text(f"🤖 **Anuj:** {response}")
            
            # Store bot response
            self.db_manager.add_message(user_id, response, 'bot')
            
        except Exception as e:
            logger.error(f"Error in AI response: {e}")
            await update.message.reply_text("🤖 **Anuj:** Samajh gaya! Koi specific doubt hai toh detail me batao. Main help karunga! 😊")

    async def get_ai_response(self, prompt: str) -> str:
        """Get AI response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Anuj, a helpful Hindi-English mixed personal assistant. Be friendly, use emojis, and keep responses concise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "Main samajh gaya! Aur detail me batao kya chahiye."

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF documents for quiz generation"""
        user_id = update.effective_user.id
        
        try:
            # Download the file
            file = await update.message.document.get_file()
            file_path = f"files/{user_id}_{update.message.document.file_name}"
            await file.download_to_drive(file_path)
            
            # Store file info
            self.file_manager.store_file(user_id, file_path, update.message.document.file_name)
            
            await update.message.reply_text("📚 **PDF received!** Quiz generate kar raha hun... ⏳")
            
            # Generate quiz from PDF
            quiz_data = await self.quiz_generator.generate_from_pdf(file_path)
            
            if quiz_data:
                await self.send_quiz(update, context, quiz_data)
            else:
                await update.message.reply_text("❌ PDF se quiz generate nahi kar paya. Koi aur file try karo!")
                
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await update.message.reply_text("❌ File process karne me error aayi. Try again!")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle images for doubt solving"""
        user_id = update.effective_user.id
        
        try:
            # Download the image
            photo = update.message.photo[-1]  # Get highest resolution
            file = await photo.get_file()
            file_path = f"files/{user_id}_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            await file.download_to_drive(file_path)
            
            await update.message.reply_text("🖼️ **Image received!** Doubt solve kar raha hun... ✏️")
            
            # Solve the image doubt
            solved_image_path = await self.image_solver.solve_doubt(file_path)
            
            if solved_image_path:
                # Send solved image
                with open(solved_image_path, 'rb') as img_file:
                    await update.message.reply_photo(
                        photo=InputFile(img_file),
                        caption="✅ **Doubt Solved!** 📝\n\nAisa lagta hai jaise copy pe kisi student ne solve kiya ho! 😊\n\n🤔 Aur doubts hai? Bhejo!"
                    )
            else:
                await update.message.reply_text("❌ Image me doubt solve nahi kar paya. Clear image bhejo!")
                
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await update.message.reply_text("❌ Image process karne me error aayi. Try again!")

    async def send_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE, quiz_data: Dict):
        """Send quiz to user"""
        questions = quiz_data.get('questions', [])
        
        if not questions:
            await update.message.reply_text("❌ Quiz generate nahi hua. PDF me readable text nahi mila!")
            return
            
        quiz_text = "🧠 **Quiz Generated!**\n\n"
        
        for i, q in enumerate(questions[:5], 1):  # Limit to 5 questions
            quiz_text += f"**Q{i}.** {q['question']}\n"
            for j, option in enumerate(q['options'], 1):
                quiz_text += f"{j}. {option}\n"
            quiz_text += f"**Answer:** {q['answer']}\n\n"
        
        await update.message.reply_text(quiz_text, parse_mode=ParseMode.MARKDOWN)

    async def send_relevant_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Send relevant files based on user query"""
        user_id = update.effective_user.id
        
        # Get user's files
        user_files = self.file_manager.get_user_files(user_id)
        
        if not user_files:
            await update.message.reply_text("📁 **Koi files nahi mili!**\n\nPehle kuch PDF ya notes upload karo, phir main forward kar dunga! 😊")
            return
            
        # Simple keyword matching for now
        relevant_files = []
        query_words = query.split()
        
        for file_info in user_files:
            file_name = file_info['filename'].lower()
            if any(word in file_name for word in query_words):
                relevant_files.append(file_info)
        
        if not relevant_files:
            relevant_files = user_files[:3]  # Send recent files
            
        files_text = "📚 **Yahan hai aapki files:**\n\n"
        for i, file_info in enumerate(relevant_files, 1):
            files_text += f"{i}. {file_info['filename']}\n"
            
        await update.message.reply_text(files_text)
        
        # Send actual files
        for file_info in relevant_files:
            try:
                if os.path.exists(file_info['filepath']):
                    with open(file_info['filepath'], 'rb') as f:
                        await update.message.reply_document(
                            document=InputFile(f, filename=file_info['filename'])
                        )
            except Exception as e:
                logger.error(f"Error sending file: {e}")

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's chat history/memory"""
        user_id = update.effective_user.id
        history = self.db_manager.get_user_history(user_id, limit=10)
        
        if not history:
            await update.message.reply_text("🧠 **Memory khali hai!**\n\nAbhi tak koi conversation nahi hui! 😊")
            return
            
        memory_text = "🧠 **Aapka Chat Memory:**\n\n"
        for msg in history:
            sender = "🤖 Anuj" if msg['sender'] == 'bot' else "👤 You"
            memory_text += f"{sender}: {msg['message'][:50]}...\n"
            
        await update.message.reply_text(memory_text)


    async def group_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Group quiz command handler"""
        await update.message.reply_text(
            "🧠 **Group Quiz!**\n\n"
            "👥 Group me add karo aur quiz start karne ke liye /start_group_quiz bolo.\n"
            "🏆 Leaderboard dekhne ke liye /leaderboard bolo.\n"
            "**Ready to challenge your friends?** 😊"
        )

    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Leaderboard command handler"""
        await update.message.reply_text(
            "🏆 **Leaderboard!**\n\n"
            "Abhi tak koi scores nahi hain. Group quiz khelo aur top par aao!\n"
            "**All the best!** 😊"
        )

    # Group handling methods
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass






if __name__ == "__main__":
    # Ensure files directory exists
    os.makedirs("files", exist_ok=True)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")

    # Get bot token from environment variables
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in .env file. Please set it.")
        exit(1)

    # Get OpenAI API key from environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in .env file. Please set it.")
        exit(1)
    openai.api_key = OPENAI_API_KEY

    # Get MongoDB connection string from environment variables
    from config.settings import USE_MONGODB, MONGODB_CONNECTION_STRING, DATABASE_PATH
    if not USE_MONGODB:
        logger.warning("MONGODB_CONNECTION_STRING not found in .env file or not a MongoDB string. Using SQLite.")

    anuj_bot = AnujBot()
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", anuj_bot.start))
    application.add_handler(CommandHandler("help", anuj_bot.help_command))
    application.add_handler(CommandHandler("quiz", anuj_bot.group_quiz_command))
    application.add_handler(CommandHandler("notes", anuj_bot.send_relevant_files))
    application.add_handler(CommandHandler("memory", anuj_bot.memory_command))
    application.add_handler(CommandHandler("leaderboard", anuj_bot.leaderboard_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.Document.ALL, anuj_bot.handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, anuj_bot.handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anuj_bot.handle_message))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anuj_bot.handle_group_message))

    # Run the bot until the user presses Ctrl+C
    logger.info("Bot is now polling for updates...")
    application.run_polling()

        def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for the bot"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            data = {
                'url': webhook_url + '/webhook',
                'allowed_updates': ['message', 'callback_query']
            }
            response = requests.post(url, data=data )
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"Webhook set successfully to {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    def get_webhook_info(self) -> dict:
        """Get current webhook information"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            response = requests.get(url )
            result = response.json()
            
            if result.get('ok'):
                return result.get('result', {})
            else:
                logger.error(f"Failed to get webhook info: {result}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {}
    
    def delete_webhook(self) -> bool:
        """Delete webhook (switch back to polling)"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
            response = requests.post(url )
            result = response.json()
            
            if result.get('ok'):
                logger.info("Webhook deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete webhook: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    async def process_webhook_update(self, update_data: dict):
        """Process webhook update from Telegram"""
        try:
            # Create Update object from webhook data
            from telegram import Update
            update = Update.de_json(update_data, self.application.bot)
            
            if update:
                # Process the update through the application
                await self.application.process_update(update)
            else:
                logger.warning("Failed to create Update object from webhook data")
                
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")


