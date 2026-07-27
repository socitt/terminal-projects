# ASCII symbol legend

Shared, state-agnostic vocabulary for region-explorer's ASCII art. Any
state's data file (`data/<state>.py`) should draw from this same set of
meanings, so the visual language stays consistent as more states are
added later — this list lives with the engine, not with Washington's
data specifically. All symbols are plain ASCII (no box-drawing unicode),
matching the rest of this repo's art (see `adventure-engine`'s scene
art for precedent).

Original vocabulary — not modeled on any specific existing game's tile
set.

## In use (drafted so far)

| Symbol      | Meaning                                              |
|-------------|-------------------------------------------------------|
| `^`         | Mountain peak / range (density = ruggedness)          |
| `#`         | Dense terrain fill inside a landform outline (forested slope, high ground) |
| `\| `(dense rows `\|\|\|\|`) | Forest / dense tree cover                |
| `~`         | Moving water — coastline, river                      |
| `=`         | Still water — lake surface, sheltered sound/bay       |
| `,.,.,.`    | Rolling hills / grass-and-farmland texture            |
| `.` (sparse)| High desert / scrub / scabland texture                |
| `/ \ -`     | Landform outline strokes (coastline, peaks, slopes)   |
| `1`-`6`     | Region selection markers (functional overlay, not terrain) |

## Proposed additions (needed for the remaining regions)

| Symbol      | Meaning                                              | Where it'll get used |
|-------------|-------------------------------------------------------|------------------------|
| `*` (atop `^`) | Snow/glacier cap on a peak — distinguishes glaciated volcanic cones (Rainier, Baker, St. Helens) from ordinary jagged `^^^` ridgeline | North/South Cascades detail art |
| `o` (small cluster) | Distant settlement — a town/city seen from a distance, paired with a text label rather than trying to draw buildings | Puget Sound (Seattle/Tacoma), Inland Northwest (Spokane) |
| small `/ \` islands surrounded by `~` | Islands | Puget Sound detail art |
| `%`         | Wetland / marsh texture, reserved in case a region needs it | not needed yet — holding the symbol so it doesn't get reused for something else later |

## Added during detail-art drafting (all 6 regions)

| Symbol      | Meaning                                              | Where it's used |
|-------------|-------------------------------------------------------|------------------|
| `*` (atop a peak) | Snow/glacier cap. Confirmed as planned above — used on Mt. Baker (North Cascades) and, distinctly, on both Mt. Rainier's symmetric cone and Mt. St. Helens' flat blown-top crater (South Cascades), so the same symbol reads correctly on two differently-shaped silhouettes | North Cascades, South Cascades |
| `:`         | Irrigated cropland / orchard rows — a wetter, human-cultivated variant of `,` (dry-farmed rolling hills); distinguishes Yakima Valley's orchards from the Palouse's dry wheat hills | Columbia Basin |

Extend this table in place as new symbols get introduced — don't
invent one-off meanings inline in a region's `detail_art` without
adding it here first, so the vocabulary doesn't drift per-region.
