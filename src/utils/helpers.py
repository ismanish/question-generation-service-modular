"""
Helper functions for question generation
"""
import json
import uuid
from typing import Dict, Any, List, Union, Tuple

from src.core.logging import LoggerMixin


class QuestionHelpers(LoggerMixin):
    """Helper functions for question generation"""
    
    @staticmethod
    def get_difficulty_description(difficulty: str) -> str:
        """Return a description of what each difficulty level means for question generation"""
        descriptions = {
            "basic": "recall of facts and basic understanding of concepts",
            "intermediate": "application of concepts and analysis of relationships", 
            "advanced": "synthesis of multiple concepts and evaluation of complex scenarios"
        }
        return descriptions.get(difficulty, "appropriate college-level understanding")
    
    @staticmethod
    def get_blooms_description(blooms_level: str) -> str:
        """Return a description of what each Bloom's taxonomy level means for question generation"""
        descriptions = {
            "remember": """Remember/Understand level - Assessment items that ask students to show they can recall basic information or understand basic concepts. Questions should focus on:
        - Recalling definitions, facts, and basic information
        - Understanding fundamental concepts
        - Identifying key terms and their meanings
        - Listing components or steps
        - Outlining basic structures or processes
        
        Examples: "What is the definition of...?", "List the components of...", "In what year was...", "What is the first stage of...?"
        """,
            
            "apply": """Apply level - Assessment items that ask students to apply their knowledge of a concept to a situation or problem. Questions should focus on:
        - Using knowledge to solve problems
        - Applying concepts to new situations
        - Calculating using formulas or procedures
        - Implementing procedures in given contexts
        - Using information to complete tasks
        
        Examples: "Solve for x in...", "Use the information in the table to calculate...", "Apply the concept of... to determine..."
        """,
            
            "analyze": """Analyze/Evaluate/Create level - Assessment items that require students to examine information by parts, make decisions, or create new solutions. Questions should focus on:
        - Examining information to identify causes and effects
        - Making decisions based on provided variables
        - Comparing and contrasting different approaches
        - Evaluating effectiveness of strategies
        - Creating new solutions or ideas
        - Analyzing scenarios to determine best outcomes
        - Synthesizing information from multiple sources
        
        Examples: "Based on the scenario, which strategy would maximize...", "Given the situation, rank the following actions...", "Which combination of factors would be most effective...", "Analyze the data to determine..."
        """
        }
        return descriptions.get(blooms_level, "appropriate cognitive level thinking")
    
    @staticmethod
    def get_blooms_question_guidelines(blooms_level: str, question_type: str) -> str:
        """Return specific guidelines for creating questions at a given Bloom's level and question type"""
        base_description = QuestionHelpers.get_blooms_description(blooms_level)
        
        if question_type == "mcq":
            if blooms_level == "remember":
                return f"""{base_description}

For Multiple Choice Questions at Remember level:
- Focus on direct recall of facts, definitions, and basic concepts
- Stem should ask for specific information covered in the material
- Correct answer should be clearly stated in the content
- Distractors should be plausible but clearly incorrect facts/terms
- Avoid scenario-based questions at this level"""
                
            elif blooms_level == "apply":
                return f"""{base_description}

For Multiple Choice Questions at Apply level:
- Present a scenario or problem that requires applying learned concepts
- Stem should describe a situation where students must use their knowledge
- Correct answer should demonstrate proper application of concepts
- Distractors should represent common misapplications or errors
- Include sufficient context for students to apply their knowledge"""
                
            elif blooms_level == "analyze":
                return f"""{base_description}

For Multiple Choice Questions at Analyze level:
- Present complex scenarios requiring analysis of multiple variables
- Stem should require students to examine, compare, or evaluate information
- Correct answer should reflect sophisticated analysis or synthesis
- Distractors should represent superficial or incomplete analysis
- Questions should require higher-order thinking beyond simple application"""
        
        elif question_type == "tf":
            if blooms_level == "remember":
                return f"""{base_description}

For True/False Questions at Remember level:
- State facts, definitions, or basic concepts clearly
- Focus on information directly covered in the material
- Statements should test recall of specific details
- False statements should contradict clearly stated facts
- Avoid complex relationships or interpretations"""
                
            elif blooms_level == "apply":
                return f"""{base_description}

For True/False Questions at Apply level:
- Present statements about applying concepts to situations
- Focus on whether procedures or principles are correctly applied
- Include statements about cause-and-effect relationships
- Test understanding of when and how to use specific concepts
- Statements should require more than simple recall"""
                
            elif blooms_level == "analyze":
                return f"""{base_description}

For True/False Questions at Analyze level:
- Present statements requiring analysis of complex relationships
- Focus on evaluations, comparisons, or synthesis of information
- Include statements about effectiveness, appropriateness, or best practices
- Test ability to analyze scenarios and draw conclusions
- Statements should require sophisticated reasoning"""
        
        elif question_type == "fib":
            if blooms_level == "remember":
                return f"""{base_description}

For Fill-in-the-Blank Questions at Remember level:
- Remove key terms, definitions, or factual information
- Focus on vocabulary, names, dates, and basic concepts
- Blanks should test recall of specific information
- Context should clearly point to the expected answer
- Avoid complex relationships or applications"""
                
            elif blooms_level == "apply":
                return f"""{base_description}

For Fill-in-the-Blank Questions at Apply level:
- Remove answers that require applying formulas or procedures
- Focus on results of calculations or applications
- Present scenarios where students must determine outcomes
- Blanks should test ability to use concepts in context
- Include sufficient information for students to work through problems"""
                
            elif blooms_level == "analyze":
                return f"""{base_description}

For Fill-in-the-Blank Questions at Analyze level:
- Remove conclusions, evaluations, or synthesis results
- Focus on analytical outcomes or judgments
- Present complex scenarios requiring analysis
- Blanks should test higher-order thinking results
- Require students to analyze information to determine answers"""
        
        return base_description
    
    @staticmethod
    def calculate_question_distribution(
        total_questions: int,
        question_type_dist: Dict[str, float],
        difficulty_dist: Dict[str, float],
        blooms_dist: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate the exact number of questions for each combination of question type, difficulty, and bloom's level"""
        # First, calculate exact fractional counts for all combinations
        fractional_distribution = {}
        
        for q_type, q_ratio in question_type_dist.items():
            for difficulty, d_ratio in difficulty_dist.items():
                for blooms, b_ratio in blooms_dist.items():
                    exact_count = total_questions * q_ratio * d_ratio * b_ratio
                    key = f"{q_type}_{difficulty}_{blooms}"
                    fractional_distribution[key] = {
                        'question_type': q_type,
                        'difficulty': difficulty,
                        'blooms_level': blooms,
                        'exact_count': exact_count,
                        'count': int(exact_count)  # Floor value
                    }
        
        # Calculate remainder needed to reach total_questions
        current_total = sum([item['count'] for item in fractional_distribution.values()])
        remainder = total_questions - current_total
        
        # Sort by fractional part (descending) to allocate remainder
        sorted_keys = sorted(
            fractional_distribution.keys(),
            key=lambda k: fractional_distribution[k]['exact_count'] - fractional_distribution[k]['count'],
            reverse=True
        )
        
        # Distribute remainder to items with highest fractional parts
        for i in range(remainder):
            if i < len(sorted_keys):
                fractional_distribution[sorted_keys[i]]['count'] += 1
        
        # Remove items with zero count and clean up the structure
        distribution = {}
        for key, item in fractional_distribution.items():
            if item['count'] > 0:
                distribution[key] = {
                    'question_type': item['question_type'],
                    'difficulty': item['difficulty'],
                    'blooms_level': item['blooms_level'],
                    'count': item['count']
                }
        
        return distribution
    
    @staticmethod
    def create_question_sequence(question_breakdown: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
        """Create a sequence of (difficulty, blooms_level) tuples based on question breakdown"""
        sequence = []
        for combo_key, specs in question_breakdown.items():
            difficulty = specs['difficulty']
            blooms_level = specs['blooms_level']
            count = specs['count']
            
            # Add this combination 'count' times to the sequence
            for _ in range(count):
                sequence.append((difficulty, blooms_level))
        
        return sequence
    
    @staticmethod
    def generate_filename(
        chapter_name: str,
        difficulty_distribution: Dict[str, float],
        blooms_distribution: Dict[str, float],
        question_type: str,
        learning_objectives: Union[str, List[str], None] = None
    ) -> str:
        """Generate a standardized filename for question output"""
        # Clean chapter name for filename
        clean_chapter_name = chapter_name.replace(" ", "_").replace("/", "_")
        
        # Create distribution strings
        difficulty_str = "_".join([f"{diff}{int(prop*100)}" for diff, prop in difficulty_distribution.items()])
        blooms_str = "_".join([f"{bloom}{int(prop*100)}" for bloom, prop in blooms_distribution.items()])
        
        filename_parts = [clean_chapter_name, difficulty_str, blooms_str]
        
        # Add learning objectives if provided
        if learning_objectives:
            obj_str = "lo" + ("_".join([str(obj) for obj in learning_objectives]) if isinstance(learning_objectives, list) else str(learning_objectives))
            filename_parts.append(obj_str)
        
        # Add question type suffix
        suffix_map = {
            "mcq": "mcqs",
            "fib": "fib", 
            "tf": "tf"
        }
        suffix = suffix_map.get(question_type, question_type)
        
        return "_".join(filename_parts) + f"_{suffix}.json"
    
    @staticmethod
    def save_questions_to_file(questions: List[Dict[str, Any]], filename: str) -> None:
        """Save questions to JSON file"""
        json_response = {"response": questions}
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(json_response, json_file, indent=4, ensure_ascii=False)


# Create a singleton instance for easy access
question_helpers = QuestionHelpers()

# Export commonly used functions
get_difficulty_description = question_helpers.get_difficulty_description
get_blooms_description = question_helpers.get_blooms_description
get_blooms_question_guidelines = question_helpers.get_blooms_question_guidelines
calculate_question_distribution = question_helpers.calculate_question_distribution
create_question_sequence = question_helpers.create_question_sequence
generate_filename = question_helpers.generate_filename
save_questions_to_file = question_helpers.save_questions_to_file
