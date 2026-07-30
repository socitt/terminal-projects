"""Simple rotating weather for `furminal`.

Deliberately not a full simulation: each day's weather either persists
or rolls over to a different state (`advance_weather`), and other
modules (`game.py`'s orchestration, not `hunting.py` itself, to keep
that module decoupled) apply `yield_multiplier` to hunting/gathering
results. `game_state["weather"]` is just one of `WEATHER_STATES`.
"""

WEATHER_STATES = ["clear", "overcast", "rain", "storm", "snow"]

YIELD_MULTIPLIER = {
    "clear": 1.0,
    "overcast": 1.0,
    "rain": 0.8,
    "storm": 0.5,
    "snow": 0.6,
}

PERSIST_CHANCE = 0.6


def advance_weather(current, rng):
    """Return the next day's weather.

    With `PERSIST_CHANCE` probability, stays `current`; otherwise
    rolls to a different state chosen at random. `rng` must support
    `random`/`choice`.
    """
    if rng.random() < PERSIST_CHANCE:
        return current
    return rng.choice([state for state in WEATHER_STATES if state != current])


def yield_multiplier(weather):
    """Return the hunting/gathering yield multiplier for `weather`."""
    return YIELD_MULTIPLIER[weather]
