"""Web search tool implementation."""

import httpx
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..config import FEEDS_CONFIG

# Simple in-memory cache for search results
_search_cache: Dict[str, tuple] = {}  # query -> (result, timestamp)
CACHE_DURATION = timedelta(minutes=15)


async def web_search(query: str) -> Dict[str, Any]:
    """
    Search the web for information.

    Uses DuckDuckGo Instant Answer API as a free option.
    Falls back to a placeholder if no API is available.

    Args:
        query: The search query

    Returns:
        Dict with search results
    """
    # Check cache first
    cache_key = query.lower().strip()
    if cache_key in _search_cache:
        cached_result, cached_time = _search_cache[cache_key]
        if datetime.utcnow() - cached_time < CACHE_DURATION:
            return {
                "success": True,
                "cached": True,
                "results": cached_result
            }

    try:
        # Use DuckDuckGo Instant Answer API (free, no API key needed)
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Parse DuckDuckGo response
        results = []

        # Abstract (main answer)
        if data.get("Abstract"):
            results.append({
                "type": "abstract",
                "title": data.get("Heading", ""),
                "content": data.get("Abstract", ""),
                "source": data.get("AbstractSource", ""),
                "url": data.get("AbstractURL", "")
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "type": "related",
                    "content": topic.get("Text", ""),
                    "url": topic.get("FirstURL", "")
                })

        # Answer (for calculations, etc.)
        if data.get("Answer"):
            results.append({
                "type": "answer",
                "content": data.get("Answer", ""),
                "answer_type": data.get("AnswerType", "")
            })

        # Cache result
        _search_cache[cache_key] = (results, datetime.utcnow())

        if results:
            return {
                "success": True,
                "cached": False,
                "query": query,
                "results": results
            }
        else:
            return {
                "success": True,
                "cached": False,
                "query": query,
                "results": [],
                "message": "No instant answer available. Results may require a full web search."
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "message": "Web search temporarily unavailable"
        }


def format_search_results(results: Dict[str, Any]) -> str:
    """
    Format search results for injection into model context.

    Args:
        results: Raw search results

    Returns:
        Formatted string
    """
    if not results.get("success"):
        return f"[Search failed: {results.get('error', 'Unknown error')}]"

    if not results.get("results"):
        return f"[No results found for: {results.get('query', 'query')}]"

    lines = [f"Web search results for: {results.get('query', 'query')}"]

    for i, result in enumerate(results.get("results", []), 1):
        result_type = result.get("type", "result")

        if result_type == "abstract":
            lines.append(f"\n{result.get('title', 'Result')}:")
            lines.append(f"  {result.get('content', '')}")
            if result.get("source"):
                lines.append(f"  Source: {result.get('source')}")

        elif result_type == "answer":
            lines.append(f"\nDirect Answer: {result.get('content', '')}")

        elif result_type == "related":
            lines.append(f"\n{i}. {result.get('content', '')}")

    return "\n".join(lines)
