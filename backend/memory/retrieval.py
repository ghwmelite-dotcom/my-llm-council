"""Memory retrieval and relevance search."""

from typing import List, Dict, Any, Tuple
from .storage import Memory, get_memory_store
from ..config import MEMORY_CONFIG
import re


def calculate_keyword_relevance(query: str, memory: Memory) -> float:
    """
    Calculate relevance score based on keyword matching.

    Args:
        query: The search query
        memory: The memory to score

    Returns:
        Relevance score between 0 and 1
    """
    # Extract keywords from query (simple word tokenization)
    query_words = set(re.findall(r'\b\w+\b', query.lower()))

    # Get words from memory content
    content_words = set(re.findall(r'\b\w+\b', memory.content.lower()))

    # Get words from memory tags
    tag_words = set()
    for tag in memory.tags:
        tag_words.update(re.findall(r'\b\w+\b', tag.lower()))

    # Calculate overlap
    content_overlap = len(query_words & content_words)
    tag_overlap = len(query_words & tag_words)

    if not query_words:
        return 0.0

    # Content match is weighted more heavily, tags provide boost
    content_score = content_overlap / len(query_words) if query_words else 0
    tag_score = tag_overlap / len(query_words) if query_words else 0

    # Combine scores (content: 70%, tags: 30%)
    base_score = (content_score * 0.7) + (tag_score * 0.3)

    # Apply importance multiplier
    importance_boost = memory.importance * 0.2

    # Apply recency boost (newer memories get slight boost)
    # Not implemented fully here but could be added

    return min(base_score + importance_boost, 1.0)


def search_memories(
    query: str,
    memory_types: List[str] = None,
    tags: List[str] = None,
    min_relevance: float = None,
    limit: int = None
) -> List[Tuple[Memory, float]]:
    """
    Search memories with relevance scoring.

    Args:
        query: Search query
        memory_types: Filter by memory types
        tags: Filter by tags
        min_relevance: Minimum relevance threshold
        limit: Maximum number of results

    Returns:
        List of (memory, relevance_score) tuples, sorted by relevance
    """
    store = get_memory_store()
    memories = store.get_all_memories()

    min_relevance = min_relevance or MEMORY_CONFIG.get('memory_relevance_threshold', 0.3)
    limit = limit or MEMORY_CONFIG.get('max_memories_per_query', 5)

    # Filter by type if specified
    if memory_types:
        memories = [m for m in memories if m.type in memory_types]

    # Filter by tags if specified
    if tags:
        memories = [m for m in memories if any(t in m.tags for t in tags)]

    # Calculate relevance scores
    scored_memories = []
    for memory in memories:
        score = calculate_keyword_relevance(query, memory)
        if score >= min_relevance:
            scored_memories.append((memory, score))

    # Sort by relevance (descending)
    scored_memories.sort(key=lambda x: x[1], reverse=True)

    # Limit results
    results = scored_memories[:limit]

    # Record access for retrieved memories
    for memory, _ in results:
        store.record_access(memory.id)

    return results


def get_relevant_memories(
    query: str,
    context: Dict[str, Any] = None,
    limit: int = None
) -> List[Memory]:
    """
    Get relevant memories for a query, with optional context filtering.

    Args:
        query: The user's query
        context: Optional context (e.g., current council, topic)
        limit: Maximum memories to return

    Returns:
        List of relevant Memory objects
    """
    limit = limit or MEMORY_CONFIG.get('max_memories_per_query', 5)

    # Extract potential topic tags from context
    tags = []
    if context:
        if 'council' in context:
            tags.append(context['council'])
        if 'topic' in context:
            tags.append(context['topic'])

    # Search with relevance scoring
    results = search_memories(
        query=query,
        tags=tags if tags else None,
        limit=limit
    )

    # Return just the memories (not the scores)
    return [memory for memory, score in results]


def get_memories_for_model(model_id: str, limit: int = 5) -> List[Memory]:
    """
    Get memories associated with a specific model.

    Args:
        model_id: The model identifier
        limit: Maximum memories to return

    Returns:
        List of Memory objects
    """
    store = get_memory_store()
    memories = store.get_memories_by_model(model_id)

    # Sort by importance and recency
    sorted_memories = sorted(
        memories,
        key=lambda m: (m.importance, m.created_at),
        reverse=True
    )

    return sorted_memories[:limit]


def get_relationship_memories(
    model_a: str,
    model_b: str,
    limit: int = 3
) -> List[Memory]:
    """
    Get memories about the relationship between two models.

    Args:
        model_a: First model ID
        model_b: Second model ID
        limit: Maximum memories to return

    Returns:
        List of relationship Memory objects
    """
    store = get_memory_store()
    relationship_memories = store.get_memories_by_type('relationship')

    # Filter for memories mentioning both models
    relevant = [
        m for m in relationship_memories
        if model_a in m.related_models and model_b in m.related_models
    ]

    # Sort by recency
    relevant.sort(key=lambda m: m.created_at, reverse=True)

    return relevant[:limit]
