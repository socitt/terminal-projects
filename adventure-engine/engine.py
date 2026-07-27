"""Choose-your-own-adventure engine: pure state-machine logic.

A "story" is plain data (see `stories/*/story.py` for real examples): a
module-like object exposing `START` (a scene id) and `SCENES` (a dict of
scene id -> scene dict). This module never imports or references any
specific story — it runs any story that matches that shape.

Scene dict shape:
    {
        "text": "...",           # required
        "art": "...",            # optional ASCII art, omitted if none
        "choices": [
            {
                "label": "...",
                "target": "scene_id",
                "requires_flags": {"flag": True},   # optional, default {}
                "requires_items": ["item"],          # optional, default []
                "sets_flags": {"flag": True},        # optional, default {}
                "add_items": ["item"],               # optional, default []
                "remove_items": ["item"],            # optional, default []
            },
            ...
        ],
    }

State dict shape (JSON-serializable, this is exactly what gets saved):
    {
        "scene": "scene_id",
        "inventory": ["item", ...],
        "flags": {"flag": True, ...},
        "visited": ["scene_id", ...],
    }
"""

import json


def new_state(story):
    """Return the initial state for `story`, at its start scene."""
    return {
        "scene": story.START,
        "inventory": [],
        "flags": {},
        "visited": [story.START],
    }


def _requirements_met(state, choice):
    requires_flags = choice.get("requires_flags", {})
    for flag, expected in requires_flags.items():
        if state["flags"].get(flag) != expected:
            return False

    requires_items = choice.get("requires_items", [])
    for item in requires_items:
        if item not in state["inventory"]:
            return False

    return True


def available_choices(story, state):
    """Return the list of choice dicts usable from the current scene."""
    scene = story.SCENES[state["scene"]]
    return [c for c in scene["choices"] if _requirements_met(state, c)]


def is_ending(story, state):
    """True if there are no available choices from the current scene."""
    return len(available_choices(story, state)) == 0


def apply_choice(story, state, choice_index):
    """Return a new state after taking `available_choices()[choice_index]`.

    Raises IndexError if `choice_index` is out of range for the currently
    available choices.
    """
    choices = available_choices(story, state)
    if choice_index < 0 or choice_index >= len(choices):
        raise IndexError(f"no available choice at index {choice_index}")
    choice = choices[choice_index]

    inventory = list(state["inventory"])
    for item in choice.get("add_items", []):
        if item not in inventory:
            inventory.append(item)
    for item in choice.get("remove_items", []):
        if item in inventory:
            inventory.remove(item)

    flags = dict(state["flags"])
    flags.update(choice.get("sets_flags", {}))

    target = choice["target"]
    visited = list(state["visited"]) + [target]

    return {
        "scene": target,
        "inventory": inventory,
        "flags": flags,
        "visited": visited,
    }


def save_state(state, path):
    with open(path, "w") as f:
        json.dump(state, f)


def load_state(path):
    with open(path) as f:
        return json.load(f)
