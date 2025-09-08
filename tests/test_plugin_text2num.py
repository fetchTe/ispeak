import pytest

from src.ispeak.plugin.builtin.text2num import Text2NumPlugin, text2num

# check if text_to_num library is available
try:
    import text_to_num

    HAS_TEXT_TO_NUM = True
except ImportError:
    HAS_TEXT_TO_NUM = False


class TestWishyWashyThreshold:
    """Test suite for text_to_num that demonstrates incorrect/wrong cardinal threshold logic"""

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_cardinal_ordinal(self) -> None:
        from text_to_num import alpha2digit

        # cardinal
        assert alpha2digit("forty-two", "en", 0.0) == "42"
        assert alpha2digit("forty-two", "en", 50) == "42"  # wrong
        # cardinal (year format)
        assert alpha2digit("nineteen eighty-five", "en", 0.0) == "19 85"
        assert alpha2digit("nineteen eighty-five", "en", 2000) == "19 85"  # wrong

        # ordinal -> all correct
        assert alpha2digit("twenty-third", "en", 0.0) == "23rd"
        assert alpha2digit("twenty-third", "en", 30) == "twenty-third"
        assert alpha2digit("forty-second", "en", 0.0) == "42nd"
        assert alpha2digit("forty-second", "en", 50) == "forty-second"

        # other cardinal tests
        assert alpha2digit("one", "en") == "one"  # correct (default threshold)
        assert alpha2digit("one", "en", 0.0) == "1"
        assert alpha2digit("one", "en", 100.0) == "one"
        assert alpha2digit("ten", "en", 0.0) == "10"
        assert alpha2digit("ten", "en", 11) == "10"  # wrong
        assert alpha2digit("ten", "en", 111) == "10"  # wrong
        assert alpha2digit("ten", "en", 9999) == "10"  # wrong
        assert alpha2digit("fourty", "en", 0.0) == "40"
        assert alpha2digit("fourty", "en", 111) == "40"  # wrong
        assert alpha2digit("fourty-three", "en", 0.0) == "43"
        assert alpha2digit("fourty-three", "en", 111) == "43"  # wrong
        assert alpha2digit("fourty three", "en", 111) == "43"  # wrong
        assert alpha2digit("four and three", "en", 0) == "4 and 3"
        assert alpha2digit("four and three", "en", 111) == "4 and 3"  # wrong

        assert alpha2digit("forty-two dollars, fifty cents", "en", 0) == "42 dollars, 50 cents"
        # wrong
        assert alpha2digit("forty-two dollars, fifty cents", "en", 100) == "42 dollars, 50 cents"

        words = """I placed twenty-third, but ninety-nine people dropped out,
        so it's unclear who's actually number one, two, or three;
        let alone first, second, or third."""
        right = """I placed 23rd, but 99 people dropped out,
        so it's unclear who's actually number 1, 2, or 3;
        let alone 1st, 2nd, or 3rd."""
        wrong = """I placed twenty-third, but 99 people dropped out,
        so it's unclear who's actually number 1, 2, or three;
        let alone 1st, 2nd, or third."""
        # correct
        assert alpha2digit(words, "en") == right

        # wrong-ish (1, 2, 99) -> but three is correct
        assert alpha2digit(words, "en", 100) == wrong

        # correct
        assert alpha2digit("seven", "en", 30) == "seven"
        assert alpha2digit("seven", "en", 0) == "7"
        assert alpha2digit("seven", "en", 8) == "seven"

        # correct
        assert alpha2digit("lucky number seven", "en", 30) == "lucky number seven"
        assert alpha2digit("lucky number seven", "en", 0) == "lucky number 7"
        assert alpha2digit("lucky number seven", "en", 8) == "lucky number seven"

        # correct
        assert alpha2digit("five", "en", 30) == "five"
        assert alpha2digit("five", "en", 0) == "5"
        assert alpha2digit("five", "en", 8) == "five"

        # correct
        assert alpha2digit("four", "en", 30) == "four"
        assert alpha2digit("four", "en", 0) == "4"
        assert alpha2digit("four", "en", 8) == "four"

        # correct
        assert alpha2digit("two", "en", 30) == "two"
        assert alpha2digit("two", "en", 0) == "2"
        assert alpha2digit("two", "en", 8) == "two"


