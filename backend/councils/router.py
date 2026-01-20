"""Route queries to appropriate specialized councils."""

from typing import Dict, List, Any, Optional, Tuple
from .definitions import (
    Council, get_council, get_all_councils,
    get_default_council, get_councils_by_keyword
)
import re


def detect_topic(query: str) -> List[str]:
    """
    Detect topic keywords from a query.

    Args:
        query: The user's query

    Returns:
        List of detected topic keywords
    """
    # Topic keyword patterns
    topic_patterns = {
        'math': [
            r'\b(math|calculate|equation|formula|solve|algebra|calculus|geometry)\b',
            r'\b(integral|derivative|proof|theorem|statistics|probability)\b',
            r'\b(\d+\s*[\+\-\*\/\^]\s*\d+)\b',  # Mathematical expressions
            r'\b(sum|product|average|mean|median|variance)\b'
        ],
        'ethics': [
            r'\b(ethics|ethical|moral|morality|right|wrong)\b',
            r'\b(should|ought|values|virtue|justice|fair)\b',
            r'\b(conscience|duty|responsibility|principle)\b',
            r'\b(philosophy|philosophical)\b'
        ],
        'creative': [
            r'\b(write|story|poem|creative|imagine|fiction)\b',
            r'\b(narrative|character|plot|scene|dialogue)\b',
            r'\b(art|artistic|design|aesthetic|beautiful)\b',
            r'\b(song|lyrics|screenplay|novel|essay)\b'
        ],
        'code': [
            r'\b(code|program|function|class|algorithm)\b',
            r'\b(python|javascript|java|typescript|rust|go)\b',
            r'\b(debug|error|bug|fix|implement)\b',
            r'\b(api|database|server|frontend|backend)\b'
        ],
        'science': [
            r'\b(science|scientific|experiment|hypothesis)\b',
            r'\b(physics|chemistry|biology|astronomy)\b',
            r'\b(research|study|evidence|data|analysis)\b',
            r'\b(molecule|atom|cell|gene|planet)\b'
        ]
    }

    query_lower = query.lower()
    detected_topics = []

    for topic, patterns in topic_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                if topic not in detected_topics:
                    detected_topics.append(topic)
                break

    return detected_topics


def calculate_council_score(
    query: str,
    council: Council,
    detected_topics: List[str]
) -> float:
    """
    Calculate how well a council matches a query.

    Args:
        query: The user's query
        council: The council to score
        detected_topics: Pre-detected topic keywords

    Returns:
        Score between 0 and 1
    """
    if not council.keywords:
        return 0.0  # General council has no keywords, matches anything

    query_lower = query.lower()
    query_words = set(re.findall(r'\b\w+\b', query_lower))

    # Check keyword matches
    keyword_matches = sum(
        1 for kw in council.keywords
        if kw.lower() in query_lower or kw.lower() in query_words
    )

    if not council.keywords:
        return 0.0

    keyword_score = keyword_matches / len(council.keywords)

    # Bonus for detected topic matching council ID
    topic_bonus = 0.2 if council.id in detected_topics else 0

    # Priority bonus
    priority_bonus = council.priority * 0.1

    return min(keyword_score + topic_bonus + priority_bonus, 1.0)


def route_query(
    query: str,
    force_council: str = None,
    min_score: float = 0.3
) -> Tuple[Council, float, Dict[str, Any]]:
    """
    Route a query to the most appropriate council.

    Args:
        query: The user's query
        force_council: Force routing to a specific council
        min_score: Minimum score to use a specialized council

    Returns:
        Tuple of (selected_council, confidence_score, routing_info)
    """
    # If a council is forced, use it
    if force_council:
        council = get_council(force_council)
        if council:
            return council, 1.0, {
                'method': 'forced',
                'council_id': force_council
            }

    # Detect topics
    detected_topics = detect_topic(query)

    # Score all councils
    council_scores = []
    for council in get_all_councils():
        if council.id == 'general':
            continue  # Skip general council for scoring
        if council.id == 'supreme':
            continue  # Supreme is only for appeals

        score = calculate_council_score(query, council, detected_topics)
        if score > 0:
            council_scores.append((council, score))

    # Sort by score
    council_scores.sort(key=lambda x: x[1], reverse=True)

    routing_info = {
        'method': 'auto',
        'detected_topics': detected_topics,
        'scores': {c.id: s for c, s in council_scores[:5]}
    }

    # Use the best match if it exceeds minimum score
    if council_scores and council_scores[0][1] >= min_score:
        best_council, best_score = council_scores[0]
        routing_info['council_id'] = best_council.id
        return best_council, best_score, routing_info

    # Default to general council
    general = get_default_council()
    routing_info['council_id'] = general.id
    routing_info['fallback'] = True

    return general, 0.5, routing_info


def suggest_councils(query: str, limit: int = 3) -> List[Tuple[Council, float]]:
    """
    Suggest councils for a query without selecting one.

    Args:
        query: The user's query
        limit: Maximum suggestions to return

    Returns:
        List of (council, score) tuples
    """
    detected_topics = detect_topic(query)

    suggestions = []
    for council in get_all_councils():
        if council.id in ('general', 'supreme'):
            continue

        score = calculate_council_score(query, council, detected_topics)
        if score > 0.1:
            suggestions.append((council, score))

    suggestions.sort(key=lambda x: x[1], reverse=True)
    return suggestions[:limit]


def get_routing_explanation(
    query: str,
    council: Council,
    score: float,
    routing_info: Dict[str, Any]
) -> str:
    """
    Generate a human-readable explanation of why a council was selected.

    Args:
        query: The original query
        council: The selected council
        score: The confidence score
        routing_info: Additional routing information

    Returns:
        Explanation string
    """
    if routing_info.get('method') == 'forced':
        return f"Council '{council.name}' was explicitly selected."

    if routing_info.get('fallback'):
        return (
            f"No specialized council matched with sufficient confidence. "
            f"Using the General Council."
        )

    topics = routing_info.get('detected_topics', [])
    topic_str = ', '.join(topics) if topics else 'general'

    return (
        f"Query appears to be about {topic_str}. "
        f"Routing to {council.name} with {score*100:.0f}% confidence. "
        f"This council specializes in: {council.description}"
    )
