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
        self.db_manager = DatabaseManager()
        self.file_manager = FileManager()
        self.quiz_generator = QuizGenerator()
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
        
        # Initialize user in database
        self.db_manager.add_user(user_id, user_name)
        
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
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
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

**Group Features:**
• Group me add karo quiz ke liye
• Members ka record rakhta hun
• Scheduled quizzes kar sakta hun

Bas message karo, main samajh jaunga! 😊
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

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

    async def quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quiz command handler"""
        await update.message.reply_text(
            "🧠 **Quiz Generate karne ke liye:**\n\n"
            "📚 PDF file bhejo\n"
            "⏳ Main automatically quiz banaunga\n"
            "🎯 Multiple choice questions milenge\n\n"
            "**Ready? PDF bhejo!** 😊"
        )

    async def notes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Notes command handler"""
        await update.message.reply_text(
            "📚 **Notes ke liye:**\n\n"
            "💬 'send me notes' likhiye\n"
            "🔍 'math notes' ya specific topic mention kariye\n"
            "📁 Main relevant files forward kar dunga\n\n"
            "**Kya notes chahiye? Batao!** 😊"
        )

    # Group handling methods
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group messages"""
        if update.message.chat.type in ['group', 'supergroup']:
            # Only respond if mentioned or specific keywords
            message_text = update.message.text.lower() if update.message.text else ""
            
            if '@anuj' in message_text or 'quiz' in message_text:
                await update.message.reply_text(
                    "🤖 **Group me Anuj present!**\n\n"
                    "📚 PDF bhejo quiz ke liye\n"
                    "🧠 Quiz conduct kar sakta hun\n"
                    "🎯 Members ka score track karunga\n\n"
                    "**Ready for group quiz?** 😊"
                )

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("quiz", self.quiz_command))
        application.add_handler(CommandHandler("notes", self.notes_command))
        application.add_handler(CommandHandler("memory", self.memory_command))
        
        # Message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # Group message handler
        application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS, 
            self.handle_group_message
        ))
        
        # Start the bot
        logger.info("🤖 Anuj Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = AnujBot()
    bot.run()

