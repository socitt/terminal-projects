import random
import unittest

from weather import (
    PERSIST_CHANCE,
    WEATHER_STATES,
    YIELD_MULTIPLIER,
    advance_weather,
    yield_multiplier,
)


class _FakeRng:
    def __init__(self, randoms=(), choices=()):
        self._randoms = list(randoms)
        self._choices = list(choices)

    def random(self):
        return self._randoms.pop(0)

    def choice(self, seq):
        return self._choices.pop(0)


class AdvanceWeatherTest(unittest.TestCase):
    def test_low_roll_persists(self):
        rng = _FakeRng(randoms=[0.1])
        self.assertEqual(advance_weather("rain", rng), "rain")

    def test_boundary_roll_at_persist_threshold_does_not_persist(self):
        rng = _FakeRng(randoms=[PERSIST_CHANCE], choices=["storm"])
        self.assertEqual(advance_weather("rain", rng), "storm")

    def test_high_roll_rolls_to_a_different_state(self):
        rng = _FakeRng(randoms=[0.99], choices=["snow"])
        result = advance_weather("clear", rng)
        self.assertEqual(result, "snow")

    def test_roll_over_never_offers_current_state_as_a_choice(self):
        captured = {}

        class _CapturingRng:
            def random(self):
                return 0.99

            def choice(self, seq):
                captured["seq"] = list(seq)
                return seq[0]

        advance_weather("storm", _CapturingRng())
        self.assertNotIn("storm", captured["seq"])
        self.assertEqual(set(captured["seq"]), set(WEATHER_STATES) - {"storm"})


class AdvanceWeatherPropertyTest(unittest.TestCase):
    def test_always_returns_a_valid_state_across_seeds(self):
        for state in WEATHER_STATES:
            for seed in range(30):
                result = advance_weather(state, random.Random(seed))
                self.assertIn(result, WEATHER_STATES)


class YieldMultiplierTest(unittest.TestCase):
    def test_matches_table_for_every_state(self):
        for state in WEATHER_STATES:
            self.assertEqual(yield_multiplier(state), YIELD_MULTIPLIER[state])

    def test_always_positive_and_at_most_one(self):
        for state in WEATHER_STATES:
            multiplier = yield_multiplier(state)
            self.assertTrue(0 < multiplier <= 1.0)


if __name__ == "__main__":
    unittest.main()
