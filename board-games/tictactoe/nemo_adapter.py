"""Nemo adapter for tic-tac-toe (protocol: nemo/search/minimax.py).

State is `(board, mark_to_move)`. The game is small enough that hard
Nemo searches to the end, so it never loses and `evaluate` is never
reached in practice.
"""

from board import EMPTY, apply_move, is_draw, winner

HARD_DEPTH = 9


def other(mark):
    return "O" if mark == "X" else "X"


def moves(state):
    board, _ = state
    return [i for i, cell in enumerate(board) if cell == EMPTY]


def play(state, index):
    board, mark = state
    return apply_move(board, index, mark), other(mark)


def to_move(state):
    return state[1]


def outcome(state):
    board, _ = state
    won = winner(board)
    if won:
        return won
    return "draw" if is_draw(board) else None


def evaluate(state, player):
    return 0.0
