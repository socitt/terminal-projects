"""furminal: terminal entrypoint. Thin wrapper -- all prompting,
rendering and save logic lives in `runner.py`, this only supplies the
save path and wires the start flow to the day loop.

The save path is `save.json` next to this file, the same convention as
`adventure-engine`'s stories. There is one save slot per install, not
per clan: v1 plays one clan at a time.
"""

import sys
from pathlib import Path

_FURMINAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_FURMINAL_DIR))

from runner import run, start_flow

SAVE_PATH = _FURMINAL_DIR / "save.json"


def main():
    state = start_flow(str(SAVE_PATH))
    if state is None:
        # The player quit out of region selection without settling
        # anywhere, so there is no clan to play.
        return
    run(state, str(SAVE_PATH))


if __name__ == "__main__":
    main()
