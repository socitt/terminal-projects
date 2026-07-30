"""Cat data and starting-roster generation for `clanhold`.

Cat dict shape (JSON-serializable, part of `game_state["cats"]`):
    {
        "name": "...",
        "traits": ["...", ...],           # 2-3 for starting cats
        "role": "leader" | "healer" | None,
        "status": "healthy" | "injured" | "sick",
    }

This module only defines the shape and how a starting roster is
generated. Status transitions (injury, illness, recovery) belong to
whichever module causes them (`hunting.py`, `population.py`, ...).
"""

NAMES = [
    "Ash", "Willow", "Juniper", "Moss", "Ember", "Thistle", "Briar",
    "Hazel", "Fern", "Storm", "Clover", "Sable", "Flint", "Reed",
    "Marigold", "Cinder", "Heather", "Birch", "Rowan", "Otter",
]

TRAITS = [
    "brave", "cautious", "quick", "keen-eyed", "gentle", "stubborn",
    "curious", "patient", "fierce", "clever", "quiet", "loyal",
    "restless", "gruff", "playful",
]

ROLES = ("leader", "healer")


def new_cat(name, traits, role=None, status="healthy"):
    """Return a new cat dict."""
    return {"name": name, "traits": list(traits), "role": role, "status": status}


def generate_starting_cats(rng):
    """Return 3-4 new cats for a freshly founded clan.

    Unique names, 2-3 unique traits each, exactly one "leader" and one
    "healer" among them (never the same cat), the rest with no role.
    `rng` must support `choice` and `sample` (inject `random` or a
    fake for testing).
    """
    count = rng.choice([3, 4])
    names = rng.sample(NAMES, count)

    cats = []
    for name in names:
        trait_count = rng.choice([2, 3])
        cats.append(new_cat(name, rng.sample(TRAITS, trait_count)))

    leader_idx, healer_idx = rng.sample(range(count), 2)
    cats[leader_idx]["role"] = "leader"
    cats[healer_idx]["role"] = "healer"
    return cats


def cat_with_role(cats, role):
    """Return the first cat in `cats` with the given `role`, or None."""
    for cat in cats:
        if cat["role"] == role:
            return cat
    return None


def set_cat_status(cats, name, status):
    """Return a new cat list with the cat named `name` updated to
    `status`. No-op (returns `cats` unchanged) if no cat has that name.
    """
    return [dict(cat, status=status) if cat["name"] == name else cat for cat in cats]
