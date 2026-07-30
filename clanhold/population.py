"""Simple periodic kit-birth chance for `clanhold` — not genetics.

A kit's name and single trait are drawn from the same pools
`cats.py` uses for starting cats, with no inheritance from parents.
"""

import cats

BIRTH_CHANCE = 0.05


def maybe_birth_kit(rng, existing_cats):
    """With `BIRTH_CHANCE` probability, return a new kit cat dict (see
    `cats.new_cat`): an unused name from `cats.NAMES`, exactly one
    random trait, no role, "healthy" status.

    Returns None if birth doesn't trigger this day, or if every name
    in `cats.NAMES` is already taken by `existing_cats`. `rng` must
    support `random`/`choice`.
    """
    if rng.random() >= BIRTH_CHANCE:
        return None

    used_names = {cat["name"] for cat in existing_cats}
    available_names = [name for name in cats.NAMES if name not in used_names]
    if not available_names:
        return None

    name = rng.choice(available_names)
    trait = rng.choice(cats.TRAITS)
    return cats.new_cat(name, [trait])
