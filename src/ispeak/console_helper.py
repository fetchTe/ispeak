"""
ANSI color utilities with rich-like markup parsing for console output
example: log("[blue]example[/blue]")
"""

from typing import Any

# aNSI color and style codes
COLORS = {
    # colors
    "black": "\033[30m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "magenta": "\033[35m",
    "red": "\033[31m",
    "white": "\033[37m",
    "yellow": "\033[33m",
    # font
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


def _parse_markup(text: str) -> str:
    """
    Parse Rich-like markup and convert to ANSI codes - handles nested tags via tracking active

    Args:
        text: Text with Rich markup like [red], [bold], etc
    Returns:
        Text with ANSI escape codes
    """
    # stack to track active styles
    active_styles = []
    result = ""
    i = 0

    while i < len(text):
        if text[i] == "[" and i + 1 < len(text):
            # find closing bracket
            end_bracket = text.find("]", i + 1)
            if end_bracket != -1:
                tag_content = text[i + 1 : end_bracket]

                # check if this is a closing tag
                if tag_content.startswith("/"):
                    tag_name = tag_content[1:] if len(tag_content) > 1 else None
                    # only process if it's a valid closing tag
                    if tag_name and tag_name in COLORS:
                        if tag_name in active_styles:
                            active_styles.remove(tag_name)
                        # apply reset and then reapply remaining styles
                        result += COLORS["reset"]
                        for style in active_styles:
                            result += COLORS[style]
                        i = end_bracket + 1
                        continue
                    elif not tag_name:  # [/] closes all
                        active_styles.clear()
                        result += COLORS["reset"]
                        i = end_bracket + 1
                        continue
                # check if this is a valid opening tag
                elif tag_content in COLORS:
                    active_styles.append(tag_content)
                    result += COLORS[tag_content]
                    i = end_bracket + 1
                    continue

                # if we get here, it's not a valid tag, treat as literal text
                result += text[i]
                i += 1
            else:
                # no closing bracket found, treat as literal
                result += text[i]
                i += 1
        else:
            result += text[i]
            i += 1

    # add final reset to ensure clean state
    if active_styles:
        result += COLORS["reset"]

    return result


def log(text: str = "", **kwargs: Any) -> None:
    """
    Print text with Rich-like markup support

    Args:
        text: Text to print, may contain markup
        **kwargs: Additional keyword arguments passed to print()
    """
    parsed_text = _parse_markup(str(text))
    print(parsed_text, **kwargs)


def log_warn(message: str, **kwargs: Any) -> None:
    """
    Print warning message with consistent formatting

    Args:
        message: Warning message to display
        **kwargs: Additional keyword arguments passed to print()
    """
    log(f"[bold][yellow][WARN][/yellow][/bold] {message}", **kwargs)


def log_erro(message: str, **kwargs: Any) -> None:
    """
    Print error message with consistent formatting

    Args:
        message: Error message to display
        **kwargs: Additional keyword arguments passed to print()
    """
    log(f"[bold][red][ERRO][/red][/bold] {message}", **kwargs)


def log_info(message: str, **kwargs: Any) -> None:
    """
    Print info message with consistent formatting

    Args:
        message: Info message to display
        **kwargs: Additional keyword arguments passed to print()
    """
    log(f"[bold][blue][INFO][/blue][/bold] {message}", **kwargs)


def ask(prompt: str | None = None, default: str | None = None, choices: list[str] | None = None) -> str:
    """
    Ask for user input with optional default and validation

    Args:
        prompt: Prompt text to display
        default: Default value if user presses enter
        choices: List of valid choices for validation
    Returns:
        User input string
    """
    while True:
        prompt = prompt if prompt else "[bold]>[/bold]"
        if default is not None:
            display_prompt = f"{prompt} ({default}) "
        else:
            display_prompt = f"{prompt} "

        log(display_prompt, end="")
        user_input = input().strip()

        # use default if empty input
        if not user_input and default is not None:
            return default

        # validate choices if provided
        if choices is not None and user_input not in choices:
            log(f"[red]Invalid choice. Please select from: {', '.join(choices)}[/red]")
            continue

        return user_input


def confirm(prompt: str | None = None, default: bool = True) -> bool:
    """
    Ask for yes/no confirmation

    Args:
        prompt: Prompt text to display
        default: Default value if user presses enter
    Returns:
        Boolean result of confirmation
    """
    default_text = "Y/n" if default else "y/N"

    while True:
        prompt = prompt if prompt else "[bold]>[/bold]"
        log(f"{prompt} ({default_text}) ", end="")
        user_input = input().strip().lower()

        if not user_input:
            return default

        if user_input in ("y", "yes", "true"):
            return True
        elif user_input in ("n", "no", "false"):
            return False
        else:
            log("[red]Please enter y/yes/true or n/no/false[/red]")


def float_ask(prompt: str | None = None, default: float | None = None) -> float:
    """
    Ask for float input with validation

    Args:
        prompt: Prompt text to display
        default: Default value if user presses enter
    Returns:
        Float value from user input
    """
    while True:
        prompt = prompt if prompt else "[bold]>[/bold]"
        if default is not None:
            display_prompt = f"{prompt} ({default}) "
        else:
            display_prompt = f"{prompt} "

        log(display_prompt, end="")
        user_input = input().strip()

        if not user_input and default is not None:
            return default

        try:
            return float(user_input)
        except ValueError:
            log("[red]Please enter a valid number[/red]")
