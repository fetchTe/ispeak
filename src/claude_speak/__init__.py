"""
Claude Speak - Speech-to-text for Claude Code

A lightweight, low-latency speech-to-text library that provides seamless
voice input integration with Claude Code.
"""

from .config import AppConfig, ClaudeSpeakConfig, ConfigManager, RealtimeSTTConfig
from .core import TextProcessor, VoiceInput
from .recorder import AudioRecorder, RealtimeSTTRecorder

__version__ = "0.1.0"
__all__ = [
    "AppConfig",
    "AudioRecorder",
    "ClaudeSpeakConfig",
    "ConfigManager",
    "RealtimeSTTConfig",
    "RealtimeSTTRecorder",
    "TextProcessor",
    "VoiceInput",
]
