import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from .cli_commands import setup_voice, show_config, test_voice
from .config import ConfigManager
from .console_helper import log_erro, log_warn
from .core import runner

try:
    __version__ = version("ispeak")
except Exception:
    __version__ = "unknown"

# Shared help text variables
HELP_BINARY = "Executable to launch with voice input (default: none)"
HELP_CONFIG = "Path to configuration file"
HELP_LOG_FILE = "Path to voice transcription append log file"
HELP_NO_OUTPUT = "Disable typing output and record indicator"
HELP_SETUP = "Configure voice settings"
HELP_TEST = "Test voice input functionality"
HELP_CONFIG_SHOW = "Show current configuration"


def print_help() -> None:
    """Print custom help message in specified format with syntax highlighting"""
    # ANSI color codes
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    D_WHITE = "\033[37;2m"
    B_WHITE = "\033[1;97m"
    RESET = "\033[0m"

    help_text = f"""{D_WHITE}#{RESET} {B_WHITE}USAGE{RESET} {D_WHITE}(v{__version__}){RESET}
  {CYAN}ispeak{RESET} {D_WHITE}[{RESET}{BLUE}options{RESET}{D_WHITE}...]{RESET}

{D_WHITE}#{RESET} {B_WHITE}OPTIONS{RESET}
  {D_WHITE}-{RESET}{BLUE}b{RESET}{D_WHITE}, --{RESET}{BLUE}binary{RESET}      {HELP_BINARY}
  {D_WHITE}-{RESET}{BLUE}c{RESET}{D_WHITE}, --{RESET}{BLUE}config{RESET}      {HELP_CONFIG}
  {D_WHITE}-{RESET}{BLUE}l{RESET}{D_WHITE}, --{RESET}{BLUE}log-file{RESET}    {HELP_LOG_FILE}
  {D_WHITE}-{RESET}{BLUE}n{RESET}{D_WHITE}, --{RESET}{BLUE}no-output{RESET}   {HELP_NO_OUTPUT}
  {D_WHITE}-{RESET}{BLUE}s{RESET}{D_WHITE}, --{RESET}{BLUE}setup{RESET}       {HELP_SETUP}
  {D_WHITE}-{RESET}{BLUE}t{RESET}{D_WHITE}, --{RESET}{BLUE}test{RESET}        {HELP_TEST}
  {D_WHITE}--{RESET}{BLUE}config-show{RESET}     {HELP_CONFIG_SHOW}"""
    print(help_text)


def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ispeak voice input",
        add_help=False,  # we'll handle help ourselves
    )

    # our specific arguments
    parser.add_argument("-b", "--binary", help=HELP_BINARY)
    parser.add_argument("-c", "--config", help=HELP_CONFIG)
    parser.add_argument("-l", "--log-file", help=HELP_LOG_FILE)
    parser.add_argument("-n", "--no-output", action="store_true", help=HELP_NO_OUTPUT)
    parser.add_argument("-s", "--setup", action="store_true", help=HELP_SETUP)
    parser.add_argument("-t", "--test", action="store_true", help=HELP_TEST)
    parser.add_argument("--config-show", action="store_true", help=HELP_CONFIG_SHOW)

    # check for help first
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return 0

    # parse known args to separate ours from executable tool's
    our_args, bin_args = parser.parse_known_args()

    # load config once and apply CLI overrides
    config_manager = ConfigManager(Path(our_args.config) if our_args.config else None)
    config = config_manager.load_config()

    # apply CLI overrides
    if our_args.log_file:
        config.ispeak.log_file = our_args.log_file
    if our_args.no_output:
        config.ispeak.no_output = our_args.no_output

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

    # check for help in binary-less mode
    if "--help" in bin_args or "-h" in bin_args:
        executable = our_args.binary or config.ispeak.binary
        if not executable:  # binary-less mode
            print_help()
            return 0

    # if no specific command, run with executable tool integration
    return runner(bin_args, our_args.binary, config)


if __name__ == "__main__":
    sys.exit(main())
