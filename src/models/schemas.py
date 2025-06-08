"""
Pydantic models for question generation requests and responses
"""
import uuid
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class QuestionType(str, Enum):
    """Question type enumeration"""
    MCQ = "mcq"
    TRUE_FALSE = "tf"
    FILL_IN_BLANK = "fib"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class BloomsTaxonomy(str, Enum):
    """Bloom's taxonomy level enumeration"""
    REMEMBER = "remember"
    APPLY = "apply"
    ANALYZE = "analyze"


class QuestionGenerationRequest(BaseModel):
    """Request model for question generation"""
    contentId: str = Field(
        default="An Invitation to Health",
        description="Book identifier for content retrieval"
    )
    chapter_name: str = Field(
        default="Chapter 1 Taking Charge of Your Health",
        description="Chapter name for content retrieval"
    )
    learning_objectives: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Learning objectives to filter content"
    )
    total_questions: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Total number of questions to generate"
    )
    question_type_distribution: Dict[str, float] = Field(
        default={"mcq": 0.4, "fib": 0.3, "tf": 0.3},
        description="Distribution of question types"
    )
    difficulty_distribution: Dict[str, float] = Field(
        default={"basic": 0.3, "intermediate": 0.3, "advanced": 0.4},
        description="Distribution of difficulty levels"
    )
    blooms_taxonomy_distribution: Dict[str, float] = Field(
        default={"remember": 0.3, "apply": 0.4, "analyze": 0.3},
        description="Distribution of Bloom's taxonomy levels"
    )
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session identifier"
    )
    max_chunks: int = Field(
        default=200,
        ge=1,
        le=1000,
        description="Maximum chunks to retrieve from OpenSearch"
    )
    max_chars: int = Field(
        default=100000,
        ge=1000,
        le=500000,
        description="Maximum characters in chapter content"
    )


class QuestionGenerationResponse(BaseModel):
    """Response model for question generation"""
    status: str = Field(description="Status of the generation request")
    message: str = Field(description="Status message or error description")
    session_id: str = Field(description="Session identifier")
    contentId: str = Field(description="Content identifier")
    chapter_name: str = Field(description="Chapter name")
    learning_objectives: Optional[Union[str, List[str]]] = Field(description="Learning objectives used")
    total_questions: int = Field(description="Total questions generated")
    question_type_distribution: Dict[str, float] = Field(description="Question type distribution used")
    difficulty_distribution: Dict[str, float] = Field(description="Difficulty distribution used")
    blooms_taxonomy_distribution: Dict[str, float] = Field(description="Bloom's taxonomy distribution used")
    files_generated: List[str] = Field(description="List of generated files")
    data: Dict[str, Any] = Field(description="Generated question data")


class MCQQuestion(BaseModel):
    """Multiple Choice Question model"""
    question_id: str = Field(description="Unique question identifier")
    question: str = Field(description="Question text")
    answer: str = Field(description="Correct answer")
    explanation: str = Field(description="Answer explanation")
    distractors: List[str] = Field(description="Incorrect answer options")
    difficulty: str = Field(description="Question difficulty level")
    blooms_level: str = Field(description="Bloom's taxonomy level")
    question_type: str = Field(default="mcq", description="Question type")


class TrueFalseQuestion(BaseModel):
    """True/False Question model"""
    question_id: str = Field(description="Unique question identifier")
    statement: str = Field(description="Statement to evaluate")
    answer: str = Field(description="TRUE or FALSE")
    explanation: str = Field(description="Answer explanation")
    difficulty: str = Field(description="Question difficulty level")
    blooms_level: str = Field(description="Bloom's taxonomy level")
    question_type: str = Field(default="tf", description="Question type")


class FillInBlankQuestion(BaseModel):
    """Fill-in-the-Blank Question model"""
    question_id: str = Field(description="Unique question identifier")
    question: str = Field(description="Question text with blanks")
    answer: List[str] = Field(description="Correct answers for blanks")
    explanation: str = Field(description="Answer explanation")
    difficulty: str = Field(description="Question difficulty level")
    blooms_level: str = Field(description="Bloom's taxonomy level")
    question_type: str = Field(default="fib", description="Question type")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(description="Health status")
    version: str = Field(description="Application version")
    optimizations: List[str] = Field(description="List of optimizations")
