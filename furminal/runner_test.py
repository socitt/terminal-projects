"""Tests for runner.py, in two layers.

`RunnerEndToEndTest` and below run the real interactive loop as a
subprocess with piped input, same style as adventure-engine's and
region-explorer's runner_test.py. They use a hand-built fixture
game_state (not `game.new_game`) with ample food/water so outcomes are
deterministic regardless of `rng` -- only the loss-path test needs a
shortfall, and a single already-"sick" cat makes that deterministic
too, since `rng.choice` over a one-cat list has only one possible
result.

`DayReportLinesTest` calls `runner._day_report_lines` directly instead:
it is pure (two states in, strings out) and every branch is a
before/after pair that would take a whole scripted playthrough to reach
through the subprocess layer.

Note the input scripts below interleave a blank line after each ended
day -- that's the "Press Enter to start the next day" prompt on the day
report. A day that ends the game shows no report, so no blank line.
"""

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RUNNER_DIR))

import runner

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
            repr(_two_cat_state()), "e\n\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 2",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("You win!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_hunting_prompts_for_zone_and_cat(self):
        result = _run(
            repr(_two_cat_state()), "h\n1\n1\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 1",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Hunt in which zone?", result.stdout)
        self.assertIn("Send which cat?", result.stdout)
        self.assertIn("You win!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_queued_action_is_shown_while_planning_the_day(self):
        result = _run(
            repr(_two_cat_state()), "h\n1\n1\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 1",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Planned today:", result.stdout)
        self.assertIn("Hunt: Ash in home", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_clearing_planned_actions_drops_them_before_the_day_resolves(self):
        # Queue the nursery, clear, then end the day: the saved state
        # proves the unlock never reached `advance_day`, which asserting
        # on cumulative stdout could not.
        result = _run(repr(_two_cat_state()), "u\n1\nc\ne\n\ns\n", self.save_path)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

        with open(self.save_path) as f:
            saved = json.load(f)
        self.assertEqual(saved["camp"]["structures"], [])

    def test_patrol_explores_and_immediately_controls_an_adjacent_zone(self):
        extra_zones = {
            "a": {
                "id": "a", "terrain": "forest", "adjacent": ["home"],
                "explored": False, "controlled": False,
            },
        }
        result = _run(
            repr(_two_cat_state(extra_zones=extra_zones)), "p\n1\ne\n\ne\n", self.save_path,
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
            repr(_two_cat_state(extra_zones=extra_zones)), "p\n1\ne\n\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 2",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("a (forest) -- controlled", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_unlock_structure_updates_camp_and_menu(self):
        result = _run(
            repr(_two_cat_state()), "u\n1\ne\n\ns\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 5",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Camp: Nursery", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_save_and_quit_writes_a_resumable_save_file(self):
        result = _run(repr(_two_cat_state()), "u\n1\ne\n\ns\n", self.save_path)
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
        result = _run(repr(state), "e\n", self.save_path)
        self.assertEqual(result.returncode, 0)
        self.assertIn("has died out", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class StartFlowTest(unittest.TestCase):
    """The region-pick half of the start flow needs region-explorer's
    whole zoom UI driven through it, so it is covered end-to-end in
    main_test.py against the real entrypoint. Here: the resume branch,
    which never reaches region-explorer, and the pure spot summary."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.save_path = Path(self.tmp.name) / "save.json"

    def test_resumes_from_an_existing_save_when_asked(self):
        saved = _two_cat_state()
        saved["day"] = 7
        with open(self.save_path, "w") as f:
            json.dump(saved, f)

        script = _FIXTURE_PREAMBLE + textwrap.dedent(f"""
            state = runner.start_flow({str(self.save_path)!r})
            print("RESUMED_DAY", state["day"])
            """)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(script)
            script_path = f.name
        result = subprocess.run(
            [sys.executable, script_path], input="y\n",
            capture_output=True, text=True, timeout=15,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("RESUMED_DAY 7", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_spot_summary_names_the_terrain_size_and_borders(self):
        zones = {
            "home": {"id": "home", "terrain": "meadow",
                     "adjacent": ["a", "b"], "explored": True, "controlled": True},
            "a": {"id": "a", "terrain": "riverbank", "adjacent": ["home"],
                  "explored": False, "controlled": False},
            "b": {"id": "b", "terrain": "ridge", "adjacent": ["home"],
                  "explored": False, "controlled": False},
        }
        self.assertEqual(
            runner._spot_summary(zones),
            "meadow (3 zones, borders riverbank, ridge)",
        )


class DayReportEndToEndTest(unittest.TestCase):
    """The report screen itself: that it renders between days, and that
    a triggered event reaches the player rather than only `event_log`."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.save_path = Path(self.tmp.name) / "save.json"

    def test_report_shows_the_day_and_the_store_change(self):
        result = _run(
            repr(_two_cat_state(food=10, water=10)), "e\n\ne\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 2",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("End of day 1", result.stdout)
        # Two cats at 1 food and 1 water each.
        self.assertIn("Food 10 -> 8, water 10 -> 8.", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_report_shows_a_triggered_event(self):
        # A single-entry EVENTS table at a certainty EVENT_CHANCE makes
        # the roll deterministic without reaching into the rng.
        result = _run(
            repr(_two_cat_state()), "e\n\ne\n", self.save_path,
            # One physical line: `_run` interpolates `extra_setup` into
            # an indented template before dedenting it, so a multi-line
            # value would land with a broken indent.
            extra_setup=(
                "import events; game.SURVIVAL_GOAL_DAYS = 2; "
                "events.EVENT_CHANCE = 1.0; events.EVENTS = ["
                "{'id': 'probe', 'text': 'A test omen crosses camp.', "
                "'food_delta': 0}]"
            ),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("A test omen crosses camp.", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_no_report_on_the_day_the_game_ends(self):
        result = _run(
            repr(_two_cat_state()), "e\n", self.save_path,
            extra_setup="game.SURVIVAL_GOAL_DAYS = 1",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("You win!", result.stdout)
        self.assertNotIn("End of day", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class DayReportLinesTest(unittest.TestCase):
    """`runner._day_report_lines` directly -- pure, and each branch is a
    before/after pair that a scripted playthrough can only reach by
    luck."""

    def _states(self, **after_overrides):
        before = _two_cat_state()
        after = {**before, "day": before["day"] + 1, **after_overrides}
        return before, after

    def test_quiet_day_reports_only_the_stores(self):
        before, after = self._states(food=98, water=98)
        self.assertEqual(
            runner._day_report_lines(before, after),
            ["Food 100 -> 98, water 100 -> 98."],
        )

    def test_reports_death_sickness_and_recovery(self):
        before = _two_cat_state()
        before["cats"] = [
            {"name": "Ash", "traits": [], "role": "leader", "status": "sick"},
            {"name": "Willow", "traits": [], "role": "healer", "status": "healthy"},
            {"name": "Moss", "traits": [], "role": None, "status": "injured"},
        ]
        after = {
            **before,
            "cats": [
                {"name": "Willow", "traits": [], "role": "healer", "status": "sick"},
                {"name": "Moss", "traits": [], "role": None, "status": "healthy"},
            ],
        }
        lines = runner._day_report_lines(before, after)
        self.assertIn("Ash has died.", lines)
        self.assertIn("Willow is now sick.", lines)
        self.assertIn("Moss has recovered.", lines)

    def test_reports_a_kit_birth(self):
        before, after = self._states()
        after["cats"] = before["cats"] + [
            {"name": "Fern", "traits": ["quiet"], "role": None, "status": "healthy"},
        ]
        self.assertIn("A kit is born: Fern.", runner._day_report_lines(before, after))

    def test_reports_a_weather_change_but_not_a_persisting_one(self):
        before, after = self._states(weather="storm")
        self.assertIn("The weather turns to storm.", runner._day_report_lines(before, after))

        _, unchanged = self._states(weather=before["weather"])
        self.assertNotIn(
            "The weather turns to clear.", runner._day_report_lines(before, unchanged)
        )

    def test_reports_scouting_and_claiming_separately(self):
        before = _two_cat_state(extra_zones={
            "a": {"id": "a", "terrain": "forest", "adjacent": ["home"],
                  "explored": False, "controlled": False},
            "b": {"id": "b", "terrain": "ridge", "adjacent": ["home"],
                  "explored": False, "controlled": False},
        })
        scouted = {
            **before,
            "zones": {**before["zones"],
                      "a": {**before["zones"]["a"], "explored": True}},
        }
        self.assertIn("a has been scouted.", runner._day_report_lines(before, scouted))

        claimed = {
            **before,
            "zones": {**before["zones"],
                      "a": {**before["zones"]["a"], "explored": True, "controlled": True}},
        }
        lines = runner._day_report_lines(before, claimed)
        self.assertIn("a is now clan territory.", lines)
        self.assertNotIn("a has been scouted.", lines)

    def test_reports_new_events_only(self):
        before = _two_cat_state()
        before["event_log"] = [{"day": 1, "id": "old", "text": "Yesterday's news."}]
        after = {
            **before,
            "event_log": before["event_log"] + [
                {"day": 2, "id": "new", "text": "Today's news."},
            ],
        }
        lines = runner._day_report_lines(before, after)
        self.assertIn("Today's news.", lines)
        self.assertNotIn("Yesterday's news.", lines)


if __name__ == "__main__":
    unittest.main()
