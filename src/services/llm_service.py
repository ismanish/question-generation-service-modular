"""
LLM service for question generation
"""
import re
import json
from typing import Generator, List
from llama_index.llms.bedrock_converse import BedrockConverse

from src.core.config import settings
from src.core.logging import LoggerMixin


class LLMService(LoggerMixin):
    """Service for Large Language Model operations"""
    
    def __init__(self):
        self._llm = None
    
    @property
    def llm(self) -> BedrockConverse:
        """Get LLM instance"""
        if self._llm is None:
            self._llm = BedrockConverse(
                model=settings.LLM_MODEL,
                profile_name=settings.AWS_PROFILE_NAME,
                region_name=settings.LLM_REGION,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            self.logger.info(f"Initialized LLM with model: {settings.LLM_MODEL}")
        return self._llm
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using the LLM"""
        try:
            self.logger.debug(f"Generating completion for prompt of length: {len(prompt)}")
            
            # Use streaming approach for better performance
            response_deltas = []
            stream_response = self.llm.stream_complete(prompt)
            
            for r in stream_response:
                response_deltas.append(r.delta)
            
            completion = "".join(response_deltas)
            self.logger.debug(f"Generated completion of length: {len(completion)}")
            
            return completion
            
        except Exception as e:
            self.logger.error(f"Error generating completion: {str(e)}")
            raise Exception(f"LLM completion error: {str(e)}")
    
    def strip_json_markers(self, json_string: str) -> str:
        """Strip triple backticks and 'json' from a JSON-formatted string"""
        pattern = r"```(?:json)?(.*?)```"
        matches = re.findall(pattern, json_string, re.DOTALL)
        
        if matches:
            return "".join(matches).strip()
        else:
            return json_string.strip()
    
    def generate_json_completion(self, prompt: str) -> dict:
        """Generate completion and parse as JSON"""
        try:
            completion = self.generate_completion(prompt)
            clean_completion = self.strip_json_markers(completion)
            
            # Parse JSON
            result = json.loads(clean_completion)
            self.logger.debug("Successfully parsed JSON response")
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {str(e)}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error generating JSON completion: {str(e)}")
            raise


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    return LLMService()
