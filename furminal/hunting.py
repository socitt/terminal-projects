"""Hunting/water-gathering resolution for `furminal`.

Per the v1 scope, ambient wildlife isn't a standalone ecosystem sim —
it's folded directly into the outcome of a hunt: most hunts just yield
food, some turn up a harmless "minor_wildlife" sighting (flavor only),
and a rarer "large_mammal" encounter can injure the hunting cat. Both
functions here are pure and rng-injectable (same pattern as
`backgammon.roll_dice(rng)`), taking a zone's terrain string (see
`territory.TERRAIN_TYPES`) rather than a whole zone dict, so they don't
depend on `territory.py`'s zone-graph shape at all.
"""

FOOD_YIELD = {
    "forest": (1, 3),
    "meadow": (2, 4),
    "thicket": (1, 2),
    "riverbank": (2, 3),
    "rocky_outcrop": (0, 2),
    "wetland": (1, 2),
    "ridge": (0, 1),
    "clearing": (1, 3),
    "scrubland": (0, 2),
    "cave": (0, 1),
    "grove": (1, 3),
    "bramble": (0, 2),
}

WATER_TERRAIN = frozenset({"riverbank", "wetland"})

LARGE_MAMMAL_CHANCE = 0.08
MINOR_WILDLIFE_CHANCE = 0.25
INJURY_CHANCE = 0.4


def resolve_hunt(terrain, rng):
    """Resolve one hunt in a zone of the given `terrain`.

    Returns {"food": int, "encounter": "none"|"minor_wildlife"|
    "large_mammal", "injured": bool}. A "large_mammal" encounter
    always scares off the catch (food 0) and may injure the cat;
    "minor_wildlife" and "none" never injure and yield the terrain's
    usual food range.
    """
    low, high = FOOD_YIELD[terrain]
    roll = rng.random()

    if roll < LARGE_MAMMAL_CHANCE:
        return {
            "food": 0,
            "encounter": "large_mammal",
            "injured": rng.random() < INJURY_CHANCE,
        }
    if roll < LARGE_MAMMAL_CHANCE + MINOR_WILDLIFE_CHANCE:
        return {"food": rng.randint(low, high), "encounter": "minor_wildlife", "injured": False}
    return {"food": rng.randint(low, high), "encounter": "none", "injured": False}


def resolve_water_gathering(terrain, rng):
    """Resolve one water-gathering pass in a zone of the given `terrain`.

    Returns {"water": int} — a larger range for `WATER_TERRAIN`
    terrain, a small chance of a trickle elsewhere.
    """
    if terrain in WATER_TERRAIN:
        return {"water": rng.randint(2, 4)}
    return {"water": rng.randint(0, 1)}
