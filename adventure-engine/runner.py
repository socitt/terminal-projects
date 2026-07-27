"""Shared interactive game loop for any story pack.

Each story pack's own thin `main.py` imports `run` from here and calls
`run(story, save_path)` with its own story module and its own save-file
path — this is the one place the engine's I/O (rendering, prompts,
save/resume) lives, so no story pack needs to reimplement it.
"""

import os
import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENGINE_DIR.parent))

import engine
from shared import input as input_module
from shared import term


def _render(scene):
    if scene.get("art"):
        print(scene["art"])
        print(term.hr())
    print(scene["text"])


def run(story, save_path):
    state = None
    if os.path.exists(save_path):
        resume = input_module.prompt_choice(
            "Saved game found. Resume? (y/n): ", ["y", "n"]
        )
        if resume == "y":
            state = engine.load_state(save_path)

    if state is None:
        state = engine.new_state(story)

    while True:
        term.clear_screen()
        scene = story.SCENES[state["scene"]]
        _render(scene)

        if engine.is_ending(story, state):
            print(f"\n{term.hr()}\nTHE END")
            if os.path.exists(save_path):
                os.remove(save_path)
            return state

        choices = engine.available_choices(story, state)
        print(f"\n{term.hr()}")
        for i, choice in enumerate(choices, start=1):
            print(f"{i}. {choice['label']}")
        print("s. Save and quit")

        valid_keys = [str(i) for i in range(1, len(choices) + 1)] + ["s"]
        key = input_module.prompt_choice("> ", valid_keys)

        if key == "s":
            engine.save_state(state, save_path)
            print("\nSaved. Run this story again to resume.")
            return state

        state = engine.apply_choice(story, state, int(key) - 1)
