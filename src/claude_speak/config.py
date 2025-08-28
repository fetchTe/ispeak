#!/usr/bin/env python3

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

VALID_MODELS = [
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v1",
    "large-v2",
]


@dataclass
class RealtimeSTTConfig:
    """Configuration for RealtimeSTT settings
    NOTE: intentionally excluded wake word activation in favor of a hotkey-driven
    workflow but it's do-able, the only real hitch is implementing a way to steal/change
    the focus from the active window to the claude code cli/terminal - in x11,
    this is pretty trivial with xdotool, but in wayland it's a bit more complicated
    """

    # Model and computation settings
    model: str = "base"
    download_root: str | None = None
    language: str = "en"
    compute_type: str = "default"
    device: str = "cuda"
    gpu_device_index: int = 0
    batch_size: int = 16

    # Audio input settings
    input_device_index: int = 0
    use_microphone: bool = True
    sample_rate: int = 16000
    buffer_size: int = 512

    # Text processing settings
    ensure_sentence_starting_uppercase: bool = True
    ensure_sentence_ends_with_period: bool = True
    normalize_audio: bool = False

    # Realtime transcription settings
    enable_realtime_transcription: bool = False
    use_main_model_for_realtime: bool = False
    realtime_model_type: str = "tiny"
    realtime_processing_pause: float = 0.1
    init_realtime_after_seconds: float = 0.2
    realtime_batch_size: int = 16

    # Voice Activity Detection (VAD) settings
    silero_sensitivity: float = 0.5
    silero_use_onnx: bool = True
    silero_deactivity_detection: bool = False
    webrtc_sensitivity: int = 3
    faster_whisper_vad_filter: bool = True

    # Recording timing settings
    post_speech_silence_duration: float = 0.7
    min_gap_between_recordings: float = 1.0
    min_length_of_recording: float = 1.0
    pre_recording_buffer_duration: float = 0.2
    early_transcription_on_silence: int = 0

    # Transcription settings
    beam_size: int = 5
    beam_size_realtime: int = 3
    initial_prompt: str | None = None
    initial_prompt_realtime: str | None = None
    suppress_tokens: list[int] | None = None

    # Performance and debug settings
    print_transcription_time: bool = False
    spinner: bool = False
    level: int = 30  # logging.WARNING
    allowed_latency_limit: int = 100
    handle_buffer_overflow: bool = True
    no_log_file: bool = False
    use_extended_logging: bool = False
    debug_mode: bool = False
    start_callback_in_new_thread: bool = False

    def __post_init__(self) -> None:
        """Set default values for complex fields."""
        if self.suppress_tokens is None:
            self.suppress_tokens = [-1]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for RealtimeSTT initialization."""
        config = asdict(self)
        # Handle empty language for auto-detection
        if config["language"] == "auto":
            config["language"] = ""
        return config


@dataclass
class ClaudeSpeakConfig:
    """Configuration for claude-speak specific settings."""

    push_to_talk_key: str = "right_shift"
    recording_indicator: str = ";"
    delete_keywords: list[str] = None
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
        return cls(realtime_stt=RealtimeSTTConfig(), claude_speak=ClaudeSpeakConfig())


class ConfigManager:
    """Manages loading, saving, and validation of configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. Defaults to CLAUDE_SPEAK_CONFIG env var,
                        then ~/.claude/claude_speak.json, then ./claude_speak.json
        """
        if config_path is None:
            # Check environment variable first
            env_config_path = os.getenv("CLAUDE_SPEAK_CONFIG")
            if env_config_path:
                config_path = Path(env_config_path)
            else:
                # Check default .claude directory
                claude_config_path = Path.home() / ".claude" / "claude_speak.json"
                if claude_config_path.exists():
                    config_path = claude_config_path
                else:
                    # Fallback to current directory
                    config_path = Path("./claude_speak.json").resolve()
        self.config_path = config_path

    def load_config(self) -> AppConfig:
        """Load configuration from file or create default.

        Returns:
            Loaded or default configuration.
        """
        if not self.config_path.exists():
            return AppConfig.default()

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            # Parse RealtimeSTT config
            realtime_stt_data = data.get("realtime_stt", {})
            realtime_stt = RealtimeSTTConfig(**realtime_stt_data)

            # Parse ClaudeSpeak config
            claude_speak_data = data.get("claude_speak", {})
            claude_speak = ClaudeSpeakConfig(**claude_speak_data)

            return AppConfig(realtime_stt=realtime_stt, claude_speak=claude_speak)
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
            "claude_speak": asdict(config.claude_speak),
        }

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def validate_config(self, config: AppConfig) -> list[str]:
        """Validate configuration and return list of errors.

        Args:
            config: Configuration to validate.

        Returns:
            List of validation error messages.
        """
        errors = []

        # Validate RealtimeSTT config
        if (
            config.realtime_stt.model not in VALID_MODELS
            and not Path(config.realtime_stt.model).exists()
        ):
            errors.append(f"Invalid model: {config.realtime_stt.model}")

        if (
            config.realtime_stt.realtime_model_type not in VALID_MODELS
            and not Path(config.realtime_stt.realtime_model_type).exists()
        ):
            errors.append(f"Invalid realtime_model_type: {config.realtime_stt.realtime_model_type}")

        # Validate timing settings
        if config.realtime_stt.post_speech_silence_duration < 0:
            errors.append("post_speech_silence_duration must be non-negative")

        if config.realtime_stt.min_gap_between_recordings < 0:
            errors.append("min_gap_between_recordings must be non-negative")

        if config.realtime_stt.min_length_of_recording < 0:
            errors.append("min_length_of_recording must be non-negative")

        if config.realtime_stt.pre_recording_buffer_duration < 0:
            errors.append("pre_recording_buffer_duration must be non-negative")

        if config.realtime_stt.realtime_processing_pause < 0:
            errors.append("realtime_processing_pause must be non-negative")

        if config.realtime_stt.init_realtime_after_seconds < 0:
            errors.append("init_realtime_after_seconds must be non-negative")

        # Validate sensitivity settings (0-1 range)
        if not 0 <= config.realtime_stt.silero_sensitivity <= 1:
            errors.append("silero_sensitivity must be between 0 and 1")

        # Validate WebRTC sensitivity (0-3 range)
        if not 0 <= config.realtime_stt.webrtc_sensitivity <= 3:
            errors.append("webrtc_sensitivity must be between 0 and 3")

        # Validate device settings
        if config.realtime_stt.device not in ["cuda", "cpu"]:
            errors.append("device must be either 'cuda' or 'cpu'")

        # Validate batch sizes
        if config.realtime_stt.batch_size <= 0:
            errors.append("batch_size must be positive")

        if config.realtime_stt.realtime_batch_size <= 0:
            errors.append("realtime_batch_size must be positive")

        if config.realtime_stt.beam_size <= 0:
            errors.append("beam_size must be positive")

        if config.realtime_stt.beam_size_realtime <= 0:
            errors.append("beam_size_realtime must be positive")

        # Validate audio settings
        if config.realtime_stt.input_device_index < 0:
            errors.append("input_device_index must be non-negative")

        if config.realtime_stt.gpu_device_index < 0:
            errors.append("gpu_device_index must be non-negative")

        if config.realtime_stt.sample_rate <= 0:
            errors.append("sample_rate must be positive")

        if config.realtime_stt.buffer_size <= 0:
            errors.append("buffer_size must be positive")

        if config.realtime_stt.allowed_latency_limit <= 0:
            errors.append("allowed_latency_limit must be positive")

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
