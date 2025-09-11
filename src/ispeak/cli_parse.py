import argparse
from pathlib import Path
from typing import Literal

from .cli_commands import setup_voice, show_config, test_voice
from .config import ConfigManager
from .console_helper import log_erro, log_warn
from .core import runner


def cli_parse() -> int:
    """Main CLI parse entry point"""
    parser = argparse.ArgumentParser(
        description="ispeak voice input",
        add_help=False,  # we'll handle help ourselves
    )

    # our specific arguments
    parser.add_argument("-b", "--binary")
    parser.add_argument("-c", "--config")
    parser.add_argument("-l", "--log-file")
    parser.add_argument("-n", "--no-output", action="store_true")
    parser.add_argument("-s", "--setup", action="store_true")
    parser.add_argument("-t", "--test", action="store_true")
    parser.add_argument("-p", "--copy", action="store_true")
    parser.add_argument("--config-show", action="store_true")

    # parse known args to separate ours from executable tool's
    our_args, bin_args = parser.parse_known_args()

    # load config once and apply CLI overrides
    config_manager = ConfigManager(Path(our_args.config) if our_args.config else None)
    config = config_manager.load_config()

    # apply CLI overrides
    if our_args.log_file:
        config.ispeak.log_file = our_args.log_file

    # validate configuration
    errors = config_manager.validate_config(config)
    if errors:
        log_erro("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        log_warn("Using default values for invalid settings")

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

    # clip or no output override
    cli_output: Literal["clipboard", False, None] = None
    if our_args.no_output:
        cli_output = False
    elif our_args.copy:
        cli_output = "clipboard"
    if cli_output is not None:
        config.ispeak.output = cli_output

    # if no specific command, run with executable tool integration
    return runner(bin_args, our_args.binary, cli_output, config)
