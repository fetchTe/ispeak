import json
import os
import platform
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from pynput.keyboard import Key, KeyCode

from .core import key_to_str

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
    """
    Configuration for RealtimeSTT settings

    - NOTE: None -> RealtimeSTT default
    - NOTE: intentionally excluded wake word activation in favor of a hotkey-driven
            workflow but it's do-able, the only real hitch is implementing a way
            to steal/change the focus from the active window to the cli/terminal -
            in x11 it's trivial with xdotool, but in wayland/ios it's best of luck!
    """
    # model and computation settings
    model: str | None = None
    download_root: str | None = None
    language: str | None = None
    compute_type: str | None = None
    device: str | None = None
    gpu_device_index: int | None = None
    batch_size: int | None = None

    # audio input settings
    input_device_index: int | None = None
    use_microphone: bool | None = None
    sample_rate: int | None = None
    buffer_size: int | None = None

    # text processing settings
    ensure_sentence_starting_uppercase: bool | None = None
    ensure_sentence_ends_with_period: bool | None = None
    normalize_audio: bool | None = None

    # realtime transcription settings
    enable_realtime_transcription: bool | None = None
    use_main_model_for_realtime: bool | None = None
    realtime_model_type: str | None = None
    realtime_processing_pause: float | None = None
    init_realtime_after_seconds: float | None = None
    realtime_batch_size: int | None = None

    # voice Activity Detection (VAD) settings
    silero_sensitivity: float | None = None
    silero_use_onnx: bool | None = None
    silero_deactivity_detection: bool | None = None
    webrtc_sensitivity: int | None = None
    faster_whisper_vad_filter: bool | None = None

    # recording timing settings
    post_speech_silence_duration: float | None = None
    min_gap_between_recordings: float | None = None
    min_length_of_recording: float | None = None
    pre_recording_buffer_duration: float | None = None
    early_transcription_on_silence: int | None = None

    # transcription settings
    beam_size: int | None = None
    beam_size_realtime: int | None = None
    initial_prompt: str | None = None
    initial_prompt_realtime: str | None = None
    suppress_tokens: list[int] | None = None

    # performance and debug settings
    print_transcription_time: bool | None = None
    spinner: bool | None = None
    level: int | None = None
    allowed_latency_limit: int | None = None
    handle_buffer_overflow: bool | None = None
    no_log_file: bool | None = None
    use_extended_logging: bool | None = None
    debug_mode: bool | None = None
    start_callback_in_new_thread: bool | None = None

    # store extra configuration keys not defined in dataclass
    _extra_config: dict[str, Any] = None  # type: ignore

    def __post_init__(self) -> None:
        # set default values for complex fields
        if self.suppress_tokens is None:
            self.suppress_tokens = [-1]
        if self._extra_config is None:
            self._extra_config = {}

    def to_dict(self) -> dict[str, Any]:
        # convert to dictionary for RealtimeSTT initialization
        config = asdict(self)
        # remove our internal _extra_config field from the output
        config.pop("_extra_config", None)

        # remove None values to let RealtimeSTT use its defaults
        config = {k: v for k, v in config.items() if v is not None}

        # handle empty language for auto-detection
        if config.get("language") == "auto":
            config["language"] = ""

        # add any extra configuration keys
        config.update(self._extra_config)

        return config


@dataclass
class CodeSpeakConfig:
    """Configuration for code-speak specific settings"""

    # default executable for AI code generation
    binary: str = "claude"
    # key to initilize rec session
    push_to_talk_key: str = "right_shift"
    # execution delay applied after push_to_talk_key (via time.sleep) - helps pervent mistypes
    push_to_talk_key_delay: float | int = 0.2
    # key to "escape" current rec session, ends without outputing transcription
    escape_key: str | Key | KeyCode | None = Key.esc
    # char/word outputed when recording starts
    recording_indicator: str = ";"
    # list of words/phrases, when detected will delete previous output
    delete_keywords: list[str] | bool | None = True
    # use a list of backspace's with pyautogui.press -> faster, but not as accurate
    fast_delete: bool = True
    # removes extra white space (an extra space is always added to end)
    strip: bool = True
    # pyautogui - interval in between each press (in seconds) - if experiancing
    # typeing/output issues like partial outputs bump this value up
    pyautogui_interval: float | int = 0.0

    def __post_init__(self) -> None:
        # set default delete keywords if not provided
        if not self.delete_keywords:
            self.delete_keywords = []
        if self.delete_keywords is True:
            self.delete_keywords = ["delete last", "undo last"]
        # keys setup
        self.escape_key = key_to_str(self.escape_key)
        self.push_to_talk_key = key_to_str(self.push_to_talk_key)


