#!/usr/bin/env python3

import time
from collections.abc import Callable

import pyautogui
import pynput.keyboard
from pynput.keyboard import Key, KeyCode
from rich.console import Console
from rich.panel import Panel

from .config import AppConfig, ConfigManager
from .recorder import AudioRecorder, RealtimeSTTRecorder


def key_to_str(key: Key | KeyCode) -> str:
    """Convert pynput key to string representation.

    Args:
        key: Key from pynput keyboard listener.

    Returns:
        String representation of the key.
    """
    if isinstance(key, KeyCode):
        if key.char:
            return key.char
        return f"vk_{key.vk}"  # fallback for non-printable KeyCodes
    elif isinstance(key, Key):
        return key.name
    return str(key)


class TextProcessor:
    """Handles text processing and normalization."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize text processor with configuration.

        Args:
            config: Application configuration.
        """
        self.config = config

    def process_text(self, text: str) -> str:
        """Process and normalize transcribed text.

        Args:
            text: Raw transcribed text.

        Returns:
            Processed text ready for output.
        """
        if not text:
            return text
        processed = text
        # strip probs not needed in most/all cases
        if self.config.claude_speak.strip:
            processed = processed.strip()
        return processed

    def is_delete_command(self, text: str) -> bool:
        """Check if text is a delete command.

        Args:
            text: Processed text to check.

        Returns:
            True if text matches a delete keyword.
        """
        normalized = text.lower().strip()
        return normalized in [
            keyword.lower() for keyword in self.config.claude_speak.delete_keywords
        ]


class VoiceInput:
    """Main voice input handler for Claude Code."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize voice input system.

        Args:
            config_path: Path to configuration file. Uses default if None.
        """
        # Load configuration
        config_manager = ConfigManager(config_path)
        self.config = config_manager.load_config()

        # Validate configuration
        errors = config_manager.validate_config(self.config)
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            print("Using default values for invalid settings.")

        # Initialize components
        self.console = Console()
        self.text_processor = TextProcessor(self.config)

        # State management
        self.active = False
        self.recording = False
        self.listener: pynput.keyboard.Listener | None = None
        self.recorder: AudioRecorder | None = None
        self.on_text: Callable[[str], None] | None = None
        self.last_input: list[str] = []  # Track last inputs for delete functionality

        # Initialize recorder
        self._init_recorder()

    def _init_recorder(self) -> None:
        """Initialize audio recorder with configuration."""
        try:
            self.recorder = RealtimeSTTRecorder(self.config.realtime_stt)
        except Exception as e:
            self.console.print(f"[red]Failed to initialize audio recorder: {e}[/red]")
            raise

    def start(self, on_text: Callable[[str], None]) -> None:
        """Start voice input system.

        Args:
            on_text: Callback function to handle transcribed text.
        """
        self.active = True
        self.on_text = on_text

        # Show startup message
        self.console.print(
            Panel.fit(
                f"[green]Voice Input Active[/green]\n"
                f"Push-to-Talk: [yellow]{self.config.claude_speak.push_to_talk_key}[/yellow]\n"
                f"Model: {self.config.realtime_stt.model}\n"
                f"Language: {self.config.realtime_stt.language or 'auto'}",
                title="🎙️ Voice Mode",
            )
        )

        # Start keyboard listener for push-to-talk
        self.listener = pynput.keyboard.Listener(on_press=self._on_key_press)
        self.listener.start()

    def stop(self) -> None:
        """Stop voice input system and cleanup resources."""
        self.active = False

        # Clear input history when session ends
        self.last_input.clear()

        # Stop keyboard listener
        if self.listener:
            self.listener.stop()
            self.listener = None

        # Stop recording if active
        if self.recording:
            self._stop_recording()

        # Shutdown recorder
        if self.recorder:
            self.recorder.shutdown()

    def _start_recording(self) -> None:
        """Start recording audio and show indicator."""
        if self.recorder is None:
            self.console.print("[red]No recorder available[/red]")
            return

        self.recording = True
        time.sleep(0.2)  # Brief delay for stability

        # Type recording indicator
        pyautogui.typewrite(self.config.claude_speak.recording_indicator)

        # Start recorder
        try:
            self.recorder.start()
        except Exception as e:
            self.console.print(f"[red]Failed to start recording: {e}[/red]")
            self.recording = False
            # Remove indicator on failure
            pyautogui.press("backspace")

    def _stop_recording(self) -> None:
        """Stop recording and process transcribed text."""
        if not self.recording or self.recorder is None:
            return

        self.recording = False
        time.sleep(0.2)  # Brief delay for stability

        # Remove recording indicator
        pyautogui.press("backspace")

        # Stop recorder and get text
        try:
            self.recorder.stop()
            raw_text = self.recorder.text()

            if raw_text:
                # Process text through text processor
                processed_text = self.text_processor.process_text(raw_text)

                # Check for delete command
                if self.text_processor.is_delete_command(processed_text):
                    self._handle_delete_last()
                else:
                    # Store for potential deletion and send to callback
                    self.last_input.append(raw_text)
                    if self.on_text:
                        self.on_text(raw_text)

        except Exception as e:
            self.console.print(f"[red]Error during transcription: {e}[/red]")

    def _handle_delete_last(self) -> None:
        """Handle delete last command by simulating backspace."""
        if self.last_input:
            # Get the most recent input to delete
            last_text = self.last_input.pop()
            # Calculate number of characters to delete (including the trailing space)
            chars_to_delete = len(last_text) + 1

            if self.config.claude_speak.fast_delete:
                # use array of backspace keys for faster deletion
                backspace_keys = ["backspace"] * chars_to_delete
                pyautogui.press(backspace_keys)
            else:
                # use loop for individual key presses
                for _ in range(chars_to_delete):
                    pyautogui.press("backspace")

    def _on_key_press(self, key: Key | KeyCode) -> None:
        """Handle keyboard key press events.

        Args:
            key: Pressed key from pynput.
        """
        if not self.active:
            return

        # Check for escape key to cancel recording
        if key == Key.esc and self.recording:
            self._stop_recording()
            return

        # Check if it's the push-to-talk key
        key_str = key_to_str(key).lower()
        ptt_key = self.config.claude_speak.push_to_talk_key.lower()

        if key_str == ptt_key:
            if self.recording:
                self._stop_recording()
            else:
                self._start_recording()

    def __del__(self) -> None:
        """Ensure cleanup on deletion."""
        self.stop()
