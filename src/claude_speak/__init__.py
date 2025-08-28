"""Claude Speak - Speech-to-text for Claude Code.

A lightweight, low-latency speech-to-text library that provides seamless
voice input integration with Claude Code.
"""

from .core import VoiceInput, TextProcessor
from .config import AppConfig, ConfigManager, RealtimeSTTConfig, ClaudeSpeakConfig
from .recorder import AudioRecorder, RealtimeSTTRecorder, MockRecorder

__version__ = "0.1.0"
__all__ = [
    "VoiceInput",
    "TextProcessor",
    "AppConfig",
    "ConfigManager", 
    "RealtimeSTTConfig",
    "ClaudeSpeakConfig",
    "AudioRecorder",
    "RealtimeSTTRecorder",
    "MockRecorder",
]
