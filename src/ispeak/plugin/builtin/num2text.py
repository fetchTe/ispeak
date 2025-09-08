# dep: https://github.com/savoirfairelinux/num2words
# lic: LGPL-2.1 (included at bottom)
# @NOTE -> using num2text to match text2num
import re
from typing import Any

from ..base import ISpeakPlugin


class Num2TextPlugin(ISpeakPlugin):
    """Convert digits to text numbers with comprehensive options (42 -> forty-two)"""

    def __init__(self) -> None:
        # basic configuration
        self.lang: str = "en"
        self.to: str = "cardinal"  # cardinal, ordinal, ordinal_num, currency, year

        # currency-specific options
        self.currency: str = "USD"  # currency code for currency conversion
        self.cents: bool = True  # whether to include cents verbosely

        # custom options
        self.min: int | float | None = None
        self.max: int | float | None = None
        self.percent: str | None = "percent"  # if '%' percent

        # store any additional language-specific options passed in settings
        self.lang_specific_options: dict[str, Any] = {}

        # internal
        self._num2text = None

    @property
    def name(self) -> str:
        return "num2text"

    @property
    def dependencies(self) -> list[str]:
        return ["num2words"]

    def configure(self, settings: dict[str, Any]) -> None:
        """
        Configure num2words plugin with comprehensive options

        Args:
            settings: Plugin settings including:
                - lang: Language code (default: "en")
                - to: Conversion type ("cardinal", "ordinal", "ordinal_num", "currency", "year")
                - min/max: Value range filtering (custom options)

                Currency options:
                - currency: Currency code (default: "USD")
                - cents: Include cents verbosely (default: True)

                Language-specific options (passed through to num2words):
                - adjective: Use currency adjectives (lang specific)
                - gender: Gender forms (lang specific)
                - prefer: Alternative forms preference (lang specific)
                - case: Case forms like 'genitive' for Russian (lang specific)
                - plural: Plural forms (lang specific)
                - others?
        """
        # basic settings
        self.lang = settings.get("lang", "en")
        self.to = settings.get("to", "cardinal")

        # currency settings
        self.currency = settings.get("currency", "USD")
        self.cents = settings.get("cents", True)

        # custom options
        self.min = settings.get("min")
        self.max = settings.get("max")
        self.percent = settings.get("percent", "percent")

        # store any additional options; might be language-specific
        reserved_keys = {"lang", "to", "currency", "cents", "min", "max", "percent"}
        self.lang_specific_options = {k: v for k, v in settings.items() if k not in reserved_keys}

        try:
            from num2words import num2words

            self._num2text = num2words
        except ImportError:
            print("Warning: num2words package not available. num2words plugin will be disabled.")
            self._num2text = None

    def _parse_number(self, number_str: str) -> int | float:
        """Parse number string handling various formats"""
        clean_str = number_str
        # handle European format (1.234,56) vs American format (1,234.56)
        if "," in clean_str and "." in clean_str:
            # determine which is decimal separator based on position
            last_comma = clean_str.rfind(",")
            last_dot = clean_str.rfind(".")
            if last_comma > last_dot:
                # european format: 1.234,56
                clean_str = clean_str.replace(".", "").replace(",", ".")
            else:
                # american format: 1,234.56
                clean_str = clean_str.replace(",", "")
        elif "," in clean_str:
            # could be thousands separator or decimal
            parts = clean_str.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # likely decimal: 1,50
                clean_str = clean_str.replace(",", ".")
            else:
                # likely thousands: 1,234
                clean_str = clean_str.replace(",", "")
        # convert to appropriate numeric type
        if "." in clean_str:
            return float(clean_str)
        else:
            return int(clean_str)

    def _convert_number_match(self, match: Any) -> str:
        """
        Convert a single number match to words with comprehensive option support

        Args:
            match: Regex match object containing the number
        Returns:
            Number converted to words according to configuration
        """
        number_str = match.group()
        original_str = number_str

        try:
            # handle currency symbols
            # @NOTE: make a pr/pull request for other currencies (with tests - it's lang specific)
            is_currency = False
            if number_str.startswith("$"):
                is_currency = True
                number_str = number_str[1:]

            # handle percentage
            is_percentage = False
            if number_str.endswith("%"):
                is_percentage = True
                number_str = number_str[:-1]

            # parse the number
            number = self._parse_number(number_str)

            # check if number should be skipped based on min/max settings (custom filtering)
            if self.min is not None and number < self.min:
                return original_str
            if self.max is not None and number > self.max:
                return original_str

            # build kwargs starting with base options
            kwargs = {"lang": self.lang, "to": self.to}

            # add all language-specific options
            kwargs.update(self.lang_specific_options)

            # convert based on type
            if is_currency or self.to == "currency":
                kwargs["to"] = "currency"
                kwargs["currency"] = self.currency
                kwargs["cents"] = self.cents  # type: ignore

            result = self._num2text(number, **kwargs)  # type: ignore

            # handle percentage suffix
            if is_percentage and isinstance(self.percent, str):
                result += f" {self.percent}"

            return result

        except (ValueError, OverflowError, TypeError) as e:
            print(f"Warning: Failed to convert '{original_str}': {e}")
            return original_str
        except Exception as e:
            print(f"Warning: Unexpected error converting '{original_str}': {e}")
            return original_str

    def process(self, text: str) -> str:
        """
        Convert digits to text numbers with full option support

        Args:
            text: Input text to process
        Returns:
            Text with digits converted to words according to configuration
        """
        if not text or not self._num2text:
            return text

        try:
            # regex to handle various number formats including currency
            number_pattern = r"(?<!\w)(-?\$?\d+(?:[.,]\d{3})*(?:[.,]\d+)?%?)(?!\w)"
            result = re.sub(number_pattern, self._convert_number_match, text)
            return result
        except Exception as e:
            print(f"Warning: num2words conversion failed: {e}")
            return text


# convenience function for direct use without plugin class
def num2text(text: str, settings: dict[str, Any] | None = None) -> str:
    """
    Convert digits to text numbers using num2words library

    Args:
        text: Input text to process
        settings: Configuration settings
    Returns:
        Text with converted numbers
    """
    if not text:
        return text

    settings = settings or {}
    lang = settings.get("lang", "en")
    to = settings.get("to", "cardinal")

    try:
        from num2words import num2words as n2w

        def convert_match(match: Any) -> str:
            try:
                number_str = match.group()
                if "." in number_str:
                    number = float(number_str)
                else:
                    number = int(number_str)
                return n2w(number, lang=lang, to=to)
            except Exception:
                return match.group()

        return re.sub(r"(([0-9]+[,.]?)+([,.][0-9]+)?)", convert_match, text)

    except ImportError:
        print("Warning: num2words package not available")
        return text
    except Exception as e:
        print(f"Warning: num2words conversion failed: {e}")
        return text


# -*- coding: utf-8 -*-
# Copyright (c) 2003, Taro Ogawa.  All Rights Reserved.
# Copyright (c) 2013, Savoir-faire Linux inc.  All Rights Reserved.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA
