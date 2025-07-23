#!/usr/bin/env python3
"""
Personal Assistant Bot "Anuj"
A comprehensive Telegram bot with advanced features
"""

import os
import logging
import json
import asyncio
import random
from datetime import datetime
from typing import Dict, Optional
from telegram import Bot, Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes
)
from telegram.constants import ParseMode
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AnujBot:
    def __init__(self, bot_token: str, openai_api_key: str):
        """Initialize the bot with necessary tokens"""
        if not bot_token or not openai_api_key:
            raise ValueError("BOT_TOKEN and OPENAI_API_KEY must be provided.")
        
        self.bot_token = bot_token
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # This will be set after the Application object is created
        self.application: Optional[Application] = None
        
        # Initialize custom modules (simplified for now)
        # TODO: Implement these modules
        # self.db_manager = DatabaseManager()
        # self.image_solver = ImageSolver()
        # self.context_manager = ContextManager()
        # self.file_manager = FileManager()
        # self.quiz_generator = QuizGenerator()
        
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
        user = update.effective_user
        user_id = user.id
        user_name = user.first_name
        
        # TODO: Initialize user in database
        # await self.db_manager.add_user(user_id, user_name)
        
        welcome_message = f"""
🤖 <b>Namaste {user_name}! Main Anuj hun, aapka Personal Assistant!</b>

🌟 <b>Main kya kar sakta hun:</b>
• 📚 Notes aur files manage kar sakta hun
• 🧠 Quiz generate kar sakta hun PDF se
• 🖼️ Images me doubts solve kar sakta hun
• 💭 Context samajh kar help kar sakta hun
• 📝 Har user ka individual memory rakhta hun
• 🎯 Auto-filter ki tarah kaam karta hun

<b>Commands:</b>
/start - Bot start karne ke liye
/help - Help menu
/quiz - Quiz generate karne ke liye
/notes - Notes search karne ke liye
/memory - Apna chat history dekhne ke liye

<b>Bas file bhejo ya question pucho, main samajh jaunga! 😊</b>
        """
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        user_id = update.effective_user.id
        help_text = """
🤖 <b>Anuj Bot Help Menu</b>

<b>📚 File Management:</b>
• PDF bhejo → Quiz banaunga
• Images bhejo → Doubts solve karunga
• "send me notes" bolo → Files forward karunga

<b>🧠 Quiz Features:</b>
• PDF upload karo → Auto quiz generate hoga
• Group me add karo → Quiz conduct karunga
• Multiple choice questions banaunga

<b>🖼️ Image Doubt Solving:</b>
• Math problems ki images bhejo
• Handwriting style me solution dunga
• Copy pe solve kiya hua lagega

<b>💭 Smart Features:</b>
• Context samajhta hun
• Individual memory rakhta hun
• Auto-filter ki tarah kaam karta hun
• Personal assistant ban jata hun

<b>Commands:</b>
/start - Bot start karne ke liye
/help - Help menu
/quiz - Quiz generate karne ke liye
/notes - Notes search karne ke liye
/memory - Apna chat history dekhne ke liye

<b>Special:</b>
• "Thanks" bolo to get a surprise!
• "Best wishes" bolo to get motivation!

<b>Don't suffer in silence, ask Anuj! 😊</b>
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages with context understanding"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        message_text = update.message.text
        
        # Context-based responses
        lower_message_text = message_text.lower()
        if any(word in lower_message_text for word in ['thanks', 'thank you']):
            surprise_link = random.choice(self.surprise_links)
            response = f"🎉 **Welcome {user_name}!**\n\nYahan hai aapke liye ek surprise: {surprise_link}\n\n✨ Aur koi doubt hai? Puchte raho!"
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

        elif 'best wishes' in lower_message_text:
            response = random.choice(self.best_wishes_responses)
            await update.message.reply_text(response)

        elif 'notes' in lower_message_text:
            await self.send_relevant_files(update, context, message_text)

        elif 'doubt' in lower_message_text:
            response = (
                "🤔 **Doubt hai? Perfect!**\n\n"
                "📸 Image bhejo agar visual problem hai\n"
                "📝 Text me likho agar theory doubt hai\n"
                "📚 PDF bhejo agar quiz chahiye\n\n"
                "**Aur doubts pucho, suffering karte rahne se kya fayda! 😊**"
            )
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

        else:
            # General context understanding
            await self.handle_general_query(update, context, message_text)

    async def handle_general_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Handle general queries with AI assistance"""
        user_id = update.effective_user.id

        try:
            response = await self.get_ai_response(query)
            await update.message.reply_text(f"🤖 **Anuj:** {response}")
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
        doc = update.message.document
        
        try:
            file = await doc.get_file()
            file_path = f"files/{user_id}_{doc.file_name}"
            await file.download_to_drive(file_path)
            
            await update.message.reply_text("📚 **PDF received!** Processing... ⏳")
            
            # TODO: Implement quiz generation
            await update.message.reply_text("🧠 Quiz generation feature coming soon!")
                
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await update.message.reply_text("❌ File process karne me error aayi. Try again!")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle images for doubt solving"""
        user_id = update.effective_user.id
        
        try:
            photo = update.message.photo[-1]  # Get highest resolution
            file = await photo.get_file()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"files/{user_id}_image_{timestamp}.jpg"
            await file.download_to_drive(file_path)
            
            await update.message.reply_text("🖼️ **Image received!** Processing... ✏️")
            
            # TODO: Implement image solving
            await update.message.reply_text("🔍 Image solving feature coming soon!")
                
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await update.message.reply_text("❌ Image process karne me error aayi. Try again!")

    async def send_relevant_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = ""):
        """Send relevant files based on user query"""
        await update.message.reply_text("📁 **File management feature coming soon!**\n\nAbhi main development stage me hun. Soon all features ready ho jayenge! 😊")

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's chat history/memory"""
        await update.message.reply_text("🧠 **Memory feature coming soon!**\n\nAbhi main tumhari baatein yaad rakhna seekh raha hun! 😊")

    async def group_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Group quiz command handler"""
        await update.message.reply_text(
            "🧠 **Group Quiz Feature Coming Soon!**\n\n"
            "👥 Group me add karo aur wait karo for amazing quiz features!\n"
            "🏆 Leaderboard bhi aayega soon.\n"
            "**Get ready to challenge your friends!** 😊"
        )

    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Leaderboard command handler"""
        await update.message.reply_text(
            "🏆 **Leaderboard Coming Soon!**\n\n"
            "Feature development me hai. Soon ready ho jayega!\n"
            "**Stay tuned!** 😊"
        )

def main():
    """Main function to setup and run the bot"""
    # Ensure 'files' directory exists
    os.makedirs("files", exist_ok=True)
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN not found in environment variables.")
        exit(1)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logger.error("FATAL: OPENAI_API_KEY not found in environment variables.")
        exit(1)

    # Initialize bot and application
    anuj_bot = AnujBot(bot_token=BOT_TOKEN, openai_api_key=OPENAI_API_KEY)
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Link the application object to the bot instance
    anuj_bot.application = application

    # Command handlers
    application.add_handler(CommandHandler("start", anuj_bot.start))
    application.add_handler(CommandHandler("help", anuj_bot.help_command))
    application.add_handler(CommandHandler("quiz", anuj_bot.group_quiz_command))
    application.add_handler(CommandHandler("notes", anuj_bot.send_relevant_files))
    application.add_handler(CommandHandler("memory", anuj_bot.memory_command))
    application.add_handler(CommandHandler("leaderboard", anuj_bot.leaderboard_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, anuj_bot.handle_document))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, anuj_bot.handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anuj_bot.handle_message))

    logger.info("Bot is starting to poll for updates...")
    application.run_polling()

if __name__ == "__main__":
    main()
