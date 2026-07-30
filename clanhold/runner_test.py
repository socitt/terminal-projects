"""End-to-end tests for runner.py: run the real interactive loop as a
subprocess with piped input, same style as adventure-engine's and
region-explorer's runner_test.py. Uses a hand-built fixture game_state
(not `game.new_game`) with ample food/water so outcomes are
deterministic regardless of `rng` -- only the loss-path test needs a
shortfall, and a single already-"sick" cat makes that deterministic
too, since `rng.choice` over a one-cat list has only one possible
result.
"""

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent

_FIXTURE_PREAMBLE = textwrap.dedent(f"""
    import sys, random
    sys.path.insert(0, {str(RUNNER_DIR)!r})
    import camp, game, runner
    """)


def _two_cat_state(food=100, water=100, extra_zones=None):
    zones = {
        "home": {
            "id": "home", "terrain": "meadow",
            "adjacent": list(extra_zones or {}), "explored": True, "controlled": True,
        },
    }
    if extra_zones:
        zones.update(extra_zones)
    return {
        "clan_name": "Test Clan",
        "region_id": "olympic",
        "day": 1,
        "cats": [
            {"name": "Ash", "traits": ["brave"], "role": "leader", "status": "healthy"},
            {"name": "Willow", "traits": ["quick"], "role": "healer", "status": "healthy"},
        ],
        "camp": {"structures": []},
        "zones": zones,
        "other_clans": [{"name": "Iron Ridge", "disposition": 10}],
        "weather": "clear",
        "food": food,
        "water": water,
        "event_log": [],
    }


def _run(state_literal, input_text, save_path, extra_setup="", timeout=15):
    script = _FIXTURE_PREAMBLE + textwrap.dedent(f"""
        {extra_setup}
        state = {state_literal}
        runner.run(state, {str(save_path)!r}, rng=random.Random(0))
        """)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name
    return subprocess.run(
        [sys.executable, script_path],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class RunnerEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.save_path = Path(self.tmp.name) / "save.json"

    def test_quiet_days_reach_the_survival_goal(self):
        result = _run(
            repr(_two_cat_state()), "e\ne\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 2",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("You win!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_hunting_prompts_for_zone_and_cat(self):
        result = _run(
            repr(_two_cat_state()), "h\n1\n1\ne\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 1",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Hunt in which zone?", result.stdout)
        self.assertIn("Send which cat?", result.stdout)
        self.assertIn("You win!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_patrol_explores_and_immediately_controls_an_adjacent_zone(self):
        extra_zones = {
            "a": {
                "id": "a", "terrain": "forest", "adjacent": ["home"],
                "explored": False, "controlled": False,
            },
        }
        result = _run(
            repr(_two_cat_state(extra_zones=extra_zones)), "p\n1\ne\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 2",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("a (forest) -- unknown", result.stdout)
        self.assertIn("a (forest) -- controlled", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_patrol_offers_an_already_explored_uncontrolled_zone(self):
        # Distinct from the explore-and-control case above: "a" is
        # already explored (so `can_explore` is False) but not yet
        # controlled, and adjacent to controlled "home" (so
        # `can_control` is True) -- this is the case a patrol-targets
        # filter that only checked `can_explore` would silently drop.
        extra_zones = {
            "a": {
                "id": "a", "terrain": "forest", "adjacent": ["home"],
                "explored": True, "controlled": False,
            },
        }
        result = _run(
            repr(_two_cat_state(extra_zones=extra_zones)), "p\n1\ne\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 2",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("a (forest) -- controlled", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_unlock_structure_updates_camp_and_menu(self):
        result = _run(
            repr(_two_cat_state()), "u\n1\ne\ns\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 5",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Camp: Nursery", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_save_and_quit_writes_a_resumable_save_file(self):
        result = _run(repr(_two_cat_state()), "u\n1\ne\ns\n", self.save_path)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Saved. Run again to resume.", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

        with open(self.save_path) as f:
            saved = json.load(f)
        self.assertEqual(saved["clan_name"], "Test Clan")
        self.assertEqual(saved["day"], 2)
        self.assertEqual(saved["camp"]["structures"], ["nursery"])

    def test_clan_dying_out_shows_the_loss_message(self):
        # One already-"sick" cat with no food/water: the shortfall that
        # hits it on upkeep is a guaranteed death (rng.choice over a
        # one-cat list has only one possible outcome), so this needs no
        # hunting/patrol input to reach a deterministic loss.
        state = _two_cat_state(food=0, water=0)
        state["cats"] = [
            {"name": "Ash", "traits": ["brave"], "role": "leader", "status": "sick"},
        ]
        result = _run(repr(state), "e\ne\ne\n", self.save_path)
        self.assertEqual(result.returncode, 0)
        self.assertIn("has died out", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
