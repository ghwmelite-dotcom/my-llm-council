"""Aggregate and filter feed data."""

from typing import Dict, List, Any, Optional
from .manager import FeedItem, get_feed_manager


async def aggregate_feeds(
    query: str = None,
    sources: List[str] = None,
    limit: int = 10
) -> List[FeedItem]:
    """
    Aggregate feed items from multiple sources.

    Args:
        query: Optional query to filter/search feeds
        sources: List of sources to include (default: all)
        limit: Maximum total items to return

    Returns:
        List of aggregated FeedItem objects
    """
    manager = get_feed_manager()

    # Determine which sources to fetch
    include_news = sources is None or 'news' in sources
    include_weather = sources is None or 'weather' in sources
    include_wikipedia = sources is None or 'wikipedia' in sources

    # Fetch all feeds
    feeds = await manager.fetch_all_feeds(
        include_news=include_news,
        include_weather=include_weather,
        include_wikipedia=include_wikipedia,
        news_query=query if query and include_news else None
    )

    # Combine all items
    all_items = []
    for source_items in feeds.values():
        all_items.extend(source_items)

    # Sort by recency (most recent first)
    all_items.sort(
        key=lambda x: x.published_at if x.published_at else '',
        reverse=True
    )

    # Filter by query if provided (simple keyword match)
    if query:
        query_lower = query.lower()
        filtered = [
            item for item in all_items
            if query_lower in item.title.lower() or query_lower in item.content.lower()
        ]
        # If filtering returns too few results, include all
        if len(filtered) >= 2:
            all_items = filtered

    return all_items[:limit]


async def get_current_context(
    topics: List[str] = None,
    include_weather: bool = True,
    max_items: int = 5
) -> Dict[str, Any]:
    """
    Get current world context for enriching prompts.

    Args:
        topics: Specific topics to focus on
        include_weather: Whether to include weather
        max_items: Maximum feed items to include

    Returns:
        Dict with structured world context
    """
    manager = get_feed_manager()

    context = {
        'timestamp': None,
        'news': [],
        'weather': None,
        'current_events': None
    }

    from datetime import datetime
    context['timestamp'] = datetime.utcnow().isoformat()

    # Fetch relevant feeds
    try:
        # Get news
        news_items = await manager.fetch_news(
            query=topics[0] if topics else None,
            limit=max_items
        )
        context['news'] = [
            {
                'title': item.title,
                'summary': item.content[:200] if item.content else '',
                'source': item.source
            }
            for item in news_items
        ]

        # Get weather if requested
        if include_weather:
            weather = await manager.fetch_weather()
            if weather:
                context['weather'] = weather.content

        # Get current events
        events = await manager.fetch_wikipedia_current_events()
        if events:
            context['current_events'] = events[0].content[:500]

    except Exception as e:
        print(f"Error getting current context: {e}")

    return context


def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """
    Format world context for inclusion in a prompt.

    Args:
        context: Context dict from get_current_context

    Returns:
        Formatted string for prompt injection
    """
    parts = []

    if context.get('timestamp'):
        parts.append(f"Current time: {context['timestamp']}")

    if context.get('weather'):
        parts.append(f"Weather: {context['weather']}")

    if context.get('news'):
        news_items = context['news'][:3]
        news_text = "\n".join([
            f"  - {item['title']}"
            for item in news_items
        ])
        parts.append(f"Recent headlines:\n{news_text}")

    if context.get('current_events'):
        parts.append(f"Current events: {context['current_events'][:300]}...")

    if not parts:
        return ""

    return "WORLD CONTEXT:\n" + "\n".join(parts)


async def get_topic_context(topic: str) -> str:
    """
    Get context specifically relevant to a topic.

    Args:
        topic: The topic to get context for

    Returns:
        Formatted context string
    """
    manager = get_feed_manager()

    # Search news for the topic
    news_items = await manager.fetch_news(query=topic, limit=3)

    if not news_items:
        return ""

    context_parts = [f"Recent news about '{topic}':"]
    for item in news_items:
        context_parts.append(f"- {item.title}")
        if item.content:
            context_parts.append(f"  {item.content[:150]}...")

    return "\n".join(context_parts)
