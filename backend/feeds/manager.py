"""Feed manager for handling real-time data sources."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import httpx
from ..config import FEEDS_CONFIG


@dataclass
class FeedItem:
    """Represents a single feed item."""
    id: str
    source: str
    title: str
    content: str
    url: Optional[str]
    published_at: str
    tags: List[str]


@dataclass
class CachedFeed:
    """Represents a cached feed with expiration."""
    source: str
    items: List[FeedItem]
    fetched_at: datetime
    expires_at: datetime


class FeedManager:
    """Manages real-time data feeds."""

    def __init__(self):
        self.cache: Dict[str, CachedFeed] = {}
        self.cache_duration = timedelta(
            minutes=FEEDS_CONFIG.get('cache_duration_minutes', 15)
        )
        self.news_api_key = FEEDS_CONFIG.get('news_api_key')
        self.weather_api_key = FEEDS_CONFIG.get('weather_api_key')

    def is_cache_valid(self, source: str) -> bool:
        """Check if cached feed is still valid."""
        if source not in self.cache:
            return False
        return datetime.utcnow() < self.cache[source].expires_at

    def get_cached(self, source: str) -> Optional[List[FeedItem]]:
        """Get cached feed items if valid."""
        if self.is_cache_valid(source):
            return self.cache[source].items
        return None

    def set_cached(self, source: str, items: List[FeedItem]):
        """Cache feed items."""
        now = datetime.utcnow()
        self.cache[source] = CachedFeed(
            source=source,
            items=items,
            fetched_at=now,
            expires_at=now + self.cache_duration
        )

    async def fetch_news(
        self,
        query: str = None,
        category: str = 'general',
        limit: int = 5
    ) -> List[FeedItem]:
        """
        Fetch news headlines from NewsAPI.

        Args:
            query: Optional search query
            category: News category
            limit: Maximum items to return

        Returns:
            List of FeedItem objects
        """
        if not self.news_api_key:
            return []

        cache_key = f"news_{category}_{query or 'top'}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached[:limit]

        try:
            async with httpx.AsyncClient() as client:
                if query:
                    url = "https://newsapi.org/v2/everything"
                    params = {
                        'q': query,
                        'apiKey': self.news_api_key,
                        'pageSize': limit,
                        'sortBy': 'publishedAt'
                    }
                else:
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {
                        'category': category,
                        'apiKey': self.news_api_key,
                        'pageSize': limit,
                        'country': 'us'
                    }

                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                items = []
                for article in data.get('articles', []):
                    items.append(FeedItem(
                        id=f"news_{hash(article.get('url', ''))}",
                        source='newsapi',
                        title=article.get('title', ''),
                        content=article.get('description', '') or article.get('content', ''),
                        url=article.get('url'),
                        published_at=article.get('publishedAt', ''),
                        tags=[category]
                    ))

                self.set_cached(cache_key, items)
                return items[:limit]

        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    async def fetch_weather(
        self,
        location: str = 'New York',
        units: str = 'metric'
    ) -> Optional[FeedItem]:
        """
        Fetch current weather from OpenWeatherMap.

        Args:
            location: City name
            units: 'metric' or 'imperial'

        Returns:
            FeedItem with weather data or None
        """
        if not self.weather_api_key:
            return None

        cache_key = f"weather_{location}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached[0] if cached else None

        try:
            async with httpx.AsyncClient() as client:
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    'q': location,
                    'appid': self.weather_api_key,
                    'units': units
                }

                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                weather = data.get('weather', [{}])[0]
                main = data.get('main', {})

                content = (
                    f"Current weather in {location}: {weather.get('description', 'Unknown')}. "
                    f"Temperature: {main.get('temp', 'N/A')}°{'C' if units == 'metric' else 'F'}. "
                    f"Humidity: {main.get('humidity', 'N/A')}%. "
                    f"Feels like: {main.get('feels_like', 'N/A')}°."
                )

                item = FeedItem(
                    id=f"weather_{location}",
                    source='openweathermap',
                    title=f"Weather in {location}",
                    content=content,
                    url=None,
                    published_at=datetime.utcnow().isoformat(),
                    tags=['weather', location.lower()]
                )

                self.set_cached(cache_key, [item])
                return item

        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None

    async def fetch_wikipedia_current_events(self) -> List[FeedItem]:
        """
        Fetch current events from Wikipedia.

        Returns:
            List of FeedItem objects
        """
        cache_key = "wikipedia_current"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient() as client:
                # Wikipedia current events portal
                today = datetime.utcnow()
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/Portal:Current_events"

                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                item = FeedItem(
                    id="wikipedia_current_events",
                    source='wikipedia',
                    title="Current Events",
                    content=data.get('extract', ''),
                    url=data.get('content_urls', {}).get('desktop', {}).get('page'),
                    published_at=today.isoformat(),
                    tags=['current_events', 'wikipedia']
                )

                self.set_cached(cache_key, [item])
                return [item]

        except Exception as e:
            print(f"Error fetching Wikipedia: {e}")
            return []

    async def fetch_all_feeds(
        self,
        include_news: bool = True,
        include_weather: bool = True,
        include_wikipedia: bool = True,
        news_query: str = None
    ) -> Dict[str, List[FeedItem]]:
        """
        Fetch from all enabled feed sources.

        Args:
            include_news: Whether to fetch news
            include_weather: Whether to fetch weather
            include_wikipedia: Whether to fetch Wikipedia
            news_query: Optional news search query

        Returns:
            Dict mapping source names to feed items
        """
        feeds = {}
        tasks = []

        if include_news and self.news_api_key:
            tasks.append(('news', self.fetch_news(query=news_query)))

        if include_weather and self.weather_api_key:
            tasks.append(('weather', self.fetch_weather()))

        if include_wikipedia:
            tasks.append(('wikipedia', self.fetch_wikipedia_current_events()))

        # Execute all fetches concurrently
        for name, task in tasks:
            try:
                result = await task
                if result:
                    feeds[name] = result if isinstance(result, list) else [result]
            except Exception as e:
                print(f"Error fetching {name}: {e}")

        return feeds

    def clear_cache(self, source: str = None):
        """Clear feed cache."""
        if source:
            self.cache.pop(source, None)
        else:
            self.cache.clear()


# Singleton instance
_feed_manager: Optional[FeedManager] = None


def get_feed_manager() -> FeedManager:
    """Get the singleton feed manager instance."""
    global _feed_manager
    if _feed_manager is None:
        _feed_manager = FeedManager()
    return _feed_manager
