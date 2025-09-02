# ispeak - a keyboard-centric CLI speech-to-text tool that works wherever you can type

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
