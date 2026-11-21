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
import tables
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


def _trait_sum(cat, effect):
    return sum(tables.TRAIT_EFFECTS.get(t, {}).get(effect, 0) for t in cat["traits"])


def _injury_scale(cat):
    scale = 1.0
    for trait in cat["traits"]:
        scale *= tables.TRAIT_EFFECTS.get(trait, {}).get("hunt_injury_scale", 1.0)
    return scale


def _structure_sum(camp_state, effect):
    return sum(tables.STRUCTURES[s]["effects"].get(effect, 0)
               for s in camp_state["structures"])


def structure_cost(structure_id):
    """Food a structure costs to build (`data/structures.json`)."""
    return tables.STRUCTURES[structure_id]["cost"]["food"]


def _hunter(cats_list, name):
    return next((cat for cat in cats_list if cat["name"] == name), None)


def advance_day(state, actions, rng):
    """Return the next day's state after applying `actions` and rolling
    every daily system (weather, clan disposition, kit birth, event).

    Raises ValueError if `hunt`/`gather_water` names an uncontrolled
    zone, if `unlock_structure` is invalid (see `camp.unlock_structure`),
    or if the clan can't afford it.

    Phase C effects, all tuned in `data/*.json` (see `tables.py`):
    the hunter's traits adjust its catch and injury risk, and a hunter
    who isn't healthy brings back half; structures cost food when built
    and then help births, recovery, or raids; cats' traits help their
    own recovery; the leader's traits push the rival's disposition; and
    a hostile rival may raid (halved by a patrol that day, and again by
    a lookout) while a friendly one may share water. The border roll is
    the day's last rng call, so it never shifts any earlier roll.
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
        hunter = _hunter(cats_list, hunt["cat"])
        if hunter is None:
            result = hunting.resolve_hunt(zone["terrain"], rng)
        else:
            result = hunting.resolve_hunt(
                zone["terrain"], rng,
                food_bonus=_trait_sum(hunter, "hunt_food_bonus"),
                injury_scale=_injury_scale(hunter))
        catch = int(result["food"] * multiplier)
        if hunter is not None and hunter["status"] != "healthy":
            catch //= 2
        food += catch
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
        cost = structure_cost(unlock_structure)
        if food < cost:
            name = tables.STRUCTURES[unlock_structure]["name"]
            raise ValueError(f"not enough food to build {name}: need {cost}, have {food}")
        food -= cost

    upkeep_result = upkeep.resolve_upkeep(cats_list, food, water, rng)
    cats_list = upkeep_result["cats"]
    food = upkeep_result["food"]
    water = upkeep_result["water"]

    herb_bonus = _structure_sum(camp_state, "recovery_bonus")
    cats_list = cats.maybe_recover(cats_list, rng, extra={
        cat["name"]: herb_bonus + _trait_sum(cat, "recovery_bonus")
        for cat in cats_list
    })

    leader = cats.cat_with_role(cats_list, cats.LEADER)
    leader_drift = _trait_sum(leader, "leader_drift") if leader else 0
    other_clans = [
        clans.new_clan(drifted["name"], drifted["disposition"] + leader_drift)
        for drifted in (clans.drift_disposition(clan, rng)
                        for clan in state["other_clans"])
    ]
    weather_state = weather.advance_weather(state["weather"], rng)

    kit = population.maybe_birth_kit(
        rng, cats_list, chance_bonus=_structure_sum(camp_state, "birth_chance_bonus"))
    if kit is not None:
        cats_list = cats_list + [kit]

    event_log = state["event_log"]
    event = events.maybe_trigger_event(rng)
    if event is not None:
        food += event["food_delta"]
        event_log = event_log + [{"day": state["day"], "id": event["id"], "text": event["text"]}]

    for clan in other_clans:
        incident = clans.border_incident(clan, tables.BORDER, rng)
        if incident is None:
            continue
        loss = -incident["food"] if incident["food"] < 0 else 0
        if loss and patrol is not None:
            loss //= 2
        for _ in range(int(_structure_sum(camp_state, "raid_shield"))):
            loss //= 2
        food += incident["food"] if incident["food"] >= 0 else -loss
        water += incident["water"]
        event_log = event_log + [{"day": state["day"],
                                  "id": "raid" if incident["food"] < 0 else "gift",
                                  "text": incident["text"]}]

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
