# backgammon

Two-player, same-screen backgammon on the standard 24-point board.

- `board.py` — pure board logic (`new_game`, movement, hits, bar
  entry, bearing off, `dice_to_moves`, `roll_dice`, `legal_actions`),
  no I/O, fully unit tested in `board_test.py` (60 tests).
- `main.py` — terminal entrypoint. Each die is played one at a time:
  pick a numbered action (enter from bar / move a point / bear off)
  and hit Enter (`shared/input.py` — no raw keypress or arrow keys).

Scope note: implements the full core ruleset (movement, blocking,
hits, mandatory bar re-entry, bearing off with the standard
exact-or-overshoot rule, doubles as four moves) but **not** the
doubling cube — a separate offer/accept/decline state machine that
adds significant complexity without which the game is still complete
and correctly playable.

Run with `python3 board-games/backgammon/main.py` from the repo root.

Built and tested via `lirk` (`BUILD.lirk`).
