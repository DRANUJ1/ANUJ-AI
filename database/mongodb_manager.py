"""
MongoDB Database Manager for Anuj Bot
Handles user data, memory, and conversation history using MongoDB
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.connected = False
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client.anuj_bot
            
            # Test connection
            await self.client.admin.command('ping')
            self.connected = True
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes for better performance
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.connected = False
            raise
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            await self.db.users.create_index("user_id", unique=True)
            
            # Conversations collection indexes
            await self.db.conversations.create_index([("user_id", 1), ("timestamp", -1)])
            
            # Files collection indexes
            await self.db.files.create_index([("user_id", 1), ("upload_date", -1)])
            
            # Quizzes collection indexes
            await self.db.quizzes.create_index([("user_id", 1), ("created_at", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                      last_name: str = None, language_code: str = None) -> bool:
        """Add or update user in database"""
        try:
            if not self.connected:
                await self.connect()
            
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "language_code": language_code,
                "is_bot": False,
                "is_premium": False,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "total_messages": 0,
                "preferences": {},
                "status": "active"
            }
            
            # Upsert user (update if exists, insert if not)
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                        "language_code": language_code,
                        "last_active": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "user_id": user_id,
                        "is_bot": False,
                        "is_premium": False,
                        "created_at": datetime.utcnow(),
                        "total_messages": 0,
                        "preferences": {},
                        "status": "active"
                    }
                },
                upsert=True
            )
            
            # Initialize user context if new user
            await self.db.user_context.update_one(
                {"user_id": user_id},
                {
                    "$setOnInsert": {
                        "user_id": user_id,
                        "current_topic": "general",
                        "context_data": {},
                        "last_query": "",
                        "query_count": 0,
                        "session_start": datetime.utcnow(),
                        "last_updated": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    async def add_message(self, user_id: int, message: str, sender: str, 
                         message_type: str = 'text', context_data: Dict = None) -> bool:
        """Add message to conversation history"""
        try:
            if not self.connected:
                await self.connect()
            
            message_doc = {
                "user_id": user_id,
                "message": message,
                "sender": sender,
                "message_type": message_type,
                "timestamp": datetime.utcnow(),
                "context_data": context_data or {}
            }
            
            # Insert message
            await self.db.conversations.insert_one(message_doc)
            
            # Update user's total messages and last active
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"total_messages": 1},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
            
            # Update user context
            if sender == 'user':
                await self.db.user_context.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "last_query": message,
                            "last_updated": datetime.utcnow()
                        },
                        "$inc": {"query_count": 1}
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return False
    
    async def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's conversation history"""
        try:
            if not self.connected:
                await self.connect()
            
            cursor = self.db.conversations.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            messages = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string and reverse order (chronological)
            history = []
            for msg in reversed(messages):
                history.append({
                    'message': msg['message'],
                    'sender': msg['sender'],
                    'message_type': msg['message_type'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'context_data': msg.get('context_data', {})
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting history for user {user_id}: {e}")
            return []
    
    async def get_user_context(self, user_id: int) -> Dict:
        """Get user's current context"""
        try:
            if not self.connected:
                await self.connect()
            
            context = await self.db.user_context.find_one({"user_id": user_id})
            
            if context:
                return {
                    'current_topic': context.get('current_topic', 'general'),
                    'context_data': context.get('context_data', {}),
                    'last_query': context.get('last_query', ''),
                    'query_count': context.get('query_count', 0),
                    'last_updated': context.get('last_updated', datetime.utcnow()).isoformat()
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting context for user {user_id}: {e}")
            return {}
    
    async def update_user_context(self, user_id: int, topic: str = None, 
                                 context_data: Dict = None) -> bool:
        """Update user's context"""
        try:
            if not self.connected:
                await self.connect()
            
            update_data = {"last_updated": datetime.utcnow()}
            
            if topic:
                update_data["current_topic"] = topic
            
            if context_data:
                update_data["context_data"] = context_data
            
            await self.db.user_context.update_one(
                {"user_id": user_id},
                {"$set": update_data},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating context for user {user_id}: {e}")
            return False
    
    async def add_file(self, user_id: int, filename: str, filepath: str, 
                      file_type: str, file_size: int, description: str = None, 
                      tags: List[str] = None) -> str:
        """Add file record to database"""
        try:
            if not self.connected:
                await self.connect()
            
            file_doc = {
                "user_id": user_id,
                "filename": filename,
                "filepath": filepath,
                "file_type": file_type,
                "file_size": file_size,
                "upload_date": datetime.utcnow(),
                "description": description,
                "tags": tags or [],
                "is_active": True
            }
            
            result = await self.db.files.insert_one(file_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error adding file for user {user_id}: {e}")
            return ""
    
    async def get_user_files(self, user_id: int, file_type: str = None, 
                            limit: int = 10) -> List[Dict]:
        """Get user's files"""
        try:
            if not self.connected:
                await self.connect()
            
            query = {"user_id": user_id, "is_active": True}
            if file_type:
                query["file_type"] = file_type
            
            cursor = self.db.files.find(query).sort("upload_date", -1).limit(limit)
            files = await cursor.to_list(length=limit)
            
            result = []
            for file_doc in files:
                result.append({
                    'id': str(file_doc['_id']),
                    'filename': file_doc['filename'],
                    'filepath': file_doc['filepath'],
                    'file_type': file_doc['file_type'],
                    'file_size': file_doc['file_size'],
                    'upload_date': file_doc['upload_date'].isoformat(),
                    'description': file_doc.get('description', ''),
                    'tags': file_doc.get('tags', [])
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting files for user {user_id}: {e}")
            return []
    
    async def add_quiz(self, user_id: int, title: str, questions: List[Dict], 
                      source_file: str = None, subject: str = None, 
                      difficulty: str = 'medium') -> str:
        """Add quiz to database"""
        try:
            if not self.connected:
                await self.connect()
            
            quiz_doc = {
                "user_id": user_id,
                "title": title,
                "questions": questions,
                "created_at": datetime.utcnow(),
                "total_questions": len(questions),
                "source_file": source_file,
                "subject": subject,
                "difficulty": difficulty
            }
            
            result = await self.db.quizzes.insert_one(quiz_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error adding quiz for user {user_id}: {e}")
            return ""
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            if not self.connected:
                await self.connect()
            
            # Get user info
            user = await self.db.users.find_one({"user_id": user_id})
            if not user:
                return {}
            
            # Get file count
            file_count = await self.db.files.count_documents({
                "user_id": user_id, 
                "is_active": True
            })
            
            # Get quiz count
            quiz_count = await self.db.quizzes.count_documents({"user_id": user_id})
            
            return {
                'total_messages': user.get('total_messages', 0),
                'member_since': user.get('created_at', datetime.utcnow()).isoformat(),
                'last_active': user.get('last_active', datetime.utcnow()).isoformat(),
                'files_uploaded': file_count,
                'quizzes_created': quiz_count,
                'quiz_attempts': 0,  # TODO: Implement quiz attempts tracking
                'average_score': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            return {}
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old conversation data"""
        try:
            if not self.connected:
                await self.connect()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.db.conversations.delete_many({
                "timestamp": {"$lt": cutoff_date},
                "sender": "user"
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old conversation records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    async def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("MongoDB connection closed")

# Synchronous wrapper for compatibility
class DatabaseManager:
    def __init__(self, connection_string: str = None):
        self.mongo_manager = MongoDBManager(connection_string)
        self.loop = None
    
    def _get_loop(self):
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, language_code: str = None) -> bool:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.add_user(user_id, username, first_name, last_name, language_code)
        )
    
    def add_message(self, user_id: int, message: str, sender: str, 
                   message_type: str = 'text', context_data: Dict = None) -> bool:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.add_message(user_id, message, sender, message_type, context_data)
        )
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.get_user_history(user_id, limit)
        )
    
    def get_user_context(self, user_id: int) -> Dict:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.get_user_context(user_id)
        )
    
    def update_user_context(self, user_id: int, topic: str = None, 
                           context_data: Dict = None) -> bool:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.update_user_context(user_id, topic, context_data)
        )
    
    def add_file(self, user_id: int, filename: str, filepath: str, 
                file_type: str, file_size: int, description: str = None, 
                tags: List[str] = None) -> str:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.add_file(user_id, filename, filepath, file_type, file_size, description, tags)
        )
    
    def get_user_files(self, user_id: int, file_type: str = None, 
                      limit: int = 10) -> List[Dict]:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.get_user_files(user_id, file_type, limit)
        )
    
    def add_quiz(self, user_id: int, title: str, questions: List[Dict], 
                source_file: str = None, subject: str = None, 
                difficulty: str = 'medium') -> str:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.add_quiz(user_id, title, questions, source_file, subject, difficulty)
        )
    
    def get_user_stats(self, user_id: int) -> Dict:
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.get_user_stats(user_id)
        )
    
    def cleanup_old_data(self, days: int = 30):
        loop = self._get_loop()
        return loop.run_until_complete(
            self.mongo_manager.cleanup_old_data(days)
        )

