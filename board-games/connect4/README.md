# connect4

Two-player, same-screen Connect Four (6 rows x 7 columns).

- `board.py` — pure board logic (`new_board`, `valid_moves`,
  `apply_move`, `winner`, `is_draw`), no I/O, fully unit tested in
  `board_test.py`.
- `main.py` — terminal entrypoint. Type a column number (1-7) and hit
  Enter to drop your piece (`shared/input.py` — no raw keypress or
  arrow keys).

Run with `python3 board-games/connect4/main.py` from the repo root.

Built and tested via `lirk` (`BUILD.lirk`).
