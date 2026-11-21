"""furminal's tuning tables, read from `furminal/data/*.json`.

Phase C moved the numbers that decide structure costs and effects,
trait effects, and what a rival clan does at the border out of the code
and into data, so balancing them is an edit to a JSON file rather than
to a module and its tests' expectations.

This is the bottom layer (below L0, see ARCHITECTURE.md §2): it imports
nothing from furminal, and L0 modules may import it. It reads its own
package-relative data once, at import -- the one filesystem read below
`runner.py` besides `game.save_state`/`load_state`.

Every table is checked by `validate` at import, so a typo in a JSON
file fails loudly at startup instead of as a KeyError mid-game.

Tables:
- `STRUCTURES`: id -> {"name", "description", "cost": {"food": int},
  "effects": {effect: number}}. Effects: `birth_chance_bonus`,
  `recovery_bonus`, `raid_shield` (halves a raid's losses).
- `TRAIT_EFFECTS`: trait -> {effect: number}. Effects:
  `hunt_food_bonus` (added to a successful hunt), `hunt_injury_scale`
  (multiplies the injury chance), `recovery_bonus`, `leader_drift`
  (daily disposition change while this cat leads). Traits not listed
  are flavour.
- `BORDER`: disposition tier -> {"chance", "food", "water", "text"},
  for "hostile" (raids) and "friendly" (gifts). "neutral" does nothing.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

STRUCTURE_EFFECTS = {"birth_chance_bonus", "recovery_bonus", "raid_shield"}
TRAIT_EFFECT_KEYS = {"hunt_food_bonus", "hunt_injury_scale", "recovery_bonus",
                     "leader_drift"}
BORDER_TIERS = {"hostile", "friendly"}


def load(name, data_dir=DATA_DIR):
    return json.loads((data_dir / f"{name}.json").read_text(encoding="utf-8"))


def _number(value, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: expected a number, got {value!r}")
    return value


def validate(structures, trait_effects, border):
    """Raise ValueError naming the first malformed entry, if any."""
    for sid, entry in structures.items():
        for key in ("name", "description", "cost", "effects"):
            if key not in entry:
                raise ValueError(f"structures.{sid}: missing {key!r}")
        cost = _number(entry["cost"].get("food"), f"structures.{sid}.cost.food")
        if cost < 0:
            raise ValueError(f"structures.{sid}.cost.food: negative")
        for effect, value in entry["effects"].items():
            if effect not in STRUCTURE_EFFECTS:
                raise ValueError(f"structures.{sid}: unknown effect {effect!r}")
            _number(value, f"structures.{sid}.effects.{effect}")
    for trait, effects in trait_effects.items():
        for effect, value in effects.items():
            if effect not in TRAIT_EFFECT_KEYS:
                raise ValueError(f"traits.{trait}: unknown effect {effect!r}")
            _number(value, f"traits.{trait}.{effect}")
    if set(border) != BORDER_TIERS:
        raise ValueError(f"border: tiers must be exactly {sorted(BORDER_TIERS)}")
    for tier, rule in border.items():
        chance = _number(rule.get("chance"), f"border.{tier}.chance")
        if not 0 <= chance <= 1:
            raise ValueError(f"border.{tier}.chance: outside [0, 1]")
        _number(rule.get("food"), f"border.{tier}.food")
        _number(rule.get("water"), f"border.{tier}.water")
        if "{rival}" not in rule.get("text", ""):
            raise ValueError(f"border.{tier}.text: must mention {{rival}}")


STRUCTURES = load("structures")
TRAIT_EFFECTS = load("traits")
BORDER = load("border")
validate(STRUCTURES, TRAIT_EFFECTS, BORDER)
