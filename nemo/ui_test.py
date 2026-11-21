import io
import os
import random
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest import mock

import nemo
from nemo import ui


class PromptOpponentTest(unittest.TestCase):
    def _answer(self, *lines):
        with mock.patch("builtins.input", side_effect=list(lines)), \
                redirect_stdout(io.StringIO()) as out:
            return ui.prompt_opponent(), out.getvalue()

    def test_zero_is_a_human_opponent(self):
        self.assertIs(self._answer("0")[0], ui.HUMAN)

    def test_digits_are_nemo_levels(self):
        self.assertEqual(self._answer("3")[0], nemo.HARD)

    def test_reprompts_on_anything_else(self):
        self.assertEqual(self._answer("9", "x", "1")[0], nemo.EASY)

    def test_menu_names_every_level_and_fits_the_screen(self):
        _, out = self._answer("0")
        for name in nemo.LEVELS.values():
            self.assertIn(name, out)
        self.assertTrue(all(len(line) <= 30 for line in out.splitlines()))


class MakeRngTest(unittest.TestCase):
    def test_seed_from_the_environment_repeats(self):
        with mock.patch.dict(os.environ, {"TP_NEMO_SEED": "42"}):
            a, b = ui.make_rng(), ui.make_rng()
        self.assertEqual([a.random() for _ in range(3)],
                         [b.random() for _ in range(3)])


class TakeTurnTest(unittest.TestCase):
    def test_returns_the_search_move_and_a_cam_panel(self):
        adapter = SimpleNamespace(
            moves=lambda s: ["win"], play=lambda s, m: "won",
            to_move=lambda s: 0, outcome=lambda s: 0 if s == "won" else None,
            evaluate=lambda s, p: 0.0, HARD_DEPTH=1)
        move, cam = ui.take_turn(adapter, "start", nemo.HARD, random.Random(0))
        self.assertEqual(move, "win")
        self.assertIn("gloating", cam[1])


if __name__ == "__main__":
    unittest.main()
