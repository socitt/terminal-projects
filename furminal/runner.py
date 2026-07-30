"""Interactive furminal day loop and status screen.

`run(state, save_path, rng=random)` is the day loop: render status,
let the player queue any/all of a day's four optional actions
(matching `game.advance_day`'s `actions` shape exactly -- each
settable once per day), call `advance_day`, show what the day did, and
repeat until `game.is_game_over` fires. `rng` is injectable (same
reasoning as `region-explorer/runner.py`'s `sleep_fn`, per
`ARCHITECTURE.md` §6's RNG-injection convention) so tests can drive a
full playthrough deterministically instead of racing real randomness;
`main.py` calls `run` with the default (the plain `random` module, same
convention as `backgammon.roll_dice(random)`).

The day report is built by *diffing* the state before and after
`advance_day` (`_day_report_lines`) rather than by having `advance_day`
return a log. Every consequence the player needs to see is already
recoverable from the two states, and the runner is the only layer that
wants it, so this keeps the L2 contract in `ARCHITECTURE.md` §4
unchanged and all player-facing phrasing in the one layer allowed to
do I/O.
"""

import importlib.util
import os
import random
import sys
import textwrap
from pathlib import Path

_FURMINAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_FURMINAL_DIR))
sys.path.insert(0, str(_FURMINAL_DIR.parent))

import camp
import clans
import game
import territory
from shared import input as input_module
from shared import term

_REGION_EXPLORER_DIR = _FURMINAL_DIR.parent / "region-explorer"

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


def _spot_summary(zones):
    """One narrow line describing a candidate camp spot: the terrain the
    camp itself sits on, how much ground there is to claim, and what it
    borders. Terrain is the whole of the choice -- it drives hunting and
    water yields (see `hunting.FOOD_YIELD`/`WATER_TERRAIN`)."""
    home = zones["home"]
    borders = ", ".join(zones[adj]["terrain"] for adj in home["adjacent"])
    return f"{home['terrain']} ({len(zones)} zones, borders {borders})"


def _prompt_camp_spot(rng):
    """Offer `game.generate_camp_spots`' candidates and return the
    chosen zone graph -- the "pick a spot" step of the start flow, after
    the region and before naming the clan."""
    spots = game.generate_camp_spots(rng)
    print("\nWhere does the clan make camp?")
    for i, zones in enumerate(spots, start=1):
        print(f"{i}. {_spot_summary(zones)}")
    keys = [str(i) for i in range(1, len(spots) + 1)]
    key = input_module.prompt_choice("> ", keys)
    return spots[int(key) - 1]


def start_flow(save_path, rng=random):
    """Resolve the game_state to start playing with: resume from
    `save_path` if it exists and the player wants to, otherwise run
    region-explorer's region picker, pick a camp spot within it, name
    the clan, and found it via `game.new_game`. Returns None if the
    player backs out of region selection without settling on one (see
    `region_explorer_runner.select_region`) -- there is no clan to
    play without a region.
    """
    if os.path.exists(save_path):
        if input_module.prompt_choice(
            "Saved clan found. Resume? (y/n): ", ["y", "n"]
        ) == "y":
            return game.load_state(save_path)

    region_explorer_runner = _load_module(
        "furminal_region_explorer_runner", _REGION_EXPLORER_DIR / "runner.py"
    )
    washington = _load_module(
        "furminal_region_explorer_washington",
        _REGION_EXPLORER_DIR / "data" / "washington.py",
    )
    region = region_explorer_runner.select_region(washington.STATE)
    if region is None:
        return None

    zones = _prompt_camp_spot(rng)

    print()
    clan_name = _prompt_clan_name()
    return game.new_game(rng, clan_name, region["id"], zones=zones)


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


def _print_wrapped(text):
    """Print `text` wrapped to the narrow-terminal width. Event text is
    full prose sentences, the only place in this project where a line
    routinely overruns `term.DEFAULT_WIDTH`."""
    print(textwrap.fill(text, width=term.DEFAULT_WIDTH))


