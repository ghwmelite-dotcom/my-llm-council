"""Real-time world feeds module for context-aware responses."""

from .manager import FeedManager, get_feed_manager
from .aggregator import aggregate_feeds, get_current_context
from .injector import inject_world_context, should_include_world_context

__all__ = [
    'FeedManager',
    'get_feed_manager',
    'aggregate_feeds',
    'get_current_context',
    'inject_world_context',
    'should_include_world_context',
]
