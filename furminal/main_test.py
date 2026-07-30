"""Integration test for main.py: runs the real script -- real
region-explorer map data, real `random`, the real save path next to
main.py -- with piped stdin, same style as region-explorer's and the
adventure-engine stories' main_test.py.

What only this layer can cover is the start flow: region-explorer's
zoom UI driven all the way to a settled region, then a camp spot, then
a named clan, then the day loop. `runner_test.py` covers the loop's
branches against fixture states, and every rule underneath has its own
unit tests; nothing here re-checks those.

Outcomes are deliberately not asserted. main.py owns the real `random`
and the real `SURVIVAL_GOAL_DAYS`, so which ending a scripted
playthrough reaches is not fixed -- `runner_test.py` pins win and loss
down by injecting an rng and patching the goal. The claim here is that
a whole game runs start to finish through the real entrypoint.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"
SAVE = Path(__file__).resolve().parent / "save.json"

# Olympic Peninsula, no zoom animation (which would sleep for real),
# settle there, first camp spot, clan name.
_START = "1\nn\ny\n1\nHollowpine\n"

# More quiet days than any clan can survive on its starting stores, so
# the run ends on its own instead of on exhausted stdin. Unread lines
# are harmless; a short script would be an EOFError.
_QUIET_DAYS = "e\n\n" * 40


def _run(input_text, timeout=60):
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class MainEndToEndTest(unittest.TestCase):
    def setUp(self):
        SAVE.unlink(missing_ok=True)

    def tearDown(self):
        SAVE.unlink(missing_ok=True)

    def test_start_flow_founds_a_clan_and_plays_through_to_an_ending(self):
        result = _run(_START + _QUIET_DAYS)
        self.assertEqual(result.returncode, 0)

        # Region-explorer's picker, then furminal's own two questions.
        self.assertIn("Olympic Peninsula", result.stdout)
        self.assertIn("Settle here?", result.stdout)
        self.assertIn("Where does the clan make camp?", result.stdout)
        self.assertIn("Hollowpine -- Day 1", result.stdout)

        # A day resolved, was reported, and the game reached an ending.
        self.assertIn("End of day 1", result.stdout)
        self.assertTrue(
            "has died out" in result.stdout or "You win!" in result.stdout,
            "playthrough never reached an ending",
        )
        self.assertFalse(SAVE.exists())
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_quitting_region_selection_founds_nothing(self):
        result = _run("q\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Where does the clan make camp?", result.stdout)
        self.assertNotIn("Name your clan", result.stdout)
        self.assertFalse(SAVE.exists())
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_save_and_resume_across_two_runs(self):
        first = _run(_START + "s\n")
        self.assertEqual(first.returncode, 0)
        self.assertIn("Saved. Run again to resume.", first.stdout)
        self.assertTrue(SAVE.exists())
        with open(SAVE) as f:
            saved = json.load(f)
        self.assertEqual(saved["clan_name"], "Hollowpine")
        self.assertEqual(saved["day"], 1)

        # The resumed run must not walk back through region selection.
        second = _run("y\ns\n")
        self.assertEqual(second.returncode, 0)
        self.assertIn("Saved clan found", second.stdout)
        self.assertIn("Hollowpine -- Day 1", second.stdout)
        self.assertNotIn("Olympic Peninsula", second.stdout)
        self.assertNotIn("Traceback", second.stdout + second.stderr)

    def test_declining_the_resume_prompt_starts_a_new_clan(self):
        first = _run(_START + "s\n")
        self.assertEqual(first.returncode, 0)
        self.assertTrue(SAVE.exists())

        second = _run("n\n" + "1\nn\ny\n1\nSecondclan\n" + "s\n")
        self.assertEqual(second.returncode, 0)
        self.assertIn("Secondclan -- Day 1", second.stdout)
        self.assertNotIn("Traceback", second.stdout + second.stderr)
        with open(SAVE) as f:
            saved = json.load(f)
        self.assertEqual(saved["clan_name"], "Secondclan")


if __name__ == "__main__":
    unittest.main()
