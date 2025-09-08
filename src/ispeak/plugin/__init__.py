from collections.abc import Callable
from typing import Any

from .base import ISpeakPlugin, PluginConfig
from .loader import PluginLoader


class PluginRegistry:
    """Central registry for managing and executing text processing plugins"""

    def __init__(self) -> None:
        self.loader = PluginLoader()
        self.plugins: list[tuple[PluginConfig, ISpeakPlugin | Callable]] = []

    def configure(self, plugin_configs: dict[str, dict[str, Any]]) -> None:
        """
        Configure registry with plugin configurations

        Args:
            plugin_configs: Dictionary mapping plugin names to their configurations
        """
        self.plugins.clear()
        loaded_plugins = []

        for name, config in plugin_configs.items():
            plugin_config = PluginConfig(name, config)

            if not plugin_config.is_enabled:
                continue

            try:
                plugin = self.loader.load_plugin(name, config)
                loaded_plugins.append((plugin_config, plugin))
            except Exception as e:
                print(f"Warning: Failed to load plugin '{name}': {e}")
                continue

        # sort plugins by order
        loaded_plugins.sort(key=lambda x: x[0].order)
        self.plugins = loaded_plugins

    def process_text(self, text: str) -> str:
        """
        Process text through all enabled plugins in order

        Args:
            text: Input text to process

        Returns:
            Text after processing through all plugins
        """
        if not text:
            return text

        result = text

        for plugin_config, plugin in self.plugins:
            try:
                if isinstance(plugin, ISpeakPlugin):
                    result = plugin.process(result)
                elif callable(plugin):
                    # handle function-based plugins
                    settings = plugin_config.settings
                    if settings:
                        result = plugin(result, settings)
                    else:
                        result = plugin(result)
            except Exception as e:
                print(f"Warning: Plugin '{plugin_config.name}' failed: {e}")
                continue

        return result

    def get_plugin_count(self) -> int:
        """Get number of active plugins"""
        return len(self.plugins)

    def get_plugin_names(self) -> list[str]:
        """Get list of active plugin names in processing order"""
        return [config.name for config, _ in self.plugins]


# convenience function for external use
def create_plugin_registry(plugin_configs: dict[str, dict[str, Any]]) -> PluginRegistry:
    """
    Create and configure a plugin registry

    Args:
        plugin_configs: Dictionary mapping plugin names to their configurations

    Returns:
        Configured plugin registry
    """
    registry = PluginRegistry()
    registry.configure(plugin_configs)
    return registry
