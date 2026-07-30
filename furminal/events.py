"""A small curated event table for `furminal`.

Deliberately not a general event-authoring framework: a flat list of
one-off flavor events with a tiny mechanical effect, no branching or
prerequisites (that belongs to `adventure-engine` if narrative
branching is ever wanted here). `game.py` appends triggered events to
`game_state["event_log"]`.
"""

EVENTS = [
    {
        "id": "traveling_loner",
        "text": "A lone traveling cat passes through camp, trading news for a share of prey.",
        "food_delta": -1,
    },
    {
        "id": "good_omen",
        "text": "A hawk circles the camp three times and moves on — the elders call it a sign of good luck.",
        "food_delta": 0,
    },
    {
        "id": "herb_bloom",
        "text": "A patch of rare herbs is found blooming near camp.",
        "food_delta": 0,
    },
    {
        "id": "storm_damage",
        "text": "A night storm scatters the camp's food stores.",
        "food_delta": -2,
    },
    {
        "id": "bountiful_catch",
        "text": "An unusually easy hunt leaves prey to spare.",
        "food_delta": 2,
    },
]

EVENT_CHANCE = 0.15


def maybe_trigger_event(rng):
    """Return a randomly chosen event dict from `EVENTS`, or None if no
    event triggers this day. `rng` must support `random`/`choice`."""
    if rng.random() >= EVENT_CHANCE:
        return None
    return rng.choice(EVENTS)
