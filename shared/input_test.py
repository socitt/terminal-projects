import unittest
from unittest.mock import patch

from shared import input as input_module


class NormalizeKeyTest(unittest.TestCase):
    def test_takes_first_char_lowercased(self):
        self.assertEqual(input_module.normalize_key("Q"), "q")

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(input_module.normalize_key("  n  "), "n")

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(input_module.normalize_key(""), "")

    def test_whitespace_only_returns_empty_string(self):
        self.assertEqual(input_module.normalize_key("   "), "")

    def test_takes_only_first_char_of_multichar_input(self):
        self.assertEqual(input_module.normalize_key("yes"), "y")


class GetKeyTest(unittest.TestCase):
    @patch("builtins.input", return_value="X")
    def test_get_key_normalizes_input(self, mock_input):
        self.assertEqual(input_module.get_key("prompt> "), "x")
        mock_input.assert_called_once_with("prompt> ")


class PromptChoiceTest(unittest.TestCase):
    @patch("builtins.input", side_effect=["z", "q"])
    def test_reprompts_until_valid_choice(self, mock_input):
        self.assertEqual(input_module.prompt_choice("> ", "qn"), "q")
        self.assertEqual(mock_input.call_count, 2)

    @patch("builtins.input", return_value="n")
    def test_accepts_first_valid_choice(self, mock_input):
        self.assertEqual(input_module.prompt_choice("> ", "qn"), "n")
        mock_input.assert_called_once()


if __name__ == "__main__":
    unittest.main()
