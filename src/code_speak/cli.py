import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pyautogui
import pynput.keyboard
from pynput.keyboard import Key, KeyCode
from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, Prompt

from .config import VALID_MODELS, ConfigManager, key_to_str
from .core import VoiceInput

OR_ENTER = "[dim](press 'enter' to keep current)[/dim]"


def print_option_header(console: Console, option_name: str, info: str, current_value: str) -> None:
    """Helper to print consistent option headers"""
    console.print(f"\n[white][dim]{"-" * 90!s}[/dim][/white]")
    console.print(f"[bold]option [/bold]: [yellow][bold]{option_name}[/bold][/yellow]")
    console.print(f"[bold]info   [/bold]: {info}")
    console.print(f"[bold]current[/bold]: {current_value}")


def capture_key(console: Console, prompt_text: str) -> str | None:
    """Helper to capture a single key press"""
    console.print(f"\n[bold][blue]>[/blue][/bold] [white]{prompt_text} {OR_ENTER}[/white]")

    captured_key = None

    def on_key_press(key: Key | KeyCode | None) -> None:
        nonlocal captured_key
        captured_key = key_to_str(key)
        listener.stop()
        if captured_key == "enter":
            console.print("\n[white][dim]>[/dim][/white] skipped... keeping current")
            return
        console.print(f"\n[bold][green]> key:[/green][/bold] {captured_key}")

    with pynput.keyboard.Listener(on_press=on_key_press, suppress=True) as listener:
        try:
            listener.wait()
            listener.join()  # wait for key press
        finally:
            listener.stop()
        return captured_key if captured_key != "enter" else None