def _day_report_lines(before, after):
    """Return the lines describing what one `advance_day` did, in the
    same order `advance_day` resolves them (`ARCHITECTURE.md` §4):
    patrol results, then upkeep, recovery, weather, birth, event.

    Deaths and status changes are read off the two rosters by name --
    upkeep is the only thing that sickens or kills a cat and hunting is
    the only thing that injures one, so a status change carries its own
    explanation without `advance_day` having to report a cause.
    """
    lines = []

    for zone_id, zone in after["zones"].items():
        was = before["zones"][zone_id]
        if zone["controlled"] and not was["controlled"]:
            lines.append(f"{zone_id} is now clan territory.")
        elif zone["explored"] and not was["explored"]:
            lines.append(f"{zone_id} has been scouted.")

    lines.append(
        f"Food {before['food']} -> {after['food']}, "
        f"water {before['water']} -> {after['water']}."
    )
    # Read off the stores rather than from upkeep's shortfall flags: an
    # empty store is what the player can act on, and phrasing it this
    # way keeps `upkeep.FOOD_PER_CAT`'s consumption rule out of the UI
    # layer, where a copy of it could quietly go stale.
    if after["food"] == 0:
        lines.append("The food stores are empty.")
    if after["water"] == 0:
        lines.append("The water stores are empty.")

    before_status = {cat["name"]: cat["status"] for cat in before["cats"]}
    after_status = {cat["name"]: cat["status"] for cat in after["cats"]}

    for name in before_status:
        if name not in after_status:
            lines.append(f"{name} has died.")
        elif after_status[name] != before_status[name]:
            if after_status[name] == "healthy":
                lines.append(f"{name} has recovered.")
            else:
                lines.append(f"{name} is now {after_status[name]}.")

    if after["weather"] != before["weather"]:
        lines.append(f"The weather turns to {after['weather']}.")

    for name in after_status:
        if name not in before_status:
            lines.append(f"A kit is born: {name}.")

    for entry in after["event_log"][len(before["event_log"]):]:
        lines.append(entry["text"])

    return lines


def _show_day_report(before, after):
    """Show what the day just did, then wait, so the report isn't wiped
    by the next day's status screen. Skipped entirely once the game is
    over -- `run` prints the ending instead."""
    if game.is_game_over(after):
        return
    term.clear_screen()
    print(f"End of day {before['day']}")
    print(term.hr())
    for line in _day_report_lines(before, after):
        _print_wrapped(line)
    input_module.get_key("\nPress Enter to start the next day: ")


def _planned_lines(actions):
    """Return one short line per queued action, so the player can see
    what the day already holds -- the status screen is redrawn (and the
    terminal cleared) after every pick."""
    lines = []
    hunt = actions.get("hunt")
    if hunt is not None:
        lines.append(f"Hunt: {hunt['cat']} in {hunt['zone']}")
    gather_water = actions.get("gather_water")
    if gather_water is not None:
        lines.append(f"Gather water: {gather_water['zone']}")
    patrol = actions.get("patrol")
    if patrol is not None:
        lines.append(f"Patrol: {patrol['zone']}")
    structure = actions.get("unlock_structure")
    if structure is not None:
        lines.append(f"Build: {camp.STRUCTURES[structure]['name']}")
    return lines


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

        planned = _planned_lines(actions)
        if planned:
            print(term.hr())
            print("Planned today:")
            for line in planned:
                print(f"  {line}")

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
        if planned:
            options.append(("c", "Clear planned actions"))
        options.append(("s", "Save and quit"))

        print()
        key = _prompt_menu("> ", options)

        if key == "e":
            return actions
        if key == "s":
            return _QUIT
        if key == "c":
            actions = {}
        elif key == "h":
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
    final state either way.

    A finished game clears `save_path`, same as `adventure-engine`'s
    runner does at an ending: a save of an already-over game would
    otherwise be resumable forever, replaying its own ending on every
    launch without a single playable day in between.
    """
    while not game.is_game_over(state):
        actions = _prompt_day_actions(state)
        if actions is _QUIT:
            game.save_state(state, save_path)
            print("\nSaved. Run again to resume.")
            return state
        next_state = game.advance_day(state, actions, rng)
        _show_day_report(state, next_state)
        state = next_state

    if os.path.exists(save_path):
        os.remove(save_path)

    term.clear_screen()
    if game.outcome(state) == "won":
        print(f"{state['clan_name']} survived to day {state['day']}. You win!")
    else:
        print(f"{state['clan_name']} has died out on day {state['day']}.")
    return state
