"""The terminal side of Nemo, shared by every board game's main.py.

- `prompt_opponent()` asks, at game start, who the second player is:
  a human or Nemo at one of three levels;
- `make_rng()` gives Nemo its random source -- seeded from
  `TP_NEMO_SEED` when set, which is how main_test.py makes a Nemo game
  repeatable through a subprocess;
- `take_turn(...)` picks Nemo's move and the Nemo cam lines to show
  with it.

Kept apart from `nemo.search`, which never prints, so the search stays
testable without a terminal.
"""

import os
import random

import nemo
from nemo.cam import avatar
from nemo.search import minimax
from shared import input as input_module

HUMAN = None


def prompt_opponent():
    """Nemo's level, or HUMAN for two players on one screen."""
    print("Opponent:")
    print("  0. Human (same screen)")
    for level, name in nemo.LEVELS.items():
        print(f"  {level}. {nemo.NAME} ({name})")
    key = input_module.prompt_choice("> ", ["0"] + [str(l) for l in nemo.LEVELS])
    return HUMAN if key == "0" else int(key)


def make_rng():
    seed = os.environ.get("TP_NEMO_SEED")
    return random.Random(int(seed)) if seed else random.Random()


def take_turn(adapter, state, level, rng):
    """(move, cam_lines): Nemo's choice in `state`, and the Nemo cam
    panel for how it feels about the position it's moving in."""
    move = minimax.choose_move(adapter, state, level, rng)
    return move, avatar.panel(avatar.mood(adapter, state))
