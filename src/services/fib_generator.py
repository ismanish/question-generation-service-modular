"""
Fill-in-the-Blank (FIB) question generation service
"""
import uuid
from typing import Dict, List, Optional, Union, Any

from src.core.logging import LoggerMixin
from src.models.schemas import FillInBlankQuestion
from src.services.content_service import get_content_service
from src.services.llm_service import get_llm_service
from src.utils.constants import CENGAGE_GUIDELINES
from src.utils.helpers import (
    get_difficulty_description,
    get_blooms_question_guidelines,
    calculate_question_distribution,
    create_question_sequence,
    generate_filename,
    save_questions_to_file
)


class FIBParser(LoggerMixin):
    """Parser for Fill-in-the-Blank responses from LLM"""
    
    def parse_fib_response(
        self,
        response_text: str,
        question_breakdown: Dict[str, Dict[str, Any]]
    ) -> List[FillInBlankQuestion]:
        """Parse Fill-in-the-Blank response and assign metadata programmatically"""
        question_blocks = response_text.split("QUESTION:")
        questions = []
        
        # Create sequence of difficulty/blooms assignments
        question_sequence = create_question_sequence(question_breakdown)
        question_index = 0
        
        for block in [b.strip() for b in question_blocks if b.strip()]:
            question_data = {
                "question_id": str(uuid.uuid4()),
                "question": "",
                "answer": [],
                "explanation": "",
                "difficulty": "",
                "blooms_level": "",
                "question_type": "fib"
            }
            
            # Extract question content
            if "ANSWER:" in block:
                question_data["question"] = block.split("ANSWER:")[0].strip()
                block = "ANSWER:" + block.split("ANSWER:")[1]
            
            # Extract answer(s)
            if "ANSWER:" in block and "EXPLANATION:" in block:
                answer_text = block.split("ANSWER:")[1].split("EXPLANATION:")[0].strip()
                answer_lines = answer_text.split('\n')
                
                for line in answer_lines:
                    line = line.strip()
                    # Check if line starts with a number followed by a period
                    if line and (line[0].isdigit() and '. ' in line):
                        # Remove the numbering and add to the list
                        answer_item = line.split('. ', 1)[1].strip()
                        question_data["answer"].append(answer_item)
                    elif line:  # If there's text but not in numbered format
                        question_data["answer"].append(line)
                
                block = "EXPLANATION:" + block.split("EXPLANATION:")[1]
            
            # Extract explanation
            if "EXPLANATION:" in block:
                explanation_text = block.split("EXPLANATION:")[1]
                question_data["explanation"] = explanation_text.strip()
            
            # Programmatically assign difficulty and blooms_level
            if question_index < len(question_sequence):
                difficulty, blooms_level = question_sequence[question_index]
                question_data["difficulty"] = difficulty
                question_data["blooms_level"] = blooms_level
                question_index += 1
            
            try:
                question = FillInBlankQuestion(**question_data)
                questions.append(question)
            except Exception as e:
                self.logger.warning(f"Failed to create FillInBlankQuestion from data: {e}")
                continue
        
        return questions


