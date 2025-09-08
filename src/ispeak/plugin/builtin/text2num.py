# dep: https://github.com/allo-media/text2num
#      https://github.com/allo-media/text2num-rs -> https://docs.rs/text2num/latest/text2num
# lic: MIT (included at bottom)
from typing import Any

from ..base import ISpeakPlugin


class Text2NumPlugin(ISpeakPlugin):
    """Convert text numbers to digits (forty-two -> 42)"""

    def __init__(self) -> None:
        self.lang = "en"
        self.threshold = 0.0
        self._alpha2digit = None

    @property
    def name(self) -> str:
        return "text2num"

    @property
    def dependencies(self) -> list[str]:
        # package is text2num
        return ["text_to_num"]

    def configure(self, settings: dict[str, Any]) -> None:
        """
        Configure text2num plugin

        Args:
            settings: Plugin settings including lang, threshold, min, max
        """
        self.lang = settings.get("lang", "en")
        self.threshold = float(settings.get("threshold", 0.0))
        try:
            from text_to_num import alpha2digit

            self._alpha2digit = alpha2digit
        except ImportError:
            print("Warning: text_to_num package not available. text2num plugin will be disabled.")
            self._alpha2digit = None

    def process(self, text: str) -> str:
        """
        Convert text numbers to digits

        Args:
            text: Input text to process
        Returns:
            Text with numbers converted to digits
        """
        if not text or not self._alpha2digit:
            return text

        try:
            # apply text-to-number conversion
            result = self._alpha2digit(text, self.lang, threshold=self.threshold)
            return result

        except Exception as e:
            print(f"Warning: text2num conversion failed: {e}")
            return text


# convenience function for direct use without plugin class
def text2num(text: str, settings: dict[str, Any] | None = None) -> str:
    """
    Convert text numbers to digits using text_to_num library

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
    threshold = float(settings.get("threshold", 0.0))

    try:
        from text_to_num import alpha2digit

        return alpha2digit(text, lang, threshold=threshold)
    except ImportError:
        print("Warning: text_to_num package not available")
        return text
    except Exception as e:
        print(f"Warning: text2num conversion failed: {e}")
        return text


# MIT License
# Copyright (c) 2018-2024 Groupe Allo-Media
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
