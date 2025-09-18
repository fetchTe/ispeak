# help defined here to avoid +1s load time
import sys
from importlib.metadata import version

try:
    __version__ = version("ispeak")
except Exception:
    __version__ = "?.?.?"

# ansi
CYAN = "\033[96m"
BLUE = "\033[94m"
D_WHITE = "\033[37;2m"
B_WHITE = "\033[1;97m"
RESET = "\033[0m"
# help messages
HELP_BINARY = "Executable to launch with voice input (default: none)"
HELP_CONFIG = "Path to configuration file"
HELP_LOG_FILE = "Path to voice transcription append log file"
HELP_NO_OUTPUT = "Disables all output/actions - typing, copying, and record indicator"
HELP_SETUP = "Configure voice settings"
HELP_TEST = "Test voice input functionality"
HELP_COPY = "Use the 'clipboard' to copy instead of the 'keyboard' to type the output"
HELP_CONFIG_SHOW = "Print current configuration"
HELP_VERSION_SHOW = "Print current version"


def print_help() -> None:
    help_text = f"""{D_WHITE}#{RESET} {B_WHITE}USAGE{RESET} {D_WHITE}(v{__version__}){RESET}
  {CYAN}ispeak{RESET} {D_WHITE}[{RESET}{BLUE}options{RESET}{D_WHITE}...]{RESET}

{D_WHITE}#{RESET} {B_WHITE}OPTIONS{RESET}
  {D_WHITE}-{RESET}{BLUE}b{RESET}{D_WHITE}, --{RESET}{BLUE}binary{RESET}      {HELP_BINARY}
  {D_WHITE}-{RESET}{BLUE}c{RESET}{D_WHITE}, --{RESET}{BLUE}config{RESET}      {HELP_CONFIG}
  {D_WHITE}-{RESET}{BLUE}l{RESET}{D_WHITE}, --{RESET}{BLUE}log-file{RESET}    {HELP_LOG_FILE}
  {D_WHITE}-{RESET}{BLUE}n{RESET}{D_WHITE}, --{RESET}{BLUE}no-output{RESET}   {HELP_NO_OUTPUT}
  {D_WHITE}-{RESET}{BLUE}p{RESET}{D_WHITE}, --{RESET}{BLUE}copy{RESET}        {HELP_COPY}
  {D_WHITE}-{RESET}{BLUE}s{RESET}{D_WHITE}, --{RESET}{BLUE}setup{RESET}       {HELP_SETUP}
  {D_WHITE}-{RESET}{BLUE}t{RESET}{D_WHITE}, --{RESET}{BLUE}test{RESET}        {HELP_TEST}
  {D_WHITE}--{RESET}{BLUE}config-show{RESET}     {HELP_CONFIG_SHOW}
  {D_WHITE}--{RESET}{BLUE}version{RESET}         {HELP_VERSION_SHOW}"""
    print(help_text)


def main() -> int:
    # run help, unless --binary is present as we assume/apply the help flag to binary instead
    is_bin = "--binary" in sys.argv or "-b" in sys.argv
    if not is_bin and ("-h" in sys.argv or "--help" in sys.argv):
        print_help()
        return 0
    elif not is_bin and ("--version" in sys.argv):
        print(__version__)
        return 0
    else:
        from .cli_parse import cli_parse

        sys.exit(cli_parse())


if __name__ == "__main__":
    sys.exit(main())
