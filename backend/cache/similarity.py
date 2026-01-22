"""Semantic similarity calculation for cache matching."""

import re
import math
from typing import Set, Dict
from collections import Counter


# Common stop words to filter out
STOP_WORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    's', 't', 'just', 'don', 'now', 'i', 'me', 'my', 'you', 'your', 'he',
    'she', 'it', 'we', 'they', 'what', 'which', 'who', 'whom', 'this',
    'that', 'these', 'those', 'am', 'but', 'if', 'or', 'because', 'until',
    'while', 'about', 'against', 'and', 'any', 'both', 'down', 'up', 'out',
    'off', 'over', 'under', 'its'
}


def tokenize(text: str) -> Set[str]:
    """
    Tokenize text into meaningful words.

    Args:
        text: Input text

    Returns:
        Set of lowercase words without stop words
    """
    words = re.findall(r'\b\w+\b', text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 1}


def calculate_tf(words: Set[str], text: str) -> Dict[str, float]:
    """
    Calculate term frequency for words in text.

    Args:
        words: Set of words to calculate TF for
        text: Original text

    Returns:
        Dict mapping word to TF score
    """
    all_words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(all_words)
    total = len(all_words) if all_words else 1

    return {w: word_counts.get(w, 0) / total for w in words}


def calculate_query_similarity(query1: str, query2: str) -> float:
    """
    Calculate semantic similarity between two queries.

    Uses a combination of:
    - Jaccard similarity (word overlap)
    - TF-weighted cosine similarity

    Args:
        query1: First query
        query2: Second query

    Returns:
        Similarity score between 0 and 1
    """
    # Tokenize both queries
    words1 = tokenize(query1)
    words2 = tokenize(query2)

    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = words1 & words2
    union = words1 | words2
    jaccard = len(intersection) / len(union) if union else 0.0

    # Calculate TF-weighted similarity
    all_words = words1 | words2

    tf1 = calculate_tf(all_words, query1)
    tf2 = calculate_tf(all_words, query2)

    # Cosine similarity of TF vectors
    dot_product = sum(tf1[w] * tf2[w] for w in all_words)
    norm1 = math.sqrt(sum(tf1[w] ** 2 for w in all_words))
    norm2 = math.sqrt(sum(tf2[w] ** 2 for w in all_words))

    cosine = dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

    # Combine scores (weight Jaccard more for short queries)
    avg_len = (len(words1) + len(words2)) / 2
    if avg_len <= 5:
        # Short queries: rely more on exact word match
        return 0.7 * jaccard + 0.3 * cosine
    else:
        # Longer queries: balance both
        return 0.5 * jaccard + 0.5 * cosine
