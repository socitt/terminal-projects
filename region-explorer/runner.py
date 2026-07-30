"""Interactive region-explorer loop: show the state overview, let the
player pick a region, then zoom into its detail art -- either
animated (a short shrinking-crop sequence) or straight to the final
detail art, chosen upfront. `shared/input.py`'s line-buffered model
can't interrupt a playing animation mid-flight, so "skip" has to be a
decision made before it starts, not a keypress during it.
"""

import sys
import time
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENGINE_DIR.parent))

import engine
from shared import input as input_module
from shared import term

FRAME_DELAY_SECONDS = 0.5
NUM_ZOOM_FRAMES = 4


def _render_grid(grid):
    print("\n".join(grid))


def _show_overview(state):
    term.clear_screen()
    print(state["name"])
    print(term.hr())
    _render_grid(state["art"])
    print(term.hr())
    for i, region in enumerate(state["regions"], start=1):
        print(f"{i}. {region['name']}")
    print("q. Quit")


def _render_zoom(state, region, animate, sleep_fn):
    """Render the zoom sequence (animated or straight to the final
    frame) ending on `region`'s detail art and landmark list. Returns
    nothing -- callers decide what prompt comes next, since `run()`'s
    browse loop and `select_region()`'s pick-and-confirm flow want
    different ones here."""
    frames = engine.zoom_frames(state, region["id"], num_frames=NUM_ZOOM_FRAMES)
    if animate:
        for frame in frames[:-1]:
            term.clear_screen()
            _render_grid(frame)
            sleep_fn(FRAME_DELAY_SECONDS)

    term.clear_screen()
    print(region["name"])
    print(term.hr())
    _render_grid(frames[-1])
    print(term.hr())
    for landmark in region["landmarks"]:
        print(f"- {landmark}")


def _show_region(state, region, animate, sleep_fn):
    _render_zoom(state, region, animate, sleep_fn)
    input_module.get_key("\nPress Enter to go back to the overview: ")


def _pick_region(state):
    """Show the overview and prompt for a region choice. Returns the
    chosen region dict, or None if the player quits."""
    _show_overview(state)
    valid_keys = [str(i) for i in range(1, len(state["regions"]) + 1)] + ["q"]
    key = input_module.prompt_choice("> ", valid_keys)
    if key == "q":
        return None
    return state["regions"][int(key) - 1]


def run(state, sleep_fn=time.sleep):
    """Run the interactive loop against `state` (a `STATE`-shaped
    dict, see `data/washington.py`) until the player quits.

    `sleep_fn` is injectable (same reasoning as `backgammon.roll_dice`
    taking an rng) so tests can assert the animation path was
    actually taken by call count, instead of racing real wall-clock
    delays against subprocess overhead.
    """
    while True:
        region = _pick_region(state)
        if region is None:
            return

        animate = (
            input_module.prompt_choice("Play zoom animation? (y/n): ", ["y", "n"])
            == "y"
        )
        _show_region(state, region, animate, sleep_fn)


def select_region(state, sleep_fn=time.sleep):
    """Same overview/zoom browsing as `run()`, but for callers that
    need the player to actually settle on one region rather than just
    browse until quitting (`furminal`'s starting flow). Loops
    overview -> zoom -> "Settle here?" until confirmed or the player
    quits from the overview. Returns the chosen region dict, or None
    on quit.
    """
    while True:
        region = _pick_region(state)
        if region is None:
            return None

        animate = (
            input_module.prompt_choice("Play zoom animation? (y/n): ", ["y", "n"])
            == "y"
        )
        _render_zoom(state, region, animate, sleep_fn)
        if input_module.prompt_choice("\nSettle here? (y/n): ", ["y", "n"]) == "y":
            return region
