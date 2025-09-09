import json
import sys
import time
from typing import Literal

import pynput.keyboard
from pynput.keyboard import Key, KeyCode

from .config import VALID_MODELS, AppConfig, ConfigManager, key_to_str
from .console_helper import ask, confirm, float_ask, log, log_erro
from .core import VoiceInput

OR_ENTER = "[dim](press 'enter' to keep current)[/dim]"
SINGLE_KEY_ONLY = (
    "[bold][yellow]!!~~~>>[/yellow]: [white]Only one key permitted[/bold];"
    " to include modifier keys such as Ctrl or Alt, adjust the config by hand with"
    " the notation of: <alt>+<...>[/white]"
)
CWAIT = 0.5  # give the key capture a bit of room to breath


def print_option_header(option_name: str, info: str, current_value: str) -> None:
    """Helper to print consistent option headers"""
    log(f"\n[white][dim]{'-' * 90!s}[/dim][/white]")
    log(f"[bold]option [/bold]: [yellow][bold]{option_name}[/bold][/yellow]")
    log(f"[bold]info   [/bold]: {info}")
    log(f"[bold]current[/bold]: {current_value}")


def capture_key(prompt_text: str) -> str | None:
    """Helper to capture a single key press"""
    log(f"\n[bold][blue]>[/blue][/bold] [white]{prompt_text} {OR_ENTER}[/white]")

    captured_key = None

    def on_key_press(key: Key | KeyCode | None) -> None:
        nonlocal captured_key
        captured_key = key_to_str(key)
        listener.stop()
        if captured_key == "enter":
            log("\n[white][dim]>[/dim][/white] skipped... keeping current")
            return
        log(f"\n[bold][green]> key:[/green][/bold] {captured_key}")

    with pynput.keyboard.Listener(on_press=on_key_press, suppress=True) as listener:
        try:
            listener.wait()
            listener.join()  # wait for key press
        finally:
            listener.stop()
        return captured_key if captured_key != "enter" else None


