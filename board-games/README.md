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
- `chess/` — two-player, same-screen chess on a standard 8x8 board;
  see `chess/README.md` for details.

Every game opens by asking for an opponent: a second human on the same
screen, or **Nemo**, the computer opponent in `nemo/` at the repo root,
at one of three levels:

- **easy** — a random legal move;
- **medium** — takes a win in one and won't hand you one;
- **hard** — searches ahead (to the end in tic-tac-toe, 4 plies in
  Connect Four, 2 in chess, the rest of its roll in backgammon, 1 in
  go) and picks the best move it finds.

Nemo plays second (O, Black in chess, White in go). A small "Nemo cam"
face under the board shows how it rates its position. Each game's
`nemo_adapter.py` is the only game-specific part; the search itself is
`nemo/search/minimax.py`. Set `TP_NEMO_SEED` to make a Nemo game (and
backgammon's dice) repeatable.
