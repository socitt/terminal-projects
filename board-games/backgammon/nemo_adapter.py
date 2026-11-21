"""Nemo adapter for backgammon (protocol: nemo/search/minimax.py).

State is `(game, player, dice_left)`: the board module's state, whose
turn it is, and the dice still to play this turn in main.py's order.
One Nemo move is one die -- `("enter",)`, `("move", point)`,
`("bear_off", point)`, or `SKIP` when that die has no legal use --
exactly the choice main.py asks a human for.

The player keeps the turn while dice remain, and the next roll is
chance, so this adapter is STOCHASTIC: hard Nemo searches the rest of
its own roll and scores the position where its turn ends.
"""

from board import (
    bear_off,
    enter_from_bar,
    is_game_over,
    legal_actions,
    move_checker,
    opponent,
    pip_distance,
    point_count,
    point_owner,
    winner,
)

SKIP = ("skip",)
HARD_DEPTH = 4
STOCHASTIC = True


def moves(state):
    game, player, dice = state
    if not dice:
        return []
    return legal_actions(game, player, dice[0]) or [SKIP]


def play(state, action):
    game, player, dice = state
    die, rest = dice[0], dice[1:]
    kind = action[0]
    if kind == "enter":
        game = enter_from_bar(game, player, die)
    elif kind == "bear_off":
        game = bear_off(game, player, action[1], die)
    elif kind == "move":
        game = move_checker(game, player, action[1], die)
    return (game, player if rest else opponent(player), rest)


def to_move(state):
    return state[1]


def outcome(state):
    game = state[0]
    return winner(game) if is_game_over(game) else None


def _standing(game, player):
    """(pips still to travel, blots, checkers on the bar, checkers off)."""
    pips = blots = 0
    for point in range(1, 25):
        if point_owner(game, point) == player:
            count = point_count(game, point)
            pips += count * pip_distance(player, point)
            blots += count == 1
    pips += game["bar"][player] * 25
    return pips, blots, game["bar"][player], game["off"][player]


def evaluate(state, player):
    game = state[0]
    my_pips, my_blots, my_bar, my_off = _standing(game, player)
    their_pips, their_blots, their_bar, their_off = _standing(game, opponent(player))
    value = (
        (their_pips - my_pips) / 150
        + (my_off - their_off) / 30
        + 0.1 * (their_bar - my_bar)
        - 0.04 * (my_blots - their_blots)
    )
    return max(-1.0, min(1.0, value))
