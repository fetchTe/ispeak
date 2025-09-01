import argparse
import sys
from pathlib import Path

from rich.console import Console

from .cli_commands import setup_voice, show_config, test_voice
from .config import ConfigManager
from .core import run_with_bin


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
    parser.add_argument("-n", "--no-typing", action="store_true", help="Disable typing output and indicator")
    parser.add_argument("-s", "--setup", action="store_true", help="Configure voice settings")
    parser.add_argument("-t", "--test", action="store_true", help="Test voice input functionality")
    parser.add_argument("--config-show", action="store_true", help="Show current configuration")

    # parse known args to separate ours from executable tool's
    our_args, bin_args = parser.parse_known_args()

    # load config once and apply CLI overrides
    config_manager = ConfigManager(Path(our_args.config) if our_args.config else None)
    config = config_manager.load_config()

    # apply CLI overrides
    if our_args.log:
        config.code_speak.log = our_args.log
    if our_args.no_typing:
        config.code_speak.no_typing = our_args.no_typing

    # validate configuration
    errors = config_manager.validate_config(config)
    if errors:
        console = Console()
        console.print("\n[red][bold]ERROR[/bold] Configuration validation errors:[/red]")
        for error in errors:
            print(f"  - {error}")
        console.print("[yellow][bold]NOTE[/bold] Using default values for invalid settings[/yellow]")

    # handle our specific commands
    if our_args.setup:
        setup_voice(config_manager)
        return 0

    if our_args.test:
        test_voice(config)
        return 0

    if our_args.config_show:
        show_config(config_manager)
        return 0

    # if no specific command, run with executable tool integration
    return run_with_bin(bin_args, our_args.binary, config)


if __name__ == "__main__":
    sys.exit(main())
