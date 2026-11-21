# furminal — architecture

Cat-clan colony sim. The player founds a clan in one `region-explorer`
region, then plays day by day: patrol to claim territory, hunt and
gather to feed the clan, and ride out weather, wildlife and a rival
clan next door.

This document is the contract between modules. It exists so work can be
picked up cold without re-deriving the design from the code. For the
original signed-off scope discussion see `docs/ACTIVE_SESSION.md`
(2026-07-27 entry); for what is built so far see the 2026-07-30 entries.
`README.md` is the player-facing view of the same thing.

The project was called `clanhold` until 2026-07-30. Dated session-log
entries keep the old name; everything else uses `furminal`.

---

## 1. Scope boundary

**In scope for v1** (agreed 2026-07-27, unchanged):

- Starting flow: pick a region via the `region-explorer` zoom UI, pick a
  spot, name the clan, roll 3–4 starting cats with 2–3 traits each.
- Minimal camp with 1–2 unlockable structures. No building tree.
- Two roles only: leader and healer.
- Fog-of-war territory claimed by patrolling, as a small zone graph.
- **One** neighbouring clan with a drifting disposition.
- Hunting, water, food, rotating weather.
- Ambient wildlife folded into the hunt/patrol risk table.
- A small curated event table and a periodic kit-birth chance.

**Explicitly deferred to v2+:** multiple clans and real diplomacy, a
standalone wildlife ecosystem, a general event-authoring framework,
extra roles or structures beyond the v1 set, cat genetics.

**Naming rule:** every player-visible name (clans, roles, structures,
cats, zones) must be original. The genre lineage this draws on is named
only in internal docs and commit messages, never in README intro text,
in-game text, or identifiers.

---

## 2. Layers and dependency rules

```
 L4  main.py                      thin entrypoint, supplies the save path
      │
 L3  runner.py                    all I/O: prompts, rendering, loop, report
      │                           ← shared/term.py, shared/input.py
      │                           ← region-explorer (start flow only)
      ├──────────────────────────────────────────────────────────────
 L2  game.py                      game_state, new_game, advance_day
      │                           the only module that knows all others
      ├──────────────────────────────────────────────────────────────
 L1  population.py                → cats.py
      ├──────────────────────────────────────────────────────────────
 L0  cats  camp  territory  hunting  clans  weather  events  upkeep
      │                           no dependencies on each other
      ├──────────────────────────────────────────────────────────────
 D   tables.py                    data/*.json, read once at import
```

Rules that hold today and must keep holding:

1. **L0 modules never import each other.** Each is independently
   unit-testable in isolation. `population.py` is the single exception
   and depends only on `cats.py` (for the shared name/trait pools).
   Any layer may import `tables.py` (D, Phase C), which imports nothing
   from furminal; today only `camp.py` and `game.py` do. Other L0
   modules take Phase C effects as plain parameters (`food_bonus`,
   `injury_scale`, `extra`, `chance_bonus`, `rules`) that `game.py`
   composes from the tables, so they stay table-agnostic.
2. **Only `game.py` composes.** Cross-module effects live in
   `advance_day`, never inside an L0 module. Weather is the worked
   example: `weather.py` exposes `yield_multiplier`, `game.py` applies
   it to hunt results, and `hunting.py` stays weather-agnostic.
3. **Only L3+ does I/O.** No `print`, no `input`, no clock, no
   filesystem below `runner.py`. The exceptions are
   `game.save_state`/`load_state`, which take an explicit path, and
   `tables.py`, which reads its own package-relative `data/*.json`
   once at import and validates them, so a malformed table fails at
   startup rather than mid-game.
4. **furminal never imports `region-explorer` below L3.** `game_state`
   carries `region_id` as an opaque string tag. `game.py` neither
   validates it nor looks it up. Only the start flow in `runner.py`/
   `main.py` touches region-explorer at all.
5. **`hunting.py` takes a terrain string, not a zone dict**, so it has
   no dependency on `territory.py`'s zone shape.

### Why `region_id` is opaque

`region-explorer` owns *visual, gameplay-agnostic* region data
(`region-explorer/data/washington.py`). furminal layers its own zone
graph on top as *gameplay* data. Keeping the id opaque means new states
can be added to region-explorer without touching furminal, and furminal
can be tested without importing map data. This mirrors the existing
`region-explorer/engine.py` vs `data/washington.py` split.

---

## 3. Module contracts

