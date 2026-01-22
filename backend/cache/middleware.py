"""Cache middleware for checking and storing responses."""

from typing import Optional, Dict, Any, List, Tuple
from .storage import CachedResponse, get_cache
from ..config import SEMANTIC_CACHE_CONFIG


def check_cache(query: str) -> Optional[Tuple[CachedResponse, float]]:
    """
    Check if a similar query exists in cache.

    Args:
        query: The user's query

    Returns:
        Tuple of (CachedResponse, similarity_score) if cache hit, None otherwise
    """
    if not SEMANTIC_CACHE_CONFIG.get("enabled", True):
        return None

    cache = get_cache()

    # First try exact match
    exact = cache.get(query)
    if exact:
        return (exact, 1.0)

    # Then try semantic similarity
    from .similarity import calculate_query_similarity

    similar = cache.find_similar(query)
    if similar:
        score = calculate_query_similarity(query, similar.query)
        return (similar, score)

    return None


def cache_response(
    query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    metadata: Dict[str, Any],
    routing_tier: Optional[int] = None
) -> None:
    """
    Cache a council response.

    Args:
        query: The original query
        stage1_results: Stage 1 responses
        stage2_results: Stage 2 rankings
        stage3_result: Stage 3 synthesis
        metadata: Additional metadata
        routing_tier: The routing tier used
    """
    if not SEMANTIC_CACHE_CONFIG.get("enabled", True):
        return

    cache = get_cache()
    cache.set(
        query=query,
        stage1_results=stage1_results,
        stage2_results=stage2_results,
        stage3_result=stage3_result,
        metadata=metadata,
        routing_tier=routing_tier
    )


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    if not SEMANTIC_CACHE_CONFIG.get("enabled", True):
        return {"enabled": False}

    cache = get_cache()
    stats = cache.get_stats()
    stats["enabled"] = True
    return stats


def clear_cache() -> Dict[str, str]:
    """Clear the cache."""
    cache = get_cache()
    cache.clear()
    return {"status": "cleared"}