def setup_voice(config_manager: ConfigManager) -> None:
    """Interactive configuration for voice settings"""
    config = config_manager.load_config()

    log("\n[bold][red]◉[/red] [green]ispeak setup[/green][/bold]")
    log(f"[bold][blue]> loading defaults via:[/blue] {config.config_path}[/bold]")
    time.sleep(CWAIT)

    binary = config.ispeak.binary
    if not binary:
        binary = "none"
    print_option_header("binary", "default executable to launch with voice input", binary)
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter executable binary/program, 'none', {OR_ENTER}[/white]")
    binary = ask(default=binary)
    # in case, literal 'none', cuz ya know
    if binary in ("none", "'none'", '"none"'):
        binary = None
    config.ispeak.binary = binary
    time.sleep(CWAIT)

    # configure delete key
    print_option_header(
        "delete_key",
        "key to trigger deletion of previous input via backspace",
        str(config.ispeak.delete_key),
    )
    log(SINGLE_KEY_ONLY)
    captured_delete_key = capture_key("press your desired 'delete' key")
    if captured_delete_key:
        config.ispeak.delete_key = captured_delete_key
    time.sleep(CWAIT)

    # configure delete keywords
    del_def = ["delete", "undo"]
    del_cur = config.ispeak.delete_keyword
    del_arr = del_cur if del_cur else del_def
    del_arr = del_def if del_arr else del_arr
    del_str = ", ".join(del_arr)
    print_option_header(
        "delete_keyword",
        "words/phrases that, when detected, will delete previous output",
        del_str,
    )
    log(
        "\n[bold][blue]>[/blue][/bold] [white]enter comma-separated delete keywords "
        "[dim](or 'true'/'false' for default behavior)[/dim][/white]"
    )
    keywords_input = ask(default=del_str)
    del_nxt = ""
    if keywords_input.lower() in ["true", "false"]:
        config.ispeak.delete_keyword = keywords_input.lower() == "true"
        del_nxt = keywords_input[0]
    else:
        config.ispeak.delete_keyword = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        del_nxt = ", ".join(config.ispeak.delete_keyword)
    time.sleep(CWAIT)

    # configure escape key
    print_option_header(
        "escape_key",
        "key to escape current recording session without outputting transcription",
        str(config.ispeak.escape_key),
    )
    log(SINGLE_KEY_ONLY)
    captured_escape_key = capture_key("press your desired 'escape' key")
    if captured_escape_key:
        config.ispeak.escape_key = captured_escape_key
    time.sleep(CWAIT)

    # configure push-to-talk key
    print_option_header("push_to_talk_key", "key to initialize recording session", config.ispeak.push_to_talk_key)
    log(SINGLE_KEY_ONLY)
    captured_key = capture_key("press your desired PTT key")
    if captured_key:
        config.ispeak.push_to_talk_key = captured_key
    time.sleep(CWAIT)

    # configure push-to-talk key delay
    print_option_header(
        "push_to_talk_key_delay",
        "execution delay after PTT key press (helps prevent mistypes)",
        f"{config.ispeak.push_to_talk_key_delay} seconds",
    )
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter delay in seconds {OR_ENTER}[/white]")
    delay = float_ask(default=config.ispeak.push_to_talk_key_delay)
    config.ispeak.push_to_talk_key_delay = delay
    time.sleep(CWAIT)

    # configure recording indicator
    print_option_header(
        "recording_indicator",
        "character/word output when recording starts",
        config.ispeak.recording_indicator,
    )
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter new indicator {OR_ENTER}[/white]")
    new_indicator = ask(default=config.ispeak.recording_indicator)
    if new_indicator:
        config.ispeak.recording_indicator = new_indicator
    time.sleep(CWAIT)

    # configure delete keywords
    output = config.ispeak.output
    output_str = output if output else "false"
    print_option_header(
        "output",
        "mode of output, either 'keyboard' (type), 'clipboard' (copy), or 'false' for none",
        output_str,
    )
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter 'keyboard', 'clipboard', 'false' {OR_ENTER}[/white]")
    ouput = ask(default=output_str).lower()
    if ouput == "false":
        config.ispeak.output = False
    elif ouput == "keyboard" or ouput == "clipboard":
        config.ispeak.output = ouput
    else:
        config.ispeak.output = "keyboard"
    ouput = config.ispeak.output
    time.sleep(CWAIT)

    # configure strip whitespace
    print_option_header(
        "strip_whitespace",
        "removes extra whitespace (an extra space is always added to end)",
        str(config.ispeak.strip_whitespace),
    )
    log("\n[bold][blue]>[/blue][/bold] [white]enable whitespace stripping? [dim](true/false)[/dim][/white]")
    strip_whitespace = confirm("[bold]>[/bold]", default=config.ispeak.strip_whitespace)
    config.ispeak.strip_whitespace = strip_whitespace
    time.sleep(CWAIT)

    # configure language
    language = config.stt.language
    if not language:
        language = "auto"
    print_option_header("language", "speech recognition language", language)
    log("- [bold]options[/bold]: en, es, fr, de, it, pt, ru, ja, ko, zh, auto")
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter language code {OR_ENTER}[/white]")
    language = ask(default=config.stt.language)
    config.stt.language = language
    time.sleep(CWAIT)

    # configure model size
    model = config.stt.model
    if not model:
        model = "base"
    print_option_header("model", "speech recognition model size", model)
    log("- [bold]options[/bold]: tiny (fastest, cpu), base (balanced), small (better accuracy), large (best accuracy)")
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter model size {OR_ENTER}[/white]")
    model = ask(default=config.stt.model, choices=VALID_MODELS)
    config.stt.model = model
    time.sleep(CWAIT)

    # configure save format
    print_option_header("save", "format to save this config file as", "json")
    log("- [bold]options[/bold]: json or toml")
    log(f"\n[bold][blue]>[/blue][/bold] [white]enter format {OR_ENTER}[/white]")
    save_fmt: Literal["json", "toml"] = ask(default="json", choices=["json", "toml"])  # type: ignore
    time.sleep(CWAIT)

    # save configuration
    try:
        save_path = config_manager.save_config(config, save_fmt)
        log(f"\n[bold][cyan]Configuration Saved:[/cyan][/bold] {save_path}")
        log("\n[bold][cyan]>> ispeak[/cyan][/bold]")
        log(f"  binary                 : [blue]{config.ispeak.binary}[/blue]")
        log(f"  delete_key             : [blue]{config.ispeak.delete_key}[/blue]")
        log(f"  delete_keyword         : [blue]{del_nxt}[/blue]")
        log(f"  escape_key             : [blue]{config.ispeak.escape_key}[/blue]")
        log(f"  output                 : [blue]{config.ispeak.output!s}[/blue]")
        log(f"  push_to_talk_key       : [blue]{config.ispeak.push_to_talk_key}[/blue]")
        log(f"  push_to_talk_key_delay : [blue]{config.ispeak.push_to_talk_key_delay}[/blue]s")
        log(f"  recording_indicator    : [blue]{config.ispeak.recording_indicator}[/blue]")
        log(f"  strip_whitespace       : [blue]{config.ispeak.strip_whitespace}[/blue]")
        log("\n[bold][cyan]>> model[/cyan][/bold]")
        log(f"  language               : [blue]{config.stt.language}[/blue]")
        log(f"  model                  : [blue]{config.stt.model}[/blue]\n")
    except Exception as e:
        log_erro(f"Failed to save configuration: {e}")
        sys.exit(1)


def test_voice(config: AppConfig) -> None:
    """Test voice input functionality"""
    log("[yellow][bold]Voice Input Test[/bold][/yellow]")
    log("[yellow]> This will test your microphone and transcription[/yellow]")
    log("[yellow]> Press ctrl+c to stop testing[/yellow]\n")

    def handle_test_text(text: str) -> None:
        log(f"[green]Transcribed:[/green] {text}")

    voice_input = None
    try:
        voice_input = VoiceInput(config)
        voice_input.start(handle_test_text)

        log("\n[yellow][bold]Instructions (ctrl+c to stop test)[/bold][/yellow]")
        log(f"[yellow]  1. Press your PTT key {voice_input.config.ispeak.push_to_talk_key}[/yellow]")
        log("[yellow]  2. Speak[/yellow]")
        log("[yellow]  3. Press your PTT key again[/yellow]")
        log("[yellow]  4. If successful, the transcribed text should then be displayed[/yellow]\n")

        # keep running until interrupted
        try:
            while True:
                input()  # wait for Enter or Ctrl+C
        except KeyboardInterrupt:
            pass

    except Exception as e:
        log_erro(f"starting voice input: {e}")
        sys.exit(1)
    finally:
        if voice_input:
            voice_input.stop()
        log("\n[yellow]Test completed[/yellow]")


def show_config(config_manager: ConfigManager) -> None:
    """Display current configuration"""
    try:
        config = config_manager.load_config()

        # convert to JSON for display
        config_dict = {
            "model": config.stt.__dict__,
            "ispeak": config.ispeak.__dict__,
        }

        log(f"[bold]Configuration File:[/bold] {config_manager.config_path}\n\n\n{json.dumps(config_dict, indent=2)}\n")

    except Exception as e:
        log_erro(f"loading configuration: {e}")
        sys.exit(1)
