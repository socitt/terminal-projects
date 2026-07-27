"""End-to-end tests for the train-mystery story: run the real main.py
as a subprocess with piped input, same style as every board game's
main_test.py. Each scenario was hand-verified live against the real
script first, same discipline as dungeon's main_test.py.
"""

import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"
SAVE = Path(__file__).resolve().parent / "save.json"


def _run(input_text, timeout=10):
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TrainMysteryEndToEndTest(unittest.TestCase):
    def tearDown(self):
        SAVE.unlink(missing_ok=True)

    def test_solving_the_case_requires_all_three_clues(self):
        # corridor -> dining (examine glass) -> corridor -> sleeper
        # (search cabin) -> corridor -> cargo (examine prints) ->
        # corridor -> confrontation -> accuse the widow.
        result = _run("1\n1\n2\n2\n1\n2\n3\n1\n2\n4\n3\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Case closed", result.stdout)
        self.assertIn("THE END", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertFalse(SAVE.exists())

    def test_widow_accusation_hidden_without_all_clues(self):
        # Go straight to confrontation with zero clues gathered: only
        # the wrong-suspect options and "keep investigating" should be
        # available -- "Accuse the widow" must not appear at all.
        result = _run("4\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Accuse the widow", result.stdout)
        self.assertIn("real killer slips away", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_accusing_wrong_suspect_lets_killer_escape(self):
        result = _run("4\n2\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("bewildered", result.stdout)
        self.assertIn("real killer slips away", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_widow_accusation_gate_opens_mid_run_as_clues_arrive(self):
        # Reach confrontation with only 2 of 3 clues (poison + letter,
        # missing footprints): "Accuse the widow" gated out, so "Keep
        # investigating" renumbers to key 3, not 4 (the same gated-
        # choice renumbering caught in dungeon's vault_entrance test).
        # Go gather the footprints, return to confrontation, and
        # confirm the option has now appeared -- same run, same story
        # instance, gate opening in response to state that changed in
        # between.
        result = _run("1\n1\n2\n2\n1\n2\n4\n3\n3\n1\n2\n4\n3\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

        parts = result.stdout.split("Time to accuse someone.")
        self.assertEqual(len(parts), 3, "expected exactly 2 confrontation visits")
        self.assertNotIn("Accuse the widow", parts[1])
        self.assertIn("Accuse the widow", parts[2])
        self.assertIn("Case closed", parts[2])

    def test_save_and_resume_across_two_runs(self):
        first = _run("1\n1\ns\n")
        self.assertEqual(first.returncode, 0)
        self.assertTrue(SAVE.exists())

        second = _run("y\n2\n2\n1\n2\n3\n1\n2\n4\n3\n")
        self.assertEqual(second.returncode, 0)
        self.assertIn("Saved game found", second.stdout)
        self.assertIn("Case closed", second.stdout)
        self.assertNotIn("Traceback", second.stdout + second.stderr)
        self.assertFalse(SAVE.exists())


if __name__ == "__main__":
    unittest.main()
