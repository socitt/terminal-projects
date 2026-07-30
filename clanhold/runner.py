"""Interactive clanhold day loop and status screen.

`run(state, save_path, rng=random)` is the day loop: render status,
let the player queue any/all of a day's four optional actions
(matching `game.advance_day`'s `actions` shape exactly -- each
settable once per day), call `advance_day`, and repeat until
`game.is_game_over` fires. `rng` is injectable (same reasoning as
`region-explorer/runner.py`'s `sleep_fn`, per `ARCHITECTURE.md` §6's
RNG-injection convention) so tests can drive a full playthrough
deterministically instead of racing real randomness; `main.py` calls
`run` with the default (the plain `random` module, same convention as
`backgammon.roll_dice(random)`).
"""

import importlib.util
import os
import random
import sys
from pathlib import Path

_CLANHOLD_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_CLANHOLD_DIR))
sys.path.insert(0, str(_CLANHOLD_DIR.parent))

import camp
import clans
import game
import territory
from shared import input as input_module
from shared import term

_REGION_EXPLORER_DIR = _CLANHOLD_DIR.parent / "region-explorer"

_QUIT = object()


def _load_module(name, path):
    """Load the module at `path` under `name`, bypassing the normal
    import system. Needed only for region-explorer's `runner.py` and
    `data/washington.py`: this file is *also* named `runner.py`, and a
    plain `import runner` from here would just return this
    already-cached module instead of region-explorer's (the first time
    two same-named project modules need to coexist in one process --
    every prior cross-project dependency in this repo was compile-time
    only, via `BUILD.lirk`, never both loaded live together)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prompt_clan_name():
    while True:
        name = input("Name your clan: ").strip()
        if name:
            return name


def start_flow(save_path, rng=random):
    """Resolve the game_state to start playing with: resume from
    `save_path` if it exists and the player wants to, otherwise run
    region-explorer's region picker and clan naming, then found a new
    clan via `game.new_game`. Returns None if the player backs out of
    region selection without settling on one (see
    `region_explorer_runner.select_region`) -- there is no clan to
    play without a region.
    """
    if os.path.exists(save_path):
        if input_module.prompt_choice(
            "Saved clan found. Resume? (y/n): ", ["y", "n"]
        ) == "y":
            return game.load_state(save_path)

    region_explorer_runner = _load_module(
        "clanhold_region_explorer_runner", _REGION_EXPLORER_DIR / "runner.py"
    )
    washington = _load_module(
        "clanhold_region_explorer_washington",
        _REGION_EXPLORER_DIR / "data" / "washington.py",
    )
    region = region_explorer_runner.select_region(washington.STATE)
    if region is None:
        return None

    print()
    clan_name = _prompt_clan_name()
    return game.new_game(rng, clan_name, region["id"])


def _show_status(state):
    term.clear_screen()
    print(f"{state['clan_name']} -- Day {state['day']}")
    print(term.hr())
    print(f"Weather: {state['weather']}")
    print(f"Food: {state['food']}   Water: {state['water']}")
    for clan in state["other_clans"]:
        print(f"{clan['name']}: {clans.disposition_tier(clan['disposition'])}")
    print(term.hr())
    print("Cats:")
    for cat in state["cats"]:
        role = f" ({cat['role']})" if cat["role"] else ""
        print(f"  {cat['name']}{role} -- {cat['status']}")
    print(term.hr())
    print("Territory:")
    for zone_id, zone in state["zones"].items():
        if zone["controlled"]:
            tag = "controlled"
        elif zone["explored"]:
            tag = "explored"
        else:
            tag = "unknown"
        print(f"  {zone_id} ({zone['terrain']}) -- {tag}")
    if state["camp"]["structures"]:
        print(term.hr())
        names = [camp.STRUCTURES[s]["name"] for s in state["camp"]["structures"]]
        print("Camp: " + ", ".join(names))


def _prompt_menu(prompt, options):
    """`options` is a list of (key, label) pairs. Prints them, prompts
    until one key is picked, and returns the chosen key."""
    for key, label in options:
        print(f"{key}. {label}")
    return input_module.prompt_choice(prompt, [key for key, _ in options])


def _prompt_zone(prompt, state, zone_ids):
    for i, zone_id in enumerate(zone_ids, start=1):
        zone = state["zones"][zone_id]
        print(f"{i}. {zone_id} ({zone['terrain']})")
    keys = [str(i) for i in range(1, len(zone_ids) + 1)]
    key = input_module.prompt_choice(prompt, keys)
    return zone_ids[int(key) - 1]


def _prompt_cat(prompt, state):
    cats_list = state["cats"]
    for i, cat in enumerate(cats_list, start=1):
        print(f"{i}. {cat['name']} ({cat['status']})")
    keys = [str(i) for i in range(1, len(cats_list) + 1)]
    key = input_module.prompt_choice(prompt, keys)
    return cats_list[int(key) - 1]["name"]


def _controlled_zones(state):
    return [zid for zid, zone in state["zones"].items() if zone["controlled"]]


def _patrol_targets(state):
    """Zones where a patrol would actually do something -- explorable
    or claimable now -- rather than every uncontrolled zone, some of
    which `advance_day`'s patrol action would silently no-op on (see
    `ARCHITECTURE.md` gap G8)."""
    zones = state["zones"]
    return [
        zid for zid in zones
        if territory.can_explore(zones, zid) or territory.can_control(zones, zid)
    ]


def _unlockable_structures(state):
    return [s for s in camp.STRUCTURES if not camp.has_structure(state["camp"], s)]


def _prompt_hunt(state):
    zone_id = _prompt_zone("Hunt in which zone? > ", state, _controlled_zones(state))
    cat_name = _prompt_cat("Send which cat? > ", state)
    return {"cat": cat_name, "zone": zone_id}


def _prompt_gather_water(state):
    zone_id = _prompt_zone(
        "Gather water in which zone? > ", state, _controlled_zones(state)
    )
    return {"zone": zone_id}


def _prompt_patrol(state, targets):
    zone_id = _prompt_zone("Patrol which zone? > ", state, targets)
    return {"zone": zone_id}


def _prompt_unlock_structure(available):
    for i, structure_id in enumerate(available, start=1):
        print(f"{i}. {camp.STRUCTURES[structure_id]['name']}")
    keys = [str(i) for i in range(1, len(available) + 1)]
    key = input_module.prompt_choice("Unlock which structure? > ", keys)
    return available[int(key) - 1]


def _prompt_day_actions(state):
    """Interactively build one day's `actions` dict for
    `game.advance_day`. Returns the dict once the player ends the day,
    or the sentinel `_QUIT` if they choose to save and quit instead."""
    actions = {}
    while True:
        _show_status(state)
        patrol_targets = _patrol_targets(state)
        available_structures = _unlockable_structures(state)

        options = []
        if "hunt" not in actions:
            options.append(("h", "Hunt"))
        if "gather_water" not in actions:
            options.append(("g", "Gather water"))
        if "patrol" not in actions and patrol_targets:
            options.append(("p", "Patrol"))
        if "unlock_structure" not in actions and available_structures:
            options.append(("u", "Unlock a structure"))
        options.append(("e", "End day"))
        options.append(("s", "Save and quit"))

        print()
        key = _prompt_menu("> ", options)

        if key == "e":
            return actions
        if key == "s":
            return _QUIT
        if key == "h":
            actions["hunt"] = _prompt_hunt(state)
        elif key == "g":
            actions["gather_water"] = _prompt_gather_water(state)
        elif key == "p":
            actions["patrol"] = _prompt_patrol(state, patrol_targets)
        elif key == "u":
            actions["unlock_structure"] = _prompt_unlock_structure(available_structures)


def run(state, save_path, rng=random):
    """Run the interactive day loop against `state` until the game
    ends (win or loss) or the player saves and quits. Returns the
    final state either way."""
    while not game.is_game_over(state):
        actions = _prompt_day_actions(state)
        if actions is _QUIT:
            game.save_state(state, save_path)
            print("\nSaved. Run again to resume.")
            return state
        state = game.advance_day(state, actions, rng)

    term.clear_screen()
    if game.outcome(state) == "won":
        print(f"{state['clan_name']} survived to day {state['day']}. You win!")
    else:
        print(f"{state['clan_name']} has died out on day {state['day']}.")
    return state
