"""Tic-tac-toe board logic: pure functions over a 3x3 board.

A board is a list of 9 cells, row-major (index = row * 3 + col), each
"X", "O", or "" (empty).
"""

EMPTY = ""

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def new_board():
    return [EMPTY] * 9


def apply_move(board, index, mark):
    """Return a new board with `mark` placed at `index`.

    Raises ValueError if `index` is out of range or already occupied.
    """
    if not 0 <= index < len(board):
        raise ValueError(f"index {index} out of range")
    if board[index] != EMPTY:
        raise ValueError(f"cell {index} already occupied")
    new = list(board)
    new[index] = mark
    return new


def winner(board):
    """Return the winning mark ("X" or "O"), or "" if no winner yet."""
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return EMPTY


def is_full(board):
    return EMPTY not in board


def is_draw(board):
    return is_full(board) and not winner(board)