class TestText2NumPlugin:
    """Test suite for Text2NumPlugin class"""

    def test_initialization(self) -> None:
        """Test plugin initialization"""
        plugin = Text2NumPlugin()
        assert plugin.name == "text2num"
        assert plugin.lang == "en"
        assert plugin.threshold == 0

    def test_dependencies(self) -> None:
        """Test plugin dependencies"""
        plugin = Text2NumPlugin()
        assert "text_to_num" in plugin.dependencies

    def test_configure(self) -> None:
        """Test plugin configuration"""
        plugin = Text2NumPlugin()
        settings = {"lang": "fr", "threshold": 5}
        plugin.configure(settings)

        assert plugin.lang == "fr"
        assert plugin.threshold == 5

    def test_configure_default_settings(self) -> None:
        """Test plugin configuration with default settings"""
        plugin = Text2NumPlugin()
        plugin.configure({})

        assert plugin.lang == "en"
        assert plugin.threshold == 0

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_process_with_real_text_to_num(self) -> None:
        """Test text processing with real text_to_num library"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en"})

        # test with real library - these are actual conversions
        test_cases = [
            ("I have twenty-three cats", "I have 23 cats"),
            ("The answer is forty-two", "The answer is 42"),
            ("Buy one hundred tickets", "Buy 100 tickets"),
            ("Chapter twenty-five", "Chapter 25"),
            ("No text numbers here", "No text numbers here"),  # should be unchanged
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}' for input '{input_text}'"

        for input_text, expected in test_cases:
            result = text_to_num.alpha2digit(input_text, "en")
            assert result == expected, f"Expected '{expected}' but got '{result}' for input '{input_text}'"

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_process_with_ordinals(self) -> None:
        """Test processing ordinal text numbers with real library"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en"})

        # test ordinal conversion
        test_cases = [
            ("I finished twenty-third", "I finished 23rd"),
            (
                "Let me show you two things: first, isolated numbers are treated differently "
                "than groups like one, two, three. And then, that decimal numbers like "
                "three point one four one five are well understood. Lest we forget, "
                "numbers like four hundred and twenty that have cultural significance.",
                "Let me show you 2 things: 1st, isolated numbers are treated differently "
                "than groups like 1, 2, 3. And then, that decimal numbers like 3.1415 are "
                "well understood. Lest we forget, numbers like 420 that have cultural significance.",
            ),
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_process_with_threshold(self) -> None:
        """Test with threshold of 10"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en", "threshold": 10})

        # test ordinal conversion
        test_cases = [
            ("I finished twenty-third", "I finished 23rd"),
            (
                "Let me show you two things: first, isolated numbers are treated differently "
                "than groups like one, two, three. And then, that decimal numbers like "
                "three point one four one five are well understood. Lest we forget, "
                "numbers like four hundred and twenty that have cultural significance.",
                "Let me show you two things: first, isolated numbers are treated differently "
                "than groups like 1, 2, 3. And then, that decimal numbers like 3.1415 are "
                "well understood. Lest we forget, numbers like 420 that have cultural significance.",
            ),
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_process_with_threshold_100(self) -> None:
        """Test with threshold of 100"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en", "threshold": 1000})

        # test ordinal conversion
        test_cases = [
            ("I finished twenty-third out of ten thousand", "I finished twenty-third out of 10000"),
            (
                "Let me show you two things: first, isolated numbers are treated differently "
                "than groups like one, two, three. And then, that decimal numbers like "
                "three point one four one five are well understood. Lest we forget, "
                "numbers like four hundred and twenty that have cultural significance.",
                "Let me show you two things: first, isolated numbers are treated differently "
                "than groups like 1, 2, 3. And then, that decimal numbers like 3.1415 are "
                "well understood. Lest we forget, numbers like 420 that have cultural significance.",
            ),
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    def test_process_without_text_to_num(self) -> None:
        """Test text processing graceful fallback when text_to_num not available"""
        plugin = Text2NumPlugin()
        plugin.configure({})

        # simulate library not available
        plugin._alpha2digit = None

        text = "The answer is forty-two"
        result = plugin.process(text)
        assert result == text  # should return original text

    def test_process_empty_text(self) -> None:
        """Test processing empty text"""
        plugin = Text2NumPlugin()
        plugin.configure({})

        assert plugin.process("") == ""
        assert plugin.process(None) is None  # type: ignore

    def test_process_with_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test processing with conversion error"""
        plugin = Text2NumPlugin()
        plugin.configure({})

        # simulate a failing conversion
        def failing_alpha2digit(text: str, lang: str) -> str:
            raise ValueError("Conversion failed")

        plugin._alpha2digit = failing_alpha2digit

        text = "some text"
        result = plugin.process(text)

        # should return original text on error
        assert result == text

        captured = capsys.readouterr()
        assert "Warning: text2num conversion failed" in captured.out


class TestText2NumFunction:
    """Test standalone text2num function"""

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_function_with_real_text_to_num(self) -> None:
        """Test standalone function with real text_to_num library"""
        test_cases = [
            ("forty-two cats", "42 cats"),
            ("twenty-three dogs", "23 dogs"),
            ("one hundred birds", "100 birds"),
            ("no numbers here", "no numbers here"),
        ]

        for input_text, expected in test_cases:
            result = text2num(input_text)
            assert result == expected, f"Expected '{expected}' but got '{result}'"

    def test_function_without_text_to_num_library(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test standalone function graceful fallback when library not available"""
        # test the actual fallback behavior in the function
        import sys
        from unittest import mock

        # temporarily hide the text_to_num module
        with mock.patch.dict(sys.modules, {"text_to_num": None}):
            # re-import to trigger ImportError path
            import importlib

            from src.ispeak.plugin.builtin import text2num as text2num_module

            importlib.reload(text2num_module)

            text = "forty-two cats"
            result = text2num_module.text2num(text)

            # should return original text when library not available
            assert result == text

            captured = capsys.readouterr()
            assert "Warning: text_to_num package not available" in captured.out

    def test_function_with_settings(self) -> None:
        """Test standalone function with settings"""
        settings = {"lang": "fr"}
        text = "some text"
        result = text2num(text, settings)

        # without library, should return original text
        assert result == text

    def test_function_empty_text(self) -> None:
        """Test standalone function with empty text"""
        assert text2num("") == ""
        assert text2num(None) is None  # type: ignore


class TestText2NumRealLibraryFeatures:
    """Test specific features that require the real text_to_num library"""

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_complex_numbers(self) -> None:
        """Test conversion of complex number phrases"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en"})

        test_cases = [
            ("two thousand and five", "2005"),
            ("three hundred forty-seven", "347"),
            ("one million", "1000000"),
        ]

        for input_text, expected in test_cases:
            result = plugin.process(input_text)
            assert expected in result, f"Expected '{expected}' to be in '{result}' for input '{input_text}'"

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_decimal_text_numbers(self) -> None:
        """Test conversion of decimal text numbers"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en"})

        # note: text_to_num library behavior with decimals may vary
        result = plugin.process("twenty-five point four")
        assert "25" in result  # should contain the converted number

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_multiple_text_numbers(self) -> None:
        """Test processing text with multiple text numbers"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en"})

        text = "I have twenty-one cats, thirty-two dogs, and forty-three birds"
        result = plugin.process(text)

        # should convert all text numbers
        assert "21" in result
        assert "32" in result
        assert "43" in result
        assert "twenty-one" not in result
        assert "thirty-two" not in result
        assert "forty-three" not in result

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_mixed_text_and_digits(self) -> None:
        """Test processing text with mixed text numbers and existing digits"""
        plugin = Text2NumPlugin()
        plugin.configure({"lang": "en"})

        text = "I have twenty-one cats and 5 dogs"
        result = plugin.process(text)

        # should convert text numbers but leave existing digits unchanged
        assert "21" in result
        assert "5" in result
        assert "twenty-one" not in result

    @pytest.mark.skipif(not HAS_TEXT_TO_NUM, reason="text_to_num package not available")
    def test_different_languages(self) -> None:
        """Test text2num with different language settings"""
        plugin = Text2NumPlugin()

        # test with French if supported by text_to_num
        try:
            plugin.configure({"lang": "fr"})
            # this test may need adjustment based on text_to_num's language support
            _ = plugin.process("vingt-trois")  # french for twenty-three
            # the behavior depends on text_to_num's French support
        except Exception:
            # if French isn't supported, that's expected
            pass
