"""Daily food/water upkeep for `clanhold`.

Closes gap G1 from `ARCHITECTURE.md` (no daily consumption) — before
this module, `food`/`water` only ever rose. Every cat consumes food
and water each day; a store that falls short doesn't just clamp at 0,
it picks a cat and makes them sick, or kills them if they're already
sick. This is the only source of cat death in v1.

Deliberately at L0 (no clanhold-internal imports, per `ARCHITECTURE.md`
§2 rule 1) — operates on plain cat dicts by name, the same shape
`cats.set_cat_status` uses, so `game.py` stays the only module that
composes.
"""

FOOD_PER_CAT = 1
WATER_PER_CAT = 1


def resolve_upkeep(cats, food, water, rng):
    """Pure. Resolve one day's food/water consumption for `cats`.

    Returns {"cats": [...], "food": int, "water": int,
             "food_shortfall": bool, "water_shortfall": bool}.
    `food`/`water` in the result are clamped at 0. A shortfall (the
    store doesn't cover every cat at `FOOD_PER_CAT`/`WATER_PER_CAT`)
    picks one cat via `rng.choice(cats)`: a cat already "sick" dies
    (dropped from the returned roster); any other cat's status becomes
    "sick". Food and water shortfalls are resolved independently and
    may pick the same cat or different ones. An empty `cats` list never
    shortfalls and is returned unchanged.
    """
    needed_food = len(cats) * FOOD_PER_CAT
    needed_water = len(cats) * WATER_PER_CAT
    food_shortfall = food < needed_food
    water_shortfall = water < needed_water

    if food_shortfall and cats:
        cats = _apply_shortfall(cats, rng)
    if water_shortfall and cats:
        cats = _apply_shortfall(cats, rng)

    return {
        "cats": cats,
        "food": max(0, food - needed_food),
        "water": max(0, water - needed_water),
        "food_shortfall": food_shortfall,
        "water_shortfall": water_shortfall,
    }


def _apply_shortfall(cats, rng):
    """Return a new cat list after one shortfall hit on a random cat:
    dies if already "sick", otherwise becomes "sick"."""
    victim_name = rng.choice(cats)["name"]
    for cat in cats:
        if cat["name"] == victim_name and cat["status"] == "sick":
            return [c for c in cats if c["name"] != victim_name]
    return [dict(cat, status="sick") if cat["name"] == victim_name else cat for cat in cats]
