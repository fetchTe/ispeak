# ispeak - a keyboard-centric CLI speech-to-text tool that works wherever you can type

from importlib.metadata import version

from .config import AppConfig, CodeSpeakConfig, ConfigManager, ModelSTTConfig
from .core import TextProcessor, VoiceInput
from .recorder import AudioRecorder, ModelSTTRecorder

try:
    __version__ = version("ispeak")
except Exception:
    __version__ = "unknown"

__all__ = [
    "AppConfig",
    "AudioRecorder",
    "CodeSpeakConfig",
    "ConfigManager",
    "ModelSTTConfig",
    "ModelSTTRecorder",
    "TextProcessor",
    "VoiceInput",
]
