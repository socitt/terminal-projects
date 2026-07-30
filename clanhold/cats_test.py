import random
import unittest

from cats import ROLES, TRAITS, cat_with_role, generate_starting_cats, new_cat


class _FakeRng:
    """Queue-based fake exposing `choice`/`sample`, each call popping the
    next queued return value in call order."""

    def __init__(self, choices, samples):
        self._choices = list(choices)
        self._samples = list(samples)

    def choice(self, seq):
        return self._choices.pop(0)

    def sample(self, seq, k):
        return self._samples.pop(0)


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

    def test_roles_constant_matches_usage(self):
        self.assertEqual(ROLES, ("leader", "healer"))


if __name__ == "__main__":
    unittest.main()
