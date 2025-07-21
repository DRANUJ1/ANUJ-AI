"""
File Manager for Anuj Bot
Handles file storage, categorization, and retrieval
"""

import os
import shutil
import mimetypes
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from config.settings import FILES_DIR, MAX_FILE_SIZE, FILE_STORAGE_CHANNEL_ID
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.files_dir = Path(FILES_DIR)
        self.files_dir.mkdir(exist_ok=True)
        self.db_manager = DatabaseManager()
        
        # Create subdirectories for different file types
        self.subdirs = {
            'pdf': self.files_dir / 'pdfs',
            'image': self.files_dir / 'images',
            'document': self.files_dir / 'documents',
            'audio': self.files_dir / 'audio',
            'video': self.files_dir / 'video',
            'other': self.files_dir / 'other'
        }
        
        for subdir in self.subdirs.values():
            subdir.mkdir(exist_ok=True)
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type based on extension"""
        mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            return 'other'
        
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'text/plain', 'application/rtf']:
            return 'document'
        else:
            return 'other'
    
    def generate_safe_filename(self, user_id: int, original_filename: str) -> str:
        """Generate a safe, unique filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(original_filename)
        
        # Clean the filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        return f"{user_id}_{timestamp}_{safe_name}{ext}"
    
    def store_file(self, user_id: int, file_path: str, original_filename: str, 
                  description: str = None, tags: List[str] = None) -> Dict:
        """Store file and add to database"""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"File size {file_size} exceeds maximum {MAX_FILE_SIZE}")
            
            # Determine file type and target directory
            file_type = self.get_file_type(original_filename)
            target_dir = self.subdirs[file_type]
            
            # Generate safe filename
            safe_filename = self.generate_safe_filename(user_id, original_filename)
            target_path = target_dir / safe_filename
            
            # Copy file to target location
            shutil.copy2(file_path, target_path)
            
            # Calculate file hash for deduplication
            file_hash = self.calculate_file_hash(target_path)
            
            # Add to database
            file_id = self.db_manager.add_file(
                user_id=user_id,
                filename=original_filename,
                filepath=str(target_path),
                file_type=file_type,
                file_size=file_size,
                description=description,
                tags=tags or []
            )
            
            logger.info(f"File stored successfully: {original_filename} -> {safe_filename}")
            
            return {
                'file_id': file_id,
                'filename': original_filename,
                'safe_filename': safe_filename,
                'filepath': str(target_path),
                'file_type': file_type,
                'file_size': file_size,
                'file_hash': file_hash,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error storing file {original_filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_user_files(self, user_id: int, file_type: str = None, 
                      limit: int = 10) -> List[Dict]:
        """Get user's files from database"""
        return self.db_manager.get_user_files(user_id, file_type, limit)
    
    def search_files(self, user_id: int, query: str, file_type: str = None) -> List[Dict]:
        """Search files by filename, description, or tags"""
        try:
            all_files = self.get_user_files(user_id, file_type, limit=100)
            query_lower = query.lower()
            
            matching_files = []
            
            for file_info in all_files:
                # Search in filename
                if query_lower in file_info['filename'].lower():
                    matching_files.append({**file_info, 'match_type': 'filename'})
                    continue
                
                # Search in description
                if file_info.get('description') and query_lower in file_info['description'].lower():
                    matching_files.append({**file_info, 'match_type': 'description'})
                    continue
                
                # Search in tags
                if any(query_lower in tag.lower() for tag in file_info.get('tags', [])):
                    matching_files.append({**file_info, 'match_type': 'tags'})
            
            return matching_files
            
        except Exception as e:
            logger.error(f"Error searching files for user {user_id}: {e}")
            return []
    
    def get_file_suggestions(self, user_id: int, context: str) -> List[Dict]:
        """Get file suggestions based on context"""
        try:
            # Extract keywords from context
            keywords = self.extract_keywords(context)
            
            suggestions = []
            for keyword in keywords:
                matches = self.search_files(user_id, keyword)
                suggestions.extend(matches)
            
            # Remove duplicates and sort by relevance
            unique_suggestions = {}
            for suggestion in suggestions:
                file_id = suggestion['id']
                if file_id not in unique_suggestions:
                    unique_suggestions[file_id] = suggestion
            
            return list(unique_suggestions.values())[:5]  # Top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting file suggestions: {e}")
            return []
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for file matching"""
        # Simple keyword extraction
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        words = text.lower().split()
        keywords = [word.strip('.,!?;:') for word in words if len(word) > 2 and word not in common_words]
        
        return keywords[:10]  # Limit to 10 keywords
    
    def delete_file(self, user_id: int, file_id: int) -> bool:
        """Delete file (soft delete in database)"""
        try:
            # Get file info
            files = self.get_user_files(user_id)
            target_file = None
            
            for file_info in files:
                if file_info['id'] == file_id:
                    target_file = file_info
                    break
            
            if not target_file:
                return False
            
            # Soft delete in database
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE files SET is_active = FALSE 
                    WHERE id = ? AND user_id = ?
                ''', (file_id, user_id))
                
                conn.commit()
                conn.close()
            
            logger.info(f"File {file_id} soft deleted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
    
    def get_file_stats(self, user_id: int) -> Dict:
        """Get file statistics for user"""
        try:
            files = self.get_user_files(user_id, limit=1000)
            
            stats = {
                'total_files': len(files),
                'total_size': sum(f['file_size'] for f in files),
                'by_type': {},
                'recent_uploads': len([f for f in files if self.is_recent(f['upload_date'])])
            }
            
            # Count by file type
            for file_info in files:
                file_type = file_info['file_type']
                if file_type not in stats['by_type']:
                    stats['by_type'][file_type] = {'count': 0, 'size': 0}
                
                stats['by_type'][file_type]['count'] += 1
                stats['by_type'][file_type]['size'] += file_info['file_size']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting file stats for user {user_id}: {e}")
            return {}
    
    def is_recent(self, upload_date: str, days: int = 7) -> bool:
        """Check if upload date is recent"""
        try:
            upload_dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
            now = datetime.now()
            return (now - upload_dt).days <= days
        except:
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = self.files_dir / 'temp'
            if temp_dir.exists():
                for file_path in temp_dir.glob('*'):
                    if file_path.is_file():
                        # Delete files older than 1 hour
                        if (datetime.now().timestamp() - file_path.stat().st_mtime) > 3600:
                            file_path.unlink()
                            logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def backup_user_files(self, user_id: int, backup_dir: str) -> bool:
        """Backup all files for a user"""
        try:
            backup_path = Path(backup_dir) / f"user_{user_id}_backup"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            files = self.get_user_files(user_id, limit=1000)
            
            for file_info in files:
                source_path = Path(file_info['filepath'])
                if source_path.exists():
                    target_path = backup_path / source_path.name
                    shutil.copy2(source_path, target_path)
            
            # Create manifest file
            manifest_path = backup_path / 'manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(files, f, indent=2, default=str)
            
            logger.info(f"Backup completed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up files for user {user_id}: {e}")
            return False
    
    def get_file_by_id(self, user_id: int, file_id: int) -> Optional[Dict]:
        """Get specific file by ID"""
        files = self.get_user_files(user_id, limit=1000)
        for file_info in files:
            if file_info['id'] == file_id:
                return file_info
        return None
    
    def update_file_tags(self, user_id: int, file_id: int, tags: List[str]) -> bool:
        """Update file tags"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                tags_json = json.dumps(tags)
                cursor.execute('''
                    UPDATE files SET tags = ? 
                    WHERE id = ? AND user_id = ?
                ''', (tags_json, file_id, user_id))
                
                conn.commit()
                conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating tags for file {file_id}: {e}")
            return False

