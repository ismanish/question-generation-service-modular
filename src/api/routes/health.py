"""
Health check API routes
"""
from fastapi import APIRouter

from src.models.schemas import HealthCheckResponse
from src.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.VERSION,
        optimizations=[
            "opensearch_content_retrieval",
            "shared_content_generation",
            "true_parallel_processing_with_threads",
            "learning_objectives_support",
            "session_management",
            "modular_architecture"
        ]
    )


@router.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"{settings.PROJECT_NAME} v{settings.VERSION}",
        "description": settings.PROJECT_DESCRIPTION,
        "documentation": "/docs",
        "health": "/health"
    }
