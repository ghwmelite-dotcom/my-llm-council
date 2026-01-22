"""Base plugin classes and interfaces."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PluginConfig:
    """Configuration for a plugin."""
    enabled: bool = True
    priority: int = 100  # Lower = higher priority
    settings: Dict[str, Any] = field(default_factory=dict)


class Plugin(ABC):
    """Base class for all plugins."""

    # Plugin metadata - override in subclasses
    name: str = "BasePlugin"
    version: str = "1.0.0"
    description: str = "Base plugin class"
    author: str = "Unknown"

    # Hook points this plugin uses
    hooks: List[str] = []

    def __init__(self, config: PluginConfig = None):
        self.config = config or PluginConfig()
        self._enabled = self.config.enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self):
        """Enable the plugin."""
        self._enabled = True

    def disable(self):
        """Disable the plugin."""
        self._enabled = False

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
            "hooks": self.hooks,
            "priority": self.config.priority,
        }

    # Hook methods - override these in subclasses

    async def on_query_received(self, query: str, context: Dict[str, Any]) -> str:
        """
        Called when a user query is received (pre-processing).

        Args:
            query: The user's query
            context: Additional context (conversation_id, etc.)

        Returns:
            Modified query string
        """
        return query

    async def on_stage1_complete(
        self,
        query: str,
        results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Called after Stage 1 responses are collected.

        Args:
            query: The user's query
            results: Stage 1 results from all models
            context: Additional context

        Returns:
            Modified results list
        """
        return results

    async def on_stage2_complete(
        self,
        query: str,
        rankings: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Called after Stage 2 rankings are collected.

        Args:
            query: The user's query
            rankings: Stage 2 rankings from all models
            context: Additional context

        Returns:
            Modified rankings list
        """
        return rankings

    async def on_synthesis_complete(
        self,
        query: str,
        synthesis: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Called after Stage 3 synthesis is complete (post-processing).

        Args:
            query: The user's query
            synthesis: The final synthesized response
            context: Additional context

        Returns:
            Modified synthesis string
        """
        return synthesis

    async def on_response_complete(
        self,
        query: str,
        full_response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called after the complete response is ready.

        Args:
            query: The user's query
            full_response: Complete response with all stages
            context: Additional context

        Returns:
            Modified full response
        """
        return full_response
