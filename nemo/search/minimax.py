"""Nemo's move choice, for any game that supplies an adapter.

An adapter is any object (in practice a module) with:

- `moves(state)` -> list of moves for the player to move (non-empty
  whenever `outcome(state)` is None);
- `play(state, move)` -> the next state (must not mutate `state`);
- `to_move(state)` -> the player to move;
- `outcome(state)` -> None while the game is on, "draw", or the winner;
- `evaluate(state, player)` -> a heuristic score of a non-final state
  from `player`'s point of view, roughly within [-1, 1];
- `HARD_DEPTH` -> how many plies the hard level searches;
- `STOCHASTIC` (optional, default False) -> True when the opponent's
  options depend on chance (dice), so looking at their reply is
  meaningless; medium and hard then judge a move by `evaluate` alone.

Levels (docs/USER_TESTING.md):

- easy (1): a random legal move;
- medium (2): takes a win in one, avoids handing the opponent a win in
  one, otherwise random;
- hard (3): negamax with alpha-beta to `HARD_DEPTH`, random among
  equally good moves.

Turns need not alternate strictly (a pass, or a backgammon turn made of
several checker moves, is one `play`): a child's value is negated only
when `to_move` changes.
"""

import nemo

WIN = 1000.0


def _terminal_value(adapter, state, player, depth_left):
    """Score of a finished game for `player`. Sooner wins score higher
    and later losses lower, so hard Nemo doesn't dawdle."""
    result = adapter.outcome(state)
    if result == "draw":
        return 0.0
    return WIN + depth_left if result == player else -WIN - depth_left


def _negamax(adapter, state, depth, alpha, beta):
    player = adapter.to_move(state)
    if adapter.outcome(state) is not None:
        return _terminal_value(adapter, state, player, depth)
    if depth == 0:
        return adapter.evaluate(state, player)
    best = -float("inf")
    for move in adapter.moves(state):
        child = adapter.play(state, move)
        if adapter.to_move(child) == player:
            value = _negamax(adapter, child, depth - 1, alpha, beta)
        else:
            value = -_negamax(adapter, child, depth - 1, -beta, -alpha)
        best = max(best, value)
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return best


def score_moves(adapter, state, depth):
    """[(value, move)] for every move, from the mover's point of view.
    Exposed for tests and for the Nemo cam's mood."""
    player = adapter.to_move(state)
    scored = []
    for move in adapter.moves(state):
        child = adapter.play(state, move)
        if adapter.outcome(child) is not None:
            value = _terminal_value(adapter, child, player, depth)
        elif depth <= 1 or getattr(adapter, "STOCHASTIC", False):
            value = adapter.evaluate(child, player)
        elif adapter.to_move(child) == player:
            value = _negamax(adapter, child, depth - 1, -float("inf"), float("inf"))
        else:
            value = -_negamax(adapter, child, depth - 1, -float("inf"), float("inf"))
        scored.append((value, move))
    return scored


def _wins_now(adapter, state, move, player):
    return adapter.outcome(adapter.play(state, move)) == player


def _gives_away_a_win(adapter, state, move, player):
    child = adapter.play(state, move)
    if adapter.outcome(child) is not None or adapter.to_move(child) == player:
        return False
    opponent = adapter.to_move(child)
    return any(_wins_now(adapter, child, reply, opponent)
               for reply in adapter.moves(child))


def _medium(adapter, state, moves, rng):
    player = adapter.to_move(state)
    wins = [m for m in moves if _wins_now(adapter, state, m, player)]
    if wins:
        return rng.choice(wins)
    if getattr(adapter, "STOCHASTIC", False):
        # No reply to look at; settle for the better half by heuristic.
        ranked = sorted(score_moves(adapter, state, 1), key=lambda vm: vm[0],
                        reverse=True)
        return rng.choice(ranked[: max(1, len(ranked) // 2)])[1]
    safe = [m for m in moves if not _gives_away_a_win(adapter, state, m, player)]
    return rng.choice(safe or moves)


def choose_move(adapter, state, level, rng):
    """Nemo's move in `state` at `level` (nemo.EASY/MEDIUM/HARD).
    `rng` is a `random.Random`, injected so play is reproducible."""
    if level not in nemo.LEVELS:
        raise ValueError(f"unknown Nemo level: {level!r}")
    moves = list(adapter.moves(state))
    if not moves:
        raise ValueError("Nemo was asked to move with no legal moves")
    if level == nemo.EASY:
        return rng.choice(moves)
    if level == nemo.MEDIUM:
        return _medium(adapter, state, moves, rng)
    scored = score_moves(adapter, state, adapter.HARD_DEPTH)
    best = max(value for value, _ in scored)
    return rng.choice([m for value, m in scored if value == best])
