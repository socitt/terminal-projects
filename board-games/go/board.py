"""Go board logic: pure functions over a 9x9 board.

A board is a list of SIZE lists of SIZE cells, `board[row][col]`,
each "" (empty), "B" (black), or "W" (white). Row 0 is the top.

Core ruleset only: placement, group/liberty tracking, captures, the
suicide rule (a move is illegal if the placed stone's group would
have zero liberties, unless the move first captures opponent stones
and thereby gains a liberty), and simple ko (a move is illegal if it
would exactly recreate the board position from just before the
opponent's last move). Scoring is area-style (Chinese rules: stones
on the board plus territory - empty regions bordered by only one
color), not Japanese territory scoring, since the latter needs a
dead-stone-removal negotiation phase that's out of scope here.
"""

SIZE = 9
EMPTY = ""
BLACK = "B"
WHITE = "W"
DEFAULT_KOMI = 5.5


def new_board(size=SIZE):
    return [[EMPTY] * size for _ in range(size)]


def opponent(color):
    return WHITE if color == BLACK else BLACK


def in_bounds(size, row, col):
    return 0 <= row < size and 0 <= col < size


def neighbors(size, row, col):
    candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
    return [(r, c) for r, c in candidates if in_bounds(size, r, c)]


def group_and_liberties(board, row, col):
    """Return (group, liberties): the set of points in the connected
    same-color group containing (row, col), and the set of empty
    points adjacent to that group. Both are empty sets if (row, col)
    is itself empty."""
    size = len(board)
    color = board[row][col]
    if color == EMPTY:
        return set(), set()
    stack = [(row, col)]
    group = {(row, col)}
    liberties = set()
    while stack:
        r, c = stack.pop()
        for nr, nc in neighbors(size, r, c):
            cell = board[nr][nc]
            if cell == EMPTY:
                liberties.add((nr, nc))
            elif cell == color and (nr, nc) not in group:
                group.add((nr, nc))
                stack.append((nr, nc))
    return group, liberties


def _copy_board(board):
    return [row[:] for row in board]


def _remove_group(board, group):
    for r, c in group:
        board[r][c] = EMPTY


def apply_move(board, row, col, color, previous_board=None):
    """Return the new board after `color` plays at (row, col).

    Raises ValueError if the point is occupied, if the move is
    suicide (the placed stone's group has zero liberties after any
    captures are resolved), or if it violates simple ko (the
    resulting board would exactly equal `previous_board`, the
    position from just before the opponent's last move).
    """
    size = len(board)
    if not in_bounds(size, row, col):
        raise ValueError("move out of bounds")
    if board[row][col] != EMPTY:
        raise ValueError("point is occupied")

    new_board = _copy_board(board)
    new_board[row][col] = color

    for nr, nc in neighbors(size, row, col):
        if new_board[nr][nc] == opponent(color):
            group, liberties = group_and_liberties(new_board, nr, nc)
            if not liberties:
                _remove_group(new_board, group)

    _, own_liberties = group_and_liberties(new_board, row, col)
    if not own_liberties:
        raise ValueError("suicide move")

    if previous_board is not None and new_board == previous_board:
        raise ValueError("ko: move repeats the position before the opponent's last move")

    return new_board


def is_legal_move(board, row, col, color, previous_board=None):
    try:
        apply_move(board, row, col, color, previous_board)
        return True
    except ValueError:
        return False


def _empty_regions(board):
    """Maximal connected regions of empty points, each paired with
    the set of stone colors bordering it."""
    size = len(board)
    visited = set()
    regions = []
    for row in range(size):
        for col in range(size):
            if board[row][col] != EMPTY or (row, col) in visited:
                continue
            stack = [(row, col)]
            visited.add((row, col))
            region = {(row, col)}
            borders = set()
            while stack:
                r, c = stack.pop()
                for nr, nc in neighbors(size, r, c):
                    cell = board[nr][nc]
                    if cell == EMPTY:
                        if (nr, nc) not in visited:
                            visited.add((nr, nc))
                            region.add((nr, nc))
                            stack.append((nr, nc))
                    else:
                        borders.add(cell)
            regions.append((region, borders))
    return regions


def score(board, komi=DEFAULT_KOMI):
    """Area score: stones on the board plus territory (empty regions
    bordered by exactly one color). Returns (black_score,
    white_score), with `komi` added to white's total."""
    black = sum(row.count(BLACK) for row in board)
    white = sum(row.count(WHITE) for row in board)
    for region, borders in _empty_regions(board):
        if borders == {BLACK}:
            black += len(region)
        elif borders == {WHITE}:
            white += len(region)
    return black, white + komi


def winner(board, komi=DEFAULT_KOMI):
    black, white = score(board, komi)
    if black > white:
        return BLACK
    if white > black:
        return WHITE
    return ""
