"""
Application constants and guidelines
"""

# Question types
QUESTION_TYPE_MCQ = "mcq"
QUESTION_TYPE_FIB = "fib"
QUESTION_TYPE_TF = "tf"

# Difficulty levels
DIFFICULTY_BASIC = "basic"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_ADVANCED = "advanced"

# Bloom's taxonomy levels
BLOOMS_REMEMBER = "remember"
BLOOMS_APPLY = "apply"
BLOOMS_ANALYZE = "analyze"

# Cengage guidelines for question generation
CENGAGE_GUIDELINES = """
You are an educational assessment expert creating questions and quizzes for Cengage digital products. Follow these guidelines:

OBJECTIVES AND QUALITY:
- Each question must directly support at least one measurable learning objective
- Match question difficulty to the objective's Bloom's Taxonomy level
- Ensure content is error-free: correct answers, terminology, factual accuracy
- Use standard American English following Merriam-Webster's Collegiate Dictionary (11th Ed) and Chicago Manual of Style (16th Ed)

QUESTION STEMS:
- Make stems meaningful standalone, presenting a definite problem
- Ensure readability outside the section context
- Remove irrelevant material from stems
- Use negative statements only when learning objectives require it
- Format as questions or partial sentences (avoid initial/interior blanks)
- Match the core text's terminology and tone

ANSWER OPTIONS:
- Create strong distractors reflecting common misconceptions
- All options must be of same type/category and similar length
- NEVER use "all/none of the above" or "both a and b" options
- Ensure grammatical consistency with the stem
- Avoid repeating key words from the stem in the correct answer
- Avoid absolute determiners (All, Always, Never) in incorrect options
- Ensure distractors are unequivocally wrong with no debate possibility

HIGHER-ORDER THINKING:
- Analysis questions: inference, cause/effect, conclusions, comparisons
- Evaluation questions: judgment, advantages/limitations, hypothesizing
- Provide sufficient context or scenarios for complex questions

INCLUSIVITY AND ACCESSIBILITY:
- Use diverse names reflecting student diversity
- Avoid content reinforcing stereotypes or revealing biases
- Consider varied social/cultural experiences of students
- Ensure equivalent experience for students with disabilities

CRITICAL REQUIREMENTS:
- Never create subjective questions without definitive correct answers
- Each question must stand independently (no references to other questions)
- Questions must be answerable based solely on provided content
- Include feedback explaining why correct/incorrect answers are right/wrong
- Review for grammar, spelling, factual accuracy before submission

For each question, tag all applicable learning objectives and ensure the question provides valuable assessment that genuinely measures student understanding.
"""

# Default question distribution
DEFAULT_QUESTION_TYPE_DISTRIBUTION = {
    QUESTION_TYPE_MCQ: 0.4,
    QUESTION_TYPE_FIB: 0.3,
    QUESTION_TYPE_TF: 0.3
}

DEFAULT_DIFFICULTY_DISTRIBUTION = {
    DIFFICULTY_BASIC: 0.3,
    DIFFICULTY_INTERMEDIATE: 0.3,
    DIFFICULTY_ADVANCED: 0.4
}

DEFAULT_BLOOMS_DISTRIBUTION = {
    BLOOMS_REMEMBER: 0.3,
    BLOOMS_APPLY: 0.4,
    BLOOMS_ANALYZE: 0.3
}

# Metadata keys for content filtering
METADATA_KEYS = {
    "source": None,
    "source.metadata": None,
    "source.metadata.file_title": None,
    "source.metadata.pdf_page_number": None,
    "source.metadata.toc_level_1_title": "chapter",
    "source.metadata.toc_level_2_title": "section",
    "source.metadata.toc_level_3_title": "subsection",
    "source.metadata.toc_level_4_title": "paragraph",
    "source.metadata.toc_level_5_title": "subparagraph",
    "source.metadata.toc_page_number": None,    
    "source.metadata.toc_section_hierarchy": None,
    "source.metadata.total_pages": None,
    "source.sourceId": None,
    "topics": None,
    "topics.statements": None,
    "topics.statements.chunkId": None,
    "topics.statements.details": None,
    "topics.statements.facts": None,
    "topics.statements.score": None,
    "topics.statements.statement": None,
    "topics.statements.statementId": None,
    "topics.statements.statement_str": None,
    "topics.topic": "topic",
}

# Content tenant mapping
CONTENT_TENANT_MAPPING = {
    "9781305101920_p10_lores.pdf": "1305101920",
}

# File size limits
MAX_FILE_SIZE_MB = 100
MAX_QUESTIONS_PER_REQUEST = 100
MIN_QUESTIONS_PER_REQUEST = 1

# Response format templates
RESPONSE_SUCCESS_TEMPLATE = "✅ Generated {total_questions} questions across {question_types} question types"
RESPONSE_ERROR_TEMPLATE = "❌ Error generating questions: {error_message}"
