# region-explorer

A WA state ASCII zoom map: pick one of six regions from a full-state
overview and (optionally, animated) zoom into a hand-authored close-up
of it.

- `engine.py` -- pure zoom logic, no I/O: `crop_window` (a shrinking,
  edge-clamped window of a char-grid centered on a point),
  `scale_nn` (nearest-neighbor scale a char-grid to a target size),
  `zoom_frames` (chains the two into a sequence of shrinking, scaled
  crops ending on the region's hand-authored `detail_art` as the crisp
  final frame), `region_by_id`. Fully unit tested in `engine_test.py`
  (19 tests, mutation-verified) against a small fixture grid.
- `data/washington.py` -- the `STATE` dict for Washington: the
  full-state overview art plus each of the 6 regions' `id`/`name`/
  `center`/`detail_art`/`landmarks`. `engine.py` only ever depends on
  this shape, never on "Washington" specifically -- a future state is
  just a new data module matching the same shape. Validated in
  `data/washington_test.py` (8 tests: grid-width consistency, every
  region center in-bounds, unique ids, etc).
- `runner.py` -- the interactive loop: render the overview, prompt a
  region number, ask "play zoom animation?" up front (this repo's
  `shared/input.py` is line-buffered, so an in-progress animation
  can't be interrupted by a keypress -- skip is a decision made before
  it starts, not during), then render the zoom sequence and the
  region's landmarks. Tested end-to-end in `runner_test.py` (5 tests,
  mutation-verified) via a tiny fixture `STATE`, subprocess-based
  (same style as every board game's `main_test.py`). `run()` takes an
  injectable `sleep_fn` (same reasoning as `backgammon.roll_dice`
  taking an rng) so tests can assert the animation path was actually
  taken by call count, not by racing wall-clock time against
  subprocess overhead.
- `main.py` -- thin entrypoint wiring `data/washington.STATE` into
  `runner.run`. Tested end-to-end against the real Washington data in
  `main_test.py` (3 tests).

## Data shape

```python
STATE = {
    "name": "Washington",
    "art": [...],       # full-state overview char-grid (equal-width rows)
    "regions": [
        {
            "id": "olympic",
            "name": "Olympic Peninsula",
            "center": (row, col),   # position in "art", used to zoom
            "detail_art": [...],    # close-up char-grid, own equal width
            "landmarks": ["Hoh Rain Forest", "Mount Olympus", ...],
        },
        ...
    ],
}
```

Two deliberately different visual registers: the overview is
clean/abstract (mostly outline strokes, sparse terrain texture, one
numbered marker per region), while each region's `detail_art` is
denser/chunkier/more organic, meant to read as a close-up. Both draw
from the shared ASCII vocabulary in `SYMBOL_LEGEND.md` -- extend that
file in place before inventing a new symbol meaning for a future
state, so the visual language stays consistent.

Run it with `python3 region-explorer/main.py` from the repo root.
Built and tested via `lirk` (`BUILD.lirk` in this directory and in
`data/`).
