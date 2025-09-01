"""
code_speak - A speech-to-text library that provides seamless voice input integration
with AI cli's: claude code, codex, aider, and the like
"""

from .config import AppConfig, CodeSpeakConfig, ConfigManager, RealtimeSTTConfig
from .core import TextProcessor, VoiceInput
from .recorder import AudioRecorder, RealtimeSTTRecorder
from .replace import TextReplacer

__version__ = "0.1.0"
__all__ = [
    "AppConfig",
    "AudioRecorder",
    "CodeSpeakConfig",
    "ConfigManager",
    "RealtimeSTTConfig",
    "RealtimeSTTRecorder",
    "TextProcessor",
    "TextReplacer",
    "VoiceInput",
]
