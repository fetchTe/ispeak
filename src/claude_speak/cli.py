import argparse
import json
import subprocess
import sys

import pyautogui
import pynput.keyboard
from pynput.keyboard import Key, KeyCode
from rich.console import Console
from rich.prompt import Prompt

from .config import VALID_MODELS, ConfigManager
from .core import VoiceInput, key_to_str


def configure_voice() -> None:
    """Interactive configuration for voice settings"""
    console = Console()
    config_manager = ConfigManager()
    config = config_manager.load_config()
    console.print("\n[bold][red]◉[/red] [green]Claude Speak Configuration[/green][/bold]")

    # configure push-to-talk key
    console.print(
        f"\nCurrent PTT (push-to-talk) key: [yellow]{config.claude_speak.push_to_talk_key}[/yellow]"
    )
    console.print("Press your desired PTT key (or Enter to keep current)...")

    captured_key = None

    def on_key_press(key: Key | KeyCode) -> bool:
        nonlocal captured_key
        captured_key = key_to_str(key)
        console.print(f"Captured: [green]{captured_key}[/green]")
        return False  # stop listener

    listener = pynput.keyboard.Listener(on_press=on_key_press)
    listener.start()
    listener.join()  # wait for key press

    if captured_key:
        config.claude_speak.push_to_talk_key = captured_key

    # configure recording indicator
    recording_indicator = config.claude_speak.recording_indicator
    console.print(f"\nRecording indicator character: [yellow]{recording_indicator}[/yellow]")
    new_indicator = Prompt.ask(
        "Enter new indicator (or press Enter to keep current)",
        default=recording_indicator,
    )
    config.claude_speak.recording_indicator = new_indicator

    # configure language
    console.print(f"\nLanguage (current: [yellow]{config.realtime_stt.language}[/yellow]):")
    console.print("Common options: en, es, fr, de, it, pt, ru, ja, ko, zh, auto")
    language = Prompt.ask("Language code", default=config.realtime_stt.language)
    config.realtime_stt.language = language

    # configure model size
    console.print(f"\nModel size (current: [yellow]{config.realtime_stt.model}[/yellow]):")
    console.print("- tiny: Fastest, lowest accuracy (cpu)")
    console.print("- base: Balance (gpu/high-end-cpu)")
    console.print("- small: Better accuracy")
    console.print("- large: Best accuracy")
    console.print("- local/huggingface path to CTranslate2 STT model")

    model = Prompt.ask(
        "Model",
        default=config.realtime_stt.model,
        choices=VALID_MODELS,
    )
    config.realtime_stt.model = model

    # save configuration
    try:
        config_manager.save_config(config)
        console.print(f"\n[green]✓ Configuration saved to {config_manager.config_path}[/green]")
        console.print(f"  PTT Key  : [blue]{config.claude_speak.push_to_talk_key}[/blue]")
        console.print(f"  Indicator: [blue]{config.claude_speak.recording_indicator}[/blue]")
        console.print(f"  Language : [blue]{config.realtime_stt.language}[/blue]")
        console.print(f"  Model    : [blue]{config.realtime_stt.model}[/blue]\n")

    except Exception as e:
        console.print(f"[red]Failed to save configuration: {e}[/red]")
        sys.exit(1)


def test_voice() -> None:
    """Test voice input functionality"""
    console = Console()
    console.print("[yellow][bold]Voice Input Test[/bold][/yellow]")
    console.print("[yellow]> This will test your microphone and transcription[/yellow]")
    console.print("[yellow]> Press ctrl+c to stop testing[/yellow]\n")

    def handle_test_text(text: str) -> None:
        console.print(f"[green]Transcribed:[/green] {text}")

    try:
        voice_input = VoiceInput()
        voice_input.start(handle_test_text)

        console.print("\n[yellow][bold]Instructions (ctrl+c to stop test)[/bold][/yellow]")
        console.print(f"[yellow]  1. Press your PTT key {voice_input.config.claude_speak.push_to_talk_key}[/yellow]")
        console.print("[yellow]  2. Speak[/yellow]")
        console.print("[yellow]  3. Press your PTT key again[/yellow]")
        console.print("[yellow]  4. If successful, the transcribed text should then be displayed[/yellow]\n")

        # keep running until interrupted
        try:
            while True:
                input()  # wait for Enter or Ctrl+C
        except KeyboardInterrupt:
            pass

    except Exception as e:
        console.print(f"[red]Error starting voice input: {e}[/red]")
        sys.exit(1)
    finally:
        if "voice_input" in locals():
            voice_input.stop()
        console.print("\n[yellow]Test completed.[/yellow]")


def show_config() -> None:
    """Display current configuration"""
    console = Console()
    config_manager = ConfigManager()

    try:
        config = config_manager.load_config()

        # convert to JSON for display
        config_dict = {
            "realtime_stt": config.realtime_stt.__dict__,
            "claude_speak": config.claude_speak.__dict__,
        }

        console.print(
            f"[bold]Configuration File:[/bold] {config_manager.config_path}\n\n"
            f"\n{json.dumps(config_dict, indent=2)}\n",
        )

    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        sys.exit(1)


def run_with_claude(claude_args: list) -> int:
    """
    Run claude with voice integration

    Args:
        claude_args: Arguments to pass to claude command.

    Returns:
        Exit code from claude execution.
    """
    console = Console()

    console.print("\n[bold][red]◉[/red] [yellow]Claude Speak Init[/yellow][/bold]\n")

    voice_enabled = False
    voice_input = None

    def handle_voice_text(text: str) -> None:
        """Handle transcribed text by typing it"""
        try:
            # for whatever reason, adding an extra space at the end resolves
            # a handful of pyautogui.typewrite glitches/hiccups
            pyautogui.typewrite(text + " ")
        except Exception as e:
            console.print(f"[red]Error typing text: {e}[/red]")

    # try to start voice input
    try:
        voice_input = VoiceInput()
        voice_input.start(handle_voice_text)
        voice_enabled = True

    except Exception as e:
        console.print(f"[yellow]Could not start voice input: {e}[/yellow]")
        console.print("[yellow]Continuing without voice support...[/yellow]")

    try:
        # build command and run claude
        cmd = ["claude", *claude_args]
        console.print("\n[green][bold]> {}[/green]".format(" ".join(cmd)))
        result = subprocess.run(cmd)
        return_code = result.returncode

    except KeyboardInterrupt:
        return_code = 0
    except FileNotFoundError:
        console.print(
            "[red]Error: 'claude' command not found. Make sure Claude Code is installed.[/red]"
        )
        return_code = 1
    except Exception as e:
        console.print(f"[red]Error running Claude: {e}[/red]")
        return_code = 1
    finally:
        # clean up voice input
        if voice_enabled and voice_input:
            try:
                voice_input.stop()
            except Exception:
                pass  # ignore cleanup errors

    return return_code


def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Code with Voice Input",
        add_help=False,  # we'll handle help ourselves to pass it to claude
    )

    # our specific arguments
    parser.add_argument("--configure-voice", action="store_true", help="Configure voice settings")
    parser.add_argument("--test-voice", action="store_true", help="Test voice input functionality")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")

    # parse known args to separate ours from claude's
    our_args, claude_args = parser.parse_known_args()

    # handle our specific commands
    if our_args.configure_voice:
        configure_voice()
        return 0

    if our_args.test_voice:
        test_voice()
        return 0

    if our_args.show_config:
        show_config()
        return 0

    # if no specific command, run with claude integration
    return run_with_claude(claude_args)


if __name__ == "__main__":
    sys.exit(main())