| Module | Owns | Key API |
| --- | --- | --- |
| `cats.py` | Cat dicts, name/trait pools, roster generation, recovery | `new_cat`, `generate_starting_cats(rng)`, `cat_with_role`, `set_cat_status`, `maybe_recover(cats, rng)` |
| `tables.py` | Phase C tuning tables from `data/*.json`, validation | `STRUCTURES`, `TRAIT_EFFECTS`, `BORDER`, `load`, `validate` |
| `camp.py` | Structure catalog (from `tables`), unlock state | `new_camp`, `has_structure`, `unlock_structure` |
| `territory.py` | Zone graph, fog-of-war gates | `generate_zone_graph(rng)`, `can_explore`/`explore_zone`, `can_control`/`control_zone` |
| `hunting.py` | Hunt & water outcomes, wildlife risk | `resolve_hunt(terrain, rng)`, `resolve_water_gathering(terrain, rng)` |
| `clans.py` | The one rival clan, disposition drift, border incidents | `generate_neighbor_clan(rng)`, `drift_disposition`, `disposition_tier`, `border_incident(clan, rules, rng)` |
| `weather.py` | Weather rotation and yield penalty | `advance_weather(current, rng)`, `yield_multiplier(weather)` |
| `events.py` | Curated event table | `maybe_trigger_event(rng)` |
| `population.py` | Kit births | `maybe_birth_kit(rng, existing_cats)` |
| `upkeep.py` | Daily food/water consumption, shortfall consequences | `resolve_upkeep(cats, food, water, rng)` |
| `game.py` | Composition, state, persistence, end conditions | `new_game(rng, clan_name, region_id, zones=None)`, `generate_camp_spots(rng, count)`, `advance_day(state, actions, rng)`, `is_game_over(state)`/`outcome(state)`, `save_state`/`load_state` |
| `runner.py` | All I/O: start flow, status screen, action menu, day report | `start_flow(save_path, rng)`, `run(state, save_path, rng)` |
| `main.py` | Save path, wiring | `main()` |

---

## 4. `game_state` reference

Single JSON-serializable dict. What `save_state` writes is exactly this.

```python
{
    "clan_name": str,
    "region_id": str,        # opaque region-explorer region id
    "day": int,              # 1-based, incremented by advance_day
    "cats": [                # see cats.py
        {"name": str, "traits": [str], "role": "leader"|"healer"|None,
         "status": "healthy"|"injured"|"sick"},
    ],
    "camp": {"structures": [str]},
    "zones": {               # zone_id -> zone, see territory.py
        "home": {"id": str, "terrain": str, "adjacent": [str],
                 "explored": bool, "controlled": bool},
    },
    "other_clans": [{"name": str, "disposition": int}],  # v1: exactly 1
    "weather": str,          # one of weather.WEATHER_STATES
    "food": int,             # >= 0
    "water": int,            # >= 0
    "event_log": [{"day": int, "id": str, "text": str}],
}
```

### `advance_day(state, actions, rng)`

Pure. Returns the next state, never mutates its input. `actions` keys
are all optional; `{}` is a valid quiet day.

```python
{
    "hunt": {"cat": "<name>", "zone": "<controlled zone id>"},
    "gather_water": {"zone": "<controlled zone id>"},
    "patrol": {"zone": "<zone id>"},
    "unlock_structure": "<structure id>",
}
```

Order of resolution — player actions first, then always-on systems:

1. `hunt` → food, possible injury to the acting cat
2. `gather_water` → water
3. `patrol` → explore, then claim if eligible
4. `unlock_structure` → camp
5. `upkeep.resolve_upkeep` → food/water consumption for the day's full
   cat count; a shortfall sickens a random cat, or kills one already
   "sick"
6. `cats.maybe_recover` → injured/sick cats may return to "healthy",
   at better odds with a healthy healer alive
7. disposition drift → weather → kit birth → event roll

Steps 5-6 run on the roster *after* actions 1-4 (so same-day hunting
food counts toward upkeep) but *before* step 7 (so a same-day injury
gets one recovery roll before the day ends).

Errors: `ValueError` for an uncontrolled hunt/gather zone or a bad
structure; `KeyError` for an unknown zone id. **`patrol` is the
exception — it silently no-ops** when the zone is neither explorable
nor claimable. See gap G8.

### `is_game_over(state)` / `outcome(state)`

Not part of `advance_day` — the runner's loop condition, checked before
each day. `outcome` returns `"lost"` (the clan has died out — checked
first), `"won"` (survived past `SURVIVAL_GOAL_DAYS`, currently 20), or
`None` if the game is still ongoing. `is_game_over` is just
`outcome(state) is not None`.

### `new_game(rng, clan_name, region_id, zones=None)`

