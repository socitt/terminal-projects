import os
import random
import tempfile
import unittest

import camp
import cats
import clans
import events
import territory
import upkeep
import weather
from game import (
    STARTING_FOOD,
    STARTING_WATER,
    SURVIVAL_GOAL_DAYS,
    advance_day,
    is_game_over,
    load_state,
    new_game,
    outcome,
    save_state,
)


class _FakeRng:
    def __init__(self, randoms=(), randints=(), choices=(), samples=()):
        self._randoms = list(randoms)
        self._randints = list(randints)
        self._choices = list(choices)
        self._samples = list(samples)

    def random(self):
        return self._randoms.pop(0)

    def randint(self, low, high):
        return self._randints.pop(0)

    def choice(self, seq):
        return self._choices.pop(0)

    def sample(self, seq, k):
        return self._samples.pop(0)


def _fixture_state(**overrides):
    state = {
        "clan_name": "Test Clan",
        "region_id": "olympic",
        "day": 5,
        "cats": [
            cats.new_cat("Ash", ["brave"], role="leader"),
            cats.new_cat("Willow", ["quick"], role="healer"),
        ],
        "camp": camp.new_camp(),
        "zones": {
            "home": territory.new_zone("home", "meadow", adjacent=[], explored=True, controlled=True),
        },
        "other_clans": [clans.new_clan("Iron Ridge", 10)],
        "weather": "clear",
        "food": 5,
        "water": 5,
        "event_log": [],
    }
    state.update(overrides)
    return state


# random()/randint() sequence for a day with no player action and every
# background system taking its "nothing happens" branch: weather persists
# (roll < PERSIST_CHANCE), no kit birth (roll >= BIRTH_CHANCE), no event
# (roll >= EVENT_CHANCE), disposition drifts by 0.
_QUIET_RANDOMS = [0.1, 0.99, 0.99]
_QUIET_RANDINTS = [0]


class NewGameTest(unittest.TestCase):
    def test_properties_hold_across_many_seeds(self):
        for seed in range(50):
            state = new_game(random.Random(seed), "Test Clan", "olympic")

            self.assertEqual(state["clan_name"], "Test Clan")
            self.assertEqual(state["region_id"], "olympic")
            self.assertEqual(state["day"], 1)
            self.assertEqual(state["food"], STARTING_FOOD)
            self.assertEqual(state["water"], STARTING_WATER)
            self.assertEqual(state["event_log"], [])
            self.assertEqual(state["camp"], {"structures": []})
            self.assertIn(state["weather"], weather.WEATHER_STATES)

            self.assertIn(len(state["cats"]), (3, 4))
            roles = [cat["role"] for cat in state["cats"]]
            self.assertEqual(roles.count("leader"), 1)
            self.assertEqual(roles.count("healer"), 1)

            self.assertIn(len(state["zones"]), range(6, 11))
            self.assertTrue(state["zones"]["home"]["explored"])
            self.assertTrue(state["zones"]["home"]["controlled"])

            self.assertEqual(len(state["other_clans"]), 1)
            self.assertTrue(-20 <= state["other_clans"][0]["disposition"] <= 20)


class AdvanceDayQuietDayTest(unittest.TestCase):
    def test_day_increments_and_background_systems_apply(self):
        state = _fixture_state()
        rng = _FakeRng(randoms=_QUIET_RANDOMS, randints=_QUIET_RANDINTS)
        updated = advance_day(state, {}, rng)

        self.assertEqual(updated["day"], 6)
        self.assertEqual(updated["weather"], "clear")
        self.assertEqual(updated["other_clans"][0]["disposition"], 10)
        self.assertEqual(updated["cats"], state["cats"])
        self.assertEqual(updated["food"], 5 - 2 * upkeep.FOOD_PER_CAT)
        self.assertEqual(updated["water"], 5 - 2 * upkeep.WATER_PER_CAT)
        self.assertEqual(updated["event_log"], [])

    def test_does_not_mutate_input_state(self):
        state = _fixture_state()
        advance_day(state, {}, _FakeRng(randoms=list(_QUIET_RANDOMS), randints=list(_QUIET_RANDINTS)))
        self.assertEqual(state["day"], 5)
        self.assertEqual(state["food"], 5)


