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
from typing import Dict
from aiohttp import web
from plugins import web_server
from plugins.clone import restart_bots


# Third-party libraries
import requests
from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes
)
from telegram.constants import ParseMode
from openai import OpenAI
from dotenv import load_dotenv

# Custom modules (Ensure these files exist in the specified paths)
# NOTE: I am assuming the structure of your custom modules.
# You might need to adjust imports if your file structure is different.
from config.settings import USE_MONGODB, DATABASE_PATH, MONGODB_CONNECTION_STRING
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
    def __init__(self, bot_token: str, openai_api_key: str):
        # Initialize API clients and managers
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize custom modules
        # Naya aur sudhara hua code
        # Naya aur Best Solution
        self.db_manager = DatabaseManager()
        self.image_solver = ImageSolver()
        self.context_manager = ContextManager()
        self.file_manager = FileManager()
        self.quiz_generator = QuizGenerator()

        
        # This will be set after the Application object is created
        self.application: Optional[Application] = None
        self.bot_token = bot_token

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

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE ):
        """Start command handler"""
        user = update.effective_user
        user_id = user.id
        user_name = user.first_name
        
        # Initialize user in database
        await self.db_manager.add_user(user_id, user_name)
        
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

<b>Group Features:</b>
• Group me add karo quiz ke liye
• Members ka record rakhta hun
• Scheduled quizzes kar sakta hun

<b>Bas message karo, main samajh jaunga! 😊</b>
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
        await self.db_manager.add_message(user_id, "/help", "user")
        await self.db_manager.add_message(user_id, help_text, "bot")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages with context understanding"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        message_text = update.message.text
        
        # Store user message in history
        await self.db_manager.add_message(user_id, message_text, 'user')

        # Context-based responses
        lower_message_text = message_text.lower()
        if any(word in lower_message_text for word in ['thanks', 'thank you']):
            surprise_link = random.choice(self.surprise_links)
            response = f"🎉 **Welcome {user_name}!**\n\nYahan hai aapke liye ek surprise: {surprise_link}\n\n✨ Aur koi doubt hai? Puchte raho!"
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            await self.db_manager.add_message(user_id, response, 'bot')

        elif 'best wishes' in lower_message_text:
            response = random.choice(self.best_wishes_responses)
            await update.message.reply_text(response)
            await self.db_manager.add_message(user_id, response, 'bot')

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
            await self.db_manager.add_message(user_id, response, 'bot')

        else:
            # General context understanding
            await self.handle_general_query(update, context, message_text)

    async def handle_general_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Handle general queries with AI assistance"""
        user_id = update.effective_user.id

        # Get user context
        user_history = await self.db_manager.get_user_history(user_id, limit=5)
        context_prompt = f"User history: {user_history}\n\nCurrent query: {query}"

        try:
            response = await self.get_ai_response(context_prompt)
            await update.message.reply_text(f"🤖 **Anuj:** {response}")
            # Store bot response
            await self.db_manager.add_message(user_id, response, 'bot')
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
            
            # Store file info
            await self.file_manager.store_file(user_id, file_path, doc.file_name)
            
            await update.message.reply_text("📚 **PDF received!** Quiz generate kar raha hun... ⏳")
            
            # Generate quiz from PDF
            quiz_data = await self.quiz_generator.generate_from_pdf(file_path)
            
            if quiz_data and quiz_data.get('questions'):
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
            photo = update.message.photo[-1]  # Get highest resolution
            file = await photo.get_file()
            
            # Sahi code
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"files/{user_id}_image_{timestamp}.jpg"
            await file.download_to_drive(file_path)
            
            await update.message.reply_text("🖼️ **Image received!** Doubt solve kar raha hun... ✏️")
            
            # Solve the image doubt
            solved_image_path = await self.image_solver.solve_doubt(file_path)
            
            if solved_image_path and os.path.exists(solved_image_path):
                caption_text = """
