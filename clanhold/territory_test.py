import random
import unittest

from territory import (
    TERRAIN_TYPES,
    can_control,
    can_explore,
    control_zone,
    explore_zone,
    generate_zone_graph,
    new_zone,
)


class _FakeRng:
    def __init__(self, randints=(), choices=()):
        self._randints = list(randints)
        self._choices = list(choices)

    def randint(self, low, high):
        return self._randints.pop(0)

    def choice(self, seq):
        return self._choices.pop(0)


def _chain_fixture():
    """home -- a -- b, only home explored/controlled."""
    return {
        "home": new_zone("home", "forest", adjacent=["a"], explored=True, controlled=True),
        "a": new_zone("a", "meadow", adjacent=["home", "b"]),
        "b": new_zone("b", "ridge", adjacent=["a"]),
    }


class GenerateZoneGraphDeterministicTest(unittest.TestCase):
    def test_exact_graph_from_fake_rng(self):
        terrains = ["forest", "meadow", "thicket", "riverbank", "ridge", "cave"]
        rng = _FakeRng(randints=[6], choices=terrains)
        zones = generate_zone_graph(rng)

        self.assertEqual(set(zones), {"home", "zone_1", "zone_2", "zone_3", "zone_4", "zone_5"})
        self.assertEqual(zones["home"]["terrain"], "forest")
        self.assertEqual(zones["zone_3"]["terrain"], "riverbank")
        self.assertEqual(sorted(zones["home"]["adjacent"]), ["zone_1", "zone_5"])
        self.assertEqual(sorted(zones["zone_1"]["adjacent"]), ["home", "zone_2"])
        self.assertTrue(zones["home"]["explored"])
        self.assertTrue(zones["home"]["controlled"])
        self.assertFalse(zones["zone_1"]["explored"])
        self.assertFalse(zones["zone_1"]["controlled"])


class GenerateZoneGraphPropertyTest(unittest.TestCase):
    def test_properties_hold_across_many_seeds(self):
        for seed in range(50):
            zones = generate_zone_graph(random.Random(seed))

            self.assertIn(len(zones), range(6, 11))

            explored_ids = [zid for zid, z in zones.items() if z["explored"]]
            controlled_ids = [zid for zid, z in zones.items() if z["controlled"]]
            self.assertEqual(explored_ids, ["home"])
            self.assertEqual(controlled_ids, ["home"])

            for zone_id, zone in zones.items():
                self.assertIn(zone["terrain"], TERRAIN_TYPES)
                self.assertEqual(len(zone["adjacent"]), 2)
                for neighbor_id in zone["adjacent"]:
                    self.assertIn(neighbor_id, zones)
                    self.assertIn(zone_id, zones[neighbor_id]["adjacent"])


class ExploreZoneTest(unittest.TestCase):
    def test_can_explore_adjacent_to_explored(self):
        zones = _chain_fixture()
        self.assertTrue(can_explore(zones, "a"))
        self.assertFalse(can_explore(zones, "b"))

    def test_explore_zone_updates_state(self):
        zones = _chain_fixture()
        updated = explore_zone(zones, "a")
        self.assertTrue(updated["a"]["explored"])
        self.assertTrue(can_explore(updated, "b"))

    def test_does_not_mutate_input(self):
        zones = _chain_fixture()
        explore_zone(zones, "a")
        self.assertFalse(zones["a"]["explored"])

    def test_rejects_already_explored(self):
        zones = _chain_fixture()
        with self.assertRaises(ValueError):
            explore_zone(zones, "home")

    def test_rejects_non_adjacent_unexplored(self):
        zones = _chain_fixture()
        with self.assertRaises(ValueError):
            explore_zone(zones, "b")


class OutwardExpansionTest(unittest.TestCase):
    def test_far_zone_needs_the_chain_claimed_first(self):
        """The two gates compose into contiguous outward growth: a zone
        two hops out cannot be reached until the intervening zone is
        both explored and controlled."""
        zones = _chain_fixture()

        self.assertFalse(can_explore(zones, "b"))
        zones = explore_zone(zones, "a")
        self.assertFalse(can_control(zones, "b"))

        zones = control_zone(zones, "a")
        zones = explore_zone(zones, "b")
        self.assertTrue(can_control(zones, "b"))
        zones = control_zone(zones, "b")

        self.assertTrue(all(z["explored"] and z["controlled"] for z in zones.values()))

    def test_generated_ring_can_be_fully_claimed_walking_one_way(self):
        zones = generate_zone_graph(random.Random(7))
        claimed = {"home"}
        for _ in range(len(zones) - 1):
            frontier = [
                zid for zid in zones
                if zid not in claimed and can_explore(zones, zid)
            ]
            self.assertTrue(frontier, "expansion stalled before claiming every zone")
            zone_id = frontier[0]
            zones = explore_zone(zones, zone_id)
            zones = control_zone(zones, zone_id)
            claimed.add(zone_id)
        self.assertEqual(claimed, set(zones))


class ControlZoneTest(unittest.TestCase):
    def test_rejects_unexplored_zone(self):
        zones = _chain_fixture()
        with self.assertRaises(ValueError):
            control_zone(zones, "a")

    def test_controls_explored_zone_adjacent_to_controlled(self):
        zones = explore_zone(_chain_fixture(), "a")
        self.assertTrue(can_control(zones, "a"))
        updated = control_zone(zones, "a")
        self.assertTrue(updated["a"]["controlled"])

    def test_rejects_explored_zone_not_adjacent_to_controlled(self):
        zones = _chain_fixture()
        zones = explore_zone(zones, "a")
        zones = explore_zone(zones, "b")
        self.assertFalse(can_control(zones, "b"))
        with self.assertRaises(ValueError):
            control_zone(zones, "b")

    def test_rejects_already_controlled(self):
        zones = _chain_fixture()
        with self.assertRaises(ValueError):
            control_zone(zones, "home")

    def test_does_not_mutate_input(self):
        zones = explore_zone(_chain_fixture(), "a")
        control_zone(zones, "a")
        self.assertFalse(zones["a"]["controlled"])


if __name__ == "__main__":
    unittest.main()
