#!/usr/bin/env python3

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Any, Dict


@dataclass
class RealtimeSTTConfig:
    """Configuration for RealtimeSTT settings."""
    model: str = "base"
    language: str = "en"
    post_speech_silence_duration: float = 0.7
    silero_use_onnx: bool = True
    print_transcription_time: bool = False
    spinner: bool = False
    start_callback_in_new_thread: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for RealtimeSTT initialization."""
        config = asdict(self)
        # Handle empty language for auto-detection
        if config['language'] == 'auto':
            config['language'] = ''
        return config


@dataclass
class ClaudeSpeakConfig:
    """Configuration for claude-speak specific settings."""
    push_to_talk_key: str = "right_shift"
    recording_indicator: str = ";"
    delete_keywords: List[str] = None
    normalize_output: bool = True
    remove_trailing_period: bool = True

    def __post_init__(self) -> None:
        """Set default delete keywords if not provided."""
        if self.delete_keywords is None:
            self.delete_keywords = ["delete", "delete last", "delete last input"]


@dataclass
class AppConfig:
    """Main application configuration."""
    realtime_stt: RealtimeSTTConfig
    claude_speak: ClaudeSpeakConfig

    @classmethod
    def default(cls) -> "AppConfig":
        """Create default configuration."""
        return cls(
            realtime_stt=RealtimeSTTConfig(),
            claude_speak=ClaudeSpeakConfig()
        )


class ConfigManager:
    """Manages loading, saving, and validation of configuration."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. Defaults to ~/.claude/claude_speak.json
        """
        if config_path is None:
            config_path = Path.home() / ".claude" / "claude_speak.json"
        self.config_path = config_path

    def load_config(self) -> AppConfig:
        """Load configuration from file or create default.
        
        Returns:
            Loaded or default configuration.
        """
        if not self.config_path.exists():
            return AppConfig.default()

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            # Parse RealtimeSTT config
            realtime_stt_data = data.get("realtime_stt", {})
            realtime_stt = RealtimeSTTConfig(**realtime_stt_data)
            
            # Parse ClaudeSpeak config
            claude_speak_data = data.get("claude_speak", {})
            claude_speak = ClaudeSpeakConfig(**claude_speak_data)
            
            return AppConfig(
                realtime_stt=realtime_stt,
                claude_speak=claude_speak
            )
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # On any configuration error, return default and warn
            print(f"Warning: Failed to load configuration from {self.config_path}: {e}")
            print("Using default configuration")
            return AppConfig.default()

    def save_config(self, config: AppConfig) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save.
        """
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary format
        data = {
            "realtime_stt": asdict(config.realtime_stt),
            "claude_speak": asdict(config.claude_speak)
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def validate_config(self, config: AppConfig) -> List[str]:
        """Validate configuration and return list of errors.
        
        Args:
            config: Configuration to validate.
            
        Returns:
            List of validation error messages.
        """
        errors = []
        
        # Validate RealtimeSTT config
        valid_models = [
            'tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en',
            'medium', 'medium.en', 'large-v1', 'large-v2'
        ]
        if (config.realtime_stt.model not in valid_models and 
            not Path(config.realtime_stt.model).exists()):
            errors.append(f"Invalid model: {config.realtime_stt.model}")
        
        if config.realtime_stt.post_speech_silence_duration < 0:
            errors.append("post_speech_silence_duration must be non-negative")
        
        # Validate ClaudeSpeak config
        if not config.claude_speak.push_to_talk_key:
            errors.append("push_to_talk_key cannot be empty")
        
        if not config.claude_speak.recording_indicator:
            errors.append("recording_indicator cannot be empty")
        
        return errors

    def create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist."""
        if not self.config_path.exists():
            default_config = AppConfig.default()
            self.save_config(default_config)