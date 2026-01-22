"""Query complexity analysis for smart routing."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import re


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis on a query."""
    score: float  # 0.0 to 1.0
    factors: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""

    @property
    def tier(self) -> int:
        """Get the recommended tier based on score."""
        if self.score < 0.3:
            return 1  # Single model
        elif self.score < 0.7:
            return 2  # Mini council
        else:
            return 3  # Full council


# Technical terms that indicate complexity
TECHNICAL_TERMS = {
    # Programming
    "algorithm", "architecture", "async", "asynchronous", "api", "backend",
    "cache", "class", "compiler", "complexity", "concurrent", "database",
    "debug", "deploy", "distributed", "docker", "encryption", "frontend",
    "function", "git", "hash", "implement", "inheritance", "interface",
    "kubernetes", "lambda", "latency", "microservice", "middleware",
    "multithread", "network", "optimization", "parallel", "pipeline",
    "polymorphism", "protocol", "queue", "recursion", "refactor", "regex",
    "rest", "scalability", "schema", "security", "server", "socket",
    "synchronous", "thread", "typescript", "virtualization", "webpack",
    # Science/Math
    "theorem", "proof", "equation", "integral", "derivative", "matrix",
    "vector", "statistical", "hypothesis", "correlation", "regression",
    "probability", "quantum", "relativity", "entropy", "thermodynamic",
    # Philosophy/Ethics
    "epistemology", "ontology", "metaphysics", "utilitarian", "deontological",
    "consequentialism", "categorical", "existential", "phenomenology",
    # General complexity indicators
    "tradeoff", "trade-off", "compare", "contrast", "analyze", "evaluate",
    "implications", "consequences", "nuanced", "multifaceted", "comprehensive",
}

# Question words that indicate simple queries
SIMPLE_INDICATORS = {
    "what is", "what's", "who is", "who's", "when is", "when was",
    "where is", "where's", "how many", "how much", "how old",
    "define", "definition of", "meaning of",
}

# Patterns that indicate sub-questions or multi-part queries
MULTI_PART_PATTERNS = [
    r'\b(first|second|third|finally|also|additionally|moreover|furthermore)\b',
    r'\b(and|or)\s+\w+\s+(should|would|could|can|will)\b',
    r'\d+\.\s+',  # Numbered lists
    r'[•\-\*]\s+',  # Bullet points
    r'\?\s+\w',  # Multiple questions
]

# Ambiguity indicators
AMBIGUITY_INDICATORS = [
    "best way", "should i", "which is better", "what do you think",
    "opinion on", "advice", "recommend", "suggestion", "depends on",
    "it varies", "context", "situation", "case by case",
]


def analyze_query_complexity(query: str) -> ComplexityAnalysis:
    """
    Analyze query complexity to determine routing tier.

    Factors considered:
    - Query length (longer queries tend to be more complex)
    - Number of sub-questions or parts
    - Presence of technical terms
    - Ambiguity level (subjective questions need more perspectives)

    Args:
        query: The user's query string

    Returns:
        ComplexityAnalysis with score, factors, and reasoning
    """
    query_lower = query.lower()
    words = re.findall(r'\b\w+\b', query_lower)
    word_count = len(words)

    factors = {}
    reasoning_parts = []

    # Factor 1: Query length (0.0 - 0.25)
    if word_count <= 5:
        length_score = 0.0
        reasoning_parts.append("Very short query")
    elif word_count <= 15:
        length_score = 0.1
        reasoning_parts.append("Short query")
    elif word_count <= 30:
        length_score = 0.15
        reasoning_parts.append("Medium-length query")
    elif word_count <= 50:
        length_score = 0.2
        reasoning_parts.append("Long query")
    else:
        length_score = 0.25
        reasoning_parts.append("Very long query")
    factors['length'] = length_score

    # Factor 2: Simple question detection (reduces score)
    simple_score = 0.0
    for indicator in SIMPLE_INDICATORS:
        if indicator in query_lower:
            simple_score = -0.2
            reasoning_parts.append(f"Simple question pattern: '{indicator}'")
            break
    factors['simplicity'] = simple_score

    # Factor 3: Technical terms (0.0 - 0.3)
    tech_count = sum(1 for word in words if word in TECHNICAL_TERMS)
    tech_ratio = tech_count / max(word_count, 1)
    tech_score = min(tech_ratio * 3, 0.3)  # Cap at 0.3
    if tech_count > 0:
        reasoning_parts.append(f"Contains {tech_count} technical term(s)")
    factors['technical'] = tech_score

    # Factor 4: Multi-part query detection (0.0 - 0.25)
    multi_part_count = 0
    for pattern in MULTI_PART_PATTERNS:
        multi_part_count += len(re.findall(pattern, query_lower))

    question_marks = query.count('?')
    if question_marks > 1:
        multi_part_count += question_marks - 1
        reasoning_parts.append(f"Contains {question_marks} questions")

    multi_score = min(multi_part_count * 0.1, 0.25)
    if multi_part_count > 0:
        reasoning_parts.append(f"Multi-part query detected ({multi_part_count} parts)")
    factors['multi_part'] = multi_score

    # Factor 5: Ambiguity/subjectivity (0.0 - 0.2)
    ambiguity_count = sum(1 for ind in AMBIGUITY_INDICATORS if ind in query_lower)
    ambiguity_score = min(ambiguity_count * 0.1, 0.2)
    if ambiguity_count > 0:
        reasoning_parts.append(f"Contains {ambiguity_count} ambiguity indicator(s)")
    factors['ambiguity'] = ambiguity_score

    # Calculate total score
    total_score = sum(factors.values())
    # Clamp to [0, 1]
    total_score = max(0.0, min(1.0, total_score))

    # Build reasoning string
    tier = 1 if total_score < 0.3 else (2 if total_score < 0.7 else 3)
    tier_names = {1: "single model", 2: "mini council", 3: "full council"}
    reasoning = f"Score: {total_score:.2f} -> {tier_names[tier]}. " + "; ".join(reasoning_parts)

    return ComplexityAnalysis(
        score=total_score,
        factors=factors,
        reasoning=reasoning
    )
