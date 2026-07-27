# go

Two-player, same-screen Go on a 9x9 board (standard beginner/
competitive size — 19x19 doesn't fit a ~30-40 col terminal or a
single-key+Enter coordinate-entry scheme reasonably).

- `board.py` — pure board logic (`group_and_liberties`, `apply_move`,
  `is_legal_move`, `score`, `winner`), no I/O, fully unit tested in
  `board_test.py` (31 tests). Full core ruleset: placement, captures,
  the suicide rule (illegal unless the move captures opponent stones
  first), and simple ko (can't immediately recreate the position from
  just before the opponent's last move).
- `main.py` — terminal entrypoint. Coordinates are entered as two
  single-digit prompts (column 1-9, then row 1-9) rather than one
  combined token, consistent with `shared/input.py`'s single-key+Enter
  model. Type `P` instead of a column to pass; two consecutive passes
  end the game and show the score.

Scope note: implements area/Chinese-style scoring (stones + fully-
surrounded empty territory) with a 5.5 komi, not Japanese territory
scoring — the latter needs a dead-stone-removal negotiation phase
that's out of scope here. Simple ko only (checks against the single
prior position), not full positional superko.

Run with `python3 board-games/go/main.py` from the repo root.

Built and tested via `lirk` (`BUILD.lirk`).
