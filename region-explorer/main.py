"""region-explorer: terminal entrypoint. Thin wrapper supplying the
Washington state data to the shared runner -- all rendering/prompt
logic lives in `runner.py`.
"""

import sys
from pathlib import Path

_REGION_EXPLORER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_REGION_EXPLORER_DIR))

from data.washington import STATE
from runner import run


def main():
    run(STATE)


if __name__ == "__main__":
    main()
