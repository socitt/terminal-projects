"""Train whodunit story pack: pure data for adventure-engine's
`engine.py`/`runner.py` -- no engine imports here, just `START` and
`SCENES`.

Scene map (hub-and-spoke, unlike dungeon's linear-with-detours shape):

    corridor (hub) <-> dining_car   (self-loop: examine glass -> clue_poison)
    corridor (hub) <-> sleeper_car  (self-loop: search cabin -> clue_letter)
    corridor (hub) <-> cargo_car    (self-loop: examine prints -> clue_footprints)
    corridor -> confrontation
        -> ending_wrong_conductor [ending]
        -> ending_wrong_stranger [ending]
        -> ending_solved [ending] (needs all 3 clue items -- the
           engine feature this story leans on, vs. dungeon's single-
           flag gate: one choice gated on a 3-item requires_items list)
        -> corridor (keep investigating, always available)

Verified programmatically (BFS over reachable states) that all 8
scenes and all 3 endings are reachable before this was committed.
"""

START = "corridor"

SCENES = {
    "corridor": {
        "art": r"""
 ___________________________
|_[]_______[]_______[]_____|
    corridor, cars both ways
""".strip("\n"),
        "text": (
            "The train rattles on. Somewhere behind you, a body was "
            "found in the dining car an hour ago. Three suspects remain "
            "aboard: the conductor, a wealthy widow, and a stranger who "
            "boarded at the last stop."
        ),
        "choices": [
            {"label": "Go to the dining car", "target": "dining_car"},
            {"label": "Go to the sleeper car", "target": "sleeper_car"},
            {"label": "Go to the cargo car", "target": "cargo_car"},
            {"label": "Confront the suspects", "target": "confrontation"},
        ],
    },
    "dining_car": {
        "art": r"""
   ___________
  |  o     o  |
  | -+-----+- |  <- wine glass
  |___________|
   dining car, table set
""".strip("\n"),
        "text": (
            "The victim's chair still sits pulled out. A half-finished "
            "glass of wine sits by the plate, faint bitter residue "
            "clinging to the rim."
        ),
        "choices": [
            {
                "label": "Examine the wine glass",
                "target": "dining_car",
                "add_items": ["clue_poison"],
                "sets_flags": {"examined_glass": True},
            },
            {"label": "Return to the corridor", "target": "corridor"},
        ],
    },
    "sleeper_car": {
        "art": r"""
   _________
  | ___     |
  ||___|    |  <- bunk, trunk
  |_________|
   sleeper cabin
""".strip("\n"),
        "text": (
            "The widow's cabin, empty for now. A locked travel trunk "
            "sits under the bunk."
        ),
        "choices": [
            {
                "label": "Search the widow's cabin for a hidden letter",
                "target": "sleeper_car",
                "add_items": ["clue_letter"],
                "sets_flags": {"found_letter": True},
            },
            {"label": "Return to the corridor", "target": "corridor"},
        ],
    },
    "cargo_car": {
        "art": r"""
   _________
  |[==] [==]|
  |[==]     |  <- muddy prints
  |_________|
   cargo car, crates
""".strip("\n"),
        "text": "Crates stacked to the ceiling. Muddy bootprints lead between them.",
        "choices": [
            {
                "label": "Examine the muddy footprints",
                "target": "cargo_car",
                "add_items": ["clue_footprints"],
                "sets_flags": {"examined_footprints": True},
            },
            {"label": "Return to the corridor", "target": "corridor"},
        ],
    },
    "confrontation": {
        "art": r"""
   (o_o) (o_o) (o_o)
    /|\   /|\   /|\
   conductor widow stranger
   all gathered, uneasy
""".strip("\n"),
        "text": "You gather the three suspects in the corridor. Time to accuse someone.",
        "choices": [
            {"label": "Accuse the conductor", "target": "ending_wrong_conductor"},
            {"label": "Accuse the stranger", "target": "ending_wrong_stranger"},
            {
                "label": "Accuse the widow",
                "target": "ending_solved",
                "requires_items": ["clue_poison", "clue_letter", "clue_footprints"],
            },
            {"label": "Keep investigating", "target": "corridor"},
        ],
    },
    "ending_solved": {
        "art": r"""
    (o_o)
     /|\  <-- cuffed
    _/ \_
   case closed!
""".strip("\n"),
        "text": (
            "The poison, the motive in her letter, the muddy footprints "
            "matching her boots -- the widow has nowhere left to turn. "
            "Case closed."
        ),
        "choices": [],
    },
    "ending_wrong_conductor": {
        "art": r"""
   ~ ~ ~  choo choo  ~ ~ ~
     _____
    |_[]__|--
   the train rolls on...
""".strip("\n"),
        "text": (
            "The conductor protests his innocence all the way to the "
            "next station -- and he's right. The real killer slips away "
            "at the platform."
        ),
        "choices": [],
    },
    "ending_wrong_stranger": {
        "art": r"""
   ~ ~ ~  choo choo  ~ ~ ~
     _____
    |_[]__|--
   the train rolls on...
""".strip("\n"),
        "text": (
            "The stranger is dragged off in cuffs, bewildered. Whatever "
            "he did before boarding, it wasn't this. The real killer "
            "slips away at the platform."
        ),
        "choices": [],
    },
}
