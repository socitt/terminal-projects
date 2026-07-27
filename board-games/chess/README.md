# chess

Two-player, same-screen chess on a standard 8x8 board.

- `board.py` — pure board logic (`new_game`, `apply_move`, `legal_moves`,
  `is_in_check`, `is_checkmate`, `is_stalemate`, `game_status`,
  `winner`), no I/O, fully unit tested in `board_test.py` (55 tests,
  mutation-verified). Full core ruleset: all piece moves, check,
  checkmate, stalemate, castling (both sides, invalidated by king/rook
  movement or rook capture, forbidden through or into check), en
  passant, and pawn promotion (explicit choice required — `apply_move`
  raises if a pawn reaches the last rank without one).
- `main.py` — terminal entrypoint. Squares are entered as two
  single-key prompts each (file letter a-h, then rank digit 1-8) —
  algebraic notation split the same way `go/` splits column/row,
  consistent with `shared/input.py`'s single-key+Enter model.
  Promotion piece (q/r/b/n) is prompted only when a pawn move actually
  reaches the last rank.

Run with `python3 board-games/chess/main.py` from the repo root.

Built and tested via `lirk` (`BUILD.lirk`).
