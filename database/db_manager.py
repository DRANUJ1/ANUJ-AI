"""
Database Manager for Anuj Bot
Handles user data, memory, and conversation history
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "database/anuj_bot.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_bot BOOLEAN DEFAULT FALSE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    preferences TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Conversations table for message history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    sender TEXT CHECK(sender IN ('user', 'bot')),
                    message_type TEXT DEFAULT 'text',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context_data TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Files table for file management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    filepath TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    tags TEXT DEFAULT '[]',
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Quizzes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quizzes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    questions TEXT,  -- JSON format
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_questions INTEGER,
                    source_file TEXT,
                    difficulty TEXT DEFAULT 'medium',
                    subject TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Quiz attempts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id INTEGER,
                    user_id INTEGER,
                    answers TEXT,  -- JSON format
                    score INTEGER,
                    total_questions INTEGER,
                    attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    time_taken INTEGER,  -- in seconds
                    FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # User context table for maintaining conversation context
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_context (
                    user_id INTEGER PRIMARY KEY,
                    current_topic TEXT,
                    context_data TEXT DEFAULT '{}',
                    last_query TEXT,
                    query_count INTEGER DEFAULT 0,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Group management table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    group_name TEXT,
                    group_type TEXT,
                    admin_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # Group members table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    user_id INTEGER,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (group_id) REFERENCES groups (group_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, language_code: str = None) -> bool:
        """Add or update user in database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing user
                    cursor.execute('''
                        UPDATE users 
                        SET username = ?, first_name = ?, last_name = ?, 
                            language_code = ?, last_active = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (username, first_name, last_name, language_code, user_id))
                else:
                    # Insert new user
                    cursor.execute('''
                        INSERT INTO users (user_id, username, first_name, last_name, language_code)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, username, first_name, last_name, language_code))
                    
                    # Initialize user context
                    cursor.execute('''
                        INSERT INTO user_context (user_id, context_data)
                        VALUES (?, '{}')
                    ''', (user_id,))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    def add_message(self, user_id: int, message: str, sender: str, 
                   message_type: str = 'text', context_data: Dict = None) -> bool:
        """Add message to conversation history"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                context_json = json.dumps(context_data or {})
                
                cursor.execute('''
                    INSERT INTO conversations (user_id, message, sender, message_type, context_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, message, sender, message_type, context_json))
                
                # Update user's total messages and last active
                cursor.execute('''
                    UPDATE users 
                    SET total_messages = total_messages + 1, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
                
                # Update user context
                cursor.execute('''
                    UPDATE user_context 
                    SET last_query = ?, query_count = query_count + 1, 
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (message if sender == 'user' else '', user_id))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return False
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's conversation history"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT message, sender, message_type, timestamp, context_data
                    FROM conversations 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                history = []
                for row in rows:
                    history.append({
                        'message': row[0],
                        'sender': row[1],
                        'message_type': row[2],
                        'timestamp': row[3],
                        'context_data': json.loads(row[4] or '{}')
                    })
                
                return list(reversed(history))  # Return in chronological order
                
        except Exception as e:
            logger.error(f"Error getting history for user {user_id}: {e}")
            return []
    
    def get_user_context(self, user_id: int) -> Dict:
        """Get user's current context"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT current_topic, context_data, last_query, query_count
                    FROM user_context 
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        'current_topic': row[0],
                        'context_data': json.loads(row[1] or '{}'),
                        'last_query': row[2],
                        'query_count': row[3]
                    }
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting context for user {user_id}: {e}")
            return {}
    
    def update_user_context(self, user_id: int, topic: str = None, 
                           context_data: Dict = None) -> bool:
        """Update user's context"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if topic:
                    updates.append("current_topic = ?")
                    params.append(topic)
                
                if context_data:
                    updates.append("context_data = ?")
                    params.append(json.dumps(context_data))
                
                if updates:
                    updates.append("last_updated = CURRENT_TIMESTAMP")
                    params.append(user_id)
                    
                    query = f"UPDATE user_context SET {', '.join(updates)} WHERE user_id = ?"
                    cursor.execute(query, params)
                    
                    conn.commit()
                
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Error updating context for user {user_id}: {e}")
            return False
    
    def add_file(self, user_id: int, filename: str, filepath: str, 
                file_type: str, file_size: int, description: str = None, 
                tags: List[str] = None) -> int:
        """Add file record to database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                tags_json = json.dumps(tags or [])
                
                cursor.execute('''
                    INSERT INTO files (user_id, filename, filepath, file_type, 
                                     file_size, description, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, filename, filepath, file_type, file_size, 
                      description, tags_json))
                
                file_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return file_id
                
        except Exception as e:
            logger.error(f"Error adding file for user {user_id}: {e}")
            return 0
    
    def get_user_files(self, user_id: int, file_type: str = None, 
                      limit: int = 10) -> List[Dict]:
        """Get user's files"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                if file_type:
                    cursor.execute('''
                        SELECT id, filename, filepath, file_type, file_size, 
                               upload_date, description, tags
                        FROM files 
                        WHERE user_id = ? AND file_type = ? AND is_active = TRUE
                        ORDER BY upload_date DESC 
                        LIMIT ?
                    ''', (user_id, file_type, limit))
                else:
                    cursor.execute('''
                        SELECT id, filename, filepath, file_type, file_size, 
                               upload_date, description, tags
                        FROM files 
                        WHERE user_id = ? AND is_active = TRUE
                        ORDER BY upload_date DESC 
                        LIMIT ?
                    ''', (user_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                files = []
                for row in rows:
                    files.append({
                        'id': row[0],
                        'filename': row[1],
                        'filepath': row[2],
                        'file_type': row[3],
                        'file_size': row[4],
                        'upload_date': row[5],
                        'description': row[6],
                        'tags': json.loads(row[7] or '[]')
                    })
                
                return files
                
        except Exception as e:
            logger.error(f"Error getting files for user {user_id}: {e}")
            return []
    
    def add_quiz(self, user_id: int, title: str, questions: List[Dict], 
                source_file: str = None, subject: str = None, 
                difficulty: str = 'medium') -> int:
        """Add quiz to database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                questions_json = json.dumps(questions)
                total_questions = len(questions)
                
                cursor.execute('''
                    INSERT INTO quizzes (user_id, title, questions, total_questions, 
                                       source_file, subject, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, title, questions_json, total_questions, 
                      source_file, subject, difficulty))
                
                quiz_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return quiz_id
                
        except Exception as e:
            logger.error(f"Error adding quiz for user {user_id}: {e}")
            return 0
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Basic user info
                cursor.execute('''
                    SELECT total_messages, created_at, last_active
                    FROM users WHERE user_id = ?
                ''', (user_id,))
                user_row = cursor.fetchone()
                
                # File count
                cursor.execute('''
                    SELECT COUNT(*) FROM files 
                    WHERE user_id = ? AND is_active = TRUE
                ''', (user_id,))
                file_count = cursor.fetchone()[0]
                
                # Quiz count
                cursor.execute('''
                    SELECT COUNT(*) FROM quizzes WHERE user_id = ?
                ''', (user_id,))
                quiz_count = cursor.fetchone()[0]
                
                # Quiz attempts
                cursor.execute('''
                    SELECT COUNT(*), AVG(score) FROM quiz_attempts 
                    WHERE user_id = ?
                ''', (user_id,))
                attempt_row = cursor.fetchone()
                
                conn.close()
                
                if user_row:
                    return {
                        'total_messages': user_row[0],
                        'member_since': user_row[1],
                        'last_active': user_row[2],
                        'files_uploaded': file_count,
                        'quizzes_created': quiz_count,
                        'quiz_attempts': attempt_row[0] or 0,
                        'average_score': round(attempt_row[1] or 0, 2)
                    }
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old conversation data"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    DELETE FROM conversations 
                    WHERE timestamp < ? AND sender = 'user'
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.info(f"Cleaned up {deleted_count} old conversation records")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

