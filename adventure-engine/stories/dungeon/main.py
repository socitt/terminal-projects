"""Dungeon crawler: terminal entrypoint. Thin wrapper around the
shared adventure-engine runner -- all rendering/prompt/save logic
lives in `runner.py`, this just supplies the story data and a save
path.
"""

import sys
from pathlib import Path

_STORY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_STORY_DIR.parent.parent))  # adventure-engine/

from runner import run

import story

SAVE_PATH = _STORY_DIR / "save.json"


def main():
    run(story, str(SAVE_PATH))


if __name__ == "__main__":
    main()
