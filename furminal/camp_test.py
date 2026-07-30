import unittest

from camp import STRUCTURES, has_structure, new_camp, unlock_structure


class NewCampTest(unittest.TestCase):
    def test_starts_with_no_structures(self):
        self.assertEqual(new_camp(), {"structures": []})


class HasStructureTest(unittest.TestCase):
    def test_true_when_present(self):
        camp = {"structures": ["nursery"]}
        self.assertTrue(has_structure(camp, "nursery"))

    def test_false_when_absent(self):
        camp = {"structures": []}
        self.assertFalse(has_structure(camp, "nursery"))


class UnlockStructureTest(unittest.TestCase):
    def test_adds_structure(self):
        camp = new_camp()
        updated = unlock_structure(camp, "nursery")
        self.assertEqual(updated["structures"], ["nursery"])

    def test_does_not_mutate_input(self):
        camp = new_camp()
        unlock_structure(camp, "nursery")
        self.assertEqual(camp["structures"], [])

    def test_can_unlock_both_structures(self):
        camp = new_camp()
        camp = unlock_structure(camp, "nursery")
        camp = unlock_structure(camp, "herb_store")
        self.assertEqual(set(camp["structures"]), {"nursery", "herb_store"})

    def test_rejects_unknown_structure(self):
        with self.assertRaises(ValueError):
            unlock_structure(new_camp(), "not_a_real_structure")

    def test_rejects_duplicate_unlock(self):
        camp = unlock_structure(new_camp(), "nursery")
        with self.assertRaises(ValueError):
            unlock_structure(camp, "nursery")

    def test_all_catalog_entries_have_name_and_description(self):
        for structure_id, info in STRUCTURES.items():
            self.assertIn("name", info)
            self.assertIn("description", info)


if __name__ == "__main__":
    unittest.main()
