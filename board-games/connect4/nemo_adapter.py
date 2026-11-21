"""Nemo adapter for Connect Four (protocol: nemo/search/minimax.py).

State is `(board, mark_to_move)`. Hard Nemo searches 4 plies; past that
it scores every four-cell window: a window holding only one player's
discs is worth more the fuller it is, and the centre column is worth a
little on its own. Moves are offered centre-first, which is what makes
alpha-beta prune well here.
"""

from board import COLS, EMPTY, ROWS, apply_move, is_draw, valid_moves, winner

HARD_DEPTH = 4

_CENTRE_FIRST = sorted(range(COLS), key=lambda c: abs(c - COLS // 2))
_WINDOW_WEIGHT = {1: 1, 2: 4, 3: 16}


def other(mark):
    return "O" if mark == "X" else "X"


def moves(state):
    board, _ = state
    open_cols = set(valid_moves(board))
    return [c for c in _CENTRE_FIRST if c in open_cols]


def play(state, col):
    board, mark = state
    return apply_move(board, col, mark), other(mark)


def to_move(state):
    return state[1]


def outcome(state):
    board, _ = state
    won = winner(board)
    if won:
        return won
    return "draw" if is_draw(board) else None


def _windows(board):
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_r, end_c = r + 3 * dr, c + 3 * dc
                if 0 <= end_r < ROWS and 0 <= end_c < COLS:
                    yield [board[r + i * dr][c + i * dc] for i in range(4)]


def evaluate(state, player):
    board, _ = state
    rival = other(player)
    total = 0
    for window in _windows(board):
        mine, theirs = window.count(player), window.count(rival)
        if mine and not theirs:
            total += _WINDOW_WEIGHT[mine]
        elif theirs and not mine:
            total -= _WINDOW_WEIGHT[theirs]
    centre = [board[r][COLS // 2] for r in range(ROWS)]
    total += 3 * (centre.count(player) - centre.count(rival))
    return max(-1.0, min(1.0, total / 200))
