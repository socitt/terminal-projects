"""Nemo: the computer opponent shared by every board game.

Nemo knows nothing about any particular game. Each game supplies an
*adapter* -- a module in its own directory, `nemo_adapter.py`, that
imports that game's `board` -- and `nemo.search.minimax.choose_move`
plays through it. The adapter protocol is documented in
`nemo/search/minimax.py`.

Requested in docs/USER_TESTING.md: three levels, picked at game start.
"""

NAME = "Nemo"

EASY = 1
MEDIUM = 2
HARD = 3

LEVELS = {EASY: "easy", MEDIUM: "medium", HARD: "hard"}
