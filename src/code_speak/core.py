import time
from collections.abc import Callable

import pyautogui
import pynput.keyboard
from pynput.keyboard import Key, KeyCode
from rich.console import Console

from .config import AppConfig, ConfigManager
from .recorder import AudioRecorder, RealtimeSTTRecorder


def key_to_str(key: str | Key | KeyCode | None) -> str:
    """
    Convert pynput key to string representation

    Args:
        key: Key from pynput keyboard listener
    Returns:
        String representation of the key
    """
    if not key:
        return ""
    if isinstance(key, KeyCode):
        if key.char:
            return str(key.char).lower()
        # fallback for non-printable KeyCodes
        return f"vk_{key.vk}".lower()
    elif isinstance(key, Key):
        return str(key.name).lower()
    return str(key)


class TextProcessor:
    """Handles text processing and normalization"""

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize text processor with configuration

        Args:
            config: Application configuration
        """
        self.config = config

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
        if self.config.code_speak.strip:
            processed = processed.strip()
        return processed

    def is_delete_command(self, text: str) -> bool:
        """
        Check if text is a delete command

        Args:
            text: Processed text to check
        Returns:
            True if text matches a delete keyword
        """
        delete_keywords = self.config.code_speak.delete_keywords
        if not delete_keywords:
            return False
        # normalized and remove end period
        normalized = text.lower().strip()
        if normalized.endswith("."):
            normalized = normalized[:-1]
        return normalized in [
            keyword.lower() for keyword in delete_keywords  # type: ignore
        ]


class VoiceInput:
    """Main voice input handler for AI code generation tools"""

    def __init__(self) -> None:
        # load configuration
        config_manager = ConfigManager()
        self.config = config_manager.load_config()
        self.console = Console()

        # validate configuration
        errors = config_manager.validate_config(self.config)
        if errors:
            self.console.print("\n[red][bold]ERROR[/bold] Configuration validation errors:[/red]")
            for error in errors:
                print(f"  - {error}")
            self.console.print("[yellow][bold]NOTE[/bold] Using default values for invalid settings[/yellow]")

        # initialize components
        self.text_processor = TextProcessor(self.config)

        # state management
        self.active = False
        self.recording = False
        self.listener: pynput.keyboard.Listener | None = None
        self.recorder: AudioRecorder | None = None
        self.on_text: Callable[[str], None] | None = None
        self.last_input: list[str] = []  # track last inputs for delete functionality

        # initialize recorder
        self._init_recorder()

    def _init_recorder(self) -> None:
        """Initialize audio recorder with configuration"""
        try:
            self.recorder = RealtimeSTTRecorder(self.config.realtime_stt)
        except Exception as e:
            self.console.print(f"[red]Failed to initialize audio recorder: {e}[/red]")
            raise

    def start(self, on_text: Callable[[str], None]) -> None:
        """
        Start voice input system

        Args:
            on_text: Callback function to handle transcribed text
        """
        self.active = True
        self.on_text = on_text

        # show startup message
        self.console.print("\n[bold][red]◉[/red] [green]Code Speak Active[/green][/bold]")
        self.console.print(f"[blue]  Model       : {self.config.realtime_stt.model}[/blue]")
        self.console.print(f"[blue]  Language    : {self.config.realtime_stt.language or 'auto'}[/blue]")
        self.console.print(f"[blue]  Push-to-Talk: {self.config.code_speak.push_to_talk_key}[/blue]")

        # start keyboard listener for push-to-talk
        self.listener = pynput.keyboard.Listener(on_press=self._on_key_press)
        self.listener.start()

    def stop(self) -> None:
        """Stop voice input system and cleanup resources"""
        self.active = False

        # clear input history when session ends
        self.last_input.clear()

        # stop keyboard listener
        if self.listener:
            self.listener.stop()
            self.listener = None

        # stop recording if active
        if self.recording:
            self._stop_recording()

        # shutdown recorder
        if self.recorder:
            self.recorder.shutdown()

    def _start_recording(self) -> None:
        """Start recording audio and show indicator"""
        if self.recorder is None:
            self.console.print("[red]No recorder available[/red]")
            return

        self.recording = True
        # brief delay required, otherwise typewrite won't fire properly
        time.sleep(self.config.code_speak.push_to_talk_key_delay)

        # type recording indicator
        pyautogui.typewrite(
            self.config.code_speak.recording_indicator,
            self.config.code_speak.pyautogui_interval,
        )

        # start recorder
        try:
            self.recorder.start()
        except Exception as e:
            self.console.print(f"[red]Failed to start recording: {e}[/red]")
            self.recording = False
            # remove indicator on failure
            self._handle_delete_indicator()

    def _stop_recording(self, is_esc: bool = False) -> None:
        """Stop recording and process transcribed text"""
        if not self.recording or self.recorder is None:
            return

        self.recording = False
        # brief delay required, otherwise typewrite won't fire properly
        time.sleep(self.config.code_speak.push_to_talk_key_delay)

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
                    self.last_input.append(raw_text)
                    if self.on_text:
                        self.on_text(raw_text)

        except Exception as e:
            self.console.print(f"[red]Error during transcription: {e}[/red]")

    def _handle_delete(self, chars_to_delete: int = 0) -> None:
        """Handles actual backspace of chars"""
        if not chars_to_delete:
            return
        if self.config.code_speak.fast_delete:
            # use array of backspace keys for faster deletion
            backspace_keys = ["backspace"] * chars_to_delete
            pyautogui.press(backspace_keys, interval=self.config.code_speak.pyautogui_interval)
            return
        # loop for individual key presses - much slower but may be more accurate in some envs
        for _ in range(chars_to_delete):
            pyautogui.press("backspace", interval=self.config.code_speak.pyautogui_interval)

    def _handle_delete_indicator(self) -> None:
        """Handle delete of rec indicator"""
        self._handle_delete(len(self.config.code_speak.recording_indicator))

    def _handle_delete_last(self) -> None:
        """Handle delete last command by simulating backspace"""
        if self.last_input:
            # get the most recent input to delete
            last_text = self.last_input.pop()
            # calculate number of characters to delete (including the trailing space)
            self._handle_delete(len(last_text) + 1)

    def _on_key_press(self, key: Key | KeyCode | None) -> None:
        """
        Handle keyboard key press events

        Args:
            key: Pressed key from pynput
        """
        if not self.active or not key:
            return

        key_str = key_to_str(key)
        # check for escape key to cancel recording
        if self.recording and self.config.code_speak.escape_key == key_str:
            self._stop_recording(is_esc=True)
            return


        # check if it's the push-to-talk key
        if key_str == self.config.code_speak.push_to_talk_key:
            if self.recording:
                self._stop_recording()
            else:
                self._start_recording()

    def __del__(self) -> None:
        # ensure cleanup on deletion
        self.stop()
