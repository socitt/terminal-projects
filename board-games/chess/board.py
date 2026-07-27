"""Chess board logic: pure functions over an 8x8 board.

A board is a list of 8 lists of 8 cells, `board[row][col]`. Row 0 is
white's back rank (rank 1), row 7 is black's back rank (rank 8); col 0
is file a, col 7 is file h. Each cell is "" (empty) or a single-letter
piece code: "P N B R Q K" for white (uppercase), "p n b r q k" for
black (lowercase).

Game state is a dict: `board`, `turn` ("w"/"b"), `castling` (dict of
four independent booleans "K"/"Q"/"k"/"q" — white/black king/queen
side), and `en_passant` (the square a pawn can capture onto via en
passant, or None — set only immediately after a two-square pawn push,
cleared every other move).

Full core ruleset: all piece moves, check, checkmate, stalemate,
castling (both sides, invalidated by king/rook movement or rook
capture, forbidden through or into check), en passant, and pawn
promotion (explicit choice required, not defaulted).
"""

SIZE = 8
EMPTY = ""
WHITE = "w"
BLACK = "b"

_BACK_RANK = ["R", "N", "B", "Q", "K", "B", "N", "R"]
_PROMOTION_PIECES = {"Q", "R", "B", "N"}

_KNIGHT_OFFSETS = [
    (1, 2), (2, 1), (2, -1), (1, -2),
    (-1, -2), (-2, -1), (-2, 1), (-1, 2),
]
_DIAGONAL_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
_STRAIGHT_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
_KING_OFFSETS = _DIAGONAL_DIRS + _STRAIGHT_DIRS


def new_board():
    board = [[EMPTY] * SIZE for _ in range(SIZE)]
    board[0] = _BACK_RANK[:]
    board[1] = ["P"] * SIZE
    board[6] = ["p"] * SIZE
    board[7] = [p.lower() for p in _BACK_RANK]
    return board


def new_game():
    return {
        "board": new_board(),
        "turn": WHITE,
        "castling": {"K": True, "Q": True, "k": True, "q": True},
        "en_passant": None,
    }


def color_of(piece):
    if not piece:
        return None
    return WHITE if piece.isupper() else BLACK


def opponent(color):
    return BLACK if color == WHITE else WHITE


def in_bounds(row, col):
    return 0 <= row < SIZE and 0 <= col < SIZE


def _copy_board(board):
    return [row[:] for row in board]


def king_position(board, color):
    king = "K" if color == WHITE else "k"
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == king:
                return row, col
    return None


def _attacked_squares_from_piece(board, row, col):
    """Squares (row, col) attacks, ignoring whose turn it is and
    ignoring castling (a king never "attacks" via castling)."""
    piece = board[row][col]
    color = color_of(piece)
    kind = piece.upper()
    squares = []

    if kind == "P":
        direction = 1 if color == WHITE else -1
        for dc in (-1, 1):
            r, c = row + direction, col + dc
            if in_bounds(r, c):
                squares.append((r, c))
    elif kind == "N":
        for dr, dc in _KNIGHT_OFFSETS:
            r, c = row + dr, col + dc
            if in_bounds(r, c):
                squares.append((r, c))
    elif kind == "K":
        for dr, dc in _KING_OFFSETS:
            r, c = row + dr, col + dc
            if in_bounds(r, c):
                squares.append((r, c))
    else:
        dirs = _DIAGONAL_DIRS if kind == "B" else _STRAIGHT_DIRS if kind == "R" else _KING_OFFSETS
        for dr, dc in dirs:
            r, c = row + dr, col + dc
            while in_bounds(r, c):
                squares.append((r, c))
                if board[r][c] != EMPTY:
                    break
                r, c = r + dr, c + dc

    return squares


def is_square_attacked(board, row, col, by_color):
    for r in range(SIZE):
        for c in range(SIZE):
            piece = board[r][c]
            if piece and color_of(piece) == by_color:
                if (row, col) in _attacked_squares_from_piece(board, r, c):
                    return True
    return False


def is_in_check(state, color):
    pos = king_position(state["board"], color)
    if pos is None:
        return False
    return is_square_attacked(state["board"], pos[0], pos[1], opponent(color))


