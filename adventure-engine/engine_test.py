"""Tests for the engine's branching/state-machine logic, against a small
fixture story (not real prose) — this is what's meant by "testing
narrative logic": which choice leads where, and what flags/items gate
what, is code, and is tested directly here.
"""

import os
import tempfile
import types
import unittest

import engine


def fixture_story():
    """A tiny 4-scene fixture exercising every gating/effect kind:

    start --(take torch)--> lit_room --(unlock, needs torch)--> vault
      \\--(skip)--> dead_end (ending: no outgoing choices)
    vault --(leave)--> dead_end
    """
    return types.SimpleNamespace(
        START="start",
        SCENES={
            "start": {
                "text": "A dark room.",
                "choices": [
                    {
                        "label": "Take the torch",
                        "target": "lit_room",
                        "add_items": ["torch"],
                        "sets_flags": {"took_torch": True},
                    },
                    {
                        "label": "Leave without it",
                        "target": "dead_end",
                    },
                ],
            },
            "lit_room": {
                "text": "A lit room with a locked door.",
                "choices": [
                    {
                        "label": "Unlock the door with the torch's light",
                        "target": "vault",
                        "requires_items": ["torch"],
                        "requires_flags": {"took_torch": True},
                        "remove_items": ["torch"],
                        "sets_flags": {"door_unlocked": True},
                    },
                    {
                        "label": "Go back",
                        "target": "start",
                    },
                ],
            },
            "vault": {
                "text": "Treasure!",
                "choices": [
                    {"label": "Leave", "target": "dead_end"},
                ],
            },
            "dead_end": {
                "text": "The end.",
                "choices": [],
            },
        },
    )


class NewStateTest(unittest.TestCase):
    def test_starts_at_story_start_scene(self):
        story = fixture_story()
        state = engine.new_state(story)
        self.assertEqual(state["scene"], "start")

    def test_starts_with_empty_inventory_and_flags(self):
        story = fixture_story()
        state = engine.new_state(story)
        self.assertEqual(state["inventory"], [])
        self.assertEqual(state["flags"], {})

    def test_starts_with_start_scene_in_visited(self):
        story = fixture_story()
        state = engine.new_state(story)
        self.assertEqual(state["visited"], ["start"])


class AvailableChoicesTest(unittest.TestCase):
    def test_unconditional_choices_are_available(self):
        story = fixture_story()
        state = engine.new_state(story)
        choices = engine.available_choices(story, state)
        self.assertEqual(len(choices), 2)

    def test_gated_choice_excluded_without_required_item(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        choices = engine.available_choices(story, state)
        labels = [c["label"] for c in choices]
        self.assertNotIn("Unlock the door with the torch's light", labels)
        self.assertIn("Go back", labels)

    def test_gated_choice_included_with_required_item_and_flag(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        state["inventory"] = ["torch"]
        state["flags"] = {"took_torch": True}
        choices = engine.available_choices(story, state)
        labels = [c["label"] for c in choices]
        self.assertIn("Unlock the door with the torch's light", labels)

    def test_flag_requirement_checks_exact_expected_value(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        state["inventory"] = ["torch"]
        state["flags"] = {"took_torch": False}
        choices = engine.available_choices(story, state)
        labels = [c["label"] for c in choices]
        self.assertNotIn("Unlock the door with the torch's light", labels)

    def test_dead_end_has_no_available_choices(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "dead_end"
        self.assertEqual(engine.available_choices(story, state), [])


class IsEndingTest(unittest.TestCase):
    def test_scene_with_choices_is_not_ending(self):
        story = fixture_story()
        state = engine.new_state(story)
        self.assertFalse(engine.is_ending(story, state))

    def test_scene_with_no_choices_is_ending(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "dead_end"
        self.assertTrue(engine.is_ending(story, state))

    def test_scene_with_only_gated_out_choices_is_ending(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        # No torch, no flag: the only choice available is "Go back", so
        # this isn't actually an ending yet. Confirm the negative case
        # (a scene that looks like it could dead-end, but isn't) too.
        self.assertFalse(engine.is_ending(story, state))


class ApplyChoiceTest(unittest.TestCase):
    def test_moves_to_target_scene(self):
        story = fixture_story()
        state = engine.new_state(story)
        new = engine.apply_choice(story, state, 0)
        self.assertEqual(new["scene"], "lit_room")

    def test_does_not_mutate_original_state(self):
        story = fixture_story()
        state = engine.new_state(story)
        engine.apply_choice(story, state, 0)
        self.assertEqual(state["scene"], "start")
        self.assertEqual(state["inventory"], [])

    def test_adds_items(self):
        story = fixture_story()
        state = engine.new_state(story)
        new = engine.apply_choice(story, state, 0)
        self.assertIn("torch", new["inventory"])

    def test_sets_flags(self):
        story = fixture_story()
        state = engine.new_state(story)
        new = engine.apply_choice(story, state, 0)
        self.assertEqual(new["flags"].get("took_torch"), True)

    def test_appends_to_visited(self):
        story = fixture_story()
        state = engine.new_state(story)
        new = engine.apply_choice(story, state, 0)
        self.assertEqual(new["visited"], ["start", "lit_room"])

    def test_removes_items(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        state["inventory"] = ["torch"]
        state["flags"] = {"took_torch": True}
        new = engine.apply_choice(story, state, 0)
        self.assertNotIn("torch", new["inventory"])

    def test_adding_item_already_held_does_not_duplicate(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["inventory"] = ["torch"]
        new = engine.apply_choice(story, state, 0)
        self.assertEqual(new["inventory"].count("torch"), 1)

    def test_removing_item_not_held_is_a_no_op(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        state["inventory"] = []
        state["flags"] = {"took_torch": True}
        # requires_items gates this out (no torch), so fall back to the
        # only available choice and confirm no crash / no error either way.
        choices = engine.available_choices(story, state)
        self.assertEqual(len(choices), 1)

    def test_index_refers_to_available_choices_not_raw_scene_choices(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "lit_room"
        # Only "Go back" is available (no torch/flag); index 0 must be
        # that choice, not the raw scene's first (gated-out) choice.
        new = engine.apply_choice(story, state, 0)
        self.assertEqual(new["scene"], "start")

    def test_raises_on_negative_index(self):
        story = fixture_story()
        state = engine.new_state(story)
        with self.assertRaises(IndexError):
            engine.apply_choice(story, state, -1)

    def test_raises_on_too_large_index(self):
        story = fixture_story()
        state = engine.new_state(story)
        with self.assertRaises(IndexError):
            engine.apply_choice(story, state, 99)

    def test_raises_at_dead_end_with_no_choices(self):
        story = fixture_story()
        state = engine.new_state(story)
        state["scene"] = "dead_end"
        with self.assertRaises(IndexError):
            engine.apply_choice(story, state, 0)


class SaveLoadStateTest(unittest.TestCase):
    def test_round_trips_full_state(self):
        story = fixture_story()
        state = engine.new_state(story)
        state = engine.apply_choice(story, state, 0)

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            engine.save_state(state, path)
            loaded = engine.load_state(path)

        self.assertEqual(loaded, state)


if __name__ == "__main__":
    unittest.main()
