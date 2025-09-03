import subprocess
import time
from collections.abc import Callable
from datetime import datetime

from pynput import keyboard
from pynput.keyboard import Controller, Key
from rich.console import Console

from .config import AppConfig
from .recorder import AudioRecorder, RealtimeSTTRecorder
from .replace import TextReplacer


class TextProcessor:
    """Handles text processing and normalization"""

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize text processor with configuration

        Args:
            config: Application configuration
        """
        self.config = config
        self.replacer = TextReplacer(config.ispeak.replace) if config.ispeak.replace else None

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

        # apply regex replacements
        if self.replacer:
            processed = self.replacer.apply_replacements(processed)

        return processed

    def is_delete_command(self, text: str) -> bool:
        """
        Check if text is a delete command

        Args:
            text: Processed text to check
        Returns:
            True if text matches a delete keyword
        """
        delete_keywords = self.config.ispeak.delete_keywords
        if not delete_keywords:
            return False
        # normalized and remove end period
        normalized = text.lower().strip()
        if normalized.endswith("."):
            normalized = normalized[:-1]
        return normalized in [
            keyword.lower()
            for keyword in delete_keywords  # type: ignore
        ]


class VoiceInput:
    """Main voice input handler for AI code generation tools"""

    def __init__(self, config: AppConfig) -> None:
        # use provided configuration
        self.config = config
        self.console = Console()

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
        self.console.print("\n[bold][red]◉[/red] [cyan]ispeak active[/cyan][/bold]")
        self.console.print(f"[blue]  model       : {self.config.realtime_stt.model}[/blue]")
        self.console.print(f"[blue]  language    : {self.config.realtime_stt.language or 'auto'}[/blue]")
        self.console.print(f"[blue]  push-to-talk: {self.config.ispeak.push_to_talk_key}[/blue]")

        # start keyboard listener for push-to-talk
        hot_rec = {self.config.ispeak.push_to_talk_key: self._on_key_press_hotkey}
        # add esc if present
        if self.config.ispeak.escape_key:
            hot_rec[self.config.ispeak.escape_key] = self._on_key_press_esckey
        # https://pynput.readthedocs.io/en/latest/keyboard-usage.html#global-hotkeys
        self.listener = keyboard.GlobalHotKeys(hot_rec)
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
        time.sleep(self.config.ispeak.push_to_talk_key_delay)

        # start recorder
        rm_indicator = False
        try:
            self.recorder.start()
        except Exception as e:
            self.console.print(f"[red]Failed to start recording: {e}[/red]")
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
                    self.last_input.append(raw_text)
                    if self.on_text:
                        self.on_text(raw_text)

        except Exception as e:
            self.console.print(f"[red]Error during transcription: {e}[/red]")

    def _handle_delete(self, chars_to_delete: int = 0) -> None:
        """Handles actual backspace of chars"""
        if not chars_to_delete or self.config.ispeak.no_output:
            return
        cont = Controller()
        for _ in range(chars_to_delete):
            cont.tap(Key.backspace.value)

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


def runner(bin_args: list, bin_cli: str | None, config: AppConfig) -> int:
    """
    Run bin/executable or bin-less with voice integration

    Args:
        bin_args: Arguments to pass to bin command.
        bin_cli: Override executable from command line.
        config: Application configuration with CLI overrides applied.

    Returns:
        Exit code from bin execution.
    """
    console = Console()

    console.print("[bold][red]◉[/red][/bold] ispeak init\n")

    voice_enabled = False
    voice_input = None

    executable = bin_cli or config.ispeak.binary
    # enable binary-less mode if executable is empty/null
    binary_less_mode = not executable
    log_print = binary_less_mode

    def handle_voice_text(text: str) -> None:
        """Handle transcribed text by typing it"""
        # log transcription if log file specified
        timestamp = datetime.now().isoformat(timespec="seconds")
        if config.ispeak.log_file:
            try:
                with open(config.ispeak.log_file, "a", encoding="utf-8") as f:
                    f.write(f"## {timestamp}\n{text}\n\n")
            except Exception as e:
                console.print(f"[red][bold][ERROR][/bold] writing to log file: {e}[/red]")

        if log_print:
            # show styled version in terminal
            console.print(f"[dim][white]##[/white][/dim] {timestamp}\n{text}\n\n", end="")

        if not config.ispeak.no_output:
            try:
                Controller().type(text + " ")
            except Exception as e:
                console.print(f"[red][bold][ERROR][/bold] typing text: {e}[/red]")

    # try to start voice input
    try:
        voice_input = VoiceInput(config)
        voice_input.start(handle_voice_text)
        voice_enabled = True

    except Exception as e:
        console.print(f"[yellow]Could not start voice input: {e}[/yellow]")
        console.print("[yellow]Continuing without voice support...[/yellow]")

    cmd = []
    try:
        if binary_less_mode:
            # binary-less mode: just run voice input without subprocess
            console.print("\n[bold][cyan]> Voice Mode[/cyan][/bold] [yellow](to exit: ctrl+c)[/yellow]")
            console.print("")
            if voice_enabled:
                try:
                    # keep running until interrupted
                    while True:
                        time.sleep(10)
                except KeyboardInterrupt:
                    pass
            return_code = 0
        else:
            # normal mode: build command and run binary
            cmd = [executable, *bin_args]
            console.print("\n[bold][cyan]> {}[/cyan][/bold]".format(" ".join(cmd)))
            result = subprocess.run(cmd)
            return_code = result.returncode

    except KeyboardInterrupt:
        return_code = 0
    except FileNotFoundError:
        console.print(
            f"[red][bold][ERROR][/bold] '{cmd[0] if cmd else 'binary'}' command not found."
            " Make sure it is installed and in PATH.[/red]"
        )
        return_code = 1
    except Exception as e:
        console.print(f"[red][bold][ERROR][/bold] running binary tool: {e}[/red]")
        return_code = 1
    finally:
        # clean up voice input
        if voice_enabled and voice_input:
            try:
                voice_input.stop()
            except Exception:
                pass  # ignore cleanup errors

    return return_code
