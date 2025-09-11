import json
import os
import platform
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Literal

try:
    import tomllib
except ImportError:
    tomllib = None

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
class ModelSTTConfig:
    """
    Configuration for ModelSTT settings

    - NOTE: None -> ModelSTT default
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
        # convert to dictionary for ModelSTT initialization
        config = asdict(self)
        # remove our internal _extra_config field from the output
        config.pop("_extra_config", None)

        # remove None values to let ModelSTT use its defaults
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
    # default output action (false disables output like old no_output: true)
    output: Literal["keyboard", "clipboard", False] = "keyboard"
    # delay applied after each 'keyboard' character (may be useful in some cases)
    keyboard_interval: float | None = None
    # list of words/phrases, when detected will delete previous output
    delete_keyword: list[str] | bool | None = True
    # key to delete last/previous output
    delete_key: str | None = None
    # removes extra white space (an extra space is always added to end)
    strip_whitespace: bool = True

    def __post_init__(self) -> None:
        # set default delete keywords if not provided
        if not self.delete_keyword:
            self.delete_keyword = []
        if self.delete_keyword is True:
            self.delete_keyword = ["delete", "undo"]
        # key setup
        self.delete_key = key_to_str(self.delete_key)
        self.escape_key = key_to_str(self.escape_key)
        self.push_to_talk_key = key_to_str(self.push_to_talk_key)


@dataclass
class AppConfig:
    """Main application configuration"""

    stt: ModelSTTConfig
    ispeak: CodeSpeakConfig
    plugin: dict[str, dict[str, Any]] | None = None
    config_path: Path | None = None

    @classmethod
    def default(cls, config_path: Path | None = None) -> "AppConfig":
        """Create default configuration"""
        default_plugins = {
            "replace": {"use": True, "order": 0, "settings": {}},
            "text2num": {
                "use": False,
                "order": 1,
                "settings": {"lang": "en", "threshold": 0, "min": None, "max": None},
            },
            "num2words": {
                "use": False,
                "order": 2,
                "settings": {"lang": "en", "to": "cardinal", "min": None, "max": None},
            },
        }
        return cls(stt=ModelSTTConfig(), ispeak=CodeSpeakConfig(), plugin=default_plugins, config_path=config_path)


class ConfigManager:
    """Manages loading, saving, and validation of configuration"""

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize configuration manager

        Args:
            config_path:
              1. ISPEAK_CONFIG env var
              2. env specific config (<config>/ispeak/ispeak.{json,toml})
                 - macOS: ~/Library/Preferences
                 - Windows: %APPDATA% (or ~/AppData/Roaming as fallback)
                 - Linux: $XDG_CONFIG_HOME (or ~/.config as fallback per XDG Base Directory spec)
              3. ./ispeak.{json,toml}
        """
        if config_path is None:
            # check environment variable first
            env_config_path = os.getenv("ISPEAK_CONFIG")
            if env_config_path:
                config_path = Path(env_config_path)
            else:
                # check default config directory using cross-platform function
                config_dir = self.get_config_dir() / "ispeak"

                # Check for both JSON and TOML files
                default_json_path = config_dir / "ispeak.json"
                default_toml_path = config_dir / "ispeak.toml"

                if default_toml_path.exists():
                    config_path = default_toml_path
                elif default_json_path.exists():
                    config_path = default_json_path
                else:
                    # fallback to current directory, prefer TOML
                    current_toml = Path("./ispeak.toml").resolve()
                    current_json = Path("./ispeak.json").resolve()

                    if current_toml.exists():
                        config_path = current_toml
                    else:
                        config_path = current_json  # Default to JSON for backward compatibility
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
            data = self._load_config_data()

            # parse ModelSTT config
            stt_data = data.get("stt", {})

            # separate known dataclass fields from extra config
            known_fields = {f.name for f in fields(ModelSTTConfig)}
            known_config = {k: v for k, v in stt_data.items() if k in known_fields}
            extra_config = {k: v for k, v in stt_data.items() if k not in known_fields}

            model = ModelSTTConfig(**known_config)
            model._extra_config = extra_config

            # parse CodeSpeak config
            ispeak_data = data.get("ispeak", {})
            ispeak = CodeSpeakConfig(**ispeak_data)

            # parse plugin config
            plugin_data = data.get("plugin", {})

            return AppConfig(stt=model, ispeak=ispeak, plugin=plugin_data, config_path=self.config_path)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # on any configuration error, return default and warn
            log_erro(f"Failed to load configuration from: {self.config_path}\n{e}")
            log_warn("Using default configuration[/yellow]")
            return AppConfig.default()
        except Exception as e:
            # handle TOML parsing errors and other issues
            log_erro(f"Failed to load configuration from: {self.config_path}\n{e}")
            log_warn("Using default configuration[/yellow]")
            return AppConfig.default()

    def _load_config_data(self) -> dict[str, Any]:
        """
        Load configuration data from JSON or TOML file

        Returns:
            Configuration data dictionary
        """
        file_extension = self.config_path.suffix.lower()

        if file_extension == ".toml":
            if tomllib is None:
                raise ImportError("TOML support requires Python 3.11+ or tomli package")

            with open(self.config_path, "rb") as f:
                return tomllib.load(f)

        elif file_extension == ".json":
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)

        else:
            # Try to detect format by content for files without proper extensions
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    content = f.read().strip()

                if content.startswith("{"):
                    # Looks like JSON
                    return json.loads(content)
                else:
                    # Try TOML
                    if tomllib is None:
                        raise ImportError("TOML support requires Python 3.11+ or tomli package")
                    return tomllib.loads(content)

            except (json.JSONDecodeError, ImportError):
                # Fallback to JSON parsing
                with open(self.config_path, encoding="utf-8") as f:
                    return json.load(f)

    def save_config(self, config: AppConfig, save_fmt: Literal["toml", "json"]) -> str:
        """
        Save configuration to file

        Args:
            config: Configuration to save
            save_fmt: Save format type 'json' | 'toml'
        """
        # Determine save format based on current config path or default to JSON
        use_toml = save_fmt == "toml"
        save_ext = "toml" if use_toml else "json"
        save_path = self.get_config_dir() / "ispeak" / f"ispeak.{save_ext}"

        # Ensure parent directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary format
        model_dict = asdict(config.stt)
        # Remove internal field
        model_dict.pop("_extra_config", None)
        # Add extra keys
        if config.stt._extra_config:
            model_dict.update(config.stt._extra_config)

        data = {"model": model_dict, "ispeak": asdict(config.ispeak), "plugin": config.plugin}

        # Add plugin config if present
        if config.plugin:
            data["plugin"] = config.plugin

        if use_toml:
            with open(save_path, "w", encoding="utf-8") as f:
                self._write_toml(f, data)
        else:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        return str(save_path)

    def _write_toml(self, f: Any, data: dict[str, Any], section_prefix: str = "") -> None:
        """
        Basic TOML writer for configuration data

        Args:
            f: File object to write to
            data: Data to write
            section_prefix: Prefix for nested sections
        """
        # Write simple key-value pairs first
        for key, value in data.items():
            if " " in key or "\\" in key:
                key = key.replace("\\", "\\\\")
                key = f'"{key}"'
            if not isinstance(value, dict):
                if isinstance(value, str):
                    value = value.replace("\\", "\\\\")
                    # if " " in value or "\\" in value:
                    #     value = f"\"{value}\""
                    f.write(f'{key} = "{value}"\n')
                elif isinstance(value, bool):
                    f.write(f"{key} = {str(value).lower()}\n")
                elif value is None:
                    # Skip None values in TOML
                    continue
                else:
                    f.write(f"{key} = {value}\n")

        # Write sections
        for key, value in data.items():
            if isinstance(value, dict):
                section_name = f"{section_prefix}.{key}" if section_prefix else key
                f.write(f"\n[{section_name}]\n")
                self._write_toml(f, value, section_name)

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
        silero_sens = config.stt.silero_sensitivity
        if silero_sens is not None and not 0 <= silero_sens <= 1:
            errors.append("silero_sensitivity must be between 0 and 1")

        return errors
