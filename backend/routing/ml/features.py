"""Feature extraction for query routing."""

import re
from typing import Dict, Any, List
from dataclasses import dataclass


# Technical domain keywords
TECHNICAL_KEYWORDS = {
    'code', 'programming', 'algorithm', 'database', 'api', 'function',
    'class', 'variable', 'bug', 'error', 'debug', 'compile', 'runtime',
    'python', 'javascript', 'java', 'typescript', 'react', 'node',
    'sql', 'docker', 'kubernetes', 'aws', 'cloud', 'server', 'deploy',
}

# Reasoning keywords
REASONING_KEYWORDS = {
    'analyze', 'compare', 'evaluate', 'explain', 'why', 'how', 'because',
    'reason', 'logic', 'argument', 'evidence', 'conclusion', 'therefore',
    'consider', 'weigh', 'trade-off', 'pros', 'cons', 'implications',
}

# Creative keywords
CREATIVE_KEYWORDS = {
    'write', 'create', 'design', 'imagine', 'story', 'poem', 'creative',
    'innovate', 'brainstorm', 'ideate', 'novel', 'unique', 'original',
}

# Simple query patterns
SIMPLE_PATTERNS = [
    r'^what is\s',
    r'^who is\s',
    r'^when (was|did|is)\s',
    r'^where is\s',
    r'^define\s',
    r'^how (do|does) (you|one)\s',
]


@dataclass
class QueryFeatures:
    """Extracted features from a query."""
    # Length features
    char_count: int
    word_count: int
    sentence_count: int
    avg_word_length: float

    # Structural features
    question_count: int
    has_multiple_questions: bool
    has_bullet_points: bool
    has_code_block: bool

    # Domain features
    technical_keyword_count: int
    reasoning_keyword_count: int
    creative_keyword_count: int

    # Pattern features
    matches_simple_pattern: bool
    has_conditional: bool
    has_comparison: bool

    # Complexity indicators
    nested_clause_count: int
    conjunction_count: int

    def to_vector(self) -> List[float]:
        """Convert features to a numerical vector."""
        return [
            self.char_count / 500,  # Normalize
            self.word_count / 100,
            self.sentence_count / 10,
            self.avg_word_length / 10,
            self.question_count,
            1.0 if self.has_multiple_questions else 0.0,
            1.0 if self.has_bullet_points else 0.0,
            1.0 if self.has_code_block else 0.0,
            self.technical_keyword_count / 5,
            self.reasoning_keyword_count / 5,
            self.creative_keyword_count / 5,
            1.0 if self.matches_simple_pattern else 0.0,
            1.0 if self.has_conditional else 0.0,
            1.0 if self.has_comparison else 0.0,
            self.nested_clause_count / 5,
            self.conjunction_count / 5,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'char_count': self.char_count,
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'avg_word_length': self.avg_word_length,
            'question_count': self.question_count,
            'has_multiple_questions': self.has_multiple_questions,
            'has_bullet_points': self.has_bullet_points,
            'has_code_block': self.has_code_block,
            'technical_keyword_count': self.technical_keyword_count,
            'reasoning_keyword_count': self.reasoning_keyword_count,
            'creative_keyword_count': self.creative_keyword_count,
            'matches_simple_pattern': self.matches_simple_pattern,
            'has_conditional': self.has_conditional,
            'has_comparison': self.has_comparison,
            'nested_clause_count': self.nested_clause_count,
            'conjunction_count': self.conjunction_count,
        }


def extract_features(query: str) -> QueryFeatures:
    """
    Extract features from a query for routing.

    Args:
        query: The user's query string

    Returns:
        QueryFeatures object
    """
    query_lower = query.lower()
    words = query.split()
    sentences = re.split(r'[.!?]+', query)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Length features
    char_count = len(query)
    word_count = len(words)
    sentence_count = len(sentences)
    avg_word_length = sum(len(w) for w in words) / max(word_count, 1)

    # Structural features
    question_count = query.count('?')
    has_multiple_questions = question_count > 1
    has_bullet_points = bool(re.search(r'^\s*[-*•]\s', query, re.MULTILINE))
    has_code_block = '```' in query or bool(re.search(r'`[^`]+`', query))

    # Domain features
    technical_keyword_count = sum(1 for kw in TECHNICAL_KEYWORDS if kw in query_lower)
    reasoning_keyword_count = sum(1 for kw in REASONING_KEYWORDS if kw in query_lower)
    creative_keyword_count = sum(1 for kw in CREATIVE_KEYWORDS if kw in query_lower)

    # Pattern features
    matches_simple_pattern = any(re.match(p, query_lower) for p in SIMPLE_PATTERNS)
    has_conditional = bool(re.search(r'\b(if|when|unless|provided|assuming)\b', query_lower))
    has_comparison = bool(re.search(r'\b(vs|versus|compare|better|worse|difference)\b', query_lower))

    # Complexity indicators
    nested_clause_count = len(re.findall(r',\s*\w+\s+\w+', query))
    conjunction_count = len(re.findall(r'\b(and|but|or|however|therefore|because)\b', query_lower))

    return QueryFeatures(
        char_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
        avg_word_length=avg_word_length,
        question_count=question_count,
        has_multiple_questions=has_multiple_questions,
        has_bullet_points=has_bullet_points,
        has_code_block=has_code_block,
        technical_keyword_count=technical_keyword_count,
        reasoning_keyword_count=reasoning_keyword_count,
        creative_keyword_count=creative_keyword_count,
        matches_simple_pattern=matches_simple_pattern,
        has_conditional=has_conditional,
        has_comparison=has_comparison,
        nested_clause_count=nested_clause_count,
        conjunction_count=conjunction_count,
    )
