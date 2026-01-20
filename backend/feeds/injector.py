"""Inject world context into prompts."""

from typing import Dict, List, Any, Optional
import re
from .aggregator import get_current_context, format_context_for_prompt, get_topic_context
from ..config import FEEDS_CONFIG


def should_include_world_context(query: str) -> bool:
    """
    Determine if a query would benefit from world context.

    Args:
        query: The user's query

    Returns:
        True if world context should be included
    """
    if not FEEDS_CONFIG.get('enabled', True):
        return False

    keywords = FEEDS_CONFIG.get('keywords', [
        'current', 'today', 'latest', 'news', 'weather', 'now', 'recent'
    ])

    query_lower = query.lower()

    # Check for time-sensitive keywords
    for keyword in keywords:
        if keyword in query_lower:
            return True

    # Check for current events patterns
    current_patterns = [
        r'\b(what|how)\b.*\b(happening|going on)\b',
        r'\b(today|yesterday|this week|this month)\b',
        r'\b(latest|recent|current|new)\b',
        r'\b(news|headline|update)\b',
        r'\b\d{4}\b',  # Year mentions often indicate time-sensitive queries
    ]

    for pattern in current_patterns:
        if re.search(pattern, query_lower):
            return True

    return False


def extract_context_topics(query: str) -> List[str]:
    """
    Extract topics from a query for targeted context retrieval.

    Args:
        query: The user's query

    Returns:
        List of topic keywords
    """
    # Common stopwords to ignore
    stopwords = {
        'what', 'is', 'are', 'the', 'a', 'an', 'how', 'why', 'when', 'where',
        'who', 'which', 'can', 'could', 'would', 'should', 'do', 'does', 'did',
        'have', 'has', 'had', 'be', 'been', 'being', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'all', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'current',
        'latest', 'recent', 'today', 'happening'
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', query.lower())

    # Filter and get unique topics
    topics = []
    for word in words:
        if word not in stopwords and len(word) > 2:
            if word not in topics:
                topics.append(word)

    return topics[:3]  # Limit to top 3 topics


async def inject_world_context(
    base_prompt: str,
    query: str,
    force_include: bool = False
) -> str:
    """
    Inject relevant world context into a prompt.

    Args:
        base_prompt: The original prompt
        query: The user's query (used for context detection)
        force_include: Force context inclusion regardless of query analysis

    Returns:
        Enhanced prompt with world context
    """
    # Check if we should include context
    if not force_include and not should_include_world_context(query):
        return base_prompt

    # Extract topics for targeted context
    topics = extract_context_topics(query)

    # Get current world context
    context = await get_current_context(
        topics=topics if topics else None,
        include_weather='weather' in query.lower(),
        max_items=3
    )

    # Format context for prompt
    context_text = format_context_for_prompt(context)

    if not context_text:
        return base_prompt

    # Build enhanced prompt
    enhanced_prompt = f"""{context_text}

---

{base_prompt}"""

    return enhanced_prompt


async def build_world_aware_prompt(
    query: str,
    system_context: str = None
) -> str:
    """
    Build a complete prompt with world awareness.

    Args:
        query: The user's query
        system_context: Optional system context to include

    Returns:
        Complete prompt with world context
    """
    # Get targeted topic context
    topics = extract_context_topics(query)

    context_parts = []

    # Add topic-specific context
    if topics:
        topic_context = await get_topic_context(topics[0])
        if topic_context:
            context_parts.append(topic_context)

    # Add general current context if query seems time-sensitive
    if should_include_world_context(query):
        general_context = await get_current_context(max_items=2)
        formatted = format_context_for_prompt(general_context)
        if formatted:
            context_parts.append(formatted)

    # Build the prompt
    prompt_parts = []

    if system_context:
        prompt_parts.append(system_context)

    if context_parts:
        prompt_parts.append("\n".join(context_parts))

    prompt_parts.append(f"User Query: {query}")

    return "\n\n---\n\n".join(prompt_parts)


def create_time_aware_system_prompt() -> str:
    """
    Create a system prompt that encourages time-awareness.

    Returns:
        System prompt string
    """
    from datetime import datetime
    now = datetime.utcnow()

    return f"""You are aware of the current date and time.
Current date: {now.strftime('%Y-%m-%d')}
Current time (UTC): {now.strftime('%H:%M')}

When answering questions about current events, recent developments, or time-sensitive topics,
consider that your knowledge may not include the very latest information.
If world context is provided, use it to inform your response while being clear about
the distinction between your training data and the provided context."""