`zones` is the camp spot the player picked out of
`generate_camp_spots(rng, count)`; None generates one instead, which is
what tests that don't care about the spot use. Spot generation lives in
`game.py` rather than the runner so `game_state` is still only ever
assembled at L2 (rule 2 above) — the runner describes the candidates
and takes the pick.

### The day report

`runner._day_report_lines(before, after)` derives the day's news by
diffing the pre- and post-`advance_day` states: territory gained,
stores, deaths and status changes, weather, births, new event-log
entries. Deliberately **not** a log returned by `advance_day` — every
consequence the player needs is already recoverable from the two
states, so this contract stays put and all player-facing phrasing stays
in the one layer allowed to do I/O. It is pure, so it is unit-tested
directly rather than through a scripted playthrough.

A corollary worth keeping: the report reads *state*, never a rule. It
says "The food stores are empty" off `food == 0`, not "the clan went
hungry" off a re-derived `len(cats) * FOOD_PER_CAT`, which would put a
second copy of upkeep's consumption rule in the UI layer.

---

## 5. Invariants

Enforced by tests; treat a break as a bug, not a design change.

- `advance_day` never mutates the input state.
- `day` increases by exactly 1 per call.
- `food`/`water` never go negative (clamped at 0).
- **Cat count can now decrease.** A food or water shortfall during
  upkeep kills a cat that was already "sick" (see `upkeep.py`). Food
  and water shortfalls resolve independently, so a single day costs at
  most two cats, and at most one kit is added, giving
  `len(cats) - 2 <= len(next_cats) <= len(cats) + 1`.
- Zone ids are stable: `advance_day` never adds or removes zones.
- Territory grows contiguously: a zone is explorable only when adjacent
  to an explored zone, claimable only when explored *and* adjacent to a
  controlled zone. Growth radiates from `home`.
- Exactly one leader and one healer at game start; they are never the
  same cat.
- Disposition stays within [-100, 100].
- Bad weather yields strictly less than clear weather.

---

## 6. Conventions

- **RNG injection.** Anything random takes an `rng` parameter, matching
  `backgammon.roll_dice(rng)`. Never call the `random` module at import
  or module scope. Tests inject a queue-backed fake with per-method
  queues (`random`/`randint`/`choice`/`sample`); property tests inject
  `random.Random(seed)` over a seed sweep.
- **Purity.** L0–L2 functions return new values. No in-place mutation of
  caller-owned dicts or lists.
- **Data as tables.** Tuning lives in module-level constants
  (`FOOD_YIELD`, `YIELD_MULTIPLIER`, `EVENTS`) so balance changes are
  data edits. Phase C's tables (structures, trait effects, border
  incidents) went one step further, into `data/*.json`: those are
  declared as lirk `data` on `//furminal:tables`, because an import
  check can't see a file that's only read.
- **New effects don't move existing rolls.** Phase C changes the
  thresholds of rolls that already happen and adds one roll only at
  the very end of the day (the border), so every seeded test written
  before it still sees the same sequence of numbers.
- **Testing discipline** (repo-wide, see `docs/ACTIVE_SESSION.md`):
  every module is mutation-verified before it is called done — inject
  2–3 realistic bugs, confirm the suite fails, restore. A test that
  cannot fail is worse than no test; see the 2026-07-30 test review for
  five that were removed for exactly that reason.
- **Commit granularity.** Source, then tests, then the `BUILD.lirk`
  target extension, as separate commits.
- **Build.** `lirk build //...` and `lirk test //...` from the repo
  root; the binary is `/root/git/lirk/bin/lirk`. Targets are declared in
  `furminal/BUILD.lirk`.

---

## 7. Known gaps

Found in the 2026-07-30 review; G1-G3 closed the same day Phase A
landed (below). The logic layer is complete and tested, but several
systems are still **inert** — they carry state that nothing reads.
None of these are bugs in what exists; they are unbuilt v1 surface.

| # | Gap | Impact |
| --- | --- | --- |
| ~~G1~~ | ~~No daily consumption.~~ **Closed by `upkeep.py`.** | — |
| ~~G2~~ | ~~Injuries are permanent.~~ **Closed by `cats.maybe_recover`.** | — |
| ~~G3~~ | ~~No end condition.~~ **Closed by `game.is_game_over`/`outcome`.** | — |
| ~~G4~~ | ~~Structures are inert and free.~~ **Closed by Phase C**: costs and effects in `data/structures.json`. | — |
| ~~G5~~ | ~~Traits are decorative.~~ **Closed by Phase C**: 10 of 15 traits have effects (`data/traits.json`); the rest stay flavour. | — |
| ~~G6~~ | ~~Disposition is decorative.~~ **Closed by Phase C**: raids when hostile, gifts when friendly (`data/border.json`). | — |
| ~~G7~~ | ~~Roles are partly decorative.~~ **Closed by Phase C**: the leader's traits drive the rival's disposition. | — |
| G8 | **`patrol` fails silently** where `hunt`/`gather_water` raise. | Low — but the runner cannot tell the player why nothing happened. |
| G9 | **Ring-only zone graphs.** Every zone has exactly 2 neighbours, so expansion is a walk along a line. | Low — fine for v1, limits replay value. |
| G10 | **The day report nets out hunting against upkeep.** It can only show `Food 5 -> 5`, never "the hunt brought 2, the clan ate 2" — a hunt's yield is not recoverable by diffing states. | Medium — a player can derive it from the one-per-cat rule in `README.md`, but a bad-weather hunt that yields 0 is indistinguishable from one that fed the clan. |

