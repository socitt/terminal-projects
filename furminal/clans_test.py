import random
import unittest

from clans import (
    DISPOSITION_MAX,
    DISPOSITION_MIN,
    NEIGHBOR_CLAN_NAMES,
    border_incident,
    disposition_tier,
    drift_disposition,
    generate_neighbor_clan,
    new_clan,
)


class _FakeRng:
    def __init__(self, choices=(), randints=()):
        self._choices = list(choices)
        self._randints = list(randints)

    def choice(self, seq):
        return self._choices.pop(0)

    def randint(self, low, high):
        return self._randints.pop(0)


class NewClanTest(unittest.TestCase):
    def test_defaults_to_neutral(self):
        self.assertEqual(new_clan("Iron Ridge"), {"name": "Iron Ridge", "disposition": 0})

    def test_clamps_above_max(self):
        clan = new_clan("Iron Ridge", 500)
        self.assertEqual(clan["disposition"], DISPOSITION_MAX)

    def test_clamps_below_min(self):
        clan = new_clan("Iron Ridge", -500)
        self.assertEqual(clan["disposition"], DISPOSITION_MIN)


class GenerateNeighborClanTest(unittest.TestCase):
    def test_exact_from_fake_rng(self):
        rng = _FakeRng(choices=["Grey Marsh"], randints=[7])
        clan = generate_neighbor_clan(rng)
        self.assertEqual(clan, {"name": "Grey Marsh", "disposition": 7})

    def test_properties_hold_across_seeds(self):
        for seed in range(30):
            clan = generate_neighbor_clan(random.Random(seed))
            self.assertIn(clan["name"], NEIGHBOR_CLAN_NAMES)
            self.assertTrue(-20 <= clan["disposition"] <= 20)


class DriftDispositionTest(unittest.TestCase):
    def test_exact_from_fake_rng(self):
        clan = new_clan("Iron Ridge", 10)
        rng = _FakeRng(randints=[-3])
        updated = drift_disposition(clan, rng)
        self.assertEqual(updated["disposition"], 7)

    def test_preserves_name(self):
        clan = new_clan("Iron Ridge", 10)
        updated = drift_disposition(clan, _FakeRng(randints=[2]))
        self.assertEqual(updated["name"], "Iron Ridge")

    def test_does_not_mutate_input(self):
        clan = new_clan("Iron Ridge", 10)
        drift_disposition(clan, _FakeRng(randints=[2]))
        self.assertEqual(clan["disposition"], 10)

    def test_clamps_at_max_over_repeated_drift(self):
        clan = new_clan("Iron Ridge", DISPOSITION_MAX)
        for _ in range(20):
            clan = drift_disposition(clan, _FakeRng(randints=[5]))
        self.assertEqual(clan["disposition"], DISPOSITION_MAX)

    def test_clamps_at_min_over_repeated_drift(self):
        clan = new_clan("Iron Ridge", DISPOSITION_MIN)
        for _ in range(20):
            clan = drift_disposition(clan, _FakeRng(randints=[-5]))
        self.assertEqual(clan["disposition"], DISPOSITION_MIN)


class DispositionTierTest(unittest.TestCase):
    def test_hostile_below_threshold(self):
        self.assertEqual(disposition_tier(-34), "hostile")
        self.assertEqual(disposition_tier(-100), "hostile")

    def test_friendly_above_threshold(self):
        self.assertEqual(disposition_tier(34), "friendly")
        self.assertEqual(disposition_tier(100), "friendly")

    def test_neutral_in_between(self):
        self.assertEqual(disposition_tier(-33), "neutral")
        self.assertEqual(disposition_tier(0), "neutral")
        self.assertEqual(disposition_tier(33), "neutral")



class BorderIncidentTest(unittest.TestCase):
    RULES = {
        "hostile": {"chance": 0.3, "food": -2, "water": 0, "text": "{rival} raided."},
        "friendly": {"chance": 0.2, "food": 0, "water": 1, "text": "{rival} gave."},
    }

    class _Rng:
        def __init__(self, *rolls):
            self.rolls = list(rolls)

        def random(self):
            return self.rolls.pop(0)

    def test_a_neutral_clan_does_nothing_and_rolls_nothing(self):
        rng = self._Rng()
        self.assertIsNone(border_incident(new_clan("Ridge", 0), self.RULES, rng))

    def test_a_hostile_clan_raids_on_a_low_roll(self):
        incident = border_incident(new_clan("Ridge", -50), self.RULES, self._Rng(0.1))
        self.assertEqual(incident, {"food": -2, "water": 0, "text": "Ridge raided."})
        self.assertIsNone(border_incident(new_clan("Ridge", -50), self.RULES,
                                          self._Rng(0.5)))

    def test_a_friendly_clan_gives_on_a_low_roll(self):
        incident = border_incident(new_clan("Ridge", 50), self.RULES, self._Rng(0.1))
        self.assertEqual(incident["water"], 1)
        self.assertEqual(incident["text"], "Ridge gave.")

if __name__ == "__main__":
    unittest.main()
