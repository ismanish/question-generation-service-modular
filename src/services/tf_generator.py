"""
True/False (TF) question generation service
"""
import uuid
from typing import Dict, List, Optional, Union, Any

from src.core.logging import LoggerMixin
from src.models.schemas import TrueFalseQuestion
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


class TFParser(LoggerMixin):
    """Parser for True/False responses from LLM"""
    
    def parse_tf_response(
        self,
        response_text: str,
        question_breakdown: Dict[str, Dict[str, Any]]
    ) -> List[TrueFalseQuestion]:
        """Parse True/False response and assign metadata programmatically"""
        # Split by STATEMENT: to separate each question
        statement_blocks = response_text.split("STATEMENT:")
        questions = []
        
        # Create sequence of difficulty/blooms assignments
        question_sequence = create_question_sequence(question_breakdown)
        question_index = 0
        
        for block in [b.strip() for b in statement_blocks if b.strip()]:
            question_data = {
                "question_id": str(uuid.uuid4()),
                "statement": "",
                "answer": "",
                "explanation": "",
                "difficulty": "",
                "blooms_level": "",
                "question_type": "tf"
            }
            
            # Extract statement
            if "ANSWER:" in block:
                question_data["statement"] = block.split("ANSWER:")[0].strip()
                block = "ANSWER:" + block.split("ANSWER:")[1]
            
            # Extract answer (TRUE or FALSE)
            if "ANSWER:" in block and "EXPLANATION:" in block:
                question_data["answer"] = block.split("ANSWER:")[1].split("EXPLANATION:")[0].strip()
            elif "ANSWER:" in block:
                question_data["answer"] = block.split("ANSWER:")[1].strip()
            
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
                question = TrueFalseQuestion(**question_data)
                questions.append(question)
            except Exception as e:
                self.logger.warning(f"Failed to create TrueFalseQuestion from data: {e}")
                continue
        
        return questions


class TFGenerator(LoggerMixin):
    """Service for generating True/False Questions"""
    
    def __init__(self):
        self.content_service = get_content_service()
        self.llm_service = get_llm_service()
        self.parser = TFParser()
    
    def generate_true_false(
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
        Generate True/False questions for specified book chapter
        
        Args:
            chapter_name: The chapter name (e.g., 'Chapter 1 Taking Charge of Your Health')
            content_id: The book identifier (e.g., 'An Invitation to Health')
            learning_objectives: Optional learning objectives for context
            num_questions: Number of true/false questions to generate
            difficulty_distribution: Distribution of difficulty levels
            blooms_taxonomy_distribution: Distribution of Bloom's taxonomy levels
            chapter_content: Pre-generated chapter content (avoids duplicate retrieval)
            max_chunks: Maximum number of chunks to retrieve from OpenSearch
            max_chars: Maximum characters in chapter content
        
        Returns:
            Dictionary containing generated true/false questions and metadata
        """
        self.logger.info(f"Generating {num_questions} true/false questions for chapter: {chapter_name}")
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
            {"tf": 1.0},  # Only True/False questions
            difficulty_distribution,
            blooms_taxonomy_distribution
        )
        
        self.logger.info(f"Question breakdown: {question_breakdown}")
        
        # Generate prompt
        prompt = self._create_tf_prompt(
            chapter_content,
            num_questions,
            question_breakdown,
            difficulty_distribution,
            blooms_taxonomy_distribution
        )
        
        # Generate True/False questions using LLM
        self.logger.info("Generating true/false questions...")
        tf_response = self.llm_service.generate_completion(prompt)
        
        # Parse response
        questions = self.parser.parse_tf_response(tf_response, question_breakdown)
        
        if not questions:
            raise ValueError("No valid true/false questions could be parsed from LLM response")
        
        # Generate filename and save
        filename = generate_filename(
            chapter_name=chapter_name,
            difficulty_distribution=difficulty_distribution,
            blooms_distribution=blooms_taxonomy_distribution,
            question_type="tf",
            learning_objectives=learning_objectives
        )
        
        # Convert questions to dict format for saving
        questions_dict = [q.dict() for q in questions]
        save_questions_to_file(questions_dict, filename)
        
        self.logger.info(f"Generated {len(questions)} true/false questions and saved to {filename}")
        
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
    
    def _create_tf_prompt(
        self,
        chapter_content: str,
        num_questions: int,
        question_breakdown: Dict[str, Dict[str, Any]],
        difficulty_distribution: Dict[str, float],
        blooms_taxonomy_distribution: Dict[str, float]
    ) -> str:
        """Create the prompt for True/False generation"""
        
        # Generate guidelines for each combination
        all_guidelines = []
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            guidelines = get_blooms_question_guidelines(blooms_level, "tf")
            difficulty_desc = get_difficulty_description(difficulty)
            
            all_guidelines.append(f"""
For {count} questions at {difficulty.upper()} difficulty and {blooms_level.upper()} Bloom's level:
- Difficulty: {difficulty_desc}
- Bloom's Level Guidelines: {guidelines}
            """)
        
        prompt = f"""
        You are a professor writing sophisticated true/false questions for an upper-level university course. The questions will be based on this chapter content:

        {chapter_content}

        Create exactly {num_questions} true/false questions following these specific guidelines:

        {' '.join(all_guidelines)}

        IMPORTANT FORMATTING INSTRUCTIONS:
        - Start IMMEDIATELY with your first question using "STATEMENT:" 
        - DO NOT write ANY introductory text like "Based on the chapter..." or "I'll create..."
        - DO NOT include ANY preamble or explanation before the first statement

        Each question should:
        1. Match the specified difficulty and Bloom's taxonomy level
        2. Present clear statements appropriate to the cognitive level required
        3. Use domain-specific terminology accurately
        4. Avoid making statements true/false based on single words like "always", "never", or "all"
        5. Be balanced (aim for approximately 50% true and 50% false statements)
        6. For false statements, make them plausible but clearly incorrect based on the chapter

        Format each question exactly as follows:
        STATEMENT: [A clear statement that is either true or false, appropriate to difficulty and Bloom's level]
        ANSWER: [Either "TRUE" or "FALSE" in all caps]
        EXPLANATION: [Explanation of why the statement is true or false, with reference to chapter content and demonstration of required cognitive level]

        Distribution of questions:
        {question_breakdown}
        
        Make sure to vary the cognitive demands according to the Bloom's taxonomy levels specified.
        
        Follow these Cengage guidelines:
        {CENGAGE_GUIDELINES}
        """
        
        return prompt


def get_tf_generator() -> TFGenerator:
    """Get True/False generator instance"""
    return TFGenerator()
