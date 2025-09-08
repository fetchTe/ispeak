import json
import tempfile
from pathlib import Path

import pytest

from src.ispeak.plugin.builtin.replace import ReplacePlugin


class TestReplacePlugin:
    """Test suite for ReplacePlugin class"""

    def test_initialization_empty(self) -> None:
        """Test ReplacePlugin with no configuration"""
        plugin = ReplacePlugin()
        plugin.configure({})
        assert plugin.get_rules_count() == 0

        # should return text unchanged
        text = "hello world"
        assert plugin.process(text) == text

    def test_plugin_name(self) -> None:
        """Test plugin name property"""
        plugin = ReplacePlugin()
        assert plugin.name == "replace"


class TestBasicStringReplacement:
    """Test basic string replacement functionality"""

    def test_simple_string_replacement(self) -> None:
        """Test simple string to string replacement"""
        rules = {"hello": "hi", "world": "universe"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("hello world") == "hi universe"
        assert plugin.process("hello") == "hi"
        assert plugin.process("world") == "universe"
        assert plugin.process("nothing") == "nothing"

    def test_whitespace_replacement(self) -> None:
        """Test replacement of whitespace patterns"""
        rules = {" white space ": " WHITESPACE "}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("test white space test") == "test WHITESPACE test"
        assert plugin.process("white space") == "white space"

    def test_case_sensitive_replacement(self) -> None:
        """Test that replacements are case sensitive by default"""
        rules = {"Example": "EXAMPLE"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("Example") == "EXAMPLE"
        assert plugin.process("example") == "example"  # should not match
        assert plugin.process("EXAMPLE") == "EXAMPLE"  # should not match

    def test_multiple_replacements_same_text(self) -> None:
        """Test multiple replacements in the same text"""
        rules = {"cat": "dog", "mouse": "cheese"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        result = plugin.process("the cat chased the mouse")
        assert result == "the dog chased the cheese"

    def test_overlapping_patterns(self) -> None:
        """Test behavior with overlapping patterns"""
        rules = {"test": "TEST", "testing": "TESTING"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        # order matters - first rule applied wins
        result = plugin.process("testing")
        # should match "test" first, leaving "ing"
        assert result == "TESTing"


class TestRegexPatterns:
    """Test regex pattern functionality"""

    def test_regex_metacharacters(self) -> None:
        """Test regex with metacharacters"""
        rules = {
            r"\s+": " ",  # multiple whitespace to single space
            r"\d+": "NUM",  # any digits to NUM
        }
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("hello   world") == "hello world"
        assert plugin.process("test123") == "testNUM"
        assert plugin.process("   multiple   spaces   ") == " multiple spaces "

    def test_regex_character_classes(self) -> None:
        """Test regex character classes"""
        rules = {
            r"[aeiou]": "*",  # replace vowels with *
            r"[0-9]+": "NUM",  # replace numbers with NUM
        }
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("hello") == "h*ll*"
        assert plugin.process("test123end") == "t*stNUM*nd"

    def test_regex_word_boundaries(self) -> None:
        """Test word boundary assertions"""
        rules = {
            r"\btest\b": "TEST",  # only match whole word "test"
        }
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("test") == "TEST"
        assert plugin.process("a test here") == "a TEST here"
        assert plugin.process("testing") == "testing"  # should not match
        assert plugin.process("protest") == "protest"  # should not match

    def test_question_mark_exclamation_examples(self) -> None:
        """Test the example patterns from requirements"""
        rules = {r"\s*question\s*mark\.?": "?", r"\s*exclamation\s*mark\.?": "!"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("question mark") == "?"
        assert plugin.process(" question mark ") == "? "
        assert plugin.process("question mark.") == "?"
        assert plugin.process("exclamation mark") == "!"
        assert plugin.process(" exclamation mark.") == "!"


class TestRegexWithFlags:
    """Test regex patterns with flags in /pattern/flags format"""

    def test_case_insensitive_flag(self) -> None:
        """Test /pattern/i for case insensitive matching"""
        rules = {"/hello/i": "HI"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("hello") == "HI"
        assert plugin.process("Hello") == "HI"
        assert plugin.process("HELLO") == "HI"
        assert plugin.process("HeLLo") == "HI"

    def test_multiline_flag(self) -> None:
        """Test /pattern/m for multiline matching"""
        rules = {"/^start/m": "BEGIN"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        text = "not start\nstart of line"
        result = plugin.process(text)
        assert result == "not start\nBEGIN of line"

    def test_dotall_flag(self) -> None:
        """Test /pattern/s for dotall (. matches newline)"""
        rules = {"/start.*end/s": "REPLACED"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        text = "start\nmiddle\nend"
        result = plugin.process(text)
        assert result == "REPLACED"

    def test_multiple_flags(self) -> None:
        """Test multiple flags combined"""
        rules = {"/start.*end/ims": "REPLACED"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        text = "START\nmiddle\nEND"
        result = plugin.process(text)
        assert result == "REPLACED"

    def test_comma_example_from_requirements(self) -> None:
        """Test the comma example from requirements"""
        rules = {r"/([\s+])(comma)([\s+])/gmi": ", "}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        # note: Python re doesn't support 'g' flag the same way as JS
        # it applies to all matches by default
        assert plugin.process("word comma word") == "word, word"
        assert plugin.process("Word COMMA Word") == "Word, Word"

    def test_anchored_patterns(self) -> None:
        """Test anchored patterns from requirements"""
        rules = {"/^start/i": "START", "/end$/i": "END"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("start middle") == "START middle"
        assert plugin.process("START middle") == "START middle"
        assert plugin.process("middle end") == "middle END"
        assert plugin.process("middle END") == "middle END"
        assert plugin.process("start middle end") == "START middle END"


class TestSubstitutionGroups:
    """Test regex substitution groups"""

    def test_basic_capture_groups(self) -> None:
        """Test basic capture group substitution"""
        rules = {
            r"(\w+) (\w+)": r"\2 \1"  # swap two words
        }
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("hello world") == "world hello"
        assert plugin.process("first second") == "second first"

    def test_named_groups_syntax(self) -> None:
        r"""Test \g<n> group syntax from requirements"""
        rules = {r"(\s+)(semi)(\s+)": r";\g<3>", r"(\s+)(comma)(\s+)": r",\g<3>"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("word semi word") == "word; word"
        assert plugin.process("word comma word") == "word, word"
        assert plugin.process("  semi  ") == ";  "
        assert plugin.process(" comma ") == ", "

    def test_complex_group_replacement(self) -> None:
        """Test complex group replacements"""
        rules = {
            r"(\d{4})-(\d{2})-(\d{2})": r"\3/\2/\1",  # date format change
            r"([A-Z]+)\.([A-Z]+)\.([A-Z]+)": r"\1_\2_\3",  # dots to underscores
        }
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("2023-12-25") == "25/12/2023"
        assert plugin.process("A.B.C") == "A_B_C"

    def test_mixed_groups_and_literals(self) -> None:
        """Test mixing groups with literal text"""
        rules = {r"(\w+) says (\w+)": r"Quote: '\2' - \1"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        result = plugin.process("John says hello")
        assert result == "Quote: 'hello' - John"

    def test_optional_groups(self) -> None:
        """Test optional capture groups"""
        rules = {r"(\w+)(\.?)": r"\1_SUFFIX\2"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("word") == "word_SUFFIX"
        assert plugin.process("word.") == "word_SUFFIX."


class TestFileLoading:
    """Test loading replacement rules from files"""

    def test_load_from_single_file(self) -> None:
        """Test loading rules from a single JSON file"""
        rules = {"test": "TEST", "hello": "hi"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(rules, f)
            temp_file = f.name

        try:
            plugin = ReplacePlugin()
            plugin.configure([temp_file])  # type: ignore
            assert plugin.get_rules_count() == 2
            assert plugin.process("test hello") == "TEST hi"
        finally:
            Path(temp_file).unlink()

    def test_load_with_replace_key(self) -> None:
        """Test loading from file with 'replace' key wrapper"""
        data = {"replace": {"wrapped": "WRAPPED"}, "other_config": "ignored"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_file = f.name

        try:
            plugin = ReplacePlugin()
            plugin.configure([temp_file])  # type: ignore
            assert plugin.get_rules_count() == 1
            assert plugin.process("wrapped") == "WRAPPED"
        finally:
            Path(temp_file).unlink()

    def test_file_not_found_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test warning when file is not found"""
        plugin = ReplacePlugin()
        plugin.configure(["/nonexistent/file.json"])  # type: ignore
        assert plugin.get_rules_count() == 0

        captured = capsys.readouterr()
        assert "Warning: Replace rules file not found" in captured.out

    def test_load_from_multiple_files(self) -> None:
        """Test loading rules from multiple JSON files"""
        rules1 = {"file1": "FILE1"}
        rules2 = {"file2": "FILE2"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
            json.dump(rules1, f1)
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
            json.dump(rules2, f2)
            temp_file2 = f2.name

        try:
            plugin = ReplacePlugin()
            plugin.configure([temp_file1, temp_file2])  # type: ignore
            assert plugin.get_rules_count() == 2
            assert plugin.process("file1 file2") == "FILE1 FILE2"
        finally:
            Path(temp_file1).unlink()
            Path(temp_file2).unlink()

    def test_invalid_json_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test warning with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            plugin = ReplacePlugin()
            plugin.configure([temp_file])  # type: ignore
            assert plugin.get_rules_count() == 0

            captured = capsys.readouterr()
            assert "Warning: Failed to load replace rules" in captured.out
        finally:
            Path(temp_file).unlink()

    def test_invalid_format_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test warning with invalid format"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["invalid", "format"], f)
            temp_file = f.name

        try:
            plugin = ReplacePlugin()
            plugin.configure([temp_file])  # type: ignore
            assert plugin.get_rules_count() == 0

            captured = capsys.readouterr()
            assert "Warning: Invalid replace rules format" in captured.out
        finally:
            Path(temp_file).unlink()


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_regex_pattern_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test warning with invalid regex pattern"""
        rules = {
            "[invalid": "test",  # missing closing bracket
            "valid": "VALID",
        }

        plugin = ReplacePlugin()
        plugin.configure(rules)
        # should have loaded only the valid rule
        assert plugin.get_rules_count() == 1
        assert plugin.process("valid") == "VALID"

        captured = capsys.readouterr()
        assert "Warning: Invalid regex pattern" in captured.out

    def test_empty_input_text(self) -> None:
        """Test with empty input text"""
        rules = {"test": "TEST"}
        plugin = ReplacePlugin()
        plugin.configure(rules)

        assert plugin.process("") == ""
        # should handle None gracefully
        assert plugin.process(None) == ""  # type: ignore

    def test_invalid_replacement_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test warning with invalid replacement during application"""
        # this test is tricky since most replacement strings are valid
        # we'll test a pattern that compiles but fails during substitution
        rules = {
            r"(\w+)": r"\g<999>"  # invalid group number
        }

        plugin = ReplacePlugin()
        plugin.configure(rules)
        result = plugin.process("test")

        # should continue with original text when replacement fails
        assert result == "test"

        captured = capsys.readouterr()
        assert "Warning: Replacement failed" in captured.out


class TestRuleManagement:
    """Test rule management methods"""

    def test_add_rule(self) -> None:
        """Test adding rules dynamically"""
        plugin = ReplacePlugin()
        assert plugin.get_rules_count() == 0

        plugin.add_rule("test", "TEST")
        assert plugin.get_rules_count() == 1
        assert plugin.process("test") == "TEST"

        plugin.add_rule("/hello/i", "HI")
        assert plugin.get_rules_count() == 2
        assert plugin.process("Hello test") == "HI TEST"

    def test_clear_rules(self) -> None:
        """Test clearing all rules"""
        rules = {"test": "TEST", "hello": "HI"}
        plugin = ReplacePlugin()
        plugin.configure(rules)
        assert plugin.get_rules_count() == 2

        plugin.clear_rules()
        assert plugin.get_rules_count() == 0
        assert plugin.process("test hello") == "test hello"

    def test_add_invalid_rule(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test adding invalid rule"""
        plugin = ReplacePlugin()

        plugin.add_rule("[invalid", "TEST")
        assert plugin.get_rules_count() == 0

        captured = capsys.readouterr()
        assert "Warning: Invalid regex pattern" in captured.out

    def test_get_rules_count(self) -> None:
        """Test getting rules count"""
        plugin = ReplacePlugin()
        assert plugin.get_rules_count() == 0

        rules = {"a": "A", "b": "B", "c": "C"}
        plugin.configure(rules)
        assert plugin.get_rules_count() == 3


class TestRealWorldExamples:
    """Test real-world usage examples"""

    def test_voice_transcription_cleanup(self) -> None:
        """Test typical voice transcription cleanup scenarios"""
        rules = {
            # common voice transcription issues
            r"\s*comma\s*": ",",
            r"\s*question\s*mark\s*": "?",
            r"\s*exclamation\s*mark\s*": "!",
            r"\s*semicolon\s*": ";",
            r"\s*colon\s*": ":",
            # code-specific replacements
            r"\s*open\s*paren\s*": "(",
            r"\s*close\s*paren\s*": ")",
            r"\s*open\s*brace\s*": "{",
            r"\s*close\s*brace\s*": "}",
            # common programming terms
            r"\bfunction\b": "def",
            r"\breturn\b": "return",
            r"\bprint\b": "print",
        }

        plugin = ReplacePlugin()
        plugin.configure(rules)

        # test voice input that might come from coding
        input_text = "function test open paren close paren colon open brace print 1 close brace"
        expected = "def test():{print 1}"
        result = plugin.process(input_text)
        assert result == expected

    def test_text_normalization(self) -> None:
        """Test text normalization scenarios"""
        rules = {
            # normalize multiple spaces
            r"\s+": " ",
            # fix common spacing issues
            r"\s*([,.!?;:])\s*": r"\1 ",
            # remove trailing spaces before punctuation
            r"\s+([.!?])": r"\1",
            # capitalize after sentence endings
            r"([.!?])\s+([a-z])": r"\1 \u\2",
        }

        plugin = ReplacePlugin()
        plugin.configure(rules)

        input_text = "hello   ,  world  .   this   is  a   test  !"
        result = plugin.process(input_text)

        # should normalize spacing around punctuation
        assert result.strip() == "hello, world. this is a test!"

    def test_code_formatting_helpers(self) -> None:
        """Test code formatting assistance"""
        rules = {
            # convert spoken operators
            r"\bequals\b": "=",
            r"\bplus\b": "+",
            r"\bminus\b": "-",
            r"\btimes\b": "*",
            r"\bdivided by\b": "/",
            r"\bgreater than\b": ">",
            r"\bless than\b": "<",
            # convert number words (simple examples)
            r"\bone\b": "1",
            r"\btwo\b": "2",
            r"\bthree\b": "3",
            # fix spacing around operators
            r"(\w)\s*=\s*(\w)": r"\1 = \2",
            r"(\w)\s*\+\s*(\w)": r"\1 + \2",
        }

        plugin = ReplacePlugin()
        plugin.configure(rules)

        input_text = "variable equals one plus two times three"
        result = plugin.process(input_text)
        assert "variable = 1 + 2 * 3" in result


class TestEdgeCasesAndCornerCases:
    """Test edge cases and corner cases"""

    def test_circular_replacements(self) -> None:
        """Test that circular replacements don't cause infinite loops"""
        rules = {"cat": "dog", "dog": "cat"}

        plugin = ReplacePlugin()
        plugin.configure(rules)

        # should apply rules once, not infinitely
        result = plugin.process("cat dog")
        # rules are applied in order, so "cat" -> "dog", then "dog" -> "cat"
        # final result depends on rule order
        assert result in ["dog cat", "cat dog", "cat cat", "dog dog"]

        # make sure it doesn't hang or crash
        assert len(result.split()) == 2

    def test_empty_replacement_string(self) -> None:
        """Test replacement with empty string (deletion)"""
        rules = {
            "delete me": "",
            r"\s+": "  ",  # double space
        }

        plugin = ReplacePlugin()
        plugin.configure(rules)

        result = plugin.process("keep delete me this delete me text")
        assert result == "keep  this  text"

    def test_replacement_with_special_characters(self) -> None:
        """Test replacements containing special characters"""
        rules = {"amp": "&", "lt": "<", "gt": ">", "quote": '"', "newline": "\n", "tab": "\t"}

        plugin = ReplacePlugin()
        plugin.configure(rules)

        result = plugin.process("amp lt gt quote newline tab")
        assert "&" in result
        assert "<" in result
        assert ">" in result
        assert '"' in result
        assert "\n" in result
        assert "\t" in result

    def test_unicode_text(self) -> None:
        """Test with Unicode text"""
        rules = {"café": "CAFÉ", "naïve": "NAIVE", "résumé": "RESUME", "émoji": "🙂"}

        plugin = ReplacePlugin()
        plugin.configure(rules)

        text = "I like café and résumé but I'm naïve about émoji"
        result = plugin.process(text)

        assert "CAFÉ" in result
        assert "RESUME" in result
        assert "NAIVE" in result
        assert "🙂" in result

    def test_very_long_pattern(self) -> None:
        """Test with very long regex pattern"""
        # create a pattern that matches a very long specific string
        long_string = "very_long_pattern_" * 50
        rules = {long_string: "SHORT"}

        plugin = ReplacePlugin()
        plugin.configure(rules)

        test_text = f"before {long_string} after"
        result = plugin.process(test_text)
        assert result == "before SHORT after"

    def test_null_bytes_and_control_characters(self) -> None:
        """Test handling of null bytes and control characters"""
        rules = {"null": "\x00", "bell": "\x07", "escape": "\x1b"}

        plugin = ReplacePlugin()
        plugin.configure(rules)

        result = plugin.process("null bell escape")
        assert "\x00" in result
        assert "\x07" in result
        assert "\x1b" in result
