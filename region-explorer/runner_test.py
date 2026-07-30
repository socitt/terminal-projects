"""End-to-end tests for runner.py: run the real interactive loop as a
subprocess with piped input, same style as adventure-engine's
runner_test.py, against a tiny fixture STATE (not real Washington
data). Covers the I/O wiring itself (overview rendering, region
selection, animate y/n prompt, zoom rendering, quit) -- crop/scale/
zoom-frame logic itself is already covered by engine_test.py.
"""

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent

# `runner.run` takes an injectable `sleep_fn` (same reasoning as
# `backgammon.roll_dice` taking an rng); the fixture below passes a
# fake that counts calls instead of actually sleeping, and prints the
# count. That lets tests assert on whether the animate y/n answer was
# actually honored by call count, instead of racing real wall-clock
# delays against subprocess overhead (which proved flaky under load).
FIXTURE_SCRIPT = textwrap.dedent(f"""
    import sys
    sys.path.insert(0, {str(RUNNER_DIR)!r})
    import runner

    state = {{
        "name": "Fixtureland",
        "art": [
            "12345678",
            "abcdefgh",
            "ABCDEFGH",
            "!@#$%^&*",
        ],
        "regions": [
            {{
                "id": "north",
                "name": "Northern Reach",
                "center": (0, 2),
                "detail_art": ["NORTH DETAIL", "row two"],
                "landmarks": ["The Frostpeak", "Icebound Lake"],
            }},
            {{
                "id": "south",
                "name": "Southern Marsh",
                "center": (3, 5),
                "detail_art": ["SOUTH DETAIL", "row two"],
                "landmarks": ["The Mire", "Reed Village"],
            }},
        ],
    }}

    sleep_calls = []
    runner.run(state, sleep_fn=sleep_calls.append)
    print(f"SLEEP_CALLS={{len(sleep_calls)}}")
    """)


def _run(fixture_path, input_text, timeout=15):
    return subprocess.run(
        [sys.executable, str(fixture_path)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class RunnerEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fixture_path = Path(self.tmp.name) / "fixture_main.py"
        self.fixture_path.write_text(FIXTURE_SCRIPT)

    def test_overview_lists_all_regions_then_quits(self):
        result = _run(self.fixture_path, "q\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Fixtureland", result.stdout)
        self.assertIn("1. Northern Reach", result.stdout)
        self.assertIn("2. Southern Marsh", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_selecting_a_region_without_animation_shows_its_detail_art(self):
        result = _run(self.fixture_path, "1\nn\n\nq\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Northern Reach", result.stdout)
        self.assertIn("NORTH DETAIL", result.stdout)
        self.assertIn("The Frostpeak", result.stdout)
        self.assertIn("Icebound Lake", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        # No animation was requested -- the "n" answer must actually
        # be honored, not just eventually reach the detail art.
        self.assertIn("SLEEP_CALLS=0", result.stdout)

    def test_selecting_a_region_with_animation_still_ends_on_detail_art(self):
        result = _run(self.fixture_path, "2\ny\n\nq\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Southern Marsh", result.stdout)
        self.assertIn("SOUTH DETAIL", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertIn("SLEEP_CALLS=3", result.stdout)

    def test_back_to_overview_allows_picking_a_second_region(self):
        # After viewing region 1, pressing Enter returns to the
        # overview where region 2 can then be picked -- proves the
        # loop actually returns rather than exiting after one view.
        result = _run(self.fixture_path, "1\nn\n\n2\nn\n\nq\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("NORTH DETAIL", result.stdout)
        self.assertIn("SOUTH DETAIL", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_invalid_region_choice_is_rejected_and_reprompts(self):
        # "9" isn't a valid region number (only 1-2 exist); the prompt
        # should reject it and wait for a real choice rather than
        # crashing or silently accepting it.
        result = _run(self.fixture_path, "9\nq\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


SELECT_REGION_FIXTURE_SCRIPT = textwrap.dedent(f"""
    import sys
    sys.path.insert(0, {str(RUNNER_DIR)!r})
    import runner

    state = {{
        "name": "Fixtureland",
        "art": [
            "12345678",
            "abcdefgh",
            "ABCDEFGH",
            "!@#$%^&*",
        ],
        "regions": [
            {{
                "id": "north",
                "name": "Northern Reach",
                "center": (0, 2),
                "detail_art": ["NORTH DETAIL", "row two"],
                "landmarks": ["The Frostpeak", "Icebound Lake"],
            }},
            {{
                "id": "south",
                "name": "Southern Marsh",
                "center": (3, 5),
                "detail_art": ["SOUTH DETAIL", "row two"],
                "landmarks": ["The Mire", "Reed Village"],
            }},
        ],
    }}

    sleep_calls = []
    picked = runner.select_region(state, sleep_fn=sleep_calls.append)
    print(f"PICKED={{picked['id'] if picked else None}}")
    """)


class SelectRegionEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fixture_path = Path(self.tmp.name) / "fixture_select.py"
        self.fixture_path.write_text(SELECT_REGION_FIXTURE_SCRIPT)

    def test_confirming_a_region_returns_it(self):
        result = _run(self.fixture_path, "1\nn\ny\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("PICKED=north", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_declining_returns_to_overview_to_pick_again(self):
        # Decline the first pick ("n" at "Settle here?"), then pick the
        # other region and confirm it -- proves the loop actually
        # returns to the overview rather than exiting on decline.
        result = _run(self.fixture_path, "1\nn\nn\n2\nn\ny\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("PICKED=south", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_quitting_from_overview_returns_none(self):
        result = _run(self.fixture_path, "q\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("PICKED=None", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_confirming_with_animation_still_returns_the_region(self):
        result = _run(self.fixture_path, "2\ny\ny\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("PICKED=south", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