def _pawn_moves(state, row, col, color):
    board = state["board"]
    direction = 1 if color == WHITE else -1
    start_row = 1 if color == WHITE else 6
    moves = []

    r = row + direction
    if in_bounds(r, col) and board[r][col] == EMPTY:
        moves.append((r, col))
        r2 = row + 2 * direction
        if row == start_row and board[r2][col] == EMPTY:
            moves.append((r2, col))

    for dc in (-1, 1):
        r, c = row + direction, col + dc
        if not in_bounds(r, c):
            continue
        target = board[r][c]
        if target and color_of(target) == opponent(color):
            moves.append((r, c))
        elif (r, c) == state["en_passant"]:
            moves.append((r, c))

    return moves


def _knight_moves(board, row, col, color):
    moves = []
    for dr, dc in _KNIGHT_OFFSETS:
        r, c = row + dr, col + dc
        if in_bounds(r, c) and color_of(board[r][c]) != color:
            moves.append((r, c))
    return moves


def _slide_moves(board, row, col, color, dirs):
    moves = []
    for dr, dc in dirs:
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            occupant = board[r][c]
            if occupant == EMPTY:
                moves.append((r, c))
            else:
                if color_of(occupant) != color:
                    moves.append((r, c))
                break
            r, c = r + dr, c + dc
    return moves


def _king_moves(state, row, col, color):
    board = state["board"]
    moves = []
    for dr, dc in _KING_OFFSETS:
        r, c = row + dr, col + dc
        if in_bounds(r, c) and color_of(board[r][c]) != color:
            moves.append((r, c))

    if is_in_check(state, color):
        return moves

    opp = opponent(color)
    castling = state["castling"]
    king_flag = "K" if color == WHITE else "k"
    queen_flag = "Q" if color == WHITE else "q"

    if castling[king_flag]:
        if board[row][col + 1] == EMPTY and board[row][col + 2] == EMPTY:
            if not is_square_attacked(board, row, col + 1, opp) and \
               not is_square_attacked(board, row, col + 2, opp):
                moves.append((row, col + 2))

    if castling[queen_flag]:
        if board[row][col - 1] == EMPTY and board[row][col - 2] == EMPTY and board[row][col - 3] == EMPTY:
            if not is_square_attacked(board, row, col - 1, opp) and \
               not is_square_attacked(board, row, col - 2, opp):
                moves.append((row, col - 2))

    return moves


def pseudo_legal_moves(state, row, col):
    """Moves for the piece at (row, col), ignoring whether they leave
    the mover's own king in check."""
    board = state["board"]
    piece = board[row][col]
    if not piece:
        return []
    color = color_of(piece)
    kind = piece.upper()

    if kind == "P":
        return _pawn_moves(state, row, col, color)
    if kind == "N":
        return _knight_moves(board, row, col, color)
    if kind == "B":
        return _slide_moves(board, row, col, color, _DIAGONAL_DIRS)
    if kind == "R":
        return _slide_moves(board, row, col, color, _STRAIGHT_DIRS)
    if kind == "Q":
        return _slide_moves(board, row, col, color, _KING_OFFSETS)
    return _king_moves(state, row, col, color)


