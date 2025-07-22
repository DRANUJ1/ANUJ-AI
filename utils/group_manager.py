"""
Group Manager for Anuj Bot
Handles group quiz conducting and member management
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from utils.quiz_generator import QuizGenerator

logger = logging.getLogger(__name__)

class GroupManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.quiz_generator = QuizGenerator()
        
        # Active group quizzes
        self.active_quizzes = {}
        
        # Quiz settings
        self.default_quiz_settings = {
            'time_limit': 300,  # 5 minutes
            'questions_per_quiz': 5,
            'show_answers': True,
            'allow_retakes': False
        }
    
    async def handle_group_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot being added to a group"""
        try:
            chat = update.effective_chat
            user = update.effective_user
            
            if chat.type in ['group', 'supergroup']:
                # Add group to database
                self.add_group(chat.id, chat.title, chat.type, user.id)
                
                welcome_message = f"""
🤖 **Namaste! Main Anuj hun, aapka Personal Assistant!**

🎉 **Group me welcome!** Main yahan kya kar sakta hun:

📚 **Quiz Features:**
• PDF bhejo → Quiz generate karunga
• Group quiz conduct kar sakta hun
• Members ka score track karunga
• Leaderboard maintain karunga

🧠 **Smart Features:**
• Doubts solve kar sakta hun
• Files manage kar sakta hun
• Context samajhta hun

**Commands:**
/groupquiz - Group quiz start karo
/leaderboard - Scores dekho
/quizsettings - Quiz settings change karo

**Ready for some fun learning?** 😊
                """
                
                await update.message.reply_text(welcome_message)
                
        except Exception as e:
            logger.error(f"Error handling group join: {e}")
    
    def add_group(self, group_id: int, group_name: str, group_type: str, admin_user_id: int):
        """Add group to database"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Check if group exists
                cursor.execute("SELECT group_id FROM groups WHERE group_id = ?", (group_id,))
                exists = cursor.fetchone()
                
                if not exists:
                    cursor.execute('''
                        INSERT INTO groups (group_id, group_name, group_type, admin_user_id)
                        VALUES (?, ?, ?, ?)
                    ''', (group_id, group_name, group_type, admin_user_id))
                    
                    logger.info(f"Added group {group_id} to database")
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Error adding group {group_id}: {e}")
    
    def add_group_member(self, group_id: int, user_id: int, role: str = 'member'):
        """Add member to group"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Check if member already exists
                cursor.execute('''
                    SELECT id FROM group_members 
                    WHERE group_id = ? AND user_id = ?
                ''', (group_id, user_id))
                exists = cursor.fetchone()
                
                if not exists:
                    cursor.execute('''
                        INSERT INTO group_members (group_id, user_id, role)
                        VALUES (?, ?, ?)
                    ''', (group_id, user_id, role))
                else:
                    # Update if inactive
                    cursor.execute('''
                        UPDATE group_members 
                        SET is_active = TRUE, joined_at = CURRENT_TIMESTAMP
                        WHERE group_id = ? AND user_id = ?
                    ''', (group_id, user_id))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Error adding group member: {e}")
    
    async def start_group_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              quiz_data: Dict = None):
        """Start a quiz in the group"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            # Check if quiz is already active
            if chat_id in self.active_quizzes:
                await update.message.reply_text(
                    "🧠 **Quiz already active!**\n\nPehle current quiz complete karo."
                )
                return
            
            # Use provided quiz or generate a default one
            if not quiz_data:
                quiz_data = await self.generate_default_quiz()
            
            if not quiz_data or not quiz_data.get('questions'):
                await update.message.reply_text(
                    "❌ **Quiz generate nahi hua!**\n\nPDF bhejo ya phir try karo."
                )
                return
            
            # Initialize quiz session
            quiz_session = {
                'quiz_data': quiz_data,
                'current_question': 0,
                'participants': {},
                'start_time': datetime.now(),
                'settings': self.default_quiz_settings.copy(),
                'admin_user_id': user_id
            }
            
            self.active_quizzes[chat_id] = quiz_session
            
            # Send quiz introduction
            intro_message = f"""
🧠 **Group Quiz Started!**

📚 **Quiz:** {quiz_data.get('title', 'General Quiz')}
🎯 **Questions:** {len(quiz_data['questions'])}
⏰ **Time Limit:** {quiz_session['settings']['time_limit']} seconds per question

