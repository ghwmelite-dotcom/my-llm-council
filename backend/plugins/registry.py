"""Plugin registry and management."""

import json
import os
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from .base import Plugin, PluginConfig
from ..config import data_path


class PluginRegistry:
    """Manages plugin registration and execution."""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = data_path("plugins", "config.json")
        self.storage_path = storage_path
        self.plugins: Dict[str, Plugin] = {}
        self._ensure_storage_dir()
        self._load_config()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """Load plugin configurations from storage."""
        # Configs are loaded when plugins are registered
        pass

    def _save_config(self):
        """Save plugin configurations to storage."""
        self._ensure_storage_dir()
        config_data = {
            "plugins": {
                name: {
                    "enabled": plugin.enabled,
                    "priority": plugin.config.priority,
                    "settings": plugin.config.settings
                }
                for name, plugin in self.plugins.items()
            }
        }
        with open(self.storage_path, 'w') as f:
            json.dump(config_data, f, indent=2)

    def _get_saved_config(self, plugin_name: str) -> Optional[Dict]:
        """Get saved configuration for a plugin."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return data.get("plugins", {}).get(plugin_name)
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def register(self, plugin_class: Type[Plugin], config: PluginConfig = None) -> Plugin:
        """
        Register a plugin.

        Args:
            plugin_class: The plugin class to register
            config: Optional configuration

        Returns:
            The registered plugin instance
        """
        # Load saved config if available
        saved_config = self._get_saved_config(plugin_class.name)
        if saved_config and config is None:
            config = PluginConfig(
                enabled=saved_config.get("enabled", True),
                priority=saved_config.get("priority", 100),
                settings=saved_config.get("settings", {})
            )

        plugin = plugin_class(config)
        self.plugins[plugin.name] = plugin
        self._save_config()
        return plugin

    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of the plugin to unregister

        Returns:
            True if unregistered, False if not found
        """
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            self._save_config()
            return True
        return False

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins."""
        return [plugin.get_info() for plugin in self.plugins.values()]

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.enable()
            self._save_config()
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.disable()
            self._save_config()
            return True
        return False

    def update_settings(self, plugin_name: str, settings: Dict[str, Any]) -> bool:
        """Update plugin settings."""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.config.settings.update(settings)
            self._save_config()
            return True
        return False

    def get_enabled_plugins(self, hook_name: str = None) -> List[Plugin]:
        """
        Get all enabled plugins, optionally filtered by hook.

        Args:
            hook_name: Optional hook name to filter by

        Returns:
            List of enabled plugins sorted by priority
        """
        plugins = [p for p in self.plugins.values() if p.enabled]

        if hook_name:
            plugins = [p for p in plugins if hook_name in p.hooks]

        return sorted(plugins, key=lambda p: p.config.priority)

    async def execute_hook(
        self,
        hook_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a hook on all enabled plugins.

        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments for the hook
            **kwargs: Keyword arguments for the hook

        Returns:
            The modified result after all plugins have processed it
        """
        plugins = self.get_enabled_plugins(hook_name)
        result = args[0] if args else kwargs.get('query') or kwargs.get('results')

        for plugin in plugins:
            hook_method = getattr(plugin, hook_name, None)
            if hook_method and callable(hook_method):
                try:
                    if hook_name == 'on_query_received':
                        result = await hook_method(result, kwargs.get('context', {}))
                    elif hook_name == 'on_synthesis_complete':
                        result = await hook_method(
                            kwargs.get('query', ''),
                            result,
                            kwargs.get('context', {})
                        )
                    else:
                        result = await hook_method(
                            kwargs.get('query', ''),
                            result,
                            kwargs.get('context', {})
                        )
                except Exception as e:
                    print(f"Plugin {plugin.name} error on {hook_name}: {e}")

        return result


# Singleton instance
_plugin_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the singleton plugin registry instance."""
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
    return _plugin_registry
