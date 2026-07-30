"""Territory as a small named zone graph, per `furminal`'s v1 design.

Deliberately a graph, not an x/y grid: each region-explorer region gets
its own small zone graph (6-10 zones) generated fresh at game start.
This module is agnostic to which `region-explorer` region the graph
belongs to — it only ever deals in zone ids, terrain, and adjacency,
the same "engine stays content-agnostic" split used by
`region-explorer/engine.py` versus `region-explorer/data/washington.py`.

Zone dict shape:
    {
        "id": "...",
        "terrain": "...",
        "adjacent": ["zone_id", ...],
        "explored": bool,
        "controlled": bool,
    }

A zone graph (`game_state["zones"]`) is a JSON-serializable dict of
`{zone_id: zone}`. Fog-of-war/territory-via-patrol is modeled as two
gates: a zone can only be explored once adjacent to an already-explored
zone, and can only be controlled once explored and adjacent to an
already-controlled zone — territory grows outward from the starting
"home" zone one hop at a time. Risk/outcome of the patrol action that
triggers exploration belongs to `hunting.py`, not here.
"""

TERRAIN_TYPES = [
    "forest", "meadow", "thicket", "riverbank", "rocky_outcrop",
    "wetland", "ridge", "clearing", "scrubland", "cave", "grove",
    "bramble",
]


def new_zone(zone_id, terrain, adjacent=(), explored=False, controlled=False):
    """Return a new zone dict."""
    return {
        "id": zone_id,
        "terrain": terrain,
        "adjacent": list(adjacent),
        "explored": explored,
        "controlled": controlled,
    }


def _zone_id(i):
    return "home" if i == 0 else f"zone_{i}"


def generate_zone_graph(rng):
    """Return a freshly generated zone graph: 6-10 zones wired into a
    ring (each zone adjacent to its two neighbors), random terrain per
    zone, with only the "home" zone (index 0) starting explored and
    controlled. `rng` must support `randint`/`choice` (inject `random`
    or a fake for testing).
    """
    count = rng.randint(6, 10)
    zones = {}
    for i in range(count):
        zone_id = _zone_id(i)
        prev_id = _zone_id((i - 1) % count)
        next_id = _zone_id((i + 1) % count)
        adjacent = sorted({prev_id, next_id} - {zone_id})
        zones[zone_id] = new_zone(
            zone_id,
            rng.choice(TERRAIN_TYPES),
            adjacent=adjacent,
            explored=(i == 0),
            controlled=(i == 0),
        )
    return zones


def can_explore(zones, zone_id):
    """True if `zone_id` is unexplored but adjacent to an explored zone."""
    zone = zones[zone_id]
    if zone["explored"]:
        return False
    return any(zones[adj]["explored"] for adj in zone["adjacent"])


def explore_zone(zones, zone_id):
    """Return a new zone graph with `zone_id` marked explored.

    Raises ValueError if `can_explore(zones, zone_id)` is False.
    """
    if not can_explore(zones, zone_id):
        raise ValueError(f"cannot explore zone: {zone_id}")
    updated = dict(zones)
    updated[zone_id] = {**zones[zone_id], "explored": True}
    return updated


def can_control(zones, zone_id):
    """True if `zone_id` is explored, uncontrolled, and adjacent to a
    controlled zone."""
    zone = zones[zone_id]
    if not zone["explored"] or zone["controlled"]:
        return False
    return any(zones[adj]["controlled"] for adj in zone["adjacent"])


def control_zone(zones, zone_id):
    """Return a new zone graph with `zone_id` marked controlled.

    Raises ValueError if `can_control(zones, zone_id)` is False.
    """
    if not can_control(zones, zone_id):
        raise ValueError(f"cannot control zone: {zone_id}")
    updated = dict(zones)
    updated[zone_id] = {**zones[zone_id], "controlled": True}
    return updated
