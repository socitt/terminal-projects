"""Connect Four board logic: pure functions over a 6-row x 7-col grid.

A board is a list of ROWS lists of COLS cells, `board[row][col]`, each
"X", "O", or "" (empty). Row 0 is the top, row ROWS - 1 is the bottom
— pieces fall to the lowest empty cell in a column, like gravity.
"""

EMPTY = ""
ROWS = 6
COLS = 7


def new_board():
    return [[EMPTY] * COLS for _ in range(ROWS)]


def valid_moves(board):
    """Columns (0-indexed) that aren't full, i.e. have an empty top cell."""
    return [c for c in range(COLS) if board[0][c] == EMPTY]


def apply_move(board, col, mark):
    """Return a new board with `mark` dropped into column `col`.

    Raises ValueError if `col` is out of range or already full.
    """
    if not 0 <= col < COLS:
        raise ValueError(f"column {col} out of range")
    new = [list(row) for row in board]
    for row in range(ROWS - 1, -1, -1):
        if new[row][col] == EMPTY:
            new[row][col] = mark
            return new
    raise ValueError(f"column {col} is full")


_DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


def winner(board):
    """Return the winning mark ("X" or "O"), or "" if no winner yet."""
    for row in range(ROWS):
        for col in range(COLS):
            mark = board[row][col]
            if mark == EMPTY:
                continue
            for dr, dc in _DIRECTIONS:
                if _four_in_a_row(board, row, col, dr, dc, mark):
                    return mark
    return EMPTY


def _four_in_a_row(board, row, col, dr, dc, mark):
    for i in range(4):
        r, c = row + dr * i, col + dc * i
        if not (0 <= r < ROWS and 0 <= c < COLS) or board[r][c] != mark:
            return False
    return True


def is_full(board):
    return not valid_moves(board)


def is_draw(board):
    return is_full(board) and not winner(board)
