import random
import unittest

from hunting import (
    FOOD_YIELD,
    INJURY_CHANCE,
    LARGE_MAMMAL_CHANCE,
    MINOR_WILDLIFE_CHANCE,
    WATER_TERRAIN,
    resolve_hunt,
    resolve_water_gathering,
)


class _FakeRng:
    def __init__(self, randoms=(), randints=()):
        self._randoms = list(randoms)
        self._randints = list(randints)

    def random(self):
        return self._randoms.pop(0)

    def randint(self, low, high):
        return self._randints.pop(0)


class ResolveHuntTest(unittest.TestCase):
    def test_low_roll_is_large_mammal_and_scares_off_catch(self):
        rng = _FakeRng(randoms=[0.05, 0.3])
        result = resolve_hunt("forest", rng)
        self.assertEqual(result, {"food": 0, "encounter": "large_mammal", "injured": True})

    def test_large_mammal_high_injury_roll_is_uninjured(self):
        rng = _FakeRng(randoms=[0.0, 0.9])
        result = resolve_hunt("forest", rng)
        self.assertEqual(result["encounter"], "large_mammal")
        self.assertFalse(result["injured"])

    def test_boundary_roll_at_large_mammal_threshold_is_not_large_mammal(self):
        rng = _FakeRng(randoms=[LARGE_MAMMAL_CHANCE], randints=[2])
        result = resolve_hunt("forest", rng)
        self.assertEqual(result["encounter"], "minor_wildlife")

    def test_mid_roll_is_minor_wildlife_with_normal_food(self):
        rng = _FakeRng(randoms=[0.2], randints=[3])
        result = resolve_hunt("forest", rng)
        self.assertEqual(result, {"food": 3, "encounter": "minor_wildlife", "injured": False})

    def test_boundary_roll_at_combined_threshold_is_none(self):
        rng = _FakeRng(randoms=[LARGE_MAMMAL_CHANCE + MINOR_WILDLIFE_CHANCE], randints=[1])
        result = resolve_hunt("forest", rng)
        self.assertEqual(result["encounter"], "none")

    def test_high_roll_is_none_with_normal_food(self):
        rng = _FakeRng(randoms=[0.9], randints=[1])
        result = resolve_hunt("forest", rng)
        self.assertEqual(result, {"food": 1, "encounter": "none", "injured": False})


class ResolveHuntPropertyTest(unittest.TestCase):
    def test_properties_hold_across_terrains_and_seeds(self):
        for terrain in FOOD_YIELD:
            low, high = FOOD_YIELD[terrain]
            for seed in range(30):
                result = resolve_hunt(terrain, random.Random(seed))

                self.assertIn(result["encounter"], ("none", "minor_wildlife", "large_mammal"))
                if result["encounter"] == "large_mammal":
                    self.assertEqual(result["food"], 0)
                else:
                    self.assertFalse(result["injured"])
                    self.assertTrue(low <= result["food"] <= high)


class ResolveWaterGatheringTest(unittest.TestCase):
    def test_water_terrain_uses_wide_range(self):
        rng = _FakeRng(randints=[4])
        self.assertEqual(resolve_water_gathering("riverbank", rng), {"water": 4})

    def test_non_water_terrain_uses_narrow_range(self):
        rng = _FakeRng(randints=[1])
        self.assertEqual(resolve_water_gathering("ridge", rng), {"water": 1})

    def test_properties_hold_across_seeds(self):
        for seed in range(30):
            water_result = resolve_water_gathering("wetland", random.Random(seed))
            self.assertTrue(2 <= water_result["water"] <= 4)
            dry_result = resolve_water_gathering("cave", random.Random(seed))
            self.assertTrue(0 <= dry_result["water"] <= 1)

    def test_water_terrain_constant_matches_usage(self):
        self.assertEqual(WATER_TERRAIN, frozenset({"riverbank", "wetland"}))


if __name__ == "__main__":
    unittest.main()
