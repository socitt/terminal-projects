"""Backgammon board logic: pure functions over a 24-point board.

State is a dict: {"points": [...], "bar": {...}, "off": {...}}.

`points` is a list of 25 ints, index 0 unused, indices 1-24 used.
A positive value is a count of X checkers on that point; negative is
a count of O checkers; 0 is empty. `bar` and `off` are dicts keyed by
player ("X"/"O") counting checkers on the bar (hit, not yet
re-entered) and borne off (removed from play, having completed the
full circuit).

X moves from point 24 toward point 1 and bears off past point 1
(home board: points 1-6). O moves from point 1 toward point 24 and
bears off past point 24 (home board: points 19-24). A player with
checkers on the bar must re-enter them (into the opponent's home
board) before making any other move.

No doubling cube: this implements the core movement/hitting/
bearing-off ruleset only.
"""

PLAYERS = ("X", "O")


def new_game():
    points = [0] * 25
    points[24] = 2
    points[13] = 5
    points[8] = 3
    points[6] = 5
    points[1] = -2
    points[12] = -5
    points[17] = -3
    points[19] = -5
    return {
        "points": points,
        "bar": {"X": 0, "O": 0},
        "off": {"X": 0, "O": 0},
    }


def opponent(player):
    return "O" if player == "X" else "X"


def direction(player):
    return -1 if player == "X" else 1


def home_range(player):
    return range(1, 7) if player == "X" else range(19, 25)


def point_owner(state, point):
    value = state["points"][point]
    if value > 0:
        return "X"
    if value < 0:
        return "O"
    return None


def point_count(state, point):
    return abs(state["points"][point])


def is_blocked(state, player, point):
    """True if `point` has 2+ of the opponent's checkers on it."""
    return point_owner(state, point) == opponent(player) and point_count(state, point) >= 2


def destination(player, point, die):
    return point + direction(player) * die


def bar_entry_point(player, die):
    """Point a checker entering from the bar lands on for a given die."""
    return 25 - die if player == "X" else die


def all_checkers_in_home(state, player):
    if state["bar"][player] > 0:
        return False
    home = set(home_range(player))
    for point in range(1, 25):
        if point_owner(state, point) == player and point not in home:
            return False
    return True


def pip_distance(player, point):
    """Pips needed to bear a checker on `point` off for `player`."""
    return point if player == "X" else 25 - point


def _copy_state(state):
    return {
        "points": list(state["points"]),
        "bar": dict(state["bar"]),
        "off": dict(state["off"]),
    }


def _place_checker(state, player, point):
    """Mutate `state` in place: place one of `player`'s checkers on
    `point`, sending a lone opposing checker to the bar (a hit)."""
    if point_owner(state, point) == opponent(player) and point_count(state, point) == 1:
        state["bar"][opponent(player)] += 1
        state["points"][point] = 0
    state["points"][point] += 1 if player == "X" else -1


def can_enter_from_bar(state, player, die):
    if state["bar"][player] <= 0:
        return False
    return not is_blocked(state, player, bar_entry_point(player, die))


def enter_from_bar(state, player, die):
    if not can_enter_from_bar(state, player, die):
        raise ValueError(f"{player} cannot enter from bar with die {die}")
    new_state = _copy_state(state)
    new_state["bar"][player] -= 1
    _place_checker(new_state, player, bar_entry_point(player, die))
    return new_state


def can_move(state, player, point, die):
    if state["bar"][player] > 0:
        return False
    if point_owner(state, point) != player:
        return False
    dest = destination(player, point, die)
    if not 1 <= dest <= 24:
        return False
    return not is_blocked(state, player, dest)


def move_checker(state, player, point, die):
    if not can_move(state, player, point, die):
        raise ValueError(f"{player} cannot move point {point} with die {die}")
    new_state = _copy_state(state)
    new_state["points"][point] -= 1 if player == "X" else -1
    _place_checker(new_state, player, destination(player, point, die))
    return new_state


def can_bear_off(state, player, point, die):
    if state["bar"][player] > 0:
        return False
    if not all_checkers_in_home(state, player):
        return False
    if point_owner(state, point) != player:
        return False
    dist = pip_distance(player, point)
    if die < dist:
        return False
    if die == dist:
        return True
    # die > dist: only legal if no checker sits farther from home.
    for other in home_range(player):
        if point_owner(state, other) == player and pip_distance(player, other) > dist:
            return False
    return True


def bear_off(state, player, point, die):
    if not can_bear_off(state, player, point, die):
        raise ValueError(f"{player} cannot bear off point {point} with die {die}")
    new_state = _copy_state(state)
    new_state["points"][point] -= 1 if player == "X" else -1
    new_state["off"][player] += 1
    return new_state


def is_game_over(state):
    return state["off"]["X"] == 15 or state["off"]["O"] == 15


def winner(state):
    if state["off"]["X"] == 15:
        return "X"
    if state["off"]["O"] == 15:
        return "O"
    return ""


def dice_to_moves(d1, d2):
    """Convert a dice roll to the list of die values usable this turn."""
    return [d1] * 4 if d1 == d2 else [d1, d2]


def roll_dice(rng):
    """Roll two dice using `rng.randint(1, 6)` (inject `random` module or
    a fake for testing)."""
    return rng.randint(1, 6), rng.randint(1, 6)


def legal_actions(state, player, die):
    """Legal actions for `player` using a single die value `die`.

    Each action is a tuple: ("enter",), ("move", point), or
    ("bear_off", point). If the player has checkers on the bar, only
    ("enter",) actions are possible (or none, if entry is blocked).
    """
    if state["bar"][player] > 0:
        return [("enter",)] if can_enter_from_bar(state, player, die) else []
    actions = []
    for point in range(1, 25):
        if point_owner(state, point) != player:
            continue
        if can_move(state, player, point, die):
            actions.append(("move", point))
        elif can_bear_off(state, player, point, die):
            actions.append(("bear_off", point))
    return actions
