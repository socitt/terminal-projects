# dungeon

A short dungeon-crawl escape story for `adventure-engine`. 9 scenes, 3
endings:

- Escape with the treasure (best ending) -- requires finding the
  torch, the rusty key, and studying the sleeping guard's patrol
  before slipping into the vault.
- Escape empty-handed -- possible at several points once the door is
  open, without ever reaching the vault.
- Caught again (bad ending) -- pounding on the cell door at the very
  start alerts the guards instead of escaping.

Exercises both of `engine.py`'s gating kinds: the corridor door
requires the rusty key (`requires_items`), and the vault's sneak-past
option requires having studied the guard first (`requires_flags`, set
by a self-looping choice in the corridor scene).

Run with `python3 adventure-engine/stories/dungeon/main.py` from the
repo root. Built and tested via `lirk` (`BUILD.lirk`).
