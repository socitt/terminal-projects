"""Nemo adapter for go (protocol: nemo/search/minimax.py).

State is `(board, color_to_move, previous_board, consecutive_passes)`,
the same four things go's main loop tracks; two passes in a row end the
game, scored by `board.winner`. A move is `(row, col)` or `PASS`.

Nemo never fills its own single-point eye (every neighbour its own
colour): that is how a go program avoids killing its own groups, and
without it random play never ends. Hard Nemo looks one ply ahead and
judges by area score, so it passes once passing wins and plays on
otherwise.
"""

from board import (
    EMPTY,
    apply_move,
    is_legal_move,
    neighbors,
    opponent,
    score,
    winner,
)

PASS = "pass"
HARD_DEPTH = 1


def new_state(board, color):
    return (board, color, None, 0)


def _own_eye(board, row, col, color):
    return all(board[r][c] == color for r, c in neighbors(len(board), row, col))


def moves(state):
    board, color, previous, _ = state
    size = len(board)
    found = [
        (r, c)
        for r in range(size)
        for c in range(size)
        if board[r][c] == EMPTY
        and not _own_eye(board, r, c, color)
        and is_legal_move(board, r, c, color, previous)
    ]
    return found + [PASS]


def play(state, move):
    board, color, previous, passes = state
    if move == PASS:
        return (board, opponent(color), previous, passes + 1)
    row, col = move
    return (apply_move(board, row, col, color, previous), opponent(color), board, 0)


def to_move(state):
    return state[1]


def outcome(state):
    board, _, _, passes = state
    if passes < 2:
        return None
    return winner(board) or "draw"


def evaluate(state, player):
    board = state[0]
    black, white = score(board)
    mine, theirs = (black, white) if player == "B" else (white, black)
    return max(-1.0, min(1.0, (mine - theirs) / (len(board) ** 2)))