class AdvanceDayHuntTest(unittest.TestCase):
    def test_hunt_in_controlled_zone_adds_food(self):
        state = _fixture_state()
        rng = _FakeRng(
            randoms=[0.5] + _QUIET_RANDOMS,
            randints=[3] + _QUIET_RANDINTS,
        )
        updated = advance_day(state, {"hunt": {"cat": "Ash", "zone": "home"}}, rng)
        self.assertEqual(updated["food"], 8 - 2 * upkeep.FOOD_PER_CAT)
        self.assertEqual(cats.cat_with_role(updated["cats"], "leader")["status"], "healthy")

    def test_large_mammal_encounter_injures_cat_and_yields_no_food(self):
        state = _fixture_state()
        # Extra 0.9 (>= the healer-boosted recovery chance) forces the
        # newly-injured leader's same-day recovery roll to fail, so the
        # injury is still observable at day's end.
        rng = _FakeRng(
            randoms=[0.02, 0.3, 0.9] + _QUIET_RANDOMS,
            randints=list(_QUIET_RANDINTS),
        )
        updated = advance_day(state, {"hunt": {"cat": "Ash", "zone": "home"}}, rng)
        self.assertEqual(updated["food"], 5 - 2 * upkeep.FOOD_PER_CAT)
        self.assertEqual(cats.cat_with_role(updated["cats"], "leader")["status"], "injured")

    def test_raises_for_uncontrolled_zone(self):
        state = _fixture_state(zones={
            "home": territory.new_zone("home", "meadow", explored=False, controlled=False),
        })
        with self.assertRaises(ValueError):
            advance_day(state, {"hunt": {"cat": "Ash", "zone": "home"}}, random.Random(0))

    def test_raises_key_error_for_unknown_zone(self):
        with self.assertRaises(KeyError):
            advance_day(
                _fixture_state(), {"hunt": {"cat": "Ash", "zone": "nowhere"}}, random.Random(0)
            )

    def test_bad_weather_scales_down_hunt_food(self):
        """Same hunt, same rng: storm (0.5x) must yield less than clear."""
        def _run(weather_state):
            rng = _FakeRng(randoms=[0.5] + _QUIET_RANDOMS, randints=[4] + _QUIET_RANDINTS)
            state = _fixture_state(weather=weather_state)
            return advance_day(state, {"hunt": {"cat": "Ash", "zone": "home"}}, rng)["food"]

        self.assertEqual(_run("clear"), 9 - 2 * upkeep.FOOD_PER_CAT)
        self.assertEqual(_run("storm"), 7 - 2 * upkeep.FOOD_PER_CAT)

    def test_injured_cat_is_the_one_that_hunted(self):
        state = _fixture_state()
        # Extra 0.5 (>= the base recovery chance; the healer herself is
        # the one injured here, so no healer bonus applies) forces the
        # same-day recovery roll to fail.
        rng = _FakeRng(randoms=[0.02, 0.3, 0.5] + _QUIET_RANDOMS, randints=list(_QUIET_RANDINTS))
        updated = advance_day(state, {"hunt": {"cat": "Willow", "zone": "home"}}, rng)
        by_name = {cat["name"]: cat for cat in updated["cats"]}
        self.assertEqual(by_name["Willow"]["status"], "injured")
        self.assertEqual(by_name["Ash"]["status"], "healthy")