@dataclass
class AppConfig:
    """Main application configuration"""

    realtime_stt: RealtimeSTTConfig
    code_speak: CodeSpeakConfig

    @classmethod
    def default(cls) -> "AppConfig":
        """Create default configuration"""
        return cls(realtime_stt=RealtimeSTTConfig(), code_speak=CodeSpeakConfig())


class ConfigManager:
    """Manages loading, saving, and validation of configuration"""

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize configuration manager

        Args:
            config_path:
              1. CODE_SPEAK_CONFIG env var
              2. env specific config (<config>/code_speak/code_speak.json)
                 - macOS: ~/Library/Preferences
                 - Windows: %APPDATA% (or ~/AppData/Roaming as fallback)
                 - Linux: $XDG_CONFIG_HOME (or ~/.config as fallback per XDG Base Directory spec)
              3. ./code_speak.json
        """
        if config_path is None:
            # check environment variable first
            env_config_path = os.getenv("CODE_SPEAK_CONFIG")
            if env_config_path:
                config_path = Path(env_config_path)
            else:
                # check default config directory using cross-platform function
                default_config_path = self.get_config_dir() / "code_speak" / "code_speak.json"
                if default_config_path.exists():
                    config_path = default_config_path
                else:
                    # fallback to current directory
                    config_path = Path("./code_speak.json").resolve()
        self.config_path = config_path

    def get_config_dir(self) -> Path:
        """
        Get the config directory based on the platform

        Returns:
            Path to the platform-appropriate config directory
        """
        system = platform.system().lower()
        if system == "darwin":  # macOS
            return Path.home() / "Library" / "Preferences"
        elif system == "windows":
            # use APPDATA if available, fallback to home/AppData/Roaming
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata)
            return Path.home() / "AppData" / "Roaming"
        else:  # linux and other Unix-like systems
            # follow XDG Base Directory Specification
            xdg_config = os.getenv("XDG_CONFIG_HOME")
            if xdg_config:
                return Path(xdg_config)
            return Path.home() / ".config"

    def load_config(self) -> AppConfig:
        """
        Load configuration from file or create default

        Returns:
            Loaded or default configuration.
        """
        if not self.config_path.exists():
            return AppConfig.default()

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            # parse RealtimeSTT config
            realtime_stt_data = data.get("realtime_stt", {})

            # separate known dataclass fields from extra config
            known_fields = {f.name for f in fields(RealtimeSTTConfig)}
            known_config = {k: v for k, v in realtime_stt_data.items() if k in known_fields}
            extra_config = {k: v for k, v in realtime_stt_data.items() if k not in known_fields}

            realtime_stt = RealtimeSTTConfig(**known_config)
            realtime_stt._extra_config = extra_config

            # parse CodeSpeak config
            code_speak_data = data.get("code_speak", {})
            code_speak = CodeSpeakConfig(**code_speak_data)

            return AppConfig(realtime_stt=realtime_stt, code_speak=code_speak)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # on any configuration error, return default and warn
            print(f"Warning: Failed to load configuration from {self.config_path}: {e}")
            print("Using default configuration")
            return AppConfig.default()

    def save_config(self, config: AppConfig) -> None:
        """
        Save configuration to file

        Args:
            config: Configuration to save
        """
        # ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # convert to dictionary format
        realtime_stt_dict = asdict(config.realtime_stt)
        # remove internal field
        realtime_stt_dict.pop("_extra_config", None)
        # add extra keys
        realtime_stt_dict.update(config.realtime_stt._extra_config)

        data = {
            "realtime_stt": realtime_stt_dict,
            "code_speak": asdict(config.code_speak),
        }

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def validate_config(self, config: AppConfig) -> list[str]:
        """
        Validate configuration and return list of errors

        Args:
            config: Configuration to validate
        Returns:
            List of validation error messages
        """
        errors = []

        # validate code_speak config
        if not config.code_speak.push_to_talk_key:
            errors.append("push_to_talk_key cannot be empty")
        if not config.code_speak.recording_indicator:
            errors.append("recording_indicator cannot be empty")

        # validate RealtimeSTT config
        model = config.realtime_stt.model
        if (model is not None and model not in VALID_MODELS and
            not Path(model).exists()):
            errors.append(f"Invalid model: {model}")
        realtime_model = config.realtime_stt.realtime_model_type
        if (realtime_model is not None and realtime_model not in VALID_MODELS and
            not Path(realtime_model).exists()):
            errors.append(f"Invalid realtime_model_type: {realtime_model}")

        # validate timing settings
        post_speech = config.realtime_stt.post_speech_silence_duration
        if post_speech is not None and post_speech < 0:
            errors.append("post_speech_silence_duration must be non-negative")
        min_gap = config.realtime_stt.min_gap_between_recordings
        if min_gap is not None and min_gap < 0:
            errors.append("min_gap_between_recordings must be non-negative")
        min_length = config.realtime_stt.min_length_of_recording
        if min_length is not None and min_length < 0:
            errors.append("min_length_of_recording must be non-negative")
        pre_buffer = config.realtime_stt.pre_recording_buffer_duration
        if pre_buffer is not None and pre_buffer < 0:
            errors.append("pre_recording_buffer_duration must be non-negative")
        processing_pause = config.realtime_stt.realtime_processing_pause
        if processing_pause is not None and processing_pause < 0:
            errors.append("realtime_processing_pause must be non-negative")
        init_realtime = config.realtime_stt.init_realtime_after_seconds
        if init_realtime is not None and init_realtime < 0:
            errors.append("init_realtime_after_seconds must be non-negative")

        # validate sensitivity settings (0-1 range)
        silero_sens = config.realtime_stt.silero_sensitivity
        if silero_sens is not None and not 0 <= silero_sens <= 1:
            errors.append("silero_sensitivity must be between 0 and 1")

        # validate WebRTC sensitivity (0-3 range)
        webrtc_sens = config.realtime_stt.webrtc_sensitivity
        if webrtc_sens is not None and not 0 <= webrtc_sens <= 3:
            errors.append("webrtc_sensitivity must be between 0 and 3")

        # validate device settings (only if specified)
        device = config.realtime_stt.device
        if device is not None and device not in ["cuda", "cpu"]:
            errors.append("device must be either 'cuda' or 'cpu'")

        # validate batch sizes
        batch_size = config.realtime_stt.batch_size
        if batch_size is not None and batch_size <= 0:
            errors.append("batch_size must be positive")
        realtime_batch = config.realtime_stt.realtime_batch_size
        if realtime_batch is not None and realtime_batch <= 0:
            errors.append("realtime_batch_size must be positive")
        beam_size = config.realtime_stt.beam_size
        if beam_size is not None and beam_size <= 0:
            errors.append("beam_size must be positive")
        beam_realtime = config.realtime_stt.beam_size_realtime
        if beam_realtime is not None and beam_realtime <= 0:
            errors.append("beam_size_realtime must be positive")

        # validate audio settings
        sample_rate = config.realtime_stt.sample_rate
        if sample_rate is not None and sample_rate <= 0:
            errors.append("sample_rate must be positive")
        buffer_size = config.realtime_stt.buffer_size
        if buffer_size is not None and buffer_size <= 0:
            errors.append("buffer_size must be positive")
        latency_limit = config.realtime_stt.allowed_latency_limit
        if latency_limit is not None and latency_limit <= 0:
            errors.append("allowed_latency_limit must be positive")

        # validate device
        input_device = config.realtime_stt.input_device_index
        if input_device is not None and input_device < 0:
            errors.append("input_device_index must be non-negative")
        gpu_device = config.realtime_stt.gpu_device_index
        if gpu_device is not None and gpu_device < 0:
            errors.append("gpu_device_index must be non-negative")

        return errors

    def create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist"""
        if not self.config_path.exists():
            default_config = AppConfig.default()
            self.save_config(default_config)
