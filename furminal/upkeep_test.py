import unittest

from upkeep import FOOD_PER_CAT, WATER_PER_CAT, resolve_upkeep


def _cat(name, status="healthy"):
    return {"name": name, "traits": [], "role": None, "status": status}


class _FakeRng:
    """Queue-based fake exposing `choice`, popping the next queued
    return value in call order (ignores the passed-in sequence, same
    convention as the other `furminal` test fakes)."""

    def __init__(self, choices):
        self._choices = list(choices)

    def choice(self, seq):
        return self._choices.pop(0)


class ResolveUpkeepNoShortfallTest(unittest.TestCase):
    def test_consumes_per_cat_with_stores_to_spare(self):
        cats = [_cat("Ash"), _cat("Willow")]
        result = resolve_upkeep(cats, food=10, water=10, rng=_FakeRng([]))

        self.assertEqual(result["food"], 10 - 2 * FOOD_PER_CAT)
        self.assertEqual(result["water"], 10 - 2 * WATER_PER_CAT)
        self.assertFalse(result["food_shortfall"])
        self.assertFalse(result["water_shortfall"])
        self.assertEqual(result["cats"], cats)

    def test_exact_store_is_not_a_shortfall(self):
        cats = [_cat("Ash"), _cat("Willow")]
        result = resolve_upkeep(cats, food=2, water=2, rng=_FakeRng([]))

        self.assertEqual(result["food"], 0)
        self.assertEqual(result["water"], 0)
        self.assertFalse(result["food_shortfall"])
        self.assertFalse(result["water_shortfall"])

    def test_empty_roster_never_shortfalls(self):
        result = resolve_upkeep([], food=0, water=0, rng=_FakeRng([]))
        self.assertEqual(result["cats"], [])
        self.assertFalse(result["food_shortfall"])
        self.assertFalse(result["water_shortfall"])

    def test_does_not_mutate_input(self):
        cats = [_cat("Ash")]
        resolve_upkeep(cats, food=0, water=10, rng=_FakeRng([_cat("Ash")]))
        self.assertEqual(cats[0]["status"], "healthy")


class ResolveUpkeepShortfallTest(unittest.TestCase):
    def test_food_shortfall_sickens_chosen_healthy_cat(self):
        cats = [_cat("Ash"), _cat("Willow")]
        result = resolve_upkeep(cats, food=0, water=10, rng=_FakeRng([_cat("Willow")]))

        self.assertTrue(result["food_shortfall"])
        self.assertFalse(result["water_shortfall"])
        self.assertEqual(result["food"], 0)
        by_name = {c["name"]: c["status"] for c in result["cats"]}
        self.assertEqual(by_name, {"Ash": "healthy", "Willow": "sick"})

    def test_water_shortfall_sickens_chosen_cat(self):
        cats = [_cat("Ash")]
        result = resolve_upkeep(cats, food=10, water=0, rng=_FakeRng([_cat("Ash")]))

        self.assertTrue(result["water_shortfall"])
        self.assertEqual(result["cats"][0]["status"], "sick")

    def test_already_sick_cat_hit_again_dies(self):
        cats = [_cat("Ash", status="sick"), _cat("Willow")]
        result = resolve_upkeep(cats, food=0, water=10, rng=_FakeRng([_cat("Ash")]))

        names = [c["name"] for c in result["cats"]]
        self.assertEqual(names, ["Willow"])

    def test_injured_cat_hit_by_shortfall_becomes_sick(self):
        cats = [_cat("Ash", status="injured")]
        result = resolve_upkeep(cats, food=0, water=10, rng=_FakeRng([_cat("Ash")]))
        self.assertEqual(result["cats"][0]["status"], "sick")

    def test_both_shortfalls_same_day_consume_two_rng_choices(self):
        cats = [_cat("Ash"), _cat("Willow")]
        result = resolve_upkeep(
            cats, food=0, water=0,
            rng=_FakeRng([_cat("Ash"), _cat("Willow")]),
        )

        by_name = {c["name"]: c["status"] for c in result["cats"]}
        self.assertEqual(by_name, {"Ash": "sick", "Willow": "sick"})

    def test_one_shortfall_kills_only_the_chosen_cat(self):
        # Being "sick" is not itself fatal — only the cat the shortfall
        # actually picks dies. Water is covered here so exactly one
        # shortfall resolves.
        cats = [_cat("Ash", status="sick"), _cat("Willow", status="sick")]
        result = resolve_upkeep(
            cats, food=0, water=10, rng=_FakeRng([_cat("Ash")]),
        )
        self.assertEqual([c["name"] for c in result["cats"]], ["Willow"])

    def test_both_shortfalls_can_kill_two_sick_cats_in_one_day(self):
        # The worst case the roster bound in ARCHITECTURE.md §5 has to
        # allow for: food and water shortfalls resolve independently,
        # so a day can cost two cats, not one.
        cats = [_cat("Ash", status="sick"), _cat("Willow", status="sick")]
        result = resolve_upkeep(
            cats, food=0, water=0,
            rng=_FakeRng([_cat("Ash"), _cat("Willow")]),
        )
        self.assertEqual(result["cats"], [])

    def test_shortfall_can_empty_the_roster(self):
        cats = [_cat("Ash", status="sick")]
        result = resolve_upkeep(cats, food=0, water=10, rng=_FakeRng([_cat("Ash")]))
        self.assertEqual(result["cats"], [])

    def test_food_and_water_stay_clamped_at_zero_under_shortfall(self):
        cats = [_cat("Ash")]
        result = resolve_upkeep(cats, food=0, water=0, rng=_FakeRng([_cat("Ash"), _cat("Ash")]))
        self.assertEqual(result["food"], 0)
        self.assertEqual(result["water"], 0)


if __name__ == "__main__":
    unittest.main()