class AdvanceDayGatherWaterTest(unittest.TestCase):
    def test_gather_water_in_controlled_zone_adds_water(self):
        state = _fixture_state(zones={
            "home": territory.new_zone("home", "riverbank", explored=True, controlled=True),
        })
        rng = _FakeRng(randoms=list(_QUIET_RANDOMS), randints=[4] + _QUIET_RANDINTS)
        updated = advance_day(state, {"gather_water": {"zone": "home"}}, rng)
        self.assertEqual(updated["water"], 9 - 2 * upkeep.WATER_PER_CAT)

    def test_raises_for_uncontrolled_zone(self):
        state = _fixture_state(zones={
            "home": territory.new_zone("home", "riverbank", explored=False, controlled=False),
        })
        with self.assertRaises(ValueError):
            advance_day(state, {"gather_water": {"zone": "home"}}, random.Random(0))

    def test_bad_weather_scales_down_gathered_water(self):
        def _run(weather_state):
            rng = _FakeRng(randoms=list(_QUIET_RANDOMS), randints=[4] + _QUIET_RANDINTS)
            state = _fixture_state(weather=weather_state, zones={
                "home": territory.new_zone(
                    "home", "riverbank", explored=True, controlled=True
                ),
            })
            return advance_day(state, {"gather_water": {"zone": "home"}}, rng)["water"]

        self.assertEqual(_run("clear"), 9 - 2 * upkeep.WATER_PER_CAT)
        self.assertEqual(_run("storm"), 7 - 2 * upkeep.WATER_PER_CAT)


class AdvanceDayPatrolTest(unittest.TestCase):
    def test_patrol_explores_and_controls_when_adjacent_to_controlled(self):
        state = _fixture_state(zones={
            "home": territory.new_zone("home", "forest", adjacent=["a"], explored=True, controlled=True),
            "a": territory.new_zone("a", "meadow", adjacent=["home"]),
        })
        rng = _FakeRng(randoms=list(_QUIET_RANDOMS), randints=list(_QUIET_RANDINTS))
        updated = advance_day(state, {"patrol": {"zone": "a"}}, rng)
        self.assertTrue(updated["zones"]["a"]["explored"])
        self.assertTrue(updated["zones"]["a"]["controlled"])

    def test_patrol_only_explores_when_not_adjacent_to_controlled(self):
        state = _fixture_state(zones={
            "home": territory.new_zone("home", "forest", adjacent=["a"], explored=True, controlled=True),
            "a": territory.new_zone("a", "meadow", adjacent=["home", "b"], explored=True, controlled=False),
            "b": territory.new_zone("b", "ridge", adjacent=["a"]),
        })
        rng = _FakeRng(randoms=list(_QUIET_RANDOMS), randints=list(_QUIET_RANDINTS))
        updated = advance_day(state, {"patrol": {"zone": "b"}}, rng)
        self.assertTrue(updated["zones"]["b"]["explored"])
        self.assertFalse(updated["zones"]["b"]["controlled"])


class AdvanceDayUnlockStructureTest(unittest.TestCase):
    def test_unlocks_structure(self):
        state = _fixture_state()
        rng = _FakeRng(randoms=list(_QUIET_RANDOMS), randints=list(_QUIET_RANDINTS))
        updated = advance_day(state, {"unlock_structure": "nursery"}, rng)
        self.assertEqual(updated["camp"]["structures"], ["nursery"])

    def test_raises_for_unknown_structure(self):
        state = _fixture_state()
        with self.assertRaises(ValueError):
            advance_day(state, {"unlock_structure": "not_real"}, random.Random(0))


class AdvanceDayWeatherTest(unittest.TestCase):
    def test_weather_persists_on_low_roll(self):
        state = _fixture_state(weather="rain")
        rng = _FakeRng(randoms=[0.1, 0.99, 0.99], randints=[0])
        updated = advance_day(state, {}, rng)
        self.assertEqual(updated["weather"], "rain")

    def test_weather_rolls_over_on_high_roll(self):
        state = _fixture_state(weather="rain")
        rng = _FakeRng(randoms=[0.9, 0.99, 0.99], randints=[0], choices=["snow"])
        updated = advance_day(state, {}, rng)
        self.assertEqual(updated["weather"], "snow")


