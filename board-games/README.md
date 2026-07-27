# board-games

Terminal board games for narrow screens, played with `shared/term.py`
and `shared/input.py`.

- `tictactoe/` — two-player, same-screen tic-tac-toe.
- `connect4/` — two-player, same-screen Connect Four.
- `backgammon/` — two-player, same-screen backgammon (no doubling
  cube; see `backgammon/README.md` for the scope note).
- `go/` — two-player, same-screen Go on a 9x9 board (no Japanese
  territory scoring or full superko; see `go/README.md` for the
  scope note).

Planned next, same layout pattern (game logic as pure `library`
functions + `test`, entrypoint as a thin `main.py`): chess.
