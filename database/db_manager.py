"""
Database Manager for Anuj Bot
Handles user data, memory, and conversation history using MongoDB
"""

from .mongodb_manager import MongoDBManager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager(MongoDBManager):
    def __init__(self, connection_string: str = None):
        super().__init__(connection_string)
        self.loop = None

    async def initialize(self):
        """Initialize the database connection"""
        await self.connect()

# This class is now the primary interface, inheriting from MongoDBManager
# All methods are already async from MongoDBManager


