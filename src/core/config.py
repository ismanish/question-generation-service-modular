"""
Core configuration settings for the application
"""
import os
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    PROJECT_NAME: str = "Question Generation API - Modular"
    PROJECT_DESCRIPTION: str = "Modular API for generating educational questions using OpenSearch and GraphRAG"
    VERSION: str = "3.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # AWS settings
    AWS_REGION: str = "us-east-1"
    AWS_PROFILE_NAME: str = "cengage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # OpenSearch settings
    OPENSEARCH_HOST: str = "https://64asp87vin20xc5bhvbf.us-east-1.aoss.amazonaws.com"
    OPENSEARCH_REGION: str = "us-east-1"
    
    # LLM settings
    LLM_MODEL: str = "arn:aws:bedrock:us-east-1:051826717360:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0"
    LLM_REGION: str = "us-east-1"
    LLM_MAX_TOKENS: int = 30000
    
    # DynamoDB settings
    DYNAMODB_REGION: str = "us-east-1"
    QUESTION_HISTORY_TABLE: str = "question_generation_history"
    CONVERSATION_TABLE: str = "conversation"
    EVENTS_TABLE: str = "events"
    
    # Question generation settings
    MAX_CHUNKS: int = 200
    MAX_CHARS: int = 100000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Initialize settings
settings = Settings()

# Set environment variables for backward compatibility
os.environ.setdefault("AWS_PROFILE", settings.AWS_PROFILE_NAME)
os.environ.setdefault("AWS_REGION", settings.AWS_REGION)
os.environ.setdefault("AWS_DEFAULT_REGION", settings.AWS_REGION)