class FIBGenerator(LoggerMixin):
    """Service for generating Fill-in-the-Blank Questions"""
    
    def __init__(self):
        self.content_service = get_content_service()
        self.llm_service = get_llm_service()
        self.parser = FIBParser()
    
    def generate_fill_in_blank(
        self,
        chapter_name: str,
        content_id: str,
        learning_objectives: Optional[Union[str, List[str]]] = None,
        num_questions: int = 10,
        difficulty_distribution: Dict[str, float] = {"advanced": 1.0},
        blooms_taxonomy_distribution: Dict[str, float] = {"analyze": 1.0},
        chapter_content: Optional[str] = None,
        max_chunks: Optional[int] = None,
        max_chars: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate Fill-in-the-Blank questions for specified book chapter
        
        Args:
            chapter_name: The chapter name (e.g., 'Chapter 1 Taking Charge of Your Health')
            content_id: The book identifier (e.g., 'An Invitation to Health')
            learning_objectives: Optional learning objectives for context
            num_questions: Number of fill-in-the-blank questions to generate
            difficulty_distribution: Distribution of difficulty levels
            blooms_taxonomy_distribution: Distribution of Bloom's taxonomy levels
            chapter_content: Pre-generated chapter content (avoids duplicate retrieval)
            max_chunks: Maximum number of chunks to retrieve from OpenSearch
            max_chars: Maximum characters in chapter content
        
        Returns:
            Dictionary containing generated fill-in-the-blank questions and metadata
        """
        self.logger.info(f"Generating {num_questions} fill-in-the-blank questions for chapter: {chapter_name}")
        self.logger.info(f"Content/Book: {content_id}")
        
        if learning_objectives:
            self.logger.info(f"Learning objectives: {learning_objectives}")
        
        self.logger.info(f"Difficulty distribution: {difficulty_distribution}")
        self.logger.info(f"Bloom's taxonomy distribution: {blooms_taxonomy_distribution}")
        
        # Get chapter content
        if chapter_content is None:
            self.logger.info("No chapter content provided, retrieving from OpenSearch...")
            chapter_content = self.content_service.retrieve_chapter_content(
                chapter_name=chapter_name,
                content_id=content_id,
                max_chunks=max_chunks,
                max_chars=max_chars
            )
        else:
            self.logger.info(f"Using provided chapter content (length: {len(chapter_content)} characters)")
        
        if not chapter_content:
            raise ValueError(f"No content found for chapter '{chapter_name}' in '{content_id}'")
        
        # Calculate question distribution
        question_breakdown = calculate_question_distribution(
            num_questions,
            {"fib": 1.0},  # Only Fill-in-the-Blank questions
            difficulty_distribution,
            blooms_taxonomy_distribution
        )
        
        self.logger.info(f"Question breakdown: {question_breakdown}")
        
        # Generate prompt
        prompt = self._create_fib_prompt(
            chapter_content,
            num_questions,
            question_breakdown,
            difficulty_distribution,
            blooms_taxonomy_distribution
        )
        
        # Generate FIB questions using LLM
        self.logger.info("Generating fill-in-the-blank questions...")
        fib_response = self.llm_service.generate_completion(prompt)
        
        # Parse response
        questions = self.parser.parse_fib_response(fib_response, question_breakdown)
        
        if not questions:
            raise ValueError("No valid fill-in-the-blank questions could be parsed from LLM response")
        
        # Generate filename and save
        filename = generate_filename(
            chapter_name=chapter_name,
            difficulty_distribution=difficulty_distribution,
            blooms_distribution=blooms_taxonomy_distribution,
            question_type="fib",
            learning_objectives=learning_objectives
        )
        
        # Convert questions to dict format for saving
        questions_dict = [q.dict() for q in questions]
        save_questions_to_file(questions_dict, filename)
        
        self.logger.info(f"Generated {len(questions)} fill-in-the-blank questions and saved to {filename}")
        
        return {
            "response": questions_dict,
            "metadata": {
                "chapter_name": chapter_name,
                "content_id": content_id,
                "learning_objectives": learning_objectives,
                "num_questions": len(questions),
                "difficulty_distribution": difficulty_distribution,
                "blooms_taxonomy_distribution": blooms_taxonomy_distribution,
                "filename": filename
            }
        }
    
    def _create_fib_prompt(
        self,
        chapter_content: str,
        num_questions: int,
        question_breakdown: Dict[str, Dict[str, Any]],
        difficulty_distribution: Dict[str, float],
        blooms_taxonomy_distribution: Dict[str, float]
    ) -> str:
        """Create the prompt for Fill-in-the-Blank generation"""
        
        # Generate guidelines for each combination
        all_guidelines = []
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            guidelines = get_blooms_question_guidelines(blooms_level, "fib")
            difficulty_desc = get_difficulty_description(difficulty)
            
            all_guidelines.append(f"""
For {count} questions at {difficulty.upper()} difficulty and {blooms_level.upper()} Bloom's level:
- Difficulty: {difficulty_desc}
- Bloom's Level Guidelines: {guidelines}
            """)
        
        prompt = f"""
        You are a professor writing sophisticated fill-in-the-blank questions for an upper-level university course. The questions will be based on this chapter content:

        {chapter_content}

        Create exactly {num_questions} fill-in-the-blank questions following these specific guidelines:

        {' '.join(all_guidelines)}

        IMPORTANT FORMATTING INSTRUCTIONS:
        - Start IMMEDIATELY with your first question using "QUESTION:" 
        - DO NOT write ANY introductory text like "Based on the chapter..." or "I'll create..."
        - DO NOT include ANY preamble or explanation before the first question
        - Each blank should be indicated by "________" (8 underscores)
        - A question may have multiple blanks if appropriate

        Each question should:
        1. Match the specified difficulty and Bloom's taxonomy level
        2. Present statements appropriate to the cognitive level required
        3. Use domain-specific terminology accurately
        4. Focus on important concepts from the chapter

        Format each question exactly as follows:
        QUESTION: [Statement with ________ for blanks, appropriate to difficulty and Bloom's level]
        ANSWER: [Correct answer(s) that should fill the blank(s), if multiple blanks, list each answer separately]
        EXPLANATION: [Explanation of why this is the correct answer and how it demonstrates the required cognitive level]

        Distribution of questions:
        {question_breakdown}
        
        Make sure to vary the cognitive demands according to the Bloom's taxonomy levels specified.
        
        Follow these Cengage guidelines:
        {CENGAGE_GUIDELINES}
        """
        
        return prompt


def get_fib_generator() -> FIBGenerator:
    """Get Fill-in-the-Blank generator instance"""
    return FIBGenerator()
