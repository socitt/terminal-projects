# User testing log

Manual playtesting notes from the person using this repo on-device,
organized by project. Each entry is dated. Treat these as a TODO
backlog, not bug reports against a spec -- most items here are feature
requests or polish, called out as such.

## 2026-07-27: first full playtest pass

Covered every playable target: all five `board-games/` entries and
both `adventure-engine` story packs. `region-explorer` (no code yet)
and `clanhold` (not started; renamed `furminal` on 2026-07-30) were
skipped as not testable.

### Cross-cutting request: a computer opponent ("Nemo")

Came up independently on every board game. Consolidating into one
request rather than repeating it five times:

- All five board games are currently two-player-same-screen only. Add
  a single-player mode against a computer opponent, selectable at
  game start.
- Three difficulty levels:
  - Easy: random legal move.
  - Medium: better than random (e.g. blocks immediate losses / takes
    immediate wins) but not fully optimal.
  - Hard: picks the best move it can (minimax/similar, scoped per
    game).
- Naming/theme idea: call the computer opponent "Nemo". Stretch idea:
  a small ASCII "Nemo cam" panel showing a creature whose expression
  reacts to whether it thinks it's winning or losing. Fun-factor
  feature, not core -- do the plain difficulty-level opponent first,
  treat the reactive avatar as a follow-on.
- Once a "Nemo" opponent exists, it needs its own playtesting pass
  across all five games before this is considered done.

### `board-games/tictactoe`

- UI is clean, simple, works well as-is. No bugs found.
- Missing: single-player vs. computer (see cross-cutting request
  above).
- Missing: no rematch prompt after a win -- game just ends. Should
  offer to play again.

### `board-games/connect4`

- UI looks good.
- Bug: entering a column number outside the valid range (e.g. `34`
  when the board is 7 wide) doesn't get rejected -- it appears to
  parse just the first digit (`3`) and plays that column instead of
  reprompting. Should validate input and reprompt on out-of-range
  input.
- Missing: no rematch prompt after a win -- game just ends, same as
  tictactoe.
- Missing: single-player vs. computer (see cross-cutting request).

### `board-games/backgammon`

- UI looks good.
- Requested: a direction indicator (arrow at top and bottom) showing
  which way each color's pieces move -- turn direction isn't obvious
  at a glance right now.
- Requested: auto-play/animation for bear-off once one side's pieces
  are all past the other's -- roll dice and slowly animate the moves
  to the end automatically, rather than requiring manual play through
  a foregone conclusion.
- Missing: single-player vs. computer (see cross-cutting request).

### `board-games/go`

- UI looks good.
- Requested: selectable board size and handicap at game start.
- Requested: selectable counting method (affects scoring/gameplay
  meaningfully, should be a choice, not fixed).
- Missing: single-player vs. computer (see cross-cutting request).
- Testing note: full/endgame playtesting is impractical two-player
  same-screen because games run long -- deferring thorough gameplay
  (especially endgame/counting) testing until a computer opponent
  exists to play against solo.

### `board-games/chess`

- Bug fixed and verified working: checkmate detection works, en
  passant works (tested and confirmed both).
- UI issue: spacing between column/row coordinate labels and the
  board is awkward/hard to read at the narrow terminal width this
  repo targets. Worth a redesign pass within the same width
  constraint.
- Requested: algebraic move input (e.g. `e2e4`) instead of specifying
  row and column separately.
- Nice-to-have, likely out of scope given ASCII/width constraints:
  a checkerboard-pattern board (alternating light/dark squares).
  Noted as probably not feasible here, not a firm ask.
- Missing: single-player vs. computer (see cross-cutting request).

### `adventure-engine/stories/dungeon`

- The first death ending landed well ("funny").
- Missing: no prompt to play again / end session cleanly after
  reaching an ending.
- Diagnosed, not a bug: in the long corridor, choosing "study the
  sleeping guard" appears to do nothing. Root cause is that it's a
  self-looping choice (`corridor` -> `corridor` in `story.py`) that
  sets a flag silently and re-renders the same scene text -- so
  there's no visible feedback that anything happened. UX gap: silent
  self-loop choices need some on-screen acknowledgment (e.g. a short
  inserted line confirming the action) so the player can tell the
  flag was set.
- Follow-up project: flesh out the story/decision tree further --
  e.g. an alternate path examining a crack in the wall that opens into
  a small puzzle dungeon, alongside the existing escape option.
  Wants to storyboard this collaboratively (back-and-forth to build
  out the scene/decision tree) before writing more `story.py` content.

### `adventure-engine/stories/train-mystery`

- Same root cause as dungeon's "study the guard": "Examine the wine
  glass" / "Examine the muddy footprints" are self-looping choices
  that set a flag and silently return to the same scene -- looked
  like nothing happened. Same UX gap as above (self-loop choices need
  visible acknowledgment), plus each is a one-shot: once the flag is
  set the choice disappears, so the player has no way to tell
  afterward that it registered, and has to remember what they found.
- Requested feature: an "interview the suspects" mechanic parallel to
  examining physical clues -- talk to each suspect and learn distinct
  details, similar to the examine-clue mechanic. Same one-shot-per-suspect
  concern applies (player must remember answers between the interview
  and the final accusation).
- Also wants a collaborative storyboarding pass on this story pack
  before further content work, same as dungeon.

## Open follow-up

- Storyboarding sessions for `dungeon` and `train-mystery` extended
  story/decision trees -- not started, to be done as back-and-forth
  design conversations before new `story.py` content is written.
- "Nemo" computer opponent (all difficulty levels, all five board
  games) -- not started.
- "Nemo cam" reactive ASCII avatar -- stretch, after the plain
  computer opponent exists.
