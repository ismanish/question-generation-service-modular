"""
Logging configuration for the application
"""
import logging
import sys
from typing import Any

from src.core.config import settings


def setup_logging() -> None:
    """Setup application logging"""
    
    # Configure logging level based on debug setting
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Setup logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party library log levels
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("opensearch").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin to add logging capability to classes"""
    
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)
