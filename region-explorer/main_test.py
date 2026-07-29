"""Integration test for main.py: runs the real script (real
Washington data, not a fixture) with piped stdin, same style as every
board game's main_test.py. Covers the real STATE actually wiring
together correctly through runner.py/engine.py end-to-end; the
individual pieces (crop/scale/zoom logic, data integrity, I/O
wiring against a fixture) are already covered by engine_test.py,
data/washington_test.py, and runner_test.py.
"""

import subprocess
import sys
import unittest
from pathlib import Path

MAIN_PATH = Path(__file__).resolve().parent / "main.py"


def _run(input_text, timeout=15):
    return subprocess.run(
        [sys.executable, str(MAIN_PATH)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class MainEndToEndTest(unittest.TestCase):
    def test_overview_shows_washington_and_all_six_regions_then_quits(self):
        result = _run("q\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Washington", result.stdout)
        for name in [
            "Olympic Peninsula",
            "Puget Sound",
            "North Cascades",
            "South Cascades",
            "Columbia Basin",
            "Inland Northwest",
        ]:
            self.assertIn(name, result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_visiting_a_region_without_animation_shows_its_landmarks(self):
        result = _run("1\nn\n\nq\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Hoh Rain Forest", result.stdout)
        self.assertIn("Mount Olympus", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_visiting_every_region_in_one_run_reaches_all_detail_arts(self):
        # 1-6, no animation each time, back to overview between each.
        script = "".join(f"{i}\nn\n\n" for i in range(1, 7)) + "q\n"
        result = _run(script, timeout=20)
        self.assertEqual(result.returncode, 0)
        for landmark in [
            "Mount Olympus",
            "Seattle",
            "Mount Baker",
            "Mount Rainier",
            "Yakima Valley orchards",
            "Spokane",
        ]:
            self.assertIn(landmark, result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