def setup_voice(config_path: str | None = None) -> None:
    """Interactive configuration for voice settings"""
    console = Console()
    config_manager = ConfigManager(Path(config_path) if config_path else None)
    config = config_manager.load_config()

    time.sleep(1)
    console.print("\n[bold][red]◉[/red] [green]Code Speak Configuration[/green][/bold]")

    # configure binary/executable
    print_option_header(
        console, "binary", "default executable to launch with voice input", config.code_speak.binary
    )
    console.print(
        f"\n[bold][blue]>[/blue][/bold] [white]enter executable binary/program, none, {OR_ENTER}[/white]"
    )
    binary = config.code_speak.binary
    if not len(config.code_speak.binary):
        binary = "none"
    binary = Prompt.ask("[bold]>[/bold]", default=config.code_speak.binary)
    config.code_speak.binary = binary
    time.sleep(1)

    # configure push-to-talk key
    print_option_header(
        console, "push_to_talk_key", "key to initialize recording session", config.code_speak.push_to_talk_key
    )
    captured_key = capture_key(console, "press your desired PTT key")
    if captured_key:
        config.code_speak.push_to_talk_key = captured_key
    time.sleep(1)

    # configure push-to-talk key delay
    print_option_header(
        console,
        "push_to_talk_key_delay",
        "execution delay after PTT key press (helps prevent mistypes)",
        f"{config.code_speak.push_to_talk_key_delay} seconds",
    )
    console.print(
        f"\n[bold][blue]>[/blue][/bold] [white]enter delay in seconds {OR_ENTER}[/white]"
    )
    delay = FloatPrompt.ask("[bold]>[/bold]", default=config.code_speak.push_to_talk_key_delay)
    config.code_speak.push_to_talk_key_delay = delay
    time.sleep(1)

    # configure escape key
    print_option_header(
        console,
        "escape_key",
        "key to escape current recording session without outputting transcription",
        str(config.code_speak.escape_key),
    )
    captured_escape_key = capture_key(console, "press your desired escape key")
    if captured_escape_key:
        config.code_speak.escape_key = captured_escape_key
    time.sleep(1)

    # configure recording indicator
    print_option_header(
        console,
        "recording_indicator",
        "character/word output when recording starts",
        config.code_speak.recording_indicator,
    )
    console.print(
        f"\n[bold][blue]>[/blue][/bold] [white]enter new indicator {OR_ENTER}[/white]"
    )
    new_indicator = Prompt.ask("[bold]>[/bold]", default=config.code_speak.recording_indicator)
    if new_indicator:
        config.code_speak.recording_indicator = new_indicator
    time.sleep(1)

    # configure delete keywords
    print_option_header(
        console,
        "delete_keywords",
        "words/phrases that, when detected, will delete previous output",
        str(config.code_speak.delete_keywords)
    )
    if isinstance(config.code_speak.delete_keywords, bool):
        console.print(
            "\n[bold][blue]>[/blue][/bold] [white]enable delete keywords? [dim](true/false)[/dim][/white]"
        )
        use_delete_keywords = Confirm.ask("[bold]>[/bold]", default=config.code_speak.delete_keywords)
        config.code_speak.delete_keywords = use_delete_keywords
    else:
        # if it's a list, show current keywords and allow editing
        console.print(
            "\n[bold][blue]>[/blue][/bold] [white]enter comma-separated delete keywords "
            "[dim](or 'true'/'false' for default behavior)[/dim][/white]"
        )
        keywords_input = Prompt.ask(
            "[bold]>[/bold]",
            default=(
                ",".join(config.code_speak.delete_keywords)
                if isinstance(config.code_speak.delete_keywords, list)
                else str(config.code_speak.delete_keywords)
            ),
        )
        if keywords_input.lower() in ["true", "false"]:
            config.code_speak.delete_keywords = keywords_input.lower() == "true"
        else:
            config.code_speak.delete_keywords = [
                kw.strip() for kw in keywords_input.split(",") if kw.strip()
            ]
    time.sleep(1)

    # configure fast delete
    print_option_header(
        console,
        "fast_delete",
        "use multiple backspaces with pyautogui.press - faster but less accurate",
        str(config.code_speak.fast_delete),
    )
    console.print(
        "\n[bold][blue]>[/blue][/bold] [white]enable fast delete mode? [dim](true/false)[/dim][/white]"
    )
    fast_delete = Confirm.ask("[bold]>[/bold]", default=config.code_speak.fast_delete)
    config.code_speak.fast_delete = fast_delete
    time.sleep(1)

    # configure strip whitespace
    print_option_header(
        console,
        "strip_whitespace",
        "removes extra whitespace (an extra space is always added to end)",
        str(config.code_speak.strip_whitespace),
    )
    console.print(
        "\n[bold][blue]>[/blue][/bold] [white]enable whitespace stripping? [dim](true/false)[/dim][/white]"
    )
    strip_whitespace = Confirm.ask("[bold]>[/bold]", default=config.code_speak.strip_whitespace)
    config.code_speak.strip_whitespace = strip_whitespace
    time.sleep(1)

    # configure pyautogui interval
    print_option_header(
        console,
        "pyautogui_interval",
        "interval between each keypress - increase if experiencing typing/output issues",
        f"{config.code_speak.pyautogui_interval} seconds",
    )
    console.print(
        f"\n[bold][blue]>[/blue][/bold] [white]enter interval in seconds {OR_ENTER}[/white]"
    )
    interval = FloatPrompt.ask("[bold]>[/bold]", default=config.code_speak.pyautogui_interval)
    config.code_speak.pyautogui_interval = interval
    time.sleep(1)

    # configure language
    language = config.realtime_stt.language
    if not language:
        language = "auto"
    print_option_header(console, "language", "speech recognition language", language)
    console.print("- [bold]options[/bold]: en, es, fr, de, it, pt, ru, ja, ko, zh, auto")
    console.print(f"\n[bold][blue]>[/blue][/bold] [white]enter language code {OR_ENTER}[/white]")
    language = Prompt.ask("[bold]>[/bold]", default=config.realtime_stt.language)
    config.realtime_stt.language = language
    time.sleep(1)

    # configure model size
    model = config.realtime_stt.model
    if not model:
        model = "base"
    print_option_header(console, "model", "speech recognition model size", model)
    console.print(
        "- [bold]options[/bold]: tiny (fastest, cpu), base (balanced), small (better accuracy), large (best accuracy)"
    )
    console.print(
        f"\n[bold][blue]>[/blue][/bold] [white]enter model size {OR_ENTER}[/white]"
    )
    model = Prompt.ask("[bold]>[/bold]", default=config.realtime_stt.model, choices=VALID_MODELS)
    config.realtime_stt.model = model
    time.sleep(1)

    # save configuration
    try:
        config_manager.save_config(config)
        console.print(
            f"\n[bold][cyan]Configuration Saved:[/cyan][/bold] {config_manager.config_path}"
        )
        console.print("\n[bold][cyan]>> code_speak[/cyan][/bold]")
        console.print(f"  binary                 : [blue]{config.code_speak.binary}[/blue]")
        console.print(f"  push_to_talk_key       : [blue]{config.code_speak.push_to_talk_key}[/blue]")
        console.print(
            f"  push_to_talk_key_delay : [blue]{config.code_speak.push_to_talk_key_delay}[/blue]s"
        )
        console.print(f"  escape_key             : [blue]{config.code_speak.escape_key}[/blue]")
        console.print(
            f"  recording_indicator    : [blue]{config.code_speak.recording_indicator}[/blue]"
        )
        console.print(
            f"  delete_keywords        : [blue]{config.code_speak.delete_keywords}[/blue]"
        )
        console.print(f"  fast_delete            : [blue]{config.code_speak.fast_delete}[/blue]")
        console.print(f"  strip_whitespace       : [blue]{config.code_speak.strip_whitespace}[/blue]")
        console.print(
            f"  pyautogui_interval     : [blue]{config.code_speak.pyautogui_interval}[/blue]s"
        )
        console.print("\n[bold][cyan]>> realtime_stt[/cyan][/bold]")
        console.print(f"  language               : [blue]{config.realtime_stt.language}[/blue]")
        console.print(f"  model                  : [blue]{config.realtime_stt.model}[/blue]\n")
    except Exception as e:
        console.print(f"[red][bold][ERROR][/bold] Failed to save configuration: {e}[/red]")
        sys.exit(1)