✅ <b>Doubt Solved!</b> 📝\n
Aisa lagta hai jaise copy pe kisi student ne solve kiya ho! 😊\n
🤔 Aur doubts hai? Bhejo!
                """
                with open(solved_image_path, 'rb') as img_file:
                    await update.message.reply_photo(
                        photo=InputFile(img_file),
                        caption=caption_text,
                        parse_mode=ParseMode.HTML
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
            quiz_text += f"**Q{i}.** {q.get('question', 'N/A')}\n"
            for j, option in enumerate(q.get('options', [])):
                quiz_text += f"{j+1}. {option}\n"
            quiz_text += f"**Answer:** {q.get('answer', 'N/A')}\n\n"
        
        await update.message.reply_text(quiz_text, parse_mode=ParseMode.MARKDOWN)

    async def send_relevant_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = ""):
        """Send relevant files based on user query"""
        user_id = update.effective_user.id
        
        user_files = await self.file_manager.get_user_files(user_id)
        
        if not user_files:
            await update.message.reply_text("📁 **Koi files nahi mili!**\n\nPehle kuch PDF ya notes upload karo, phir main forward kar dunga! 😊")
            return
            
        relevant_files = []
        if query:
            query_words = query.lower().split()
            for file_info in user_files:
                file_name = file_info.get('filename', '').lower()
                if any(word in file_name for word in query_words):
                    relevant_files.append(file_info)
        
        if not relevant_files:
            relevant_files = user_files[:3]  # Send recent files if no match
            
        files_text = "📚 **Yahan hai aapki files:**\n\n"
        for i, file_info in enumerate(relevant_files, 1):
            files_text += f"{i}. {file_info.get('filename', 'Unknown File')}\n"
            
        await update.message.reply_text(files_text)
        
        for file_info in relevant_files:
            filepath = file_info.get('filepath')
            if filepath and os.path.exists(filepath):
                try:
                    with open(filepath, 'rb') as f:
                        await update.message.reply_document(
                            document=InputFile(f, filename=file_info.get('filename'))
                        )
                except Exception as e:
                    logger.error(f"Error sending file {filepath}: {e}")
                    await update.message.reply_text(f"😥 File {file_info.get('filename')} bhejne mein error aa gayi.")

    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's chat history/memory"""
        user_id = update.effective_user.id
        history = await self.db_manager.get_user_history(user_id, limit=10)
        
        if not history:
            await update.message.reply_text("🧠 **Memory khali hai!**\n\nAbhi tak koi conversation nahi hui! 😊")
            return
            
        memory_text = "🧠 **Aapka Chat Memory:**\n\n"
        for msg in reversed(history): # Show oldest first
            sender = "You" if msg.get('sender') == 'user' else "🤖 Anuj"
            message_content = msg.get('message', '')
            # Truncate long messages for readability
            if len(message_content) > 100:
                message_content = message_content[:100] + "..."
            memory_text += f"*{sender}:* {message_content}\n"
            
        await update.message.reply_text(memory_text, parse_mode=ParseMode.MARKDOWN)

    async def group_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Group quiz command handler"""
        await update.message.reply_text(
            "🧠 **Group Quiz!**\n\n"
            "👥 Group me add karo aur quiz start karne ke liye `/start_group_quiz` bolo.\n"
            "🏆 Leaderboard dekhne ke liye `/leaderboard` bolo.\n"
            "**Ready to challenge your friends?** 😊"
        )

    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Leaderboard command handler"""
        await update.message.reply_text(
            "🏆 **Leaderboard!**\n\n"
            "Abhi tak koi scores nahi hain. Group quiz khelo aur top par aao!\n"
            "**All the best!** 😊"
        )

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Placeholder for handling group messages"""
        # This function can be expanded to handle group-specific logic
        logger.info(f"Received a message in group {update.message.chat.title}")
        # For now, it does nothing to avoid spamming groups.
        pass

    # --- Webhook Methods ---
    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for the bot"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
            params = {'url': webhook_url, 'allowed_updates': json.dumps(["message", "callback_query"] )}
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"Webhook set successfully to {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result.get('description')}")
                return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    async def process_webhook_update(self, update_data: dict):
        """Process a single update from a webhook"""
        if not self.application:
            logger.error("Application not initialized. Cannot process webhook update.")
            return
        try:
            update = Update.de_json(update_data, self.application.bot)
            await self.application.process_update(update)
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")


def main():
    """Main function to setup and run the bot"""
    # Ensure 'files' directory exists
    os.makedirs("files", exist_ok=True)
    
    # Load environment variables from .env file
    load_dotenv()

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN not found in environment variables or .env file.")
        exit(1)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logger.error("FATAL: OPENAI_API_KEY not found in environment variables or .env file.")
        exit(1)

    # Initialize bot and application
    anuj_bot = AnujBot(bot_token=BOT_TOKEN, openai_api_key=OPENAI_API_KEY)
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Link the application object to the bot instance for webhook processing
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
    
    # Group message handler (optional, can be more specific)
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, anuj_bot.handle_group_message))

    logger.info("Bot is starting to poll for updates...")
    application.run_polling()

    async def start_web():
    app = web.AppRunner(web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    site = web.TCPSite(app, bind_address, PORT)
    await site.start()
    await idle()

if __name__ == "__main__":
    asyncio.run(start_web())
