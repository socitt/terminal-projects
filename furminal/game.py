"""Orchestrating module for `furminal`: game_state shape, new_game, and
the daily advance_day seam that composes every other module.

game_state dict shape (JSON-serializable, this is exactly what gets
saved via `save_state`/`load_state`):
    {
        "clan_name": "...",
        "region_id": "...",     # a region-explorer region id (opaque tag;
                                 # this module never imports region-explorer)
        "day": int,
        "cats": [...],           # see cats.py
        "camp": {...},           # see camp.py
        "zones": {...},          # see territory.py
        "other_clans": [...],    # see clans.py, v1 always has exactly one
        "weather": "...",        # see weather.py
        "food": int,
        "water": int,
        "event_log": [{"day": int, "id": "...", "text": "..."}, ...],
    }

`advance_day(state, actions, rng)` is the key pure/testable seam: given
a state, one day's chosen actions, and an injectable rng (same pattern
as `backgammon.roll_dice(rng)`), it returns the next day's state.
`actions` is a dict where every key is optional — an empty dict `{}`
still runs daily upkeep, recovery, weather, clan disposition, and rolls
for a kit birth and a random event:
    {
        "hunt": {"cat": "<name>", "zone": "<controlled zone id>"},
        "gather_water": {"zone": "<controlled zone id>"},
        "patrol": {"zone": "<zone id to explore/control>"},
        "unlock_structure": "<structure id>",
    }
"""

import json

import camp
import cats
import clans
import events
import hunting
import population
import territory
import upkeep
import weather

STARTING_FOOD = 5
STARTING_WATER = 5
CAMP_SPOT_CHOICES = 3


def generate_camp_spots(rng, count=CAMP_SPOT_CHOICES):
    """Return `count` candidate zone graphs for the start flow to offer
    as camp spots, one of which comes back as `new_game`'s `zones`.

    Here rather than in the runner so game_state is still only ever
    assembled at L2 (`ARCHITECTURE.md` §2 rule 2) — the runner's job is
    to describe the candidates and take the player's pick.
    """
    return [territory.generate_zone_graph(rng) for _ in range(count)]


def new_game(rng, clan_name, region_id, zones=None):
    """Return a freshly founded game_state for `clan_name` settling in
    region `region_id` (an opaque region-explorer region id).

    `zones` is the chosen camp spot: pass one of `generate_camp_spots`'
    graphs to found the clan there, or leave it None to generate one
    (which every test that doesn't care about the spot does).
    """
    return {
        "clan_name": clan_name,
        "region_id": region_id,
        "day": 1,
        "cats": cats.generate_starting_cats(rng),
        "camp": camp.new_camp(),
        "zones": territory.generate_zone_graph(rng) if zones is None else zones,
        "other_clans": [clans.generate_neighbor_clan(rng)],
        "weather": rng.choice(weather.WEATHER_STATES),
        "food": STARTING_FOOD,
        "water": STARTING_WATER,
        "event_log": [],
    }


def advance_day(state, actions, rng):
    """Return the next day's state after applying `actions` and rolling
    every daily system (weather, clan disposition, kit birth, event).

    Raises ValueError if `hunt`/`gather_water` names an uncontrolled
    zone, or if `unlock_structure` is invalid (see `camp.unlock_structure`).
    Raises KeyError if any action names a zone id not in `state["zones"]`.

    Cat count can decrease: a food/water shortfall during upkeep can
    kill an already-"sick" cat (see `upkeep.resolve_upkeep`).
    """
    cats_list = state["cats"]
    zones = state["zones"]
    camp_state = state["camp"]
    food = state["food"]
    water = state["water"]
    multiplier = weather.yield_multiplier(state["weather"])

    hunt = actions.get("hunt")
    if hunt is not None:
        zone = zones[hunt["zone"]]
        if not zone["controlled"]:
            raise ValueError(f"cannot hunt in uncontrolled zone: {hunt['zone']}")
        result = hunting.resolve_hunt(zone["terrain"], rng)
        food += int(result["food"] * multiplier)
        if result["injured"]:
            cats_list = cats.set_cat_status(cats_list, hunt["cat"], "injured")

    gather_water = actions.get("gather_water")
    if gather_water is not None:
        zone = zones[gather_water["zone"]]
        if not zone["controlled"]:
            raise ValueError(f"cannot gather water in uncontrolled zone: {gather_water['zone']}")
        result = hunting.resolve_water_gathering(zone["terrain"], rng)
        water += int(result["water"] * multiplier)

    patrol = actions.get("patrol")
    if patrol is not None:
        zone_id = patrol["zone"]
        if territory.can_explore(zones, zone_id):
            zones = territory.explore_zone(zones, zone_id)
        if territory.can_control(zones, zone_id):
            zones = territory.control_zone(zones, zone_id)

    unlock_structure = actions.get("unlock_structure")
    if unlock_structure is not None:
        camp_state = camp.unlock_structure(camp_state, unlock_structure)

    upkeep_result = upkeep.resolve_upkeep(cats_list, food, water, rng)
    cats_list = upkeep_result["cats"]
    food = upkeep_result["food"]
    water = upkeep_result["water"]

    cats_list = cats.maybe_recover(cats_list, rng)

    other_clans = [clans.drift_disposition(clan, rng) for clan in state["other_clans"]]
    weather_state = weather.advance_weather(state["weather"], rng)

    kit = population.maybe_birth_kit(rng, cats_list)
    if kit is not None:
        cats_list = cats_list + [kit]

    event_log = state["event_log"]
    event = events.maybe_trigger_event(rng)
    if event is not None:
        food += event["food_delta"]
        event_log = event_log + [{"day": state["day"], "id": event["id"], "text": event["text"]}]

    return {
        **state,
        "day": state["day"] + 1,
        "cats": cats_list,
        "camp": camp_state,
        "zones": zones,
        "other_clans": other_clans,
        "weather": weather_state,
        "food": max(0, food),
        "water": max(0, water),
        "event_log": event_log,
    }


SURVIVAL_GOAL_DAYS = 20


def outcome(state):
    """Return "lost", "won", or None if `state` isn't a finished game.

    "lost": the clan has died out (no cats left) — checked first, so a
    clan that survives to day `SURVIVAL_GOAL_DAYS` but is then wiped
    out the same day still reads as a loss.
    "won" (the v1 win condition): survived past `SURVIVAL_GOAL_DAYS`.
    """
    if not state["cats"]:
        return "lost"
    if state["day"] > SURVIVAL_GOAL_DAYS:
        return "won"
    return None


def is_game_over(state):
    """True if `outcome(state)` is not None."""
    return outcome(state) is not None


def save_state(state, path):
    with open(path, "w") as f:
        json.dump(state, f)


def load_state(path):
    with open(path) as f:
        return json.load(f)
