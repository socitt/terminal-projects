# tictactoe

Two-player, same-screen tic-tac-toe.

- `board.py` — pure board logic (`new_board`, `apply_move`, `winner`,
  `is_draw`), no I/O, fully unit tested in `board_test.py`.
- `main.py` — terminal entrypoint. Cells are numbered 1-9,
  left-to-right, top-to-bottom; type a number and hit Enter to place
  your mark (`shared/input.py` — no raw keypress or arrow keys).

Run with `python3 board-games/tictactoe/main.py` from the repo root.

Built and tested via `lirk` (`BUILD.lirk`) — see
`docs/ACTIVE_SESSION.md` for why this repo moved off Please for new
targets.
