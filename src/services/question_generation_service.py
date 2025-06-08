"""
Main question generation service that orchestrates all question types
"""
import asyncio
import concurrent.futures
import datetime
from typing import Dict, List, Optional, Union, Any, Tuple

from src.core.logging import LoggerMixin
from src.models.schemas import QuestionGenerationRequest, QuestionGenerationResponse
from src.services.content_service import get_content_service
from src.services.mcq_generator import get_mcq_generator
from src.services.fib_generator import get_fib_generator
from src.services.tf_generator import get_tf_generator
from src.utils.helpers import calculate_question_distribution
from src.utils.constants import RESPONSE_SUCCESS_TEMPLATE, RESPONSE_ERROR_TEMPLATE


class QuestionGenerationService(LoggerMixin):
    """Main service for generating questions using multiple generators in parallel"""
    
    def __init__(self):
        self.content_service = get_content_service()
        self.mcq_generator = get_mcq_generator()
        self.fib_generator = get_fib_generator()
        self.tf_generator = get_tf_generator()
    
    async def generate_questions(
        self,
        request: QuestionGenerationRequest,
        source_id: str
    ) -> QuestionGenerationResponse:
        """
        Generate questions based on the request parameters with optimized parallel processing
        
        Args:
            request: Question generation request
            source_id: Source identifier
            
        Returns:
            Question generation response
        """
        start_time = datetime.datetime.utcnow()
        status = "success"
        error_message = ""
        all_question_data = {}
        files_generated = []
        
        self.logger.info(f"Processing question generation request for source: {source_id}")
        self.logger.info(f"Request: {request.dict()}")
        
        try:
            # OPTIMIZATION 1: Generate shared content ONCE
            self.logger.info("🚀 OPTIMIZATION: Generating shared content once...")
            content_start_time = datetime.datetime.utcnow()
            
            chapter_content = self.content_service.retrieve_chapter_content(
                chapter_name=request.chapter_name,
                content_id=request.contentId,
                max_chunks=request.max_chunks,
                max_chars=request.max_chars
            )
            
            if not chapter_content:
                raise ValueError(f"No content found for chapter '{request.chapter_name}' in '{request.contentId}'")
            
            content_time = (datetime.datetime.utcnow() - content_start_time).total_seconds()
            self.logger.info(f"✅ Shared content generated in {content_time:.2f} seconds (length: {len(chapter_content)} characters)")
            
            # Calculate question distribution
            question_dist = calculate_question_distribution(
                request.total_questions,
                request.question_type_distribution,
                request.difficulty_distribution,
                request.blooms_taxonomy_distribution
            )
            
            self.logger.info(f"Question distribution: {question_dist}")
            
            # Group by question type for generation
            type_groups = self._group_by_question_type(question_dist)
            
            # OPTIMIZATION 2: Run question generators in TRUE PARALLEL
            self.logger.info("🚀 OPTIMIZATION: Running question generators in TRUE PARALLEL...")
            parallel_start_time = datetime.datetime.utcnow()
            
            # Generate questions in parallel
            results = await self._generate_questions_parallel(
                type_groups=type_groups,
                chapter_content=chapter_content,
                request=request
            )
            
            parallel_time = (datetime.datetime.utcnow() - parallel_start_time).total_seconds()
            self.logger.info(f"✅ TRUE parallel question generation completed in {parallel_time:.2f} seconds")
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    raise result
                
                question_type, file_name, question_data, error = result
                
                if error:
                    raise Exception(f"Error in {question_type}: {error}")
                
                if file_name:
                    files_generated.append(file_name)
                all_question_data[question_type] = question_data
            
            total_time = (datetime.datetime.utcnow() - start_time).total_seconds()
            
            learning_obj_str = f" with learning objectives: {request.learning_objectives}" if request.learning_objectives else ""
            
            message = RESPONSE_SUCCESS_TEMPLATE.format(
                total_questions=request.total_questions,
                question_types=len(type_groups)
            ) + f" for source: {source_id}, chapter: {request.chapter_name}{learning_obj_str} in {total_time:.2f} seconds (Content: {content_time:.2f}s, Parallel Generation: {parallel_time:.2f}s)"
            
            return QuestionGenerationResponse(
                status=status,
                message=message,
                session_id=request.session_id,
                contentId=request.contentId,
                chapter_name=request.chapter_name,
                learning_objectives=request.learning_objectives,
                total_questions=request.total_questions,
                question_type_distribution=request.question_type_distribution,
                difficulty_distribution=request.difficulty_distribution,
                blooms_taxonomy_distribution=request.blooms_taxonomy_distribution,
                files_generated=files_generated,
                data=all_question_data
            )
            
        except Exception as e:
            import traceback
            error_message = str(e)
            error_details = traceback.format_exc()
            self.logger.error(f"Error generating questions: {error_details}")
            status = "error"
            
            message = RESPONSE_ERROR_TEMPLATE.format(error_message=error_message)
            
            return QuestionGenerationResponse(
                status=status,
                message=message,
                session_id=request.session_id,
                contentId=request.contentId,
                chapter_name=request.chapter_name,
                learning_objectives=request.learning_objectives,
                total_questions=request.total_questions,
                question_type_distribution=request.question_type_distribution,
                difficulty_distribution=request.difficulty_distribution,
                blooms_taxonomy_distribution=request.blooms_taxonomy_distribution,
                files_generated=[],
                data={}
            )
    
    def _group_by_question_type(self, question_dist: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group question distribution by question type"""
        type_groups = {}
        for key, config in question_dist.items():
            q_type = config['question_type']
            if q_type not in type_groups:
                type_groups[q_type] = []
            type_groups[q_type].append(config)
        return type_groups
    
    async def _generate_questions_parallel(
        self,
        type_groups: Dict[str, List[Dict[str, Any]]],
        chapter_content: str,
        request: QuestionGenerationRequest
    ) -> List[Any]:
        """Generate questions in parallel using ThreadPoolExecutor"""
        
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Create futures for each question type
            futures = []
            
            for question_type, configs in type_groups.items():
                # Create combined distributions for this question type
                total_for_type = sum([config['count'] for config in configs])
                difficulty_dist_for_type = {}
                blooms_dist_for_type = {}
                
                for config in configs:
                    diff = config['difficulty']
                    blooms = config['blooms_level']
                    count = config['count']
                    
                    if diff not in difficulty_dist_for_type:
                        difficulty_dist_for_type[diff] = 0
                    if blooms not in blooms_dist_for_type:
                        blooms_dist_for_type[blooms] = 0
                    
                    difficulty_dist_for_type[diff] += count / total_for_type
                    blooms_dist_for_type[blooms] += count / total_for_type
                
                # Submit task to thread pool
                future = loop.run_in_executor(
                    executor,
                    self._generate_single_question_type_sync,
                    question_type,
                    configs,
                    chapter_content,
                    request.chapter_name,
                    request.contentId,
                    request.learning_objectives,
                    difficulty_dist_for_type,
                    blooms_dist_for_type,
                    request.max_chunks,
                    request.max_chars
                )
                futures.append(future)
            
            # Wait for all futures to complete
            self.logger.info(f"⚡ Running {len(futures)} question generators in parallel threads...")
            results = await asyncio.gather(*futures, return_exceptions=True)
        
        return results
    
    def _generate_single_question_type_sync(
        self,
        question_type: str,
        configs: List[Dict[str, Any]],
        chapter_content: str,
        chapter_name: str,
        content_id: str,
        learning_objectives: Optional[Union[str, List[str]]],
        difficulty_distribution: Dict[str, float],
        blooms_distribution: Dict[str, float],
        max_chunks: int,
        max_chars: int
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """
        Synchronous function for generating a single question type using shared content.
        This function will be run in parallel using ThreadPoolExecutor.
        """
        try:
            total_for_type = sum([config['count'] for config in configs])
            
            self.logger.info(f"[THREAD] Generating {question_type} questions (count: {total_for_type})...")
            
            # Generate questions based on type
            if question_type == "mcq":
                result = self.mcq_generator.generate_mcqs(
                    chapter_name=chapter_name,
                    content_id=content_id,
                    learning_objectives=learning_objectives,
                    num_questions=total_for_type,
                    difficulty_distribution=difficulty_distribution,
                    blooms_taxonomy_distribution=blooms_distribution,
                    chapter_content=chapter_content,
                    max_chunks=max_chunks,
                    max_chars=max_chars
                )
            elif question_type == "fib":
                result = self.fib_generator.generate_fill_in_blank(
                    chapter_name=chapter_name,
                    content_id=content_id,
                    learning_objectives=learning_objectives,
                    num_questions=total_for_type,
                    difficulty_distribution=difficulty_distribution,
                    blooms_taxonomy_distribution=blooms_distribution,
                    chapter_content=chapter_content,
                    max_chunks=max_chunks,
                    max_chars=max_chars
                )
            elif question_type == "tf":
                result = self.tf_generator.generate_true_false(
                    chapter_name=chapter_name,
                    content_id=content_id,
                    learning_objectives=learning_objectives,
                    num_questions=total_for_type,
                    difficulty_distribution=difficulty_distribution,
                    blooms_taxonomy_distribution=blooms_distribution,
                    chapter_content=chapter_content,
                    max_chunks=max_chunks,
                    max_chars=max_chars
                )
            else:
                raise ValueError(f"Unknown question type: {question_type}")
            
            file_name = result.get('metadata', {}).get('filename')
            question_data = result.get('response', [])
            
            self.logger.info(f"[THREAD] Completed generating {question_type} questions")
            return question_type, file_name, {"response": question_data}, None
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"[THREAD] Error generating {question_type} questions: {error_details}")
            return question_type, None, None, str(e)


def get_question_generation_service() -> QuestionGenerationService:
    """Get question generation service instance"""
    return QuestionGenerationService()
