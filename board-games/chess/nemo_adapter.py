"""Nemo adapter for chess (protocol: nemo/search/minimax.py).

State is the board module's own state dict. A move is
`(from_sq, to_sq, promotion)`; Nemo always promotes to a queen.

Hard Nemo searches 2 plies -- its move and the reply -- on material plus
a small bonus for knights and pawns in the centre. That is enough to
take a free piece, not hang its own, and find mate in one; it is not a
strong player, and isn't meant to be on a phone. Captures are offered
first so alpha-beta prunes early.
"""

from board import SIZE, apply_move, color_of, game_status, legal_moves, opponent

HARD_DEPTH = 2

_VALUE = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}
_CENTRE = {(3, 3), (3, 4), (4, 3), (4, 4)}
_MAX_MATERIAL = 39


def moves(state):
    board, color = state["board"], state["turn"]
    captures, quiet = [], []
    for row in range(SIZE):
        for col in range(SIZE):
            piece = board[row][col]
            if not piece or color_of(piece) != color:
                continue
            for to_sq in legal_moves(state, row, col):
                promo = "Q" if piece.upper() == "P" and to_sq[0] in (0, SIZE - 1) else None
                move = ((row, col), to_sq, promo)
                (captures if board[to_sq[0]][to_sq[1]] else quiet).append(move)
    return captures + quiet


def play(state, move):
    from_sq, to_sq, promo = move
    return apply_move(state, from_sq, to_sq, promo)


def to_move(state):
    return state["turn"]


def outcome(state):
    status = game_status(state)
    if status == "checkmate":
        return opponent(state["turn"])
    if status == "stalemate":
        return "draw"
    return None


def evaluate(state, player):
    total = 0.0
    for row in range(SIZE):
        for col in range(SIZE):
            piece = state["board"][row][col]
            if not piece:
                continue
            value = _VALUE[piece.upper()]
            if piece.upper() in "NP" and (row, col) in _CENTRE:
                value += 0.25
            total += value if color_of(piece) == player else -value
    return max(-1.0, min(1.0, total / _MAX_MATERIAL))
