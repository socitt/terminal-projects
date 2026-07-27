# train-mystery

A whodunit set aboard a train, for `adventure-engine`. 8 scenes, 3
endings:

- Solve the case (best ending) -- accuse the widow after gathering all
  three clues (the poisoned wine glass, the widow's hidden letter, and
  the muddy footprints).
- Accuse the conductor or the stranger (bad endings) -- either wrong
  suspect can be accused at any time; the real killer escapes.

Hub-and-spoke shape, unlike `dungeon`'s linear-with-detours layout: a
central corridor scene links to three self-looping clue rooms (each
collects one item on its first visit) and to a confrontation scene.
The correct accusation is gated on a single `requires_items` list of
all three clues -- a different `engine.py` feature than `dungeon`'s
single-flag gate.

Run with `python3 adventure-engine/stories/train-mystery/main.py` from
the repo root. Built and tested via `lirk` (`BUILD.lirk`).
