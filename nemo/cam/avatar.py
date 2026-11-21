"""Nemo cam: map Nemo's own opinion of the position to a face.

`mood` is a number in [-1, 1] -- Nemo's best move value, squashed -- and
`panel` turns it into a few narrow lines a game prints beside or under
its board. Pure functions, no I/O.
"""

from nemo.search import minimax

# (lowest mood for this face, face, caption), best first.
_FACES = [
    (0.6, "(^o^)", "Nemo is gloating"),
    (0.2, "(^_^)", "Nemo likes this"),
    (-0.2, "(o_o)", "Nemo is thinking"),
    (-0.6, "(;_;)", "Nemo is worried"),
    (-float("inf"), "(T_T)", "Nemo is sulking"),
]


def mood(adapter, state, depth=1):
    """Nemo's view of `state` for the player to move, in [-1, 1]: the
    best move value at `depth`, with a decided game pinned to +-1."""
    if adapter.outcome(state) is not None:
        return 0.0
    best = max(value for value, _ in minimax.score_moves(adapter, state, depth))
    if abs(best) >= minimax.WIN:
        return 1.0 if best > 0 else -1.0
    return max(-1.0, min(1.0, best))


def face(mood_value):
    for floor, glyph, caption in _FACES:
        if mood_value >= floor:
            return glyph, caption
    raise AssertionError("unreachable: the last floor is -inf")


def panel(mood_value):
    """Two lines, at most 20 columns: the face and its caption."""
    glyph, caption = face(mood_value)
    return [f"  {glyph}", caption[:20]]
