"""
Context Manager for Anuj Bot
Handles context understanding and intelligent responses
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # Intent patterns for context understanding
        self.intent_patterns = {
            'file_request': [
                r'send me (.*)',
                r'(.*) notes chahiye',
                r'(.*) file do',
                r'share (.*)',
                r'(.*) notes bhejo'
            ],
            'quiz_request': [
                r'quiz (.*)',
                r'test (.*)',
                r'questions (.*)',
                r'mcq (.*)'
            ],
            'doubt_solving': [
                r'doubt (.*)',
                r'problem (.*)',
                r'help (.*)',
                r'solve (.*)',
                r'explain (.*)'
            ],
            'greeting': [
                r'hi|hello|hey|namaste|namaskar',
                r'good morning|good afternoon|good evening',
                r'kaise ho|how are you'
            ],
            'thanks': [
                r'thanks|thank you|dhanyawad|shukriya',
                r'great|awesome|perfect|excellent'
            ],
            'best_wishes': [
                r'best wishes|good luck|all the best',
                r'wish you|wishing you'
            ]
        }
        
        # Subject keywords for context
        self.subject_keywords = {
            'math': ['math', 'mathematics', 'algebra', 'geometry', 'calculus', 'trigonometry', 'statistics'],
            'physics': ['physics', 'mechanics', 'thermodynamics', 'optics', 'electricity', 'magnetism'],
            'chemistry': ['chemistry', 'organic', 'inorganic', 'physical chemistry', 'biochemistry'],
            'biology': ['biology', 'botany', 'zoology', 'genetics', 'ecology', 'anatomy'],
            'computer': ['computer', 'programming', 'coding', 'software', 'algorithm', 'data structure'],
            'english': ['english', 'grammar', 'literature', 'essay', 'writing', 'reading'],
            'hindi': ['hindi', 'sahitya', 'vyakaran', 'kavita', 'kahani']
        }
        
        # Response templates
        self.response_templates = {
            'file_request': [
                "🔍 **{subject} files dhund raha hun...**\n\nYahan hai aapki files:",
                "📚 **{subject} notes mil gayi!**\n\nCheck karo:",
                "✅ **{subject} ke liye files ready hai:**"
            ],
            'quiz_request': [
                "🧠 **{subject} quiz banata hun!**\n\nPDF bhejo ya topic batao:",
                "🎯 **Quiz time!**\n\n{subject} ke liye ready ho?",
                "📝 **{subject} quiz generate kar raha hun...**"
            ],
            'doubt_solving': [
                "🤔 **{subject} doubt solve karta hun!**\n\nImage bhejo ya detail me batao:",
                "💡 **Doubt clear karte hai!**\n\n{subject} me kya problem hai?",
                "🎯 **{subject} doubt? No problem!**\n\nExplain karo detail me:"
            ],
            'general_help': [
                "😊 **Main Anuj hun, aapka personal assistant!**\n\nKya help chahiye?",
                "🤖 **Anuj here!**\n\nBatao kya karna hai:",
                "✨ **Ready to help!**\n\nKoi doubt, file, ya quiz chahiye?"
            ]
        }
    
    def analyze_message_context(self, user_id: int, message: str) -> Dict:
        """Analyze message context and intent"""
        try:
            # Get user's conversation history
            history = self.db_manager.get_user_history(user_id, limit=5)
            user_context = self.db_manager.get_user_context(user_id)
            
            # Detect intent
            intent = self.detect_intent(message)
            
            # Extract subject/topic
            subject = self.extract_subject(message, history)
            
            # Determine response type
            response_type = self.determine_response_type(intent, subject, user_context)
            
            # Get contextual information
            contextual_info = self.get_contextual_info(user_id, intent, subject)
            
            context_analysis = {
                'intent': intent,
                'subject': subject,
                'response_type': response_type,
                'contextual_info': contextual_info,
                'user_history': history,
                'confidence': self.calculate_confidence(intent, subject, message)
            }
            
            # Update user context
            self.update_user_context(user_id, intent, subject, context_analysis)
            
            return context_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing message context: {e}")
            return {
                'intent': 'general',
                'subject': 'general',
                'response_type': 'general_help',
                'contextual_info': {},
                'confidence': 0.5
            }
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        # Default intent based on keywords
        if any(word in message_lower for word in ['file', 'notes', 'send', 'share']):
            return 'file_request'
        elif any(word in message_lower for word in ['quiz', 'test', 'questions']):
            return 'quiz_request'
        elif any(word in message_lower for word in ['doubt', 'problem', 'help', 'solve']):
            return 'doubt_solving'
        elif any(word in message_lower for word in ['thanks', 'thank']):
            return 'thanks'
        elif any(word in message_lower for word in ['best wishes', 'good luck']):
            return 'best_wishes'
        else:
            return 'general'
    
    def extract_subject(self, message: str, history: List[Dict]) -> str:
        """Extract subject/topic from message and history"""
        message_lower = message.lower()
        
        # Check for subject keywords in current message
        for subject, keywords in self.subject_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return subject
        
        # Check recent conversation history
        for msg in history[-3:]:  # Last 3 messages
            msg_text = msg.get('message', '').lower()
            for subject, keywords in self.subject_keywords.items():
                if any(keyword in msg_text for keyword in keywords):
                    return subject
        
        return 'general'
    
    def determine_response_type(self, intent: str, subject: str, user_context: Dict) -> str:
        """Determine appropriate response type"""
        # Map intent to response type
        intent_to_response = {
            'file_request': 'file_request',
            'quiz_request': 'quiz_request',
            'doubt_solving': 'doubt_solving',
            'greeting': 'general_help',
            'thanks': 'thanks',
            'best_wishes': 'best_wishes',
            'general': 'general_help'
        }
        
        return intent_to_response.get(intent, 'general_help')
    
    def get_contextual_info(self, user_id: int, intent: str, subject: str) -> Dict:
        """Get contextual information based on intent and subject"""
        contextual_info = {}
        
        try:
            if intent == 'file_request':
                # Get user's files related to subject
                from utils.file_manager import FileManager
                file_manager = FileManager()
                
                if subject != 'general':
                    files = file_manager.search_files(user_id, subject)
                else:
                    files = file_manager.get_user_files(user_id, limit=5)
                
                contextual_info['relevant_files'] = files
                contextual_info['file_count'] = len(files)
            
            elif intent == 'quiz_request':
                # Get user's quiz history
                from utils.quiz_generator import QuizGenerator
                quiz_generator = QuizGenerator()
                
                quizzes = quiz_generator.get_user_quizzes(user_id, limit=3)
                contextual_info['recent_quizzes'] = quizzes
                contextual_info['quiz_count'] = len(quizzes)
            
            elif intent == 'doubt_solving':
                # Get recent doubts/problems
                history = self.db_manager.get_user_history(user_id, limit=10)
                doubt_messages = [msg for msg in history if 'doubt' in msg.get('message', '').lower()]
                contextual_info['recent_doubts'] = doubt_messages[-3:]
            
        except Exception as e:
            logger.error(f"Error getting contextual info: {e}")
        
        return contextual_info
    
    def calculate_confidence(self, intent: str, subject: str, message: str) -> float:
        """Calculate confidence score for context analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on clear intent indicators
        if intent != 'general':
            confidence += 0.2
        
        # Increase confidence based on subject detection
        if subject != 'general':
            confidence += 0.2
        
        # Increase confidence based on message clarity
        if len(message.split()) > 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def update_user_context(self, user_id: int, intent: str, subject: str, context_analysis: Dict):
        """Update user's context in database"""
        try:
            current_context = self.db_manager.get_user_context(user_id)
            
            # Update context data
            context_data = current_context.get('context_data', {})
            context_data.update({
                'last_intent': intent,
                'last_subject': subject,
                'last_analysis': context_analysis,
                'updated_at': datetime.now().isoformat()
            })
            
            # Update topic if it's more specific
            topic = subject if subject != 'general' else current_context.get('current_topic', 'general')
            
            self.db_manager.update_user_context(user_id, topic, context_data)
            
        except Exception as e:
            logger.error(f"Error updating user context: {e}")
    
    def generate_contextual_response(self, context_analysis: Dict, user_name: str = "Friend") -> str:
        """Generate contextual response based on analysis"""
        try:
            intent = context_analysis.get('intent', 'general')
            subject = context_analysis.get('subject', 'general')
            response_type = context_analysis.get('response_type', 'general_help')
            contextual_info = context_analysis.get('contextual_info', {})
            
            # Handle special responses
            if intent == 'thanks':
                return self.get_thanks_response(user_name)
            elif intent == 'best_wishes':
                return self.get_best_wishes_response()
            
            # Get appropriate template
            templates = self.response_templates.get(response_type, self.response_templates['general_help'])
            template = templates[0]  # Use first template for now
            
            # Format template with context
            if '{subject}' in template:
                subject_display = subject.title() if subject != 'general' else 'General'
                response = template.format(subject=subject_display)
            else:
                response = template
            
            # Add contextual information
            if response_type == 'file_request' and contextual_info.get('file_count', 0) == 0:
                response += "\n\n❌ **Koi files nahi mili!**\nPehle kuch files upload karo."
            
            elif response_type == 'quiz_request' and contextual_info.get('quiz_count', 0) > 0:
                response += f"\n\n📊 **Previous quizzes:** {contextual_info['quiz_count']}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "😊 **Anuj here!** Kya help chahiye?"
    
    def get_thanks_response(self, user_name: str) -> str:
        """Get special thanks response with surprise"""
        import random
        
        surprise_links = [
            "🎉 https://youtu.be/dQw4w9WgXcQ",
            "🌟 https://youtu.be/ZZ5LpwO-An4", 
            "✨ https://youtu.be/L_jWHffIx5E",
            "🎊 https://youtu.be/fJ9rUzIMcZQ"
        ]
        
        surprise_link = random.choice(surprise_links)
        
        return f"""🎉 **Welcome {user_name}!**

Yahan hai aapke liye ek surprise: {surprise_link}

✨ **Aur koi doubt hai? Puchte raho!**
🤔 **Suffering karte rahne se kya fayda - ask away!** 😊"""
    
    def get_best_wishes_response(self) -> str:
        """Get best wishes response"""
        import random
        
        responses = [
            "🌟 **Best wishes to you too!** Aur koi doubt hai? Puchte raho, main yahan hun!",
            "✨ **Thank you!** Koi aur question hai? Don't suffer in silence, ask away!",
            "🎉 **Best wishes!** Aur doubts lao, main solve kar dunga!",
            "🌈 **Same to you!** Koi problem ho toh batana, suffering karne ki zarurat nahi!"
        ]
        
        return random.choice(responses)
    
    def get_conversation_summary(self, user_id: int, days: int = 7) -> Dict:
        """Get conversation summary for user"""
        try:
            # Get recent conversations
            history = self.db_manager.get_user_history(user_id, limit=50)
            
            if not history:
                return {'summary': 'No recent conversations'}
            
            # Analyze conversation patterns
            intents = []
            subjects = []
            
            for msg in history:
                if msg['sender'] == 'user':
                    intent = self.detect_intent(msg['message'])
                    subject = self.extract_subject(msg['message'], [])
                    intents.append(intent)
                    subjects.append(subject)
            
            # Count frequencies
            from collections import Counter
            intent_counts = Counter(intents)
            subject_counts = Counter(subjects)
            
            summary = {
                'total_messages': len(history),
                'user_messages': len([m for m in history if m['sender'] == 'user']),
                'bot_messages': len([m for m in history if m['sender'] == 'bot']),
                'top_intents': dict(intent_counts.most_common(3)),
                'top_subjects': dict(subject_counts.most_common(3)),
                'conversation_period': f"Last {days} days"
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {'summary': 'Error generating summary'}
    
    def predict_user_needs(self, user_id: int) -> List[str]:
        """Predict what user might need based on context"""
        try:
            context = self.db_manager.get_user_context(user_id)
            history = self.db_manager.get_user_history(user_id, limit=10)
            
            predictions = []
            
            # Based on recent activity
            recent_intents = [self.detect_intent(msg['message']) for msg in history[-5:] if msg['sender'] == 'user']
            
            if 'file_request' in recent_intents:
                predictions.append("User might need more files or notes")
            
            if 'doubt_solving' in recent_intents:
                predictions.append("User might have more doubts to solve")
            
            if 'quiz_request' in recent_intents:
                predictions.append("User might want to practice more quizzes")
            
            # Based on subjects
            last_subject = context.get('context_data', {}).get('last_subject', 'general')
            if last_subject != 'general':
                predictions.append(f"User might need more {last_subject} related help")
            
            return predictions[:3]  # Top 3 predictions
            
        except Exception as e:
            logger.error(f"Error predicting user needs: {e}")
            return []
    
    def should_proactive_help(self, user_id: int) -> bool:
        """Determine if bot should offer proactive help"""
        try:
            context = self.db_manager.get_user_context(user_id)
            
            # Check if user has been inactive
            last_updated = context.get('last_updated')
            if last_updated:
                last_update_time = datetime.fromisoformat(last_updated)
                if (datetime.now() - last_update_time).days > 1:
                    return True
            
            # Check if user had repeated failed attempts
            query_count = context.get('query_count', 0)
            if query_count > 5:  # Many queries might indicate confusion
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking proactive help: {e}")
            return False

