import json
import re
from pathlib import Path
from typing import Any

from ..base import ISpeakPlugin


class ReplacePlugin(ISpeakPlugin):
    """Regex-based text replacement plugin"""

    def __init__(self) -> None:
        self.rules: list[tuple[re.Pattern, str]] = []

    @property
    def name(self) -> str:
        return "replace"

    def configure(self, settings: dict[str, Any]) -> None:
        """
        Configure replacement rules from settings

        Args:
            settings: Dict of pattern/replacement pairs or list of file paths
        """
        self.rules.clear()
        if settings:
            self._load_rules(settings)

    def process(self, text: str) -> str:
        """
        Apply all replacement rules to text

        Args:
            text: Input text to process
        Returns:
            Text with all replacements applied
        """
        if not isinstance(text, str):
            return ""

        result = text

        for pattern, replacement in self.rules:
            try:
                result = pattern.sub(replacement, result)
            except re.error as e:
                print(f"Warning: Replacement failed for pattern {pattern.pattern}: {e}")
                continue

        return result

    def _load_rules(self, config: dict[str, str] | list[str]) -> None:
        """Load replacement rules from config"""
        if isinstance(config, dict):
            # direct pattern/replacement pairs
            self._parse_rule_dict(config)
        elif isinstance(config, list):
            # list of file paths containing rule dicts
            for file_path in config:
                self._load_rules_from_file(file_path)

    def _load_rules_from_file(self, file_path: str) -> None:
        """Load replacement rules from JSON file"""
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"Warning: Replace rules file not found: {file_path}")
                return

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                if "replace" in data and isinstance(data["replace"], dict):
                    self._parse_rule_dict(data["replace"])
                else:
                    self._parse_rule_dict(data)
            else:
                print(f"Warning: Invalid replace rules format in {file_path}")
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load replace rules from {file_path}: {e}")

    def _parse_rule_dict(self, rules: dict[str, str]) -> None:
        """Parse dictionary of pattern/replacement pairs into compiled regex rules"""
        for pattern, replacement in rules.items():
            try:
                compiled_pattern = self._compile_pattern(pattern)
                self.rules.append((compiled_pattern, replacement))
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern}': {e}")

    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """
        Compile regex pattern, handling both simple strings and /pattern/flags format

        Args:
            pattern: Pattern string, either plain text or /regex/flags format
        Returns:
            Compiled regex pattern object
        """
        # check if pattern is in /pattern/flags format
        if pattern.startswith("/") and pattern.count("/") >= 2:
            # parse /pattern/flags format
            parts = pattern.split("/")
            if len(parts) >= 3:
                regex_pattern = "/".join(parts[1:-1])  # handle patterns with / inside
                flags_str = parts[-1]

                # convert flag characters to re flags
                flags = 0
                if "i" in flags_str:
                    flags |= re.IGNORECASE
                if "m" in flags_str:
                    flags |= re.MULTILINE
                if "s" in flags_str:
                    flags |= re.DOTALL
                if "x" in flags_str:
                    flags |= re.VERBOSE

                return re.compile(regex_pattern, flags)

        # treat as literal pattern if not in /pattern/flags format
        # but still allow regex metacharacters to work
        return re.compile(pattern)

    def add_rule(self, pattern: str, replacement: str) -> None:
        r"""
        Add a new replacement rule

        Args:
            pattern: Regex pattern to match
            replacement: Replacement string (can include \g<n> groups)
        """
        try:
            compiled_pattern = self._compile_pattern(pattern)
            self.rules.append((compiled_pattern, replacement))
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pattern}': {e}")

    def clear_rules(self) -> None:
        """Clear all replacement rules"""
        self.rules.clear()

    def get_rules_count(self) -> int:
        """Get number of active replacement rules"""
        return len(self.rules)
