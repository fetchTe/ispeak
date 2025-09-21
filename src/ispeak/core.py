import subprocess
import time
from collections.abc import Callable
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode
from pyperclip import copy

from .config import AppConfig
from .console_helper import log, log_erro, log_warn
from .plugin import PluginRegistry
from .recorder import AudioRecorder, ModelSTTRecorder

try:
    __version__ = version("ispeak")
except Exception:
    __version__ = "?.?.?"


def type_output(text: str = "", interval: float | None = None, tap: tuple[KeyCode, int] | None = None) -> None:
    """
    Keyboard/pynput typper & tapper wrapper

    Args:
        text: Text to type
        interval: Delay to apply after every typed char
        tap: If to "tap" the given KeyCode x times
    """
    cont = Controller()
    # tap
    if tap:
        key, x = tap
        for _ in range(x):
            if interval:
                time.sleep(interval)
            cont.tap(key)
        return
    # type
    if not interval:
        cont.type(text)
        return
    for char in text:
        time.sleep(interval)
        cont.type(char)


class TextProcessor:
    """Handles text processing and normalization"""

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize text processor with configuration

        Args:
            config: Application configuration
        """
        self.config = config
        self.plugin_registry = PluginRegistry()

        # configure plugins
        plugin_config = config.plugin or {}

        self.plugin_registry.configure(plugin_config)

    def process_text(self, text: str) -> str:
        """
        Process and normalize transcribed text

        Args:
            text: Raw transcribed text
        Returns:
            Processed text ready for output
        """
        if not text:
            return text
        processed = text

        # strip probs not needed in most/all cases
        if self.config.ispeak.strip_whitespace:
            processed = processed.strip()

        # apply all plugin transformations
        processed = self.plugin_registry.process_text(processed)

        return processed

    def is_delete_command(self, text: str) -> bool:
        """
        Check if text is a delete command

        Args:
            text: Processed text to check
        Returns:
            True if text matches a delete keyword
        """
        delete_keyword = self.config.ispeak.delete_keyword
        if not delete_keyword:
            return False
        # normalized and remove end period
        normalized = text.lower().strip()
        if normalized.endswith("."):
            normalized = normalized[:-1]
        return normalized in [
            keyword.lower()
            for keyword in delete_keyword  # type: ignore
        ]


class VoiceInput:
    """Main voice input handler for AI code generation tools"""

    def __init__(self, config: AppConfig) -> None:
        # use provided configuration
        self.config = config
        # remove console instance - use class methods directly

        # initialize components
        self.text_processor = TextProcessor(self.config)

        # state management
        self.active = False
        self.recording = False
        self.listener: keyboard.Listener | None = None
        self.recorder: AudioRecorder | None = None
        self.on_text: Callable[[str], None] | None = None
        self.last_input: list[str] = []  # track last inputs for delete functionality

        # initialize recorder
        self._init_recorder()

    def _init_recorder(self) -> None:
        """Initialize audio recorder with configuration"""
        try:
            self.recorder = ModelSTTRecorder(self.config.stt)
        except Exception as e:
            log_erro(f"Failed to initialize audio recorder: {e}")
            raise

    def start(self, on_text: Callable[[str], None]) -> None:
        """
        Start voice input system

        Args:
            on_text: Callback function to handle transcribed text
        """
        self.active = True
        self.on_text = on_text

        # start keyboard listener for push-to-talk
        hot_rec = {self.config.ispeak.push_to_talk_key: self._on_key_press_hotkey}
        # add esc if present
        if self.config.ispeak.escape_key:
            hot_rec[self.config.ispeak.escape_key] = self._on_key_press_esckey
        # add delete if present
        if self.config.ispeak.delete_key:
            hot_rec[self.config.ispeak.delete_key] = self._handle_delete_last
        # https://pynput.readthedocs.io/en/latest/keyboard-usage.html#global-hotkeys
        self.listener = keyboard.GlobalHotKeys(hot_rec)
        self.listener.start()

    def stop(self, abort: bool = False) -> None:
        """Stop voice input system and cleanup resources"""
        self.active = False

        # stop keyboard listener
        if self.listener:
            self.listener.stop()
            self.listener = None

        # stop recording if active
        if self.recording:
            self._stop_recording(is_esc=abort)

        # shutdown recorder
        if self.recorder:
            self.recorder.shutdown()

    def _start_recording(self) -> None:
        """Start recording audio and show indicator"""
        if self.recorder is None:
            log_erro("No recorder available")
            return

        self.recording = True
        # brief delay required, otherwise typewrite won't fire properly
        time.sleep(self.config.ispeak.push_to_talk_key_delay)

        # start recorder
        rm_indicator = False
        try:
            self.recorder.start()
            recording_indicator = self.config.ispeak.recording_indicator
            # type recording indicator
            if len(recording_indicator) and self.config.ispeak.output is not False:
                type_output(recording_indicator, self.config.ispeak.keyboard_interval)
                rm_indicator = True
        except Exception as e:
            log_erro(f"Failed to start recording: {e}")
            self.recording = False
            if rm_indicator:
                self._handle_delete_indicator()

    def _stop_recording(self, is_esc: bool = False) -> None:
        """Stop recording and process transcribed text"""
        if not self.recording or self.recorder is None:
            return

        self.recording = False
        # brief delay required, otherwise typewrite won't fire properly
        time.sleep(self.config.ispeak.push_to_talk_key_delay)

        # remove recording indicator
        self._handle_delete_indicator()

        # stop recorder and get text
        try:
            self.recorder.stop()
            # is escape we stop witout outputing transcription
            if is_esc:
                return
            raw_text = self.recorder.text()

            if raw_text:
                # process text through text processor
                processed_text = self.text_processor.process_text(raw_text)

                # check for delete command
                if self.text_processor.is_delete_command(processed_text):
                    self._handle_delete_last()
                else:
                    # store for potential deletion and send to callback
                    self.last_input.append(processed_text)
                    if self.on_text:
                        self.on_text(processed_text)

        except Exception as e:
            log_erro(f"Error during transcription: {e}")

    def _handle_delete(self, chars_to_delete: int = 0) -> None:
        """Handles actual backspace of chars"""
        if not chars_to_delete or self.config.ispeak.output is False:
            return
        tap: tuple[KeyCode, int] = (Key.backspace.value, chars_to_delete)
        type_output(interval=self.config.ispeak.keyboard_interval, tap=tap)

    def _handle_delete_indicator(self) -> None:
        """Handle delete of rec indicator"""
        self._handle_delete(len(self.config.ispeak.recording_indicator))

    def _handle_delete_last(self) -> None:
        """Handle delete last command by simulating backspace"""
        if self.last_input:
            # get the most recent input to delete
            last_text = self.last_input.pop()
            # calculate number of characters to delete (including the trailing space)
            self._handle_delete(len(last_text) + 1)

    def _on_key_press_esckey(self) -> None:
        """
        Handle keyboard 'escape' key press events

        Args:
            key: Pressed key from pynput
        """
        if not self.active:
            return
        if self.recording:
            self._stop_recording(is_esc=True)
            return

    def _on_key_press_hotkey(self) -> None:
        """
        Handle keyboard 'hotkey' key press events

        Args:
            key: Pressed key from pynput
        """
        if not self.active:
            return
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def __del__(self) -> None:
        # ensure cleanup on deletion
        self.stop()


def runner(
    bin_args: list, bin_cli: str | None, cli_output: Literal["clipboard", False, None], config: AppConfig
) -> int:
    """
    Run bin/executable or bin-less with voice integration

    Args:
        bin_args: Arguments to pass to bin command
        bin_cli: Override executable from command line
        cli_output: If output mode is copy, no-output, or none - default
        config: Application configuration with CLI overrides applied
    Returns:
        Exit code from bin execution.
    """
    # show startup message
    voice_enabled = False
    voice_input = None

    executable = bin_cli or config.ispeak.binary
    # enable binary-less mode if executable is empty/null
    is_standalone = not executable
    cmd = [executable, *bin_args] if executable else []
    is_noop = cli_output is False or config.ispeak.output is False
    is_copy = not is_noop and "clipboard" in [cli_output, config.ispeak.output]
    # cli_output
    output = "none" if is_noop else "clipboard" if is_copy else "keyboard"
    mode = "standalone" if is_standalone else "binary -> {}".format(" ".join(cmd))

    log(f"[bold][red]◉[/red] [blue]init[/blue][/bold] [dim][white](v{__version__})[/white][/dim]")
    log(f"[blue]  config      :[/blue] {config.config_path!s}")
    log(f"[blue]  language    :[/blue] {config.stt.language or 'auto'}")
    log(f"[blue]  mode        :[/blue] {mode}")
    log(f"[blue]  model       :[/blue] {config.stt.model}")
    log(f"[blue]  output      :[/blue] {output}")
    log(f"[blue]  push-to-talk:[/blue] {config.ispeak.push_to_talk_key}\n")

    def handle_voice_text(text: str) -> None:
        """Handle transcribed text by typing it"""
        # log transcription if log file specified
        timestamp = datetime.now().isoformat(timespec="seconds")
        if config.ispeak.log_file:
            try:
                log_path = Path(config.ispeak.log_file).expanduser()
                if log_path.parent:
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"## {timestamp}\n{text}\n\n")
            except Exception as e:
                log_erro(f"writing to log file: {e}")

        if is_standalone:
            # show styled version in terminal
            log(f"[dim][white]##[/white][/dim] {timestamp}\n{text}\n\n", end="")

        # noop
        if is_noop:
            return
        # copy
        if is_copy:
            try:
                copy(text + " ")
            except Exception as e:
                log_erro(f"typing text: {e}")
            return
        # type
        try:
            type_output(text + " ", config.ispeak.keyboard_interval)
        except Exception as e:
            log_erro(f"typing text: {e}")

    # try to start voice input
    try:
        voice_input = VoiceInput(config)
        voice_input.start(handle_voice_text)
        voice_enabled = True
        log("\n[bold][red]◉[/red] [cyan]active[/cyan][/bold]")

    except Exception as e:
        log_erro(f"Could not start voice input due to: {e}")
        if not is_standalone:
            log_warn("Continuing without ispeak voice support...")

    # abort on ctrl+c
    abort_on_exit = False
    try:
        if is_standalone:
            # binary-less mode: just run voice input without subprocess
            if voice_enabled:
                try:
                    # keep running until interrupted
                    while True:
                        time.sleep(10)
                except KeyboardInterrupt:
                    abort_on_exit = True
                    return_code = 0
                    print("")
            else:
                return_code = 1
        else:
            # normal mode: build command and run binary
            result = subprocess.run(cmd)
            return_code = result.returncode

    except KeyboardInterrupt:
        abort_on_exit = True
        return_code = 0
        print("")
    except FileNotFoundError:
        log_erro(f"'{cmd[0] if cmd else 'binary'}' command not found. Make sure it is installed and in PATH.")
        return_code = 1
    except Exception as e:
        log_erro(f"running binary: {e}")
        return_code = 1
    finally:
        # clean up voice input
        if voice_enabled and voice_input:
            try:
                voice_input.stop(abort=abort_on_exit)
            except Exception:
                pass  # ignore cleanup errors

    return return_code
