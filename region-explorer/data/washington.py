"""Washington state data: the full-state overview art and each
region's detail art/metadata. See `../SYMBOL_LEGEND.md` for the
shared ASCII vocabulary this draws from.

`engine.py` only ever depends on the `STATE` dict shape (never on
"Washington" specifically), so future states are just new data
modules matching this same shape: `{"name", "art", "regions": [...]}`,
with each region `{"id", "name", "center", "detail_art",
"landmarks"}`. `art` and `detail_art` are both char-grids: a list of
equal-length row strings.

Two deliberately different visual registers, per the design: the
overview is clean/abstract (mostly outline strokes, sparse texture,
one numbered marker per region), while each region's `detail_art` is
denser/chunkier/more organic, since it's meant to read as a close-up.
"""

def _pad_grid(art):
    """Right-pad every row to the block's own max row length.

    Hand-typed rows with escaped characters (e.g. `\\` for a single
    backslash) are easy to miscount by eye; padding here guarantees
    every row in a block is actually equal-length, which `engine.py`'s
    crop/scale functions require, rather than trusting manual spacing.
    """
    width = max(len(row) for row in art)
    return [row.ljust(width) for row in art]


_OVERVIEW = _pad_grid([
    "~/-\\           ^^           .,.,.,.,",
    "~   \\          ^^*          ,.,.,.,.",
    "~ ^1 |         ^^           .,.,.o.,",
    "~  ^ |         ^3           ,.,.,.,.",
    "~   /          ^^           .,.,.,.,",
    "~\\-/      =    ^^           ,.,.6.,.",
    "~         =    ^^           .,.,.,.,",
    "~         =    ^^           ,.,.,.,.",
    "~         2    ^^* ,..,..,. .,.,.,.,",
    "~         =    ^^  ..,..,.. ,.,.,.,.",
    "~         =    ^^* .,..,.., .,.,.,.,",
    "~         =    ^4  ,..5..,. .,.,.,.,",
    "~              ^^  ..,..,.. .,.,.,.,",
    "~              ^^  .,..,.., ,.,.,.,.",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
])

_OLYMPIC_DETAIL = _pad_grid([
    "        ^^^Olympus^^^          ",
    "       ^^^^^*^^^^^^^           ",
    "      ^^^###########^          ",
    "     ^^###|||||||###^^         ",
    "    ^^####|||||||####^         ",
    "   ~~/####|||HOH|####\\~~       ",
    "  ~~/#####|||||||#####\\~~      ",
    " ~~/#RAINFOREST#####\\~~~~      ",
    "~~/###################\\~~~     ",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~     ",
    "  ~  ~  PACIFIC COAST  ~  ~     ",
])

_PUGET_DETAIL = _pad_grid([
    "  o          o                  ",
    " /o\\ SEATTLE /o\\ EVERETT        ",
    "=====                =====      ",
    "==/=\\================/=\\==      ",
    "=|===|====SOUND=====|===|=      ",
    "==\\=/==================\\=/=     ",
    "====   /\\  ISLANDS  /\\    =     ",
    "=======\\/===========\\/====      ",
    "==/o\\================           ",
    "=|TAC|===============           ",
    "==\\o/================           ",
])

_NORTH_CASCADES_DETAIL = _pad_grid([
    "        ****                    ",
    "       ^^^^^^  BAKER            ",
    "      ^^####^^                  ",
    "     ^^######^^                 ",
    "    ^^^^##^^^^^^^               ",
    "   ^^^^^^^^^^^^^^^^             ",
    "  ^^|||^^^^^|||^^^^^            ",
    " ^^|||||^^|||||||^^^            ",
    "^^|||||||^|||||||||^^           ",
    "#|||||||||||||||||||#           ",
])

_SOUTH_CASCADES_DETAIL = _pad_grid([
    "      ****                      ",
    "    ^^^^^^^^  RAINIER           ",
    "   ^^^^^^^^^^^                  ",
    "  ^^^^^^^^^^^^^                 ",
    " ^^############^                ",
    "^^##############^               ",
    "#################               ",
    "                 ______         ",
    "        *       /      \\        ",
    "     ^^^^^==== ST HELENS        ",
    "    ^^^####^====                ",
    "   ^^#######^====               ",
    "  #############====             ",
])

_COLUMBIA_BASIN_DETAIL = _pad_grid([
    "::::::::::,,,,,,,,,,,,,,,,,     ",
    "::YAKIMA::,,,,,,,,,,,,,,,,,     ",
    "::VALLEY::,,,PALOUSE,,,,,,,     ",
    "::::::::::,,,,,,,,,,,,,,,,,     ",
    ".........,,,,,,,,,,,,,,,,,,     ",
    "..SCABLAND.,,,,,,,,,,,,,,,,     ",
    "...........,,,,,,,,,,,,,,,,     ",
    "~~~~~~.......~~~~~~~~~~~~~~     ",
    "  COLUMBIA RIVER                ",
])

_INLAND_NW_DETAIL = _pad_grid([
    ",,,,,,,,,,,,,^^^^^^^^           ",
    ",,,,,,,,,,,^^^^^^^^^^^          ",
    ",,,,,,,,,^^^^^^^^^^^^^^         ",
    ",,,,,,,,^^^^^^^^^^^^^^^^        ",
    ",,ROLLING,,,,^^^^^^^^^^^^       ",
    ",,,HILLS,,,,,,^^IDAHO^^^^       ",
    ",,,,,,,,,,,,,,,^^^^^^^^^^       ",
    "  /o\\                           ",
    " |SPO|  SPOKANE                 ",
    "  \\o/                           ",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,       ",
])

STATE = {
    "name": "Washington",
    "art": _OVERVIEW,
    "regions": [
        {
            "id": "olympic",
            "name": "Olympic Peninsula",
            "center": (2, 3),
            "detail_art": _OLYMPIC_DETAIL,
            "landmarks": [
                "Hoh Rain Forest",
                "Mount Olympus",
                "Pacific coastline",
            ],
        },
        {
            "id": "puget_sound",
            "name": "Puget Sound",
            "center": (8, 10),
            "detail_art": _PUGET_DETAIL,
            "landmarks": ["Seattle", "Tacoma", "Everett", "the Sound's islands"],
        },
        {
            "id": "north_cascades",
            "name": "North Cascades",
            "center": (3, 16),
            "detail_art": _NORTH_CASCADES_DETAIL,
            "landmarks": ["Mount Baker", "North Cascades peaks"],
        },
        {
            "id": "south_cascades",
            "name": "South Cascades",
            "center": (11, 16),
            "detail_art": _SOUTH_CASCADES_DETAIL,
            "landmarks": ["Mount Rainier", "Mount St. Helens"],
        },
        {
            "id": "columbia_basin",
            "name": "Columbia Basin",
            "center": (11, 22),
            "detail_art": _COLUMBIA_BASIN_DETAIL,
            "landmarks": [
                "Yakima Valley orchards",
                "Palouse wheat hills",
                "the Channeled Scablands",
                "the Columbia River",
            ],
        },
        {
            "id": "inland_northwest",
            "name": "Inland Northwest",
            "center": (5, 32),
            "detail_art": _INLAND_NW_DETAIL,
            "landmarks": ["Spokane", "rolling hills toward the Idaho border"],
        },
    ],
}
