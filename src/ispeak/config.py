import json
import os
import platform
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from pynput.keyboard import Key, KeyCode

from .console_helper import log_erro, log_warn

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


def key_to_str(ikey: str | Key | KeyCode | None) -> str:
    """
    Convert pynput key to string representation

    Args:
        ikey: Key from pynput keyboard listener
    Returns:
        String representation of the key
    """
    if not ikey:
        return ""

    # enum key/value check like 'esc' which in turn is transformed to <65307>
    if isinstance(ikey, str) and hasattr(Key, ikey):
        ikey = Key[ikey].value

    if isinstance(ikey, KeyCode):
        if ikey.char:
            return str(ikey.char).lower()
        # fallback for non-printable KeyCodes
        return f"<{ikey.vk}>".lower()
    elif isinstance(ikey, Key):
        return str(ikey.name).lower()
    return str(ikey)


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

    model: str = "tiny"
    language: str = "auto"

    # text processing settings
    ensure_sentence_starting_uppercase: bool | None = True
    ensure_sentence_ends_with_period: bool | None = True
    normalize_audio: bool | None = True

    # realtime transcription settings
    enable_realtime_transcription: bool | None = False

    # voice Activity Detection (VAD) settings
    silero_sensitivity: float | None = 0.5

    # recording timing settings
    post_speech_silence_duration: float | None = None

    # performance and debug settings
    print_transcription_time: bool | None = False
    spinner: bool | None = False

    # store extra configuration keys not defined in dataclass
    _extra_config: dict[str, Any] = None  # type: ignore

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

    # default binary/executable (empty string enables binary-less mode)
    binary: str | None = None
    # key to initilize rec session
    push_to_talk_key: str = "end"
    # execution delay applied after push_to_talk_key (via time.sleep) - helps pervent mistypes
    push_to_talk_key_delay: float | int = 0.2
    # key to "escape" current rec session, ends without outputing transcription
    escape_key: str | None = "esc"
    # char/word outputed when recording starts
    recording_indicator: str = ";"
    # path to log file for voice transcriptions
    log_file: str | None = None
    # disable typing output and recording indicator (disables pyautogui)
    no_output: bool = False
    # regex replacement rules - dict of patterns/replacements or list of file paths
    replace: dict[str, str] | list[str] | None = None
    # list of words/phrases, when detected will delete previous output
    delete_keywords: list[str] | bool | None = True
    # removes extra white space (an extra space is always added to end)
    strip_whitespace: bool = True
    # # default action
    # action: Literal["type", "copy"] = "type"

    def __post_init__(self) -> None:
        # set default delete keywords if not provided
        if not self.delete_keywords:
            self.delete_keywords = []
        if self.delete_keywords is True:
            self.delete_keywords = ["delete", "undo"]
        # key setup
        self.escape_key = key_to_str(self.escape_key)
        self.push_to_talk_key = key_to_str(self.push_to_talk_key)


@dataclass
class AppConfig:
    """Main application configuration"""

    realtime_stt: RealtimeSTTConfig
    ispeak: CodeSpeakConfig
    config_path: Path | None = None

    @classmethod
    def default(cls, config_path: Path | None = None) -> "AppConfig":
        """Create default configuration"""
        return cls(realtime_stt=RealtimeSTTConfig(), ispeak=CodeSpeakConfig(), config_path=config_path)


class ConfigManager:
    """Manages loading, saving, and validation of configuration"""

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize configuration manager

        Args:
            config_path:
              1. ISPEAK_CONFIG env var
              2. env specific config (<config>/ispeak/ispeak.json)
                 - macOS: ~/Library/Preferences
                 - Windows: %APPDATA% (or ~/AppData/Roaming as fallback)
                 - Linux: $XDG_CONFIG_HOME (or ~/.config as fallback per XDG Base Directory spec)
              3. ./ispeak.json
        """
        if config_path is None:
            # check environment variable first
            env_config_path = os.getenv("ISPEAK_CONFIG")
            if env_config_path:
                config_path = Path(env_config_path)
            else:
                # check default config directory using cross-platform function
                default_config_path = self.get_config_dir() / "ispeak" / "ispeak.json"
                if default_config_path.exists():
                    config_path = default_config_path
                else:
                    # fallback to current directory
                    config_path = Path("./ispeak.json").resolve()
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
            ispeak_data = data.get("ispeak", {})
            ispeak = CodeSpeakConfig(**ispeak_data)
            return AppConfig(realtime_stt=realtime_stt, ispeak=ispeak, config_path=self.config_path)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # on any configuration error, return default and warn
            log_erro(f"Failed to load configuration from: {self.config_path}\n{e}")
            log_warn("Using default configuration[/yellow]")
            return AppConfig.default()

    def save_config(self, config: AppConfig) -> str:
        """
        Save configuration to file

        Args:
            config: Configuration to save
        """
        # ensure parent directory exists
        save_path = self.get_config_dir() / "ispeak" / "ispeak.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # convert to dictionary format
        realtime_stt_dict = asdict(config.realtime_stt)
        # remove internal field
        realtime_stt_dict.pop("_extra_config", None)
        # add extra keys
        realtime_stt_dict.update(config.realtime_stt._extra_config)

        data = {
            "realtime_stt": realtime_stt_dict,
            "ispeak": asdict(config.ispeak),
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)
        return str(save_path)

    def validate_config(self, config: AppConfig) -> list[str]:
        """
        Validate configuration and return list of errors

        Args:
            config: Configuration to validate
        Returns:
            List of validation error messages
        """
        errors = []

        # validate ispeak config
        if not config.ispeak.push_to_talk_key:
            errors.append("push_to_talk_key cannot be empty")
        if not config.ispeak.recording_indicator:
            errors.append("recording_indicator cannot be empty")

        # @NOTE -> skipping validating model due to custom possibilities

        # validate sensitivity settings (0-1 range)
        silero_sens = config.realtime_stt.silero_sensitivity
        if silero_sens is not None and not 0 <= silero_sens <= 1:
            errors.append("silero_sensitivity must be between 0 and 1")

        return errors

    def create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist"""
        if not self.config_path.exists():
            default_config = AppConfig.default()
            self.save_config(default_config)