class AdvanceDayPopulationTest(unittest.TestCase):
    def test_kit_birth_appends_new_cat(self):
        state = _fixture_state()
        rng = _FakeRng(
            randoms=[0.1, 0.01, 0.99],
            randints=[0],
            choices=["Otter", "gentle"],
        )
        updated = advance_day(state, {}, rng)
        self.assertEqual(len(updated["cats"]), 3)
        kit = updated["cats"][-1]
        self.assertEqual(kit["name"], "Otter")
        self.assertEqual(kit["traits"], ["gentle"])
        self.assertIsNone(kit["role"])


class AdvanceDayEventTest(unittest.TestCase):
    def test_event_triggers_applies_food_delta_and_logs(self):
        state = _fixture_state()
        chosen_event = events.EVENTS[3]
        rng = _FakeRng(
            randoms=[0.1, 0.99, 0.01],
            randints=[0],
            choices=[chosen_event],
        )
        updated = advance_day(state, {}, rng)
        self.assertEqual(
            updated["food"],
            max(0, 5 - 2 * upkeep.FOOD_PER_CAT + chosen_event["food_delta"]),
        )
        self.assertEqual(updated["event_log"], [
            {"day": 5, "id": chosen_event["id"], "text": chosen_event["text"]},
        ])


class AdvanceDayFoodClampTest(unittest.TestCase):
    def test_negative_event_delta_clamps_food_at_zero(self):
        """food=3 clears upkeep (2 cats, no shortfall) with 1 left, then
        the event's -2 delta pushes it negative — still the clamp this
        test is about, just composed with upkeep instead of standing
        alone."""
        storm_damage = next(e for e in events.EVENTS if e["food_delta"] == -2)
        state = _fixture_state(food=3)
        rng = _FakeRng(randoms=[0.1, 0.99, 0.01], randints=[0], choices=[storm_damage])
        updated = advance_day(state, {}, rng)
        self.assertEqual(updated["food"], 0)


class AdvanceDayCombinedActionsTest(unittest.TestCase):
    def test_all_four_actions_apply_in_one_day(self):
        """Each action is unit-tested in isolation above; this pins that
        they compose in a single advance_day call without clobbering each
        other's slice of the state."""
        state = _fixture_state(zones={
            "home": territory.new_zone(
                "home", "riverbank", adjacent=["a"], explored=True, controlled=True
            ),
            "a": territory.new_zone("a", "meadow", adjacent=["home"]),
        })
        rng = _FakeRng(
            randoms=[0.5] + _QUIET_RANDOMS,
            randints=[3, 4] + _QUIET_RANDINTS,
        )
        updated = advance_day(state, {
            "hunt": {"cat": "Ash", "zone": "home"},
            "gather_water": {"zone": "home"},
            "patrol": {"zone": "a"},
            "unlock_structure": "nursery",
        }, rng)

        self.assertEqual(updated["food"], 8 - 2 * upkeep.FOOD_PER_CAT)
        self.assertEqual(updated["water"], 9 - 2 * upkeep.WATER_PER_CAT)
        self.assertTrue(updated["zones"]["a"]["controlled"])
        self.assertEqual(updated["camp"]["structures"], ["nursery"])
        self.assertEqual(updated["day"], 6)


class AdvanceDayDispositionTest(unittest.TestCase):
    def test_disposition_drifts_by_rng_step(self):
        state = _fixture_state(other_clans=[clans.new_clan("Iron Ridge", 10)])
        rng = _FakeRng(randoms=[0.1, 0.99, 0.99], randints=[-3])
        updated = advance_day(state, {}, rng)
        self.assertEqual(updated["other_clans"][0]["disposition"], 7)


