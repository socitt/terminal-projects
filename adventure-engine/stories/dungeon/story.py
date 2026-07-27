"""Dungeon crawler story pack: pure data for adventure-engine's
`engine.py`/`runner.py` -- no engine imports here, just `START` and
`SCENES`.

Scene map (gate in parens):

    cell -> torch_room (get torch) -> found_key_room (get rusty_key)
    cell -> caught_again [ending]
    torch_room/found_key_room -> corridor (needs rusty_key)
    corridor -> escape_plain [ending]
    corridor -> vault_entrance -> vault (needs studied_guard flag,
        set by a self-looping "study the guard" choice in corridor)
    vault -> escape_with_treasure [ending] (grab treasure) or
        escape_plain [ending] (leave it)

Verified programmatically (BFS over reachable states) that all 9
scenes and all 3 endings are reachable before this was committed.
"""

START = "cell"

SCENES = {
    "cell": {
        "art": r"""
+----------------------------------+
|////////////////////////////////|
| |   |   |   |   |   |   |   | |
|                                  |
|      .   straw bedding   .      |
|                                  |
| |   |   |   |   |   |   |   | |
+----------------------------------+
""".strip("\n"),
        "text": (
            "You wake on cold stone. A locked door of iron bars is the "
            "only way out. Straw bedding is piled in the corner."
        ),
        "choices": [
            {
                "label": "Search the straw bedding",
                "target": "torch_room",
                "add_items": ["torch"],
                "sets_flags": {"took_torch": True},
            },
            {
                "label": "Pound on the door and shout",
                "target": "caught_again",
            },
        ],
    },
    "torch_room": {
        "art": r"""
   \|/
  --*--    _____
   /|\    | ~~~ |  <- loose stone
    |     |_____|
    |
  torch bracket, dim room
""".strip("\n"),
        "text": (
            "Buried in the straw was a stub of torch, now lit from the "
            "wall bracket. Its light shows a loose stone in the floor, "
            "and the heavy door beyond."
        ),
        "choices": [
            {
                "label": "Pry up the loose stone in the floor",
                "target": "found_key_room",
                "add_items": ["rusty_key"],
                "sets_flags": {"found_key": True},
            },
            {
                "label": "Try the heavy door",
                "target": "corridor",
                "requires_items": ["rusty_key"],
            },
            {
                "label": "Sit back down and wait",
                "target": "cell",
            },
        ],
    },
    "found_key_room": {
        "art": r"""
      ,_
     / /\
    | () |==-------
     \_/
    a rusty key
""".strip("\n"),
        "text": "Under the stone: a rusty key, just small enough for the door lock.",
        "choices": [
            {
                "label": "Try the heavy door",
                "target": "corridor",
                "requires_items": ["rusty_key"],
            },
            {
                "label": "Go back",
                "target": "torch_room",
            },
        ],
    },
    "corridor": {
        "art": r"""
*   .   .   .   .   *
|===================|
|                   |
|===================|
*   .   .   .   .   *
   a long corridor
""".strip("\n"),
        "text": (
            "The door creaks open onto a torch-lit corridor. Stairs lead "
            "down into darkness and up toward cold night air."
        ),
        "choices": [
            {
                "label": "Study the sleeping guard's patrol by torchlight",
                "target": "corridor",
                "sets_flags": {"studied_guard": True},
            },
            {
                "label": "Head down toward the vault",
                "target": "vault_entrance",
            },
            {
                "label": "Head up toward the exit",
                "target": "escape_plain",
            },
        ],
    },
    "vault_entrance": {
        "art": r"""
   zzz
   (o_o)   +======+
    /|\    | VAULT |
    / \    +======+
  sleeping guard
""".strip("\n"),
        "text": (
            "A guard dozes before a heavy vault door, torch flickering "
            "against the walls."
        ),
        "choices": [
            {
                "label": "Slip past the sleeping guard",
                "target": "vault",
                "requires_flags": {"studied_guard": True},
            },
            {
                "label": "Turn back",
                "target": "corridor",
            },
        ],
    },
    "vault": {
        "art": r"""
   $$$   $$$$   $$
  [======CHEST======]
   $$    $$$   $$$$
      treasure!
""".strip("\n"),
        "text": "An open chest overflows with coin and gems.",
        "choices": [
            {
                "label": "Grab the treasure and run",
                "target": "escape_with_treasure",
                "add_items": ["treasure"],
            },
            {
                "label": "Leave it, just escape",
                "target": "escape_plain",
            },
        ],
    },
    "escape_plain": {
        "art": r"""
        .  *  .
       /|\
      / | \
     /  |  \  <- stairs up
    ----+----
""".strip("\n"),
        "text": "You slip past the last guard and out into the cold night air. Free.",
        "choices": [],
    },
    "escape_with_treasure": {
        "art": r"""
        .  *  .
       /|\   [$]
      / | \  (sack of
     /  |  \  gold)
    ----+----
""".strip("\n"),
        "text": "You slip out into the night, a sack of gold slung over your shoulder. Free, and rich.",
        "choices": [],
    },
    "caught_again": {
        "art": r"""
  =||=  =||=  =||=  =||=
  ||          ||
  ||   YOU    ||
  ||  AGAIN   ||
  ||          ||
  =||=  =||=  =||=  =||=
""".strip("\n"),
        "text": "Guards storm in at the noise. Your cell door is bolted twice over now.",
        "choices": [],
    },
}
