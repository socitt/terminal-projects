"""Camp state for `furminal`: a flat catalog of unlockable structures.

Per the v1 scope there is no building tree — each structure in
`STRUCTURES` can be unlocked independently, with no prerequisites.
This module only knows the catalog and the pure state transition.

Camp dict shape (JSON-serializable, `game_state["camp"]`):
    {"structures": ["nursery", ...]}   # unlocked structure ids

The catalog -- names, costs, effects -- lives in
`data/structures.json` (Phase C), loaded by `tables.py`. Paying the
cost and applying the effects are `game.py`'s job.
"""

import tables

STRUCTURES = tables.STRUCTURES


def new_camp():
    """Return a freshly founded camp with no structures unlocked."""
    return {"structures": []}


def has_structure(camp, structure_id):
    """True if `structure_id` is already unlocked at `camp`."""
    return structure_id in camp["structures"]


def unlock_structure(camp, structure_id):
    """Return a new camp with `structure_id` unlocked.

    Raises ValueError if `structure_id` isn't in `STRUCTURES` or is
    already unlocked.
    """
    if structure_id not in STRUCTURES:
        raise ValueError(f"unknown structure: {structure_id}")
    if has_structure(camp, structure_id):
        raise ValueError(f"structure already unlocked: {structure_id}")
    return {"structures": camp["structures"] + [structure_id]}
