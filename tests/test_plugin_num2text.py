import importlib.util
from typing import Any, Never

import pytest

from src.ispeak.plugin.builtin.num2text import Num2TextPlugin, num2text

# check if num2words library is available
HAS_NUM2WORDS = importlib.util.find_spec("num2words") is not None


class TestNum2TextPlugin:
    """Test suite for Num2TextPlugin class"""

    def test_initialization(self) -> None:
        """Test plugin initialization"""
        plugin = Num2TextPlugin()
        assert plugin.name == "num2text"
        assert plugin.lang == "en"
        assert plugin.to == "cardinal"
        assert plugin.min is None
        assert plugin.max is None

    def test_dependencies(self) -> None:
        """Test plugin dependencies"""
        plugin = Num2TextPlugin()
        assert "num2words" in plugin.dependencies

    def test_configure(self) -> None:
        """Test plugin configuration"""
        plugin = Num2TextPlugin()
        settings = {
            "lang": "fr",
            "to": "ordinal",
            "min": 1,
            "max": 100,
            "case": "nominative",
            "plural": True,
            "prefer": ["ain"],
        }
        plugin.configure(settings)

        assert plugin.lang == "fr"
        assert plugin.to == "ordinal"
        assert plugin.min == 1
        assert plugin.max == 100

    def test_configure_default_settings(self) -> None:
        """Test plugin configuration with default settings"""
        plugin = Num2TextPlugin()
        plugin.configure({})

        assert plugin.lang == "en"
        assert plugin.to == "cardinal"
        assert plugin.min is None
        assert plugin.max is None

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_process_with_real_num2text(self) -> None:
        """Test text processing with real num2words library"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en", "to": "cardinal"})

        # test with real library - these are actual conversions
        test_cases = [
            ("I have 1 cat", "I have one cat"),
            ("Buy 2 tickets", "Buy two tickets"),
            ("The answer is 42", "The answer is forty-two"),
            ("Page 100", "Page one hundred"),
            ("No digits here", "No digits here"),  # should be unchanged
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}' for input '{input_text}'"

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_process_with_ordinals(self) -> None:
        """Test processing ordinal numbers with real library"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en", "to": "ordinal"})

        test_cases = [
            ("I finished 1", "I finished first"),
            ("Chapter 2", "Chapter second"),
            ("The 3 option", "The third option"),
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_process_with_min_max_filtering(self) -> None:
        """Test number conversion with min/max filtering using real library"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en", "min": 10, "max": 100})

        test_cases = [
            ("Value is 5", "Value is 5"),  # below min, unchanged
            ("Value is 50", "Value is fifty"),  # within range, converted
            ("Value is 200", "Value is 200"),  # above max, unchanged
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    def test_process_without_num2text(self) -> None:
        """Test text processing graceful fallback when num2words not available"""
        plugin = Num2TextPlugin()
        plugin.configure({})

        # simulate library not available
        plugin._num2text = None

        text = "The answer is 42"
        result = plugin.process(text)
        assert result == text  # should return original text

    def test_process_empty_text(self) -> None:
        """Test processing empty text"""
        plugin = Num2TextPlugin()
        plugin.configure({})

        assert plugin.process("") == ""
        assert plugin.process(None) is None  # type: ignore

    def test_process_with_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test processing with conversion error"""
        plugin = Num2TextPlugin()
        plugin.configure({})

        # simulate num2words raising an error
        def failing_num2text(num: Any, **kwargs: Any) -> Never:
            raise ValueError("Conversion failed")

        plugin._num2text = failing_num2text

        text = "Number 42 here"
        result = plugin.process(text)

        # should return original text on error
        assert result == text

        # captured = capsys.readouterr()
        # assert "Warning: num2words conversion failed" in captured.out

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_convert_number_match_with_real_library(self) -> None:
        """Test converting number matches with real library"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        # test with mock regex match object
        class MockMatch:
            def __init__(self, text: str) -> None:
                self.text = text

            def group(self) -> str:
                return self.text

        result = plugin._convert_number_match(MockMatch("42"))
        assert result == "forty-two"

        result = plugin._convert_number_match(MockMatch("123"))
        assert result == "one hundred and twenty-three"

    def test_convert_number_match_invalid_number(self) -> None:
        """Test converting invalid number matches"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        # set up real num2words if available, otherwise skip this specific test
        if not HAS_NUM2WORDS:
            plugin._num2text = None

        class MockMatch:
            def __init__(self, text: str) -> None:
                self.text = text

            def group(self) -> str:
                return self.text

        # should return original string for non-numeric input
        result = plugin._convert_number_match(MockMatch("not-a-number"))
        assert result == "not-a-number"


class TestNum2WordsFunction:
    """Test standalone num2words function"""

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_function_with_real_num2text(self) -> None:
        """Test standalone function with real num2words library"""
        test_cases = [
            ("I have 42 cats", "I have forty-two cats"),
            ("Buy 23 items", "Buy twenty-three items"),
            ("Total: 100", "Total: one hundred"),
            ("No numbers here", "No numbers here"),
        ]

        for input_text, expected in test_cases:
            result = num2text(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_function_with_settings(self) -> None:
        """Test standalone function with settings using real library"""
        settings = {"lang": "en", "to": "ordinal"}

        result = num2text("I finished 1 place", settings)
        assert result == "I finished first place"

    def test_function_without_num2text_library(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test standalone function graceful fallback when library not available"""
        # test the actual fallback behavior in the function
        import sys
        from unittest import mock

        # temporarily hide the num2words module
        with mock.patch.dict(sys.modules, {"num2words": None}):
            # re-import to trigger ImportError path
            import importlib

            from src.ispeak.plugin.builtin import num2text as num2text_module

            importlib.reload(num2text_module)

            text = "I have 42 cats"
            result = num2text_module.num2text(text)

            # should return original text when library not available
            assert result == text

            captured = capsys.readouterr()
            assert "Warning: num2words package not available" in captured.out

    def test_function_empty_text(self) -> None:
        """Test standalone function with empty text"""
        assert num2text("") == ""
        assert num2text(None) is None  # type: ignore


class TestNum2WordsRealLibraryFeatures:
    """Test specific features that require the real num2words library"""

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_decimal_numbers(self) -> None:
        """Test processing decimal numbers"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        # note: Real num2words might handle decimals differently
        result = plugin.process("Pi is approximately 3.14")
        # the exact output depends on how num2words handles decimals
        assert "3.14" not in result or "three" in result.lower()

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_large_numbers(self) -> None:
        """Test processing large numbers"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        result = plugin.process("The population is 1000000")
        assert "million" in result

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_multiple_numbers(self) -> None:
        """Test processing text with multiple numbers"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        text = "I have 1 cat, 2 dogs, and 3 birds"
        result = plugin.process(text)
        expected = "I have one cat, two dogs, and three birds"
        assert result == expected

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_zero_and_negative_numbers(self) -> None:
        """Test processing zero and negative numbers"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        # test zero
        result = plugin.process("I have 0 items")
        assert "zero" in result

        # test negative int
        result = plugin.process("it's -30 degrees")
        assert result == "it's minus thirty degrees"

        # test negative dec point
        result = plugin.process("I have -1.12 items")
        assert result == "I have minus one point one two items"

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_percent(self) -> None:
        """Test processing zero and negative numbers"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        result = plugin.process("I'm 100%")
        assert result == "I'm one hundred percent"

        result = plugin.process("Give me $100.00")
        assert result == "Give me one hundred dollars, zero cents"

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_edge_silly_nums(self) -> None:
        """Test processing zero and negative numbers"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})
        # test: -1.12
        # test: 1,0
        # test: 1,000
        # test: 1,000,000.75
        # test: 50,000
        # test: -50,000
        # test: 1.000.000
        # test: -1.000.000
        # test: -4.20.420
        # test: 2fine
        # test: no0p2

        # test: minus one point one two
        # test: one
        # test: one thousand
        # test: one million point seven five
        # test: fifty thousand
        # test: minus fifty thousand
        # test: 1.000.000
        # test: -1.000.000
        # test: minus four point two.four hundred and twenty
        # test: 2fine
        # test: no0p2
        input_text = (
            "test: -1.12 test: 1,0 test: 1,000 test: 1,000,000.75 test: 50,000 test: -50,000 "
            "test: 1.000.000 test: -1.000.000 test: -4.20.420 test: 2fine test: no0p2"
        )
        result = plugin.process(input_text)
        expected = (
            "test: minus one point one two test: one test: one thousand test: one million point seven five "
            "test: fifty thousand test: minus fifty thousand test: 1.000.000 test: -1.000.000 "
            "test: minus four point two.four hundred and twenty test: 2fine test: no0p2"
        )
        assert result == expected

    @pytest.mark.skipif(not HAS_NUM2WORDS, reason="num2words package not available")
    def test_reverse_text2num(self) -> None:
        """Test reversing output text2num"""
        plugin = Num2TextPlugin()
        plugin.configure({"lang": "en"})

        # test ordinal conversion
        test_cases = [
            ("I finished twenty-third out of ten thousand", "I finished twenty-third out of 10000"),
            (
                "Let me show you two things: first, isolated numbers are treated differently than groups like "
                "one, two, three. And then, that decimal numbers like three point one four one five are well "
                "understood. Lest we forget, numbers like four hundred and twenty that have cultural significance.",
                "Let me show you two things: first, isolated numbers are treated differently than groups like "
                "1, 2, 3. And then, that decimal numbers like 3.1415 are well understood. Lest we forget, "
                "numbers like 420 that have cultural significance.",
            ),
        ]

        for expected, input_text in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"