def test_voice(config_path: str | None = None) -> None:
    """Test voice input functionality"""
    console = Console()
    console.print("[yellow][bold]Voice Input Test[/bold][/yellow]")
    console.print("[yellow]> This will test your microphone and transcription[/yellow]")
    console.print("[yellow]> Press ctrl+c to stop testing[/yellow]\n")

    def handle_test_text(text: str) -> None:
        console.print(f"[green]Transcribed:[/green] {text}")

    voice_input = None
    try:
        voice_input = VoiceInput(config_path)
        voice_input.start(handle_test_text)

        console.print("\n[yellow][bold]Instructions (ctrl+c to stop test)[/bold][/yellow]")
        console.print(
            f"[yellow]  1. Press your PTT key {voice_input.config.code_speak.push_to_talk_key}[/yellow]"
        )
        console.print("[yellow]  2. Speak[/yellow]")
        console.print("[yellow]  3. Press your PTT key again[/yellow]")
        console.print(
            "[yellow]  4. If successful, the transcribed text should then be displayed[/yellow]\n"
        )

        # keep running until interrupted
        try:
            while True:
                input()  # wait for Enter or Ctrl+C
        except KeyboardInterrupt:
            pass

    except Exception as e:
        console.print(f"[red][bold][ERROR][/bold] starting voice input: {e}[/red]")
        sys.exit(1)
    finally:
        if voice_input:
            voice_input.stop()
        console.print("\n[yellow]Test completed[/yellow]")


def show_config(config_path: str | None = None) -> None:
    """Display current configuration"""
    console = Console()
    config_manager = ConfigManager(Path(config_path) if config_path else None)

    try:
        config = config_manager.load_config()

        # convert to JSON for display
        config_dict = {
            "realtime_stt": config.realtime_stt.__dict__,
            "code_speak": config.code_speak.__dict__,
        }

        console.print(
            f"[bold]Configuration File:[/bold] {config_manager.config_path}\n\n"
            f"\n{json.dumps(config_dict, indent=2)}\n"
        )

    except Exception as e:
        console.print(f"[red][bold][ERROR][/bold] loading configuration: {e}[/red]")
        sys.exit(1)