**Ready to participate?** Click the button below!
            """
            
            keyboard = [[InlineKeyboardButton("🎯 Join Quiz", callback_data=f"join_quiz_{chat_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(intro_message, reply_markup=reply_markup)
            
            # Wait for participants (30 seconds)
            await asyncio.sleep(30)
            
            # Start first question
            await self.send_question(update, context, chat_id)
            
        except Exception as e:
            logger.error(f"Error starting group quiz: {e}")
            await update.message.reply_text("❌ Quiz start karne me error aayi!")
    
    async def handle_quiz_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user joining quiz"""
        try:
            query = update.callback_query
            await query.answer()
            
            chat_id = int(query.data.split('_')[-1])
            user_id = query.from_user.id
            user_name = query.from_user.first_name
            
            if chat_id not in self.active_quizzes:
                await query.edit_message_text("❌ Quiz expired or not found!")
                return
            
            quiz_session = self.active_quizzes[chat_id]
            
            # Add participant
            quiz_session['participants'][user_id] = {
                'name': user_name,
                'score': 0,
                'answers': [],
                'join_time': datetime.now()
            }
            
            # Add to group members
            self.add_group_member(chat_id, user_id)
            
            await query.edit_message_text(
                f"✅ **{user_name} joined the quiz!**\n\n"
                f"👥 **Participants:** {len(quiz_session['participants'])}"
            )
            
        except Exception as e:
            logger.error(f"Error handling quiz join: {e}")
    
    async def send_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
        """Send current question to group"""
        try:
            if chat_id not in self.active_quizzes:
                return
            
            quiz_session = self.active_quizzes[chat_id]
            questions = quiz_session['quiz_data']['questions']
            current_q_index = quiz_session['current_question']
            
            if current_q_index >= len(questions):
                await self.end_quiz(update, context, chat_id)
                return
            
            question = questions[current_q_index]
            
            # Create question message
            question_text = f"""
🧠 **Question {current_q_index + 1}/{len(questions)}**

**{question['question']}**

A. {question['options'][0]}
B. {question['options'][1]}
C. {question['options'][2]}
D. {question['options'][3]}

⏰ **Time:** {quiz_session['settings']['time_limit']} seconds
            """
            
            # Create answer buttons
            keyboard = [
                [
                    InlineKeyboardButton("A", callback_data=f"answer_{chat_id}_A"),
                    InlineKeyboardButton("B", callback_data=f"answer_{chat_id}_B")
                ],
                [
                    InlineKeyboardButton("C", callback_data=f"answer_{chat_id}_C"),
                    InlineKeyboardButton("D", callback_data=f"answer_{chat_id}_D")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send question
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=question_text,
                reply_markup=reply_markup
            )
            
            quiz_session['current_message_id'] = message.message_id
            quiz_session['question_start_time'] = datetime.now()
            
            # Set timer for next question
            context.job_queue.run_once(
                self.question_timeout,
                quiz_session['settings']['time_limit'],
                data={'chat_id': chat_id, 'question_index': current_q_index}
            )
            
        except Exception as e:
            logger.error(f"Error sending question: {e}")
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user answer"""
        try:
            query = update.callback_query
            await query.answer()
            
            data_parts = query.data.split('_')
            chat_id = int(data_parts[1])
            answer = data_parts[2]
            user_id = query.from_user.id
            
            if chat_id not in self.active_quizzes:
                return
            
            quiz_session = self.active_quizzes[chat_id]
            
            if user_id not in quiz_session['participants']:
                await query.answer("❌ Quiz join nahi kiya hai!", show_alert=True)
                return
            
            current_q_index = quiz_session['current_question']
            questions = quiz_session['quiz_data']['questions']
            
            if current_q_index >= len(questions):
                return
            
            current_question = questions[current_q_index]
            participant = quiz_session['participants'][user_id]
            
            # Check if already answered
            if len(participant['answers']) > current_q_index:
                await query.answer("❌ Already answered!", show_alert=True)
                return
            
            # Record answer
            is_correct = answer == current_question['answer']
            participant['answers'].append({
                'question_index': current_q_index,
                'answer': answer,
                'correct': is_correct,
                'time_taken': (datetime.now() - quiz_session['question_start_time']).seconds
            })
            
            if is_correct:
                participant['score'] += 1
            
            await query.answer(
                "✅ Answer recorded!" if is_correct else "❌ Wrong answer!",
                show_alert=True
            )
            
        except Exception as e:
            logger.error(f"Error handling answer: {e}")
    
    async def question_timeout(self, context: ContextTypes.DEFAULT_TYPE):
        """Handle question timeout"""
        try:
            job_data = context.job.data
            chat_id = job_data['chat_id']
            question_index = job_data['question_index']
            
            if chat_id not in self.active_quizzes:
                return
            
            quiz_session = self.active_quizzes[chat_id]
            
            # Move to next question
            quiz_session['current_question'] += 1
            
            # Show correct answer
            questions = quiz_session['quiz_data']['questions']
            if question_index < len(questions):
                correct_answer = questions[question_index]['answer']
                explanation = questions[question_index].get('explanation', '')
                
                answer_text = f"""
⏰ **Time's up!**

✅ **Correct Answer:** {correct_answer}
{f"💡 **Explanation:** {explanation}" if explanation else ""}

**Moving to next question...**
                """
                
                await context.bot.send_message(chat_id=chat_id, text=answer_text)
            
            # Send next question or end quiz
            if quiz_session['current_question'] < len(questions):
                await asyncio.sleep(3)  # Brief pause
                # Note: We need to create a dummy update object for send_question
                # In a real implementation, you'd handle this differently
                await self.send_next_question(context, chat_id)
            else:
                await self.end_quiz_from_timeout(context, chat_id)
            
        except Exception as e:
            logger.error(f"Error in question timeout: {e}")
    
    async def send_next_question(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
        """Send next question (helper for timeout)"""
        try:
            if chat_id not in self.active_quizzes:
                return
            
            quiz_session = self.active_quizzes[chat_id]
            questions = quiz_session['quiz_data']['questions']
            current_q_index = quiz_session['current_question']
            
            if current_q_index >= len(questions):
                await self.end_quiz_from_timeout(context, chat_id)
                return
            
            question = questions[current_q_index]
            
            question_text = f"""
🧠 **Question {current_q_index + 1}/{len(questions)}**

**{question['question']}**

A. {question['options'][0]}
B. {question['options'][1]}
C. {question['options'][2]}
D. {question['options'][3]}

⏰ **Time:** {quiz_session['settings']['time_limit']} seconds
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("A", callback_data=f"answer_{chat_id}_A"),
                    InlineKeyboardButton("B", callback_data=f"answer_{chat_id}_B")
                ],
                [
                    InlineKeyboardButton("C", callback_data=f"answer_{chat_id}_C"),
                    InlineKeyboardButton("D", callback_data=f"answer_{chat_id}_D")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=question_text,
                reply_markup=reply_markup
            )
            
            quiz_session['question_start_time'] = datetime.now()
            
            # Set timer for next question
            context.job_queue.run_once(
                self.question_timeout,
                quiz_session['settings']['time_limit'],
                data={'chat_id': chat_id, 'question_index': current_q_index}
            )
            
        except Exception as e:
            logger.error(f"Error sending next question: {e}")
    
    async def end_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
        """End quiz and show results"""
        try:
            if chat_id not in self.active_quizzes:
                return
            
            quiz_session = self.active_quizzes[chat_id]
            participants = quiz_session['participants']
            
            if not participants:
                await update.message.reply_text("❌ **No participants!** Quiz cancelled.")
                del self.active_quizzes[chat_id]
                return
            
            # Calculate results
            results = []
            for user_id, participant in participants.items():
                results.append({
                    'user_id': user_id,
                    'name': participant['name'],
                    'score': participant['score'],
                    'total': len(quiz_session['quiz_data']['questions']),
                    'percentage': (participant['score'] / len(quiz_session['quiz_data']['questions'])) * 100
                })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Create results message
            results_text = "🏆 **Quiz Results!**\n\n"
            
            for i, result in enumerate(results[:10], 1):  # Top 10
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                results_text += f"{emoji} **{result['name']}** - {result['score']}/{result['total']} ({result['percentage']:.1f}%)\n"
            
            results_text += f"\n🎯 **Total Participants:** {len(participants)}"
            results_text += f"\n⏰ **Quiz Duration:** {(datetime.now() - quiz_session['start_time']).seconds // 60} minutes"
            
            await context.bot.send_message(chat_id=chat_id, text=results_text)
            
            # Store results in database
            self.store_quiz_results(chat_id, quiz_session, results)
            
            # Clean up
            del self.active_quizzes[chat_id]
            
        except Exception as e:
            logger.error(f"Error ending quiz: {e}")
    
    async def end_quiz_from_timeout(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
        """End quiz from timeout (helper method)"""
        try:
            if chat_id not in self.active_quizzes:
                return
            
            quiz_session = self.active_quizzes[chat_id]
            participants = quiz_session['participants']
            
            # Calculate results
            results = []
            for user_id, participant in participants.items():
                results.append({
                    'user_id': user_id,
                    'name': participant['name'],
                    'score': participant['score'],
                    'total': len(quiz_session['quiz_data']['questions']),
                    'percentage': (participant['score'] / len(quiz_session['quiz_data']['questions'])) * 100
                })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            
            results_text = "🏆 **Quiz Completed!**\n\n"
            
            for i, result in enumerate(results[:10], 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                results_text += f"{emoji} **{result['name']}** - {result['score']}/{result['total']} ({result['percentage']:.1f}%)\n"
            
            results_text += f"\n🎯 **Total Participants:** {len(participants)}"
            
            await context.bot.send_message(chat_id=chat_id, text=results_text)
            
            # Store results
            self.store_quiz_results(chat_id, quiz_session, results)
            
            # Clean up
            del self.active_quizzes[chat_id]
            
        except Exception as e:
            logger.error(f"Error ending quiz from timeout: {e}")
    
    def store_quiz_results(self, chat_id: int, quiz_session: Dict, results: List[Dict]):
        """Store quiz results in database"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Store group quiz session
                cursor.execute('''
                    INSERT INTO group_quiz_sessions 
                    (group_id, quiz_title, start_time, end_time, total_participants, quiz_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    chat_id,
                    quiz_session['quiz_data'].get('title', 'Group Quiz'),
                    quiz_session['start_time'].isoformat(),
                    datetime.now().isoformat(),
                    len(results),
                    json.dumps(quiz_session['quiz_data'])
                ))
                
                session_id = cursor.lastrowid
                
                # Store individual results
                for result in results:
                    cursor.execute('''
                        INSERT INTO group_quiz_results
                        (session_id, user_id, score, total_questions, percentage)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        session_id,
                        result['user_id'],
                        result['score'],
                        result['total'],
                        result['percentage']
                    ))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Error storing quiz results: {e}")
    
    async def generate_default_quiz(self) -> Dict:
        """Generate a default quiz for groups"""
        try:
            # Simple general knowledge questions
            default_questions = [
                {
                    "question": "Bharat ka capital kya hai?",
                    "options": ["Mumbai", "Delhi", "Kolkata", "Chennai"],
                    "answer": "B",
                    "explanation": "New Delhi is the capital of India"
                },
                {
                    "question": "2 + 2 = ?",
                    "options": ["3", "4", "5", "6"],
                    "answer": "B",
                    "explanation": "Basic addition: 2 + 2 = 4"
                },
                {
                    "question": "Sabse bada planet kaun sa hai?",
                    "options": ["Earth", "Jupiter", "Saturn", "Mars"],
                    "answer": "B",
                    "explanation": "Jupiter is the largest planet in our solar system"
                },
                {
                    "question": "HTML ka full form kya hai?",
                    "options": ["Hyper Text Markup Language", "High Tech Modern Language", "Home Tool Markup Language", "Hyperlink Text Management Language"],
                    "answer": "A",
                    "explanation": "HTML stands for Hyper Text Markup Language"
                },
                {
                    "question": "1 minute me kitne seconds hote hai?",
                    "options": ["50", "60", "70", "80"],
                    "answer": "B",
                    "explanation": "1 minute = 60 seconds"
                }
            ]
            
            return {
                'title': 'General Knowledge Quiz',
                'questions': default_questions,
                'total_questions': len(default_questions),
                'difficulty': 'easy'
            }
            
        except Exception as e:
            logger.error(f"Error generating default quiz: {e}")
            return None
    
    async def get_group_leaderboard(self, chat_id: int, limit: int = 10) -> str:
        """Get group leaderboard"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Get top performers
                cursor.execute('''
                    SELECT u.first_name, AVG(gqr.percentage) as avg_score, COUNT(gqr.session_id) as quiz_count
                    FROM group_quiz_results gqr
                    JOIN users u ON gqr.user_id = u.user_id
                    JOIN group_quiz_sessions gqs ON gqr.session_id = gqs.id
                    WHERE gqs.group_id = ?
                    GROUP BY gqr.user_id, u.first_name
                    ORDER BY avg_score DESC, quiz_count DESC
                    LIMIT ?
                ''', (chat_id, limit))
                
                results = cursor.fetchall()
                conn.close()
                
                if not results:
                    return "📊 **No quiz data available!**\n\nPehle koi quiz khelo!"
                
                leaderboard_text = "🏆 **Group Leaderboard**\n\n"
                
                for i, (name, avg_score, quiz_count) in enumerate(results, 1):
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    leaderboard_text += f"{emoji} **{name}** - {avg_score:.1f}% avg ({quiz_count} quizzes)\n"
                
                return leaderboard_text
                
        except Exception as e:
            logger.error(f"Error getting group leaderboard: {e}")
            return "❌ Error getting leaderboard!"

