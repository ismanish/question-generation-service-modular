"""
Database connection and management
"""
import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.logging import LoggerMixin


class DynamoDBClient(LoggerMixin):
    """DynamoDB client wrapper"""
    
    def __init__(self):
        self._client = None
        self._resource = None
        self._tables: Dict[str, Any] = {}
    
    @property
    def client(self):
        """Get DynamoDB client"""
        if self._client is None:
            self._client = boto3.client(
                'dynamodb',
                region_name=settings.DYNAMODB_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        return self._client
    
    @property
    def resource(self):
        """Get DynamoDB resource"""
        if self._resource is None:
            self._resource = boto3.resource(
                'dynamodb',
                region_name=settings.DYNAMODB_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        return self._resource
    
    def get_table(self, table_name: str):
        """Get DynamoDB table"""
        if table_name not in self._tables:
            try:
                table = self.resource.Table(table_name)
                # Test if table exists
                table.scan(Limit=1)
                self._tables[table_name] = table
                self.logger.info(f"Successfully connected to DynamoDB table: {table_name}")
            except ClientError as e:
                self.logger.warning(f"DynamoDB table access error for {table_name}: {str(e)}")
                self._tables[table_name] = None
        
        return self._tables[table_name]
    
    def close(self):
        """Close connections"""
        self._client = None
        self._resource = None
        self._tables.clear()


class DatabaseManager(LoggerMixin):
    """Database manager for all database connections"""
    
    def __init__(self):
        self.dynamodb_client = DynamoDBClient()
        self._tables: Dict[str, Optional[Any]] = {}
    
    async def initialize(self):
        """Initialize database connections"""
        self.logger.info("Initializing database connections...")
        
        # Initialize DynamoDB tables
        table_names = {
            'history': settings.QUESTION_HISTORY_TABLE,
            'conversation': settings.CONVERSATION_TABLE,
            'events': settings.EVENTS_TABLE
        }
        
        for key, table_name in table_names.items():
            self._tables[key] = self.dynamodb_client.get_table(table_name)
        
        self.logger.info("Database connections initialized")
    
    def get_table(self, table_key: str) -> Optional[Any]:
        """Get a DynamoDB table by key"""
        return self._tables.get(table_key)
    
    @property
    def history_table(self):
        """Get question history table"""
        return self.get_table('history')
    
    @property
    def conversation_table(self):
        """Get conversation table"""
        return self.get_table('conversation')
    
    @property
    def events_table(self):
        """Get events table"""
        return self.get_table('events')
    
    async def close(self):
        """Close all database connections"""
        self.logger.info("Closing database connections...")
        self.dynamodb_client.close()
        self._tables.clear()
        self.logger.info("Database connections closed")