def run_with_bin(
 bin_args: list,
 bin_cli: str | None = None,
 config_path: str | None = None,
 log_file: str | None = None
) -> int:
    """
    Run bin/executable with voice integration

    Args:
        bin_args: Arguments to pass to bin command.
        bin_cli: Override executable from command line.
        config_path: Path to config file.
        log_file: Path to log file for transcriptions.

    Returns:
        Exit code from bin execution.
    """
    console = Console()

    console.print("\n[bold][red]◉[/red] [cyan]Code Speak Init[/cyan][/bold]\n")

    voice_enabled = False
    voice_input = None

    config_manager = ConfigManager(Path(config_path) if config_path else None)
    config = config_manager.load_config()
    executable = bin_cli or config.code_speak.binary
    log = log_file if log_file else config.code_speak.log
    log_print = None if executable else True

    def log_format(content: str = "", stylize: bool = False) -> str:
        """Format content for markdown logging"""
        timestamp = datetime.now().isoformat(timespec='seconds')
        if stylize:
            return f"[dim][white]## [/white][blue]{timestamp}[/blue][/dim]\n{content}\n\n"
        else:
            return f"## {timestamp}\n{content}\n\n"

    def handle_log(text: str) -> None:
        """Handle logging transcribed text"""
        if log:
            try:
                log_entry = log_format(text)
                with open(log, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except Exception as e:
                console.print(f"[red][bold][ERROR][/bold] writing to log file: {e}[/red]")
        if log_print:
            # show styled version in terminal
            console.print(log_format(text, stylize=True), end='')

    def handle_type(text: str) -> None:
        """Handle typing transcribed text"""
        try:
            # for whatever reason, adding an extra space at the end resolves
            # a handful of pyautogui.typewrite glitches/hiccups
            pyautogui.typewrite(text + " ")
        except Exception as e:
            console.print(f"[red][bold][ERROR][/bold] typing text: {e}[/red]")

    def handle_voice_text(text: str) -> None:
        """Handle transcribed text by typing it"""
        handle_log(text)
        handle_type(text)

    # try to start voice input
    try:
        voice_input = VoiceInput(config_path)
        voice_input.start(handle_voice_text)
        voice_enabled = True

    except Exception as e:
        console.print(f"[yellow]Could not start voice input: {e}[/yellow]")
        console.print("[yellow]Continuing without voice support...[/yellow]")

    cmd = []
    try:
        # build command and run binary
        cmd = [executable, *bin_args]
        console.print("\n[cyan][bold]> {}[/cyan]".format(" ".join(cmd)))
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


def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Code Speak Voice Input",
        add_help=False,  # we'll handle help ourselves
    )

    # our specific arguments
    parser.add_argument("-b", "--binary", help="Executable to launch with voice input (default from config)")
    parser.add_argument("-c", "--config", help="Path to configuration file")
    parser.add_argument("-l", "--log", help="Path to log file for voice transcriptions (append log)")
    parser.add_argument("-s", "--setup", action="store_true", help="Configure voice settings")
    parser.add_argument("-t", "--test", action="store_true", help="Test voice input functionality")
    parser.add_argument("--config-show", action="store_true", help="Show current configuration")

    # parse known args to separate ours from executable tool's
    our_args, bin_args = parser.parse_known_args()

    # handle our specific commands
    if our_args.setup:
        setup_voice(our_args.config)
        return 0

    if our_args.test:
        test_voice(our_args.config)
        return 0

    if our_args.config_show:
        show_config(our_args.config)
        return 0

    # if no specific command, run with executable tool integration
    return run_with_bin(bin_args, our_args.binary, our_args.config, our_args.log)


if __name__ == "__main__":
    sys.exit(main())
