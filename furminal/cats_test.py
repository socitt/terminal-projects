import random
import unittest

from cats import (
    HEALER_RECOVERY_BONUS,
    RECOVERY_CHANCE,
    TRAITS,
    cat_with_role,
    generate_starting_cats,
    maybe_recover,
    new_cat,
    set_cat_status,
)


class _FakeRng:
    """Queue-based fake exposing `choice`/`sample`/`random`, each call
    popping the next queued return value in call order."""

    def __init__(self, choices=(), samples=(), randoms=()):
        self._choices = list(choices)
        self._samples = list(samples)
        self._randoms = list(randoms)

    def choice(self, seq):
        return self._choices.pop(0)

    def sample(self, seq, k):
        return self._samples.pop(0)

    def random(self):
        return self._randoms.pop(0)


class NewCatTest(unittest.TestCase):
    def test_defaults(self):
        cat = new_cat("Ash", ["brave", "quick"])
        self.assertEqual(cat, {
            "name": "Ash",
            "traits": ["brave", "quick"],
            "role": None,
            "status": "healthy",
        })

    def test_traits_copied_not_aliased(self):
        traits = ["brave"]
        cat = new_cat("Ash", traits)
        traits.append("quick")
        self.assertEqual(cat["traits"], ["brave"])


class GenerateStartingCatsDeterministicTest(unittest.TestCase):
    def test_exact_assignment_from_fake_rng(self):
        rng = _FakeRng(
            choices=[3, 2, 2, 3],
            samples=[
                ["Ash", "Willow", "Moss"],
                ["brave", "quick"],
                ["gentle", "fierce"],
                ["clever", "quiet", "loyal"],
                [1, 2],
            ],
        )
        cats = generate_starting_cats(rng)

        self.assertEqual(len(cats), 3)
        self.assertEqual(cats[0]["name"], "Ash")
        self.assertEqual(cats[0]["traits"], ["brave", "quick"])
        self.assertIsNone(cats[0]["role"])
        self.assertEqual(cats[1]["name"], "Willow")
        self.assertEqual(cats[1]["role"], "leader")
        self.assertEqual(cats[2]["name"], "Moss")
        self.assertEqual(cats[2]["role"], "healer")
        self.assertEqual(cats[2]["traits"], ["clever", "quiet", "loyal"])


class GenerateStartingCatsPropertyTest(unittest.TestCase):
    def test_properties_hold_across_many_seeds(self):
        for seed in range(50):
            cats = generate_starting_cats(random.Random(seed))

            self.assertIn(len(cats), (3, 4))

            names = [c["name"] for c in cats]
            self.assertEqual(len(names), len(set(names)))

            roles = [c["role"] for c in cats]
            self.assertEqual(roles.count("leader"), 1)
            self.assertEqual(roles.count("healer"), 1)
            self.assertEqual(roles.count(None), len(cats) - 2)

            for cat in cats:
                self.assertIn(len(cat["traits"]), (2, 3))
                self.assertEqual(len(cat["traits"]), len(set(cat["traits"])))
                for trait in cat["traits"]:
                    self.assertIn(trait, TRAITS)
                self.assertEqual(cat["status"], "healthy")


class CatWithRoleTest(unittest.TestCase):
    def test_finds_matching_role(self):
        cats = [
            new_cat("Ash", ["brave"], role=None),
            new_cat("Willow", ["quick"], role="leader"),
        ]
        self.assertEqual(cat_with_role(cats, "leader")["name"], "Willow")

    def test_returns_none_when_absent(self):
        cats = [new_cat("Ash", ["brave"])]
        self.assertIsNone(cat_with_role(cats, "healer"))


class SetCatStatusTest(unittest.TestCase):
    def test_updates_matching_cat(self):
        cats = [new_cat("Ash", ["brave"]), new_cat("Willow", ["quick"])]
        updated = set_cat_status(cats, "Ash", "injured")
        self.assertEqual(updated[0]["status"], "injured")
        self.assertEqual(updated[1]["status"], "healthy")

    def test_does_not_mutate_input(self):
        cats = [new_cat("Ash", ["brave"])]
        set_cat_status(cats, "Ash", "injured")
        self.assertEqual(cats[0]["status"], "healthy")

    def test_no_op_when_name_not_found(self):
        cats = [new_cat("Ash", ["brave"])]
        updated = set_cat_status(cats, "Nobody", "injured")
        self.assertEqual(updated, cats)

    def test_preserves_other_fields(self):
        cats = [new_cat("Ash", ["brave"], role="leader")]
        updated = set_cat_status(cats, "Ash", "sick")
        self.assertEqual(updated[0], {
            "name": "Ash", "traits": ["brave"], "role": "leader", "status": "sick",
        })


class MaybeRecoverTest(unittest.TestCase):
    def test_recovers_below_threshold(self):
        cats = [new_cat("Ash", ["brave"], status="sick")]
        rng = _FakeRng(randoms=[RECOVERY_CHANCE - 0.01])
        updated = maybe_recover(cats, rng)
        self.assertEqual(updated[0]["status"], "healthy")

    def test_stays_sick_above_threshold(self):
        cats = [new_cat("Ash", ["brave"], status="sick")]
        rng = _FakeRng(randoms=[RECOVERY_CHANCE + 0.01])
        updated = maybe_recover(cats, rng)
        self.assertEqual(updated[0]["status"], "sick")

    def test_healthy_cats_never_roll(self):
        cats = [new_cat("Ash", ["brave"], status="healthy")]
        updated = maybe_recover(cats, _FakeRng(randoms=[]))
        self.assertEqual(updated[0]["status"], "healthy")

    def test_healer_present_and_healthy_boosts_chance(self):
        cats = [
            new_cat("Ash", ["brave"], status="injured"),
            new_cat("Willow", ["quick"], role="healer", status="healthy"),
        ]
        boosted_threshold = RECOVERY_CHANCE + HEALER_RECOVERY_BONUS - 0.01
        rng = _FakeRng(randoms=[boosted_threshold])
        updated = maybe_recover(cats, rng)
        self.assertEqual(updated[0]["status"], "healthy")

    def test_sick_healer_gives_no_bonus(self):
        cats = [
            new_cat("Ash", ["brave"], status="injured"),
            new_cat("Willow", ["quick"], role="healer", status="sick"),
        ]
        rng = _FakeRng(randoms=[RECOVERY_CHANCE + 0.01, 1.0])
        updated = maybe_recover(cats, rng)
        by_name = {c["name"]: c["status"] for c in updated}
        self.assertEqual(by_name["Ash"], "injured")

    def test_does_not_mutate_input(self):
        cats = [new_cat("Ash", ["brave"], status="sick")]
        maybe_recover(cats, _FakeRng(randoms=[0.0]))
        self.assertEqual(cats[0]["status"], "sick")

    def test_never_adds_or_removes_cats(self):
        cats = [
            new_cat("Ash", ["brave"], status="sick"),
            new_cat("Willow", ["quick"], status="healthy"),
        ]
        updated = maybe_recover(cats, _FakeRng(randoms=[1.0]))
        self.assertEqual(len(updated), 2)


if __name__ == "__main__":
    unittest.main()
