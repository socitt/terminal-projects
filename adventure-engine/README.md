# adventure-engine

A choose-your-own-adventure engine, reused across multiple story packs
under `stories/` -- the engine itself never references any specific
story's content.

- `engine.py` -- pure state-machine logic, no I/O: `new_state`,
  `available_choices` (filters a scene's choices by `requires_flags`/
  `requires_items`), `apply_choice` (applies `sets_flags`/`add_items`/
  `remove_items` and moves to the target scene), `is_ending` (true once
  a scene has no available choices), `save_state`/`load_state` (plain
  JSON -- state is already JSON-serializable). Fully unit tested in
  `engine_test.py` (24 tests, mutation-verified) against a small
  fixture story, not real prose.
- `runner.py` -- the shared interactive game loop every story pack's
  own thin `main.py` calls directly: `run(story, save_path)` renders
  each scene (ASCII art + text via `shared.term`), shows numbered
  choices via `shared.input`, offers "s" to save-and-quit, and offers
  to resume if a save file already exists. Tested end-to-end in
  `runner_test.py` (4 tests, mutation-verified) via a tiny fixture
  story, subprocess-based (same style as every board game's
  `main_test.py`).
- `stories/` -- story packs as data. Each is a `story.py` module
  exposing `START` (a scene id) and `SCENES` (a dict of scene id ->
  `{"art": ..., "text": ..., "choices": [...]}`), no engine imports.
  The engine runs any story matching that shape with zero code
  changes:
  - `stories/dungeon/` -- a dungeon crawler, 9 scenes, 3 endings.
  - `stories/train-mystery/` -- a whodunit set on a train, 8 scenes,
    3 endings.

## State model

A save is exactly the state dict:

```python
{
    "scene": "scene_id",
    "inventory": ["item", ...],   # order-preserving, no duplicates
    "flags": {"flag_name": True, ...},
    "visited": ["scene_id", ...], # ordered scene history
}
```

A scene's choices carry optional `requires_flags`/`requires_items`
(gates -- an unmet choice simply doesn't appear, rather than blocking
navigation with an error) and `sets_flags`/`add_items`/`remove_items`
(effects, applied when the choice is taken). A scene with no available
choices is an ending -- no separate ending flag needed.

Each story pack was verified programmatically (a BFS over all
reachable `(scene, inventory, flags)` states) to confirm every scene
and every ending is actually reachable, before any content was
committed -- not just hand-traced.

Run a story with e.g. `python3 adventure-engine/stories/dungeon/main.py`
from the repo root. Built and tested via `lirk` (`BUILD.lirk` in this
directory and in each story pack's directory).
