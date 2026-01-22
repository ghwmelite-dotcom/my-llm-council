"""Plugin system for extending council capabilities."""

from .registry import PluginRegistry, get_plugin_registry
from .base import Plugin, PluginConfig
from .hooks import PluginHook

__all__ = [
    'PluginRegistry',
    'get_plugin_registry',
    'Plugin',
    'PluginConfig',
    'PluginHook',
]