class AdvanceDayPropertyTest(unittest.TestCase):
    def test_invariants_hold_across_many_seeds(self):
        """Cat count is no longer non-decreasing (upkeep can kill an
        already-"sick" cat on a shortfall) — every 5th seed starts with
        a sick leader and low food/water specifically to exercise that
        path here rather than assume it, matching upkeep_test.py's
        direct coverage of the same rule. The lower bound is
        `len(cats) - 2`, not `0`: food and water shortfalls resolve
        independently, so one day can cost at most two cats."""
        for seed in range(100):
            rng = random.Random(seed)
            state = _fixture_state(
                food=rng.randint(0, 4),
                water=rng.randint(0, 4),
                cats=[
                    cats.new_cat(
                        "Ash", ["brave"], role="leader",
                        status="sick" if seed % 5 == 0 else "healthy",
                    ),
                    cats.new_cat("Willow", ["quick"], role="healer"),
                ],
            )
            updated = advance_day(state, {}, rng)

            self.assertEqual(updated["day"], state["day"] + 1)
            self.assertGreaterEqual(updated["food"], 0)
            self.assertGreaterEqual(updated["water"], 0)
            self.assertGreaterEqual(len(updated["cats"]), len(state["cats"]) - 2)
            self.assertLessEqual(len(updated["cats"]), len(state["cats"]) + 1)
            self.assertEqual(set(updated["zones"]), set(state["zones"]))
            self.assertEqual(len(updated["other_clans"]), len(state["other_clans"]))
            self.assertIn(updated["weather"], weather.WEATHER_STATES)


class AdvanceDayUpkeepIntegrationTest(unittest.TestCase):
    """Direct rule coverage lives in upkeep_test.py; these confirm the
    seam actually fires inside advance_day, cats and all."""

    def test_food_shortfall_sickens_the_chosen_cat(self):
        state = _fixture_state(food=0, water=5)
        # Recovery roll (0.9) forced to fail so the new "sick" status is
        # still observable at day's end, same reasoning as the hunt
        # tests above.
        rng = _FakeRng(randoms=[0.9, 0.1, 0.99, 0.99], randints=[0], choices=[state["cats"][0]])
        updated = advance_day(state, {}, rng)

        self.assertEqual(cats.cat_with_role(updated["cats"], "leader")["status"], "sick")
        self.assertEqual(len(updated["cats"]), 2)
        self.assertEqual(updated["food"], 0)

    def test_shortfall_kills_an_already_sick_cat(self):
        state = _fixture_state(food=0, water=5, cats=[
            cats.new_cat("Ash", ["brave"], role="leader", status="sick"),
            cats.new_cat("Willow", ["quick"], role="healer"),
        ])
        rng = _FakeRng(randoms=list(_QUIET_RANDOMS), randints=[0], choices=[state["cats"][0]])
        updated = advance_day(state, {}, rng)

        self.assertEqual([c["name"] for c in updated["cats"]], ["Willow"])


class OutcomeTest(unittest.TestCase):
    def test_none_while_ongoing(self):
        state = _fixture_state(day=1)
        self.assertIsNone(outcome(state))
        self.assertFalse(is_game_over(state))

    def test_lost_when_clan_dies_out(self):
        state = _fixture_state(cats=[])
        self.assertEqual(outcome(state), "lost")
        self.assertTrue(is_game_over(state))

    def test_not_won_on_the_goal_day_itself(self):
        state = _fixture_state(day=SURVIVAL_GOAL_DAYS)
        self.assertIsNone(outcome(state))
        self.assertFalse(is_game_over(state))

    def test_won_after_surviving_past_the_goal_day(self):
        state = _fixture_state(day=SURVIVAL_GOAL_DAYS + 1)
        self.assertEqual(outcome(state), "won")
        self.assertTrue(is_game_over(state))

    def test_lost_takes_priority_over_won(self):
        state = _fixture_state(day=SURVIVAL_GOAL_DAYS + 1, cats=[])
        self.assertEqual(outcome(state), "lost")


class SaveLoadStateTest(unittest.TestCase):
    def test_round_trips_through_json(self):
        state = new_game(random.Random(0), "Test Clan", "olympic")
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "save.json")
            save_state(state, path)
            loaded = load_state(path)
        self.assertEqual(loaded, state)


if __name__ == "__main__":
    unittest.main()
