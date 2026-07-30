# furminal

A cat-clan colony sim for a narrow terminal. Found a clan in one
`region-explorer` region, then play it day by day: patrol to claim
ground, hunt and gather to feed the roster, and ride out weather,
wildlife, and the clan next door. Survive 20 days and you win; lose
every cat and you don't.

Named `clanhold` until 2026-07-30; dated entries in
`docs/ACTIVE_SESSION.md` still use the old name.

Run it with `python3 furminal/main.py` from the repo root. Built and
tested via `lirk` (`BUILD.lirk` in this directory).

`ARCHITECTURE.md` is the module contract, layering rules, invariant
list and roadmap — read that before changing anything here.

## Playing

Each day you may queue up to four actions, in any combination, each
once per day, then end the day:

- **Hunt** — send one cat to a controlled zone for food. The zone's
  terrain sets the range. A large-mammal encounter scares off the catch
  and can injure the cat.
- **Gather water** — a controlled zone. `riverbank` and `wetland` yield
  properly; anywhere else gives a trickle at best.
- **Patrol** — scout a zone next to explored ground, and claim it if
  it's already scouted and next to territory you hold. Only zones where
  a patrol would actually accomplish something are offered.
- **Unlock a structure** — the Nursery or the Herb Store. Free in v1,
  and neither does anything yet (`ARCHITECTURE.md` gap G4).

Then, every day, whether you acted or not: every cat eats and drinks
one of each. A store that can't cover the roster makes a cat sick, or
kills one already sick — the only way cats die. Injured and sick cats
roll to recover, at better odds while a healthy healer is alive. Then
the rival clan's mood drifts, the weather turns, a kit may be born, and
an event may fire. The end-of-day report is the diff of all of it.

Bad weather multiplies hunting and gathering down (`storm` is the
worst at 0.5), so a run of storms is what turns a comfortable margin
into a shortfall.

Save-and-quit writes `furminal/save.json` and the next launch offers to
resume it. Reaching an ending deletes it.

## Modules

Layered L0 → L4 with strict dependency rules; `ARCHITECTURE.md` §2 has
the diagram and the reasoning.

- **L0, no internal dependencies, each independently unit tested.**
  `cats.py` (cat dicts, name/trait pools, starting roster, recovery
  odds — 17 tests), `camp.py` (structure catalog and unlock state — 9),
  `territory.py` (the zone graph and the two fog-of-war gates: scout
  next to scouted, claim next to claimed, so territory grows outward
  from `home` — 14), `hunting.py` (hunt and water outcomes with
  wildlife folded into the risk table, taking a terrain string rather
  than a zone dict so it doesn't depend on the graph shape — 11),
  `clans.py` (the one rival clan and its drifting disposition — 13),
  `weather.py` (rotation and yield penalty — 8), `events.py` (a
  curated event table, not an authoring framework — 6), `upkeep.py`
  (daily consumption and what a shortfall costs — 13).
- **L1** `population.py` — the kit-birth chance, drawing names and
  traits from `cats.py`'s pools. Not genetics. 7 tests.
- **L2** `game.py` — `game_state`, `new_game`, `generate_camp_spots`,
  `advance_day`, `is_game_over`/`outcome`, `save_state`/`load_state`.
  The only module that composes: cross-module effects (weather scaling
  a hunt, upkeep running over the post-action roster) live in
  `advance_day`, never inside an L0 module. `advance_day` is pure —
  state in, next state out, rng injected. 37 tests including a
  100-seed property sweep.
- **L3** `runner.py` — all I/O: the start flow (region pick via
  region-explorer, camp spot, clan name), the status screen, the action
  menu, and the end-of-day report. 22 tests: the day loop driven as a
  subprocess with piped input, plus direct unit tests of the pure
  report builder.
- **L4** `main.py` — thin entrypoint, supplies the save path. 4 tests
  driving the real script, real map data and real rng end to end.

The day report is built by diffing the state before and after
`advance_day` rather than by `advance_day` returning a log: every
consequence the player needs is already recoverable from the two
states, so the L2 contract stays put and all player-facing phrasing
stays in the one layer allowed to print.

## Save shape

A save is exactly the `game_state` dict:

```python
{
    "clan_name": "...",
    "region_id": "olympic",  # opaque region-explorer id; game.py never resolves it
    "day": 1,                # 1-based
    "cats": [{"name": ..., "traits": [...],
              "role": "leader" | "healer" | None,
              "status": "healthy" | "injured" | "sick"}, ...],
    "camp": {"structures": [...]},
    "zones": {"home": {"id": ..., "terrain": ..., "adjacent": [...],
                       "explored": bool, "controlled": bool}, ...},
    "other_clans": [{"name": ..., "disposition": int}],  # v1: exactly one
    "weather": "clear",
    "food": 5,
    "water": 5,
    "event_log": [{"day": int, "id": ..., "text": ...}, ...],
}
```

`region_id` stays an opaque tag: `region-explorer` owns visual,
gameplay-agnostic region data, furminal layers its own gameplay zone
graph on top, and only the start flow ever touches region-explorer at
all. New states can be added there without furminal noticing.