---

## 8. Roadmap

**Phase A — make it a game.** Closes G1–G3. Nothing here needs UI, so it
stayed inside the fast pure-logic test loop. **Done (2026-07-30).**

- A1 `upkeep.py`: daily food/water consumption, starvation → `"sick"`.
- A2 recovery: healer clears `"injured"`/`"sick"` over time; gives the
  role a mechanical purpose (G2, part of G7).
- A3 `is_game_over(state)` / `outcome(state)`: lose when the clan dies
  out, survive-N-days as the v1 win (G3).

Reviewed again after Phase B landed, by simulating 200 seeds per policy
rather than by reading the code: doing nothing loses 200/200 (avg 7
days), a reasonable hunt/gather/patrol policy wins ~49%, and a total
famine wipes a clan out in 3–8 days. The pressure Phase A was for is
real and the win condition is reachable, so v1 needs no retuning. The
probe also found the roster-bound wording corrected in §5.

**Phase B — make it playable.** The terminal UI. **Done
(2026-07-30).**

- B1 `runner.py` day loop and status screen, plus the end-of-day report
  and the planned-action list (both found by playing the WIP loop: the
  screen used to clear straight from one day into the next, so events,
  deaths and births were invisible, and a mis-picked zone could not be
  taken back).
- B2 start flow: region pick via region-explorer's `select_region`,
  camp spot, clan name.
- B3 `main.py` entrypoint. Ending a game deletes the save, or it would
  stay resumable forever and replay its own ending on every launch.
- B4 subprocess integration tests (`runner_test.py`, `main_test.py`).
- B5 `furminal/README.md`.

**Phase C — depth.** Closes G4–G7. **Done (2026-11-21).** Every
number is in `data/*.json`, read and validated by `tables.py`.

- C1 structure costs and effects: Nursery (3 food, +0.1 birth chance),
  Herb Store (2, +0.15 recovery), Lookout (2, halves raids). The runner
  only offers what the clan can afford.
- C2 traits with mechanical weight: hunt yield and injury risk,
  recovery, and — for the leader — disposition drift. A hunter who
  isn't healthy brings back half, closing the "status doesn't gate
  hunting" finding below.
- C3 disposition consequences: a hostile rival raids (30%, -2 food;
  halved by a patrol that day and by a Lookout), a friendly one shares
  water (20%, +1).

Balanced by simulation, 1000 seeds per policy, same scripted policy
before and after: plain hunt/gather/patrol won 33.0% before Phase C and
30.4% after; with building, at the first costs tried (4/3/3), clans
built 0.36 structures a game and won 30.1% — too dear to matter. At
3/2/2 they build about one a game and win 36.3%, so building is now a
choice that pays. (These are lower than Phase A's ~49% only because
this is a different, simpler scripted policy.)

Phase A before Phase B was deliberate: building UI over a loop with no
consumption and no ending would have meant rewriting the screens once
those landed.

Three things Phase B surfaced for whoever picks up Phase C:

- **G10 needs a contract decision, not a patch.** Closing it means
  either `advance_day` returning a per-day result alongside the state
  (clean, but it is the one L2 signature everything depends on), or the
  runner re-deriving `len(cats) * upkeep.FOOD_PER_CAT` to split the
  line (cheap, but puts a second copy of the consumption rule in the UI
  layer, exactly what the day-report rule in §4 exists to prevent).
  The first is the right one if the report is worth changing the seam
  for; neither should be done in passing.

- **A cat's status doesn't gate hunting.** A sick cat hunts as well as
  a healthy one, and the runner offers it. Part of the same decorative
  cluster as G5/G7.
- **G8 is worked around, not closed.** `runner._patrol_targets` only
  offers zones where a patrol will accomplish something, so the silent
  no-op is unreachable from the UI. `advance_day`'s contract is still
  inconsistent for any other caller.
