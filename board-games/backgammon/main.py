"""Backgammon: terminal entrypoint for narrow screens, iOS on-screen
keyboard (single key + Enter, no arrow/modifier chords).
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared import input as input_module
from shared import term

from board import (
    bear_off,
    dice_to_moves,
    enter_from_bar,
    is_game_over,
    legal_actions,
    move_checker,
    new_game,
    opponent,
    point_count,
    point_owner,
    roll_dice,
    winner,
)


def _cell(state, point):
    """A fixed-width (2-char) label for `point`: owner letter + count,
    or " ." if empty. Counts of 10+ are shown as "+" to keep columns
    aligned in the narrow board display."""
    owner = point_owner(state, point)
    if owner is None:
        return " ."
    count = point_count(state, point)
    digit = str(count) if count < 10 else "+"
    return f"{owner}{digit}"


def render(state):
    top = " ".join(_cell(state, p) for p in range(13, 25))
    bottom = " ".join(_cell(state, p) for p in range(12, 0, -1))
    return "\n".join(
        [
            top,
            term.hr(),
            bottom,
            "",
            f"Bar  X:{state['bar']['X']}  O:{state['bar']['O']}",
            f"Off  X:{state['off']['X']}  O:{state['off']['O']}",
        ]
    )


def _describe(action):
    kind = action[0]
    if kind == "enter":
        return "enter from bar"
    verb = "bear off" if kind == "bear_off" else "move"
    return f"{verb} point {action[1]}"


def _apply(state, player, action, die):
    kind = action[0]
    if kind == "enter":
        return enter_from_bar(state, player, die)
    if kind == "bear_off":
        return bear_off(state, player, action[1], die)
    return move_checker(state, player, action[1], die)


def _play_die(state, player, die):
    actions = legal_actions(state, player, die)
    if not actions:
        print(f"\nNo legal move for die {die}.")
        input_module.get_key("Press Enter to continue... ")
        return state
    print(f"\nDie {die}:")
    for i, action in enumerate(actions, start=1):
        print(f"  {i}. {_describe(action)}")
    keys = [str(i) for i in range(1, len(actions) + 1)]
    key = input_module.prompt_choice("> ", keys)
    return _apply(state, player, actions[int(key) - 1], die)


def main():
    state = new_game()
    turn = "X"
    while True:
        d1, d2 = roll_dice(random)
        for die in dice_to_moves(d1, d2):
            term.clear_screen()
            print(render(state))
            print(f"\n{turn}'s turn. Dice: {d1} {d2}")
            state = _play_die(state, turn, die)
            if is_game_over(state):
                term.clear_screen()
                print(render(state))
                print(f"\n{winner(state)} wins!")
                return
        turn = opponent(turn)


if __name__ == "__main__":
    main()
