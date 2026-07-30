# clanhold — architecture

Cat-clan colony sim. The player founds a clan in one `region-explorer`
region, then plays day by day: patrol to claim territory, hunt and
gather to feed the clan, and ride out weather, wildlife and a rival
clan next door.

This document is the contract between modules. It exists so work can be
picked up cold without re-deriving the design from the code. For the
original signed-off scope discussion see `docs/ACTIVE_SESSION.md`
(2026-07-27 entry); for what is built so far see the 2026-07-30 entry.

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
 L4  main.py                      thin entrypoint, supplies real data
      │
 L3  runner.py                    all I/O: prompts, rendering, loop
      │                           ← shared/term.py, shared/input.py
      │                           ← region-explorer (start flow only)
      ├──────────────────────────────────────────────────────────────
 L2  game.py                      game_state, new_game, advance_day
      │                           the only module that knows all others
      ├──────────────────────────────────────────────────────────────
 L1  population.py                → cats.py
      ├──────────────────────────────────────────────────────────────
 L0  cats  camp  territory  hunting  clans  weather  events
                                  no clanhold-internal dependencies
```

Rules that hold today and must keep holding:

1. **L0 modules never import each other.** Each is independently
   unit-testable in isolation. `population.py` is the single exception
   and depends only on `cats.py` (for the shared name/trait pools).
2. **Only `game.py` composes.** Cross-module effects live in
   `advance_day`, never inside an L0 module. Weather is the worked
   example: `weather.py` exposes `yield_multiplier`, `game.py` applies
   it to hunt results, and `hunting.py` stays weather-agnostic.
3. **Only L3+ does I/O.** No `print`, no `input`, no clock, no
   filesystem below `runner.py`. The one exception is
   `game.save_state`/`load_state`, which take an explicit path.
4. **clanhold never imports `region-explorer` below L3.** `game_state`
   carries `region_id` as an opaque string tag. `game.py` neither
   validates it nor looks it up. Only the start flow in `runner.py`/
   `main.py` touches region-explorer at all.
5. **`hunting.py` takes a terrain string, not a zone dict**, so it has
   no dependency on `territory.py`'s zone shape.

### Why `region_id` is opaque

`region-explorer` owns *visual, gameplay-agnostic* region data
(`region-explorer/data/washington.py`). clanhold layers its own zone
graph on top as *gameplay* data. Keeping the id opaque means new states
can be added to region-explorer without touching clanhold, and clanhold
can be tested without importing map data. This mirrors the existing
`region-explorer/engine.py` vs `data/washington.py` split.

---

## 3. Module contracts

| Module | Owns | Key API |
| --- | --- | --- |
| `cats.py` | Cat dicts, name/trait pools, roster generation | `new_cat`, `generate_starting_cats(rng)`, `cat_with_role`, `set_cat_status` |
| `camp.py` | Structure catalog, unlock state | `new_camp`, `has_structure`, `unlock_structure` |
| `territory.py` | Zone graph, fog-of-war gates | `generate_zone_graph(rng)`, `can_explore`/`explore_zone`, `can_control`/`control_zone` |
| `hunting.py` | Hunt & water outcomes, wildlife risk | `resolve_hunt(terrain, rng)`, `resolve_water_gathering(terrain, rng)` |
| `clans.py` | The one rival clan, disposition drift | `generate_neighbor_clan(rng)`, `drift_disposition`, `disposition_tier` |
| `weather.py` | Weather rotation and yield penalty | `advance_weather(current, rng)`, `yield_multiplier(weather)` |
| `events.py` | Curated event table | `maybe_trigger_event(rng)` |
| `population.py` | Kit births | `maybe_birth_kit(rng, existing_cats)` |
| `game.py` | Composition, state, persistence | `new_game(rng, clan_name, region_id)`, `advance_day(state, actions, rng)`, `save_state`/`load_state` |

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
5. disposition drift → weather → kit birth → event roll

Errors: `ValueError` for an uncontrolled hunt/gather zone or a bad
structure; `KeyError` for an unknown zone id. **`patrol` is the
exception — it silently no-ops** when the zone is neither explorable
nor claimable. See gap G8.

---

## 5. Invariants

Enforced by tests; treat a break as a bug, not a design change.

- `advance_day` never mutates the input state.
- `day` increases by exactly 1 per call.
- `food`/`water` never go negative (clamped at 0).
- Cat count never decreases (nothing kills cats yet — see G3).
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
  data edits.
- **Testing discipline** (repo-wide, see `docs/ACTIVE_SESSION.md`):
  every module is mutation-verified before it is called done — inject
  2–3 realistic bugs, confirm the suite fails, restore. A test that
  cannot fail is worse than no test; see the 2026-07-30 test review for
  five that were removed for exactly that reason.
- **Commit granularity.** Source, then tests, then the `BUILD.lirk`
  target extension, as separate commits.
- **Build.** `lirk build //...` and `lirk test //...` from the repo
  root; the binary is `/root/git/lirk/bin/lirk`. Targets are declared in
  `clanhold/BUILD.lirk`.

---

## 7. Known gaps

Found in the 2026-07-30 review. The logic layer is complete and tested,
but several systems are **inert** — they carry state that nothing reads.
None of these are bugs in what exists; they are unbuilt v1 surface.

| # | Gap | Impact |
| --- | --- | --- |
| G1 | **No daily consumption.** Cats never eat or drink. `food`/`water` only ever rise. | Critical — there is no survival pressure, so no game. |
| G2 | **Injuries are permanent.** `set_cat_status` sets `"injured"`; nothing clears it. The `healer` role has no effect. | High — injury is a one-way ratchet. |
| G3 | **No end condition.** Nothing can end a run, win or lose. | High — needed before the loop is playable. |
| G4 | **Structures are inert and free.** `nursery`/`herb_store` unlock at no cost and change nothing. | Medium |
| G5 | **Traits are decorative.** 15 traits, zero mechanical effect. | Medium |
| G6 | **Disposition is decorative.** It drifts and is never read; `disposition_tier` has no caller. | Medium |
| G7 | **Roles are decorative** beyond being assigned. | Medium |
| G8 | **`patrol` fails silently** where `hunt`/`gather_water` raise. | Low — but the runner cannot tell the player why nothing happened. |
| G9 | **Ring-only zone graphs.** Every zone has exactly 2 neighbours, so expansion is a walk along a line. | Low — fine for v1, limits replay value. |

G1–G3 are what stand between the current logic layer and something
playable. They are Phase A below.

---

## 8. Roadmap

**Phase A — make it a game.** Closes G1–G3. Nothing here needs UI, so it
stays inside the fast pure-logic test loop.

- A1 `upkeep.py`: daily food/water consumption, starvation → `"sick"`.
- A2 recovery: healer clears `"injured"`/`"sick"` over time; gives the
  role a mechanical purpose (G2, part of G7).
- A3 `is_game_over(state)` / `outcome(state)`: lose when the clan dies
  out, survive-N-days as the v1 win (G3).

**Phase B — make it playable.** The terminal UI. After Phase A this
produces a game someone can finish.

- B1 `runner.py` day loop and status screen.
- B2 start flow: region pick via region-explorer, spot, clan name.
- B3 `main.py` entrypoint.
- B4 subprocess integration tests.
- B5 `clanhold/README.md`.

**Phase C — depth.** Optional, closes G4–G7. Only worth doing once
Phase B proves the loop is fun.

- C1 structure costs and effects.
- C2 traits with mechanical weight.
- C3 disposition consequences (raids when hostile).

Phase A before Phase B is deliberate: building UI over a loop with no
consumption and no ending would mean rewriting the screens once those
land.
