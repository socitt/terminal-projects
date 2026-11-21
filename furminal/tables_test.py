import copy
import json
import tempfile
import unittest
from pathlib import Path

import cats
import tables


class RealTablesTest(unittest.TestCase):
    def test_the_shipped_tables_validate(self):
        tables.validate(tables.STRUCTURES, tables.TRAIT_EFFECTS, tables.BORDER)

    def test_every_trait_with_an_effect_is_a_real_trait(self):
        self.assertLessEqual(set(tables.TRAIT_EFFECTS), set(cats.TRAITS))

    def test_some_traits_are_still_flavour(self):
        self.assertTrue(set(cats.TRAITS) - set(tables.TRAIT_EFFECTS))

    def test_load_reads_the_named_file_from_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "x.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
            self.assertEqual(tables.load("x", Path(tmp)), {"a": 1})


class ValidateTest(unittest.TestCase):
    def _check(self, mutate, message):
        structures = copy.deepcopy(tables.STRUCTURES)
        traits = copy.deepcopy(tables.TRAIT_EFFECTS)
        border = copy.deepcopy(tables.BORDER)
        mutate(structures, traits, border)
        with self.assertRaisesRegex(ValueError, message):
            tables.validate(structures, traits, border)

    def test_rejects_an_unknown_structure_effect(self):
        self._check(lambda s, t, b: s["nursery"]["effects"].update(flight=1),
                    r"structures\.nursery: unknown effect 'flight'")

    def test_rejects_a_missing_structure_field(self):
        self._check(lambda s, t, b: s["lookout"].pop("cost"),
                    r"structures\.lookout: missing 'cost'")

    def test_rejects_a_negative_or_non_numeric_cost(self):
        self._check(lambda s, t, b: s["nursery"]["cost"].update(food=-1), "negative")
        self._check(lambda s, t, b: s["nursery"]["cost"].update(food="4"),
                    "expected a number")
        self._check(lambda s, t, b: s["nursery"]["cost"].update(food=True),
                    "expected a number")

    def test_rejects_an_unknown_trait_effect(self):
        self._check(lambda s, t, b: t["brave"].update(roar=2),
                    r"traits\.brave: unknown effect 'roar'")

    def test_rejects_a_chance_outside_zero_to_one(self):
        self._check(lambda s, t, b: b["hostile"].update(chance=1.5), "outside")

    def test_rejects_text_that_never_names_the_rival(self):
        self._check(lambda s, t, b: b["friendly"].update(text="Gifts!"), "rival")

    def test_rejects_missing_or_extra_tiers(self):
        self._check(lambda s, t, b: b.pop("friendly"), "tiers")
        self._check(lambda s, t, b: b.update(neutral=b["friendly"]), "tiers")


if __name__ == "__main__":
    unittest.main()
