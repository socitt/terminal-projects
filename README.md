# terminal-projects

A monorepo of small terminal-only tools and games, built and run entirely
on-device in [iSH-AOK](https://ish.app/) (native aarch64 Alpine Linux
running on an iPhone). No desktop, no mouse — narrow vertical terminal,
iOS on-screen keyboard only.

## Constraints this repo is designed around

- **Terminal-only.** Every tool/game is a plain terminal program. No
  GUI, no web server, no external display.
- **Narrow screen.** Output should target roughly 30-40 columns wide.
- **Python** for game/tool logic.
- **On-device build tooling.** Everything here needs to actually run
  under iSH-AOK's aarch64 emulation, which rules out anything requiring
  a JVM (see below).
- **Minimal dependencies.** New external libraries are added only when
  asked for, not by default.

## Build system: Please, not Bazel

This repo uses [Please](https://please.build) (the `plz` binary) as its
build system, structured the way you'd structure a Bazel repo: BUILD
files declaring targets, explicit dependencies between them, visibility
rules, and a queryable target graph.

The reason it's Please and not actual Bazel: Bazel's client is a small
launcher that hands off to a JVM-based server, and that JVM crashes
under iSH-AOK's aarch64 emulation — a gap in the emulation layer itself,
not something fixable from userspace here. Please implements the same
core ideas (BUILD files, hermetic-ish builds, explicit deps, visibility,
a target graph you can query) but ships as a single static Go binary
with no JVM dependency, so it actually runs in this environment.

Practically, this means: if you know Bazel, the mental model transfers
directly — `BUILD` files, `plz build //path/to:target`,
`plz test //path/to:target`, `plz query`, etc. Where Please's syntax or
behavior diverges from Bazel in a way that matters, it'll be called out
inline in that part of the repo.

## Layout

- `shared/` — common terminal rendering and single-keypress input
  helpers used across tools.
- `weather-narrative/` — turns weather data into narrative text.
- `board-games/` — terminal board games (tictactoe, connect4,
  backgammon, go, chess).
- `adventure-engine/` — text adventure engine, with individual stories
  under `adventure-engine/stories/` (dungeon, train-mystery).
- `world-events-tracker/` — world events tracking tool.
- `docs/ACTIVE_SESSION.md` — running session log, used to resume work
  after a crash. If you're picking up an interrupted session, read this
  first.

Each tool/game directory has its own README with specifics.