def _make_move(state, from_sq, to_sq, promotion):
    """Apply a pseudo-legal move and return the new state, without
    checking legality (king safety). `promotion` is used whenever a
    pawn reaches the last rank."""
    row, col = from_sq
    trow, tcol = to_sq
    board = state["board"]
    piece = board[row][col]
    color = color_of(piece)
    kind = piece.upper()

    new_board = _copy_board(board)
    captured = new_board[trow][tcol]
    new_en_passant = None

    if kind == "P" and tcol != col and captured == EMPTY:
        new_board[row][tcol] = EMPTY  # en passant: captured pawn is beside the mover, not on the target square

    if kind == "P" and abs(trow - row) == 2:
        new_en_passant = ((row + trow) // 2, col)

    new_board[row][col] = EMPTY
    new_board[trow][tcol] = piece

    if kind == "P" and trow in (0, SIZE - 1):
        new_board[trow][tcol] = promotion.upper() if color == WHITE else promotion.lower()

    new_castling = dict(state["castling"])

    if kind == "K":
        if color == WHITE:
            new_castling["K"] = False
            new_castling["Q"] = False
        else:
            new_castling["k"] = False
            new_castling["q"] = False
        if abs(tcol - col) == 2:
            if tcol > col:
                rook_from, rook_to = SIZE - 1, tcol - 1
            else:
                rook_from, rook_to = 0, tcol + 1
            new_board[row][rook_to] = new_board[row][rook_from]
            new_board[row][rook_from] = EMPTY

    if kind == "R":
        if color == WHITE and row == 0 and col == 0:
            new_castling["Q"] = False
        elif color == WHITE and row == 0 and col == SIZE - 1:
            new_castling["K"] = False
        elif color == BLACK and row == SIZE - 1 and col == 0:
            new_castling["q"] = False
        elif color == BLACK and row == SIZE - 1 and col == SIZE - 1:
            new_castling["k"] = False

    if captured == "R" and trow == 0 and tcol == 0:
        new_castling["Q"] = False
    elif captured == "R" and trow == 0 and tcol == SIZE - 1:
        new_castling["K"] = False
    elif captured == "r" and trow == SIZE - 1 and tcol == 0:
        new_castling["q"] = False
    elif captured == "r" and trow == SIZE - 1 and tcol == SIZE - 1:
        new_castling["k"] = False

    return {
        "board": new_board,
        "turn": opponent(color),
        "castling": new_castling,
        "en_passant": new_en_passant,
    }


def legal_moves(state, row, col):
    """Pseudo-legal moves for the piece at (row, col), filtered to
    exclude any that leave the mover's own king in check."""
    piece = state["board"][row][col]
    if not piece:
        return []
    color = color_of(piece)
    legal = []
    for to_sq in pseudo_legal_moves(state, row, col):
        candidate = _make_move(state, (row, col), to_sq, "Q")
        if not is_in_check(candidate, color):
            legal.append(to_sq)
    return legal


def apply_move(state, from_sq, to_sq, promotion=None):
    """Return the new state after moving the piece at `from_sq` to
    `to_sq`. Raises ValueError if there's no piece to move, it isn't
    that color's turn, the move isn't legal, or the move promotes a
    pawn and `promotion` (one of "Q"/"R"/"B"/"N", case-insensitive)
    wasn't supplied.
    """
    row, col = from_sq
    board = state["board"]
    piece = board[row][col]
    if not piece:
        raise ValueError("no piece at source square")
    color = color_of(piece)
    if color != state["turn"]:
        raise ValueError("not that color's turn")
    if to_sq not in legal_moves(state, row, col):
        raise ValueError("illegal move")

    trow, _ = to_sq
    is_promotion = piece.upper() == "P" and trow in (0, SIZE - 1)
    if is_promotion:
        if promotion is None or promotion.upper() not in _PROMOTION_PIECES:
            raise ValueError("promotion piece required (Q, R, B, or N)")

    return _make_move(state, from_sq, to_sq, promotion.upper() if promotion else "Q")


def has_any_legal_move(state, color):
    board = state["board"]
    for row in range(SIZE):
        for col in range(SIZE):
            piece = board[row][col]
            if piece and color_of(piece) == color and legal_moves(state, row, col):
                return True
    return False


def is_checkmate(state):
    color = state["turn"]
    return is_in_check(state, color) and not has_any_legal_move(state, color)


def is_stalemate(state):
    color = state["turn"]
    return not is_in_check(state, color) and not has_any_legal_move(state, color)


def game_status(state):
    """One of "checkmate", "stalemate", "check", "ongoing"."""
    if is_checkmate(state):
        return "checkmate"
    if is_stalemate(state):
        return "stalemate"
    if is_in_check(state, state["turn"]):
        return "check"
    return "ongoing"


def winner(state):
    """Color that won by checkmate, or "" if the game isn't a
    decisive checkmate (ongoing, check, or stalemate)."""
    if is_checkmate(state):
        return opponent(state["turn"])
    return ""
