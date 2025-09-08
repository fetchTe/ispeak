import importlib.util
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .base import ISpeakPlugin


class PluginLoader:
    """Dynamic plugin loader supporting builtin, file, and package sources"""

    def __init__(self) -> None:
        self._builtin_cache: dict[str, Any] = {}

    def load_plugin(self, key: str, config: dict[str, Any]) -> ISpeakPlugin | Callable:
        """
        Load plugin from various sources

        Args:
            key: Plugin identifier
            config: Plugin configuration dict
        Returns:
            Plugin instance or callable function
        """
        src = config.get("src")

        if not src:
            # try to load as builtin plugin
            try:
                return self._load_builtin(key, config)
            except ImportError as e:
                raise ValueError(f"Unknown builtin plugin: {key}") from e

        if src.startswith("file://"):
            return self._load_from_file(src, config)
        elif src.startswith("package://"):
            return self._load_from_package(src, config)
        elif src.startswith("builtin://"):
            plugin_name = src.replace("builtin://", "")
            return self._load_builtin(plugin_name, config)
        else:
            raise ValueError(f"Unknown plugin source: {src}")

    def _load_builtin(self, name: str, config: dict[str, Any]) -> ISpeakPlugin | Callable:
        """Load builtin plugin from ispeak.plugin.builtin package"""
        if name in self._builtin_cache:
            plugin_class = self._builtin_cache[name]
        else:
            try:
                module = importlib.import_module(f"ispeak.plugin.builtin.{name}")

                # look for plugin class or function
                function_name = config.get("function")
                if function_name:
                    if hasattr(module, function_name):
                        plugin_func = getattr(module, function_name)
                        if callable(plugin_func):
                            return plugin_func
                        else:
                            raise ValueError(f"'{function_name}' is not callable in {name}")
                    else:
                        raise ValueError(f"Function '{function_name}' not found in {name}")

                # look for plugin class (default behavior)
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr) and issubclass(attr, ISpeakPlugin) and attr is not ISpeakPlugin:
                        plugin_class = attr
                        break

                if plugin_class is None:
                    # look for a function with the same name as the module
                    if hasattr(module, name):
                        plugin_func = getattr(module, name)
                        if callable(plugin_func):
                            return plugin_func
                    raise ValueError(f"No plugin class or function found in builtin.{name}")

                self._builtin_cache[name] = plugin_class
            except ImportError as e:
                raise ImportError(f"Builtin plugin '{name}' not found") from e

        # create instance and configure
        plugin = plugin_class()
        plugin.configure(config.get("settings", {}))
        return plugin

    def _load_from_file(self, src: str, config: dict[str, Any]) -> Callable:
        """Load plugin from file path"""
        file_path = src.replace("file://", "")
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {file_path}")

        # load module from file
        spec = importlib.util.spec_from_file_location("external_plugin", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load plugin from {file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # get function name or use default
        function_name = config.get("function", path.stem)

        if not hasattr(module, function_name):
            raise ValueError(f"Function '{function_name}' not found in {file_path}")

        plugin_func = getattr(module, function_name)
        if not callable(plugin_func):
            raise ValueError(f"'{function_name}' is not callable in {file_path}")

        return plugin_func

    def _load_from_package(self, src: str, config: dict[str, Any]) -> ISpeakPlugin | Callable:
        """Load plugin from installed package"""
        package_path = src.replace("package://", "")

        try:
            module = importlib.import_module(package_path)
        except ImportError as e:
            raise ImportError(f"Package '{package_path}' not found") from e

        # get function name or look for plugin class
        function_name = config.get("function")
        if function_name:
            if hasattr(module, function_name):
                plugin_func = getattr(module, function_name)
                if callable(plugin_func):
                    return plugin_func
                else:
                    raise ValueError(f"'{function_name}' is not callable in {package_path}")
            else:
                raise ValueError(f"Function '{function_name}' not found in {package_path}")

        # look for plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if inspect.isclass(attr) and issubclass(attr, ISpeakPlugin) and attr is not ISpeakPlugin:
                plugin = attr()
                plugin.configure(config.get("settings", {}))
                return plugin

        raise ValueError(f"No plugin class or function found in package {package_path}")
