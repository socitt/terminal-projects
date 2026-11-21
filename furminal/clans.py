"""The single neighboring clan for `furminal`'s v1 scope.

Not multi-clan diplomacy: one rival clan with a disposition value that
drifts by a small random step each day, no player-driven diplomacy
actions. Clan dict shape (JSON-serializable, `game_state["other_clans"]`
holds a list of these, though v1 only ever populates one):
    {"name": "...", "disposition": int}   # clamped to [-100, 100]
"""

DISPOSITION_MIN = -100
DISPOSITION_MAX = 100
DRIFT_STEP = 5

NEIGHBOR_CLAN_NAMES = [
    "Silver Hollow", "Iron Ridge", "Grey Marsh", "Thorn Vale",
    "Stone Hollow", "Amber Vale", "Cedar Ridge", "Salt Marsh",
]


def new_clan(name, disposition=0):
    """Return a new clan dict, disposition clamped to its valid range."""
    return {"name": name, "disposition": _clamp(disposition)}


def _clamp(value):
    return max(DISPOSITION_MIN, min(DISPOSITION_MAX, value))


def generate_neighbor_clan(rng):
    """Return a freshly generated rival clan with a random starting
    disposition. `rng` must support `choice`/`randint`."""
    return new_clan(rng.choice(NEIGHBOR_CLAN_NAMES), rng.randint(-20, 20))


def drift_disposition(clan, rng):
    """Return a new clan with disposition shifted by a small random
    step (-DRIFT_STEP..+DRIFT_STEP), clamped to its valid range."""
    step = rng.randint(-DRIFT_STEP, DRIFT_STEP)
    return new_clan(clan["name"], clan["disposition"] + step)


def disposition_tier(disposition):
    """Return a coarse named tier for display: "hostile", "neutral", or
    "friendly"."""
    if disposition <= -34:
        return "hostile"
    if disposition >= 34:
        return "friendly"
    return "neutral"


def border_incident(clan, rules, rng):
    """What `clan` does at the border today, per its disposition tier
    (Phase C, closes G6): None, or {"food": int, "water": int,
    "text": str} from `rules[tier]` (the "hostile" raid or "friendly"
    gift in `data/border.json`). A neutral clan does nothing and makes
    no rng call; the others make exactly one."""
    rule = rules.get(disposition_tier(clan["disposition"]))
    if rule is None or rng.random() >= rule["chance"]:
        return None
    return {"food": rule["food"], "water": rule["water"],
            "text": rule["text"].format(rival=clan["name"])}
