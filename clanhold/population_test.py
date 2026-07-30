import random
import unittest

import cats
from population import BIRTH_CHANCE, maybe_birth_kit


class _FakeRng:
    def __init__(self, randoms=(), choices=()):
        self._randoms = list(randoms)
        self._choices = list(choices)

    def random(self):
        return self._randoms.pop(0)

    def choice(self, seq):
        return self._choices.pop(0)


class MaybeBirthKitTest(unittest.TestCase):
    def test_low_roll_births_a_kit(self):
        rng = _FakeRng(randoms=[0.01], choices=["Otter", "brave"])
        kit = maybe_birth_kit(rng, [])
        self.assertEqual(kit, {
            "name": "Otter",
            "traits": ["brave"],
            "role": None,
            "status": "healthy",
        })

    def test_boundary_roll_at_threshold_does_not_birth(self):
        rng = _FakeRng(randoms=[BIRTH_CHANCE])
        self.assertIsNone(maybe_birth_kit(rng, []))

    def test_high_roll_does_not_birth(self):
        rng = _FakeRng(randoms=[0.9])
        self.assertIsNone(maybe_birth_kit(rng, []))

    def test_picks_a_name_not_already_used(self):
        existing = [cats.new_cat(name, ["brave"]) for name in cats.NAMES if name != "Otter"]
        rng = _FakeRng(randoms=[0.0], choices=["Otter", "quick"])
        kit = maybe_birth_kit(rng, existing)
        self.assertEqual(kit["name"], "Otter")

    def test_returns_none_when_every_name_is_taken(self):
        existing = [cats.new_cat(name, ["brave"]) for name in cats.NAMES]
        rng = _FakeRng(randoms=[0.0])
        self.assertIsNone(maybe_birth_kit(rng, existing))


class MaybeBirthKitPropertyTest(unittest.TestCase):
    def test_result_is_none_or_a_valid_unused_kit(self):
        for seed in range(300):
            existing = [cats.new_cat("Ash", ["brave"])]
            kit = maybe_birth_kit(random.Random(seed), existing)
            if kit is not None:
                self.assertNotEqual(kit["name"], "Ash")
                self.assertIn(kit["name"], cats.NAMES)
                self.assertEqual(len(kit["traits"]), 1)
                self.assertIn(kit["traits"][0], cats.TRAITS)
                self.assertIsNone(kit["role"])
                self.assertEqual(kit["status"], "healthy")

    def test_triggers_roughly_at_expected_rate(self):
        triggered = sum(
            1 for seed in range(3000) if maybe_birth_kit(random.Random(seed), []) is not None
        )
        rate = triggered / 3000
        self.assertTrue(abs(rate - BIRTH_CHANCE) < 0.02)


if __name__ == "__main__":
    unittest.main()
