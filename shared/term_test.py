import unittest

from shared import term


class TermTest(unittest.TestCase):
    def test_pad_line_pads_short_text(self):
        self.assertEqual(term.pad_line("hi", width=5), "hi   ")

    def test_pad_line_truncates_long_text(self):
        self.assertEqual(term.pad_line("abcdef", width=4), "abcd")

    def test_center_line_centers_text(self):
        self.assertEqual(term.center_line("hi", width=6), "  hi  ")

    def test_hr_repeats_char(self):
        self.assertEqual(term.hr(width=5, char="="), "=====")

    def test_default_width_fits_narrow_terminal(self):
        self.assertLessEqual(term.DEFAULT_WIDTH, 40)


if __name__ == "__main__":
    unittest.main()
