from abc import ABC, abstractmethod
from typing import Any


class ISpeakPlugin(ABC):
    """Abstract base class for text processing plugins"""

    @abstractmethod
    def process(self, text: str) -> str:
        """Process input text and return transformed text"""
        pass

    @abstractmethod
    def configure(self, settings: dict[str, Any]) -> None:
        """Configure plugin with user settings"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name for identification"""
        pass

    @property
    def dependencies(self) -> list[str]:
        """Optional dependencies required by plugin"""
        return []


class PluginConfig:
    """Configuration wrapper for plugin settings"""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.use = config.get("use", True)
        self.enabled = config.get("enabled", True)
        self.order = config.get("order", 999)
        self.src = config.get("src")
        self.function = config.get("function")
        self.settings = config.get("settings", {})

        # handle both 'use' and 'enabled' fields
        if isinstance(self.use, bool):
            self.is_enabled = self.use and self.enabled
        elif isinstance(self.use, (int, float)):
            # treat numeric values as ordering priority
            self.is_enabled = self.use > 0 and self.enabled
            if self.order == 999:  # use the numeric value as order if not explicitly set
                self.order = int(self.use)
        else:
            self.is_enabled = bool(self.use) and self.enabled
