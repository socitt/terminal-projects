# Active Session Log

This file is the resume point if the session crashes. Keep it current:
update it (and commit+push) before and after every step, not just at the
end. If you're picking this up cold, read "Just finished" and "Next up"
below and continue from there.

## Environment

- iSH-AOK (native aarch64 Alpine 3.23.3), running on an iPhone.
- Narrow vertical terminal, iOS on-screen keyboard only.
- Build system: [Please](https://please.build) (`plz`, v17.31.2 confirmed
  installed and working) — NOT Bazel. Real Bazel needs a JVM, which
  crashes under iSH-AOK's aarch64 emulation. Please is a single Go
  binary, no JVM, and deliberately modeled on Bazel's concepts (BUILD
  files, hermetic builds, explicit deps, visibility, target graph), so
  it's being used both as the working build tool and as a way to learn
  Bazel's mental model.
- Game/tool logic: Python. Terminal output should target ~30-40 cols
  wide (narrow phone screen).
- Ask before adding any external library or dependency.

## Working rules (why this file exists)

- Smallest possible increments: one file or one logical change, then
  commit. Never batch multiple uncommitted files into one session.
- Commit after every checkpoint. Push after every commit — no batching.
- No interactive editors (vi/nano) — commit messages always inline via
  `-m`. Merges/rebases handled non-interactively.
- Every new target/module needs a minimal test before being considered
  done; run it and confirm it passes before committing.
- Route `plz build`/`plz test` invocations through
  `scripts/plz-retry.sh <args...>` rather than calling `./pleasew`/`plz`
  directly — it retries flaky `signal: hangup` failures (fresh subshell
  per attempt). See `docs/KNOWN_ISSUES.md` for why this is necessary.
- This log gets updated before and after every step.

## Status: STARTING FRESH

A prior scaffolding attempt crashed before anything was committed.
Confirmed via `git log`, `git status`, `ls -la` that there was nothing
to resume — repo only contained `LICENSE` and `.claude/`. Treating this
as a clean start.

## Just finished

- Verified repo state (clean, only `LICENSE` + `.claude/` present).
- Verified `plz --version` works (17.31.2).
- Created `docs/ACTIVE_SESSION.md` (this file), committed + pushed
  (`21bc9ad`).
- Created root `README.md` (purpose, constraints, Please-vs-Bazel
  rationale), committed + pushed (`ba91354`).
- Ran `plz init`, pinned Please to version 17.31.2 in `.plzconfig`
  (reproducibility, like a Bazel `.bazelversion`), added the `pleasew`
  wrapper script, added `.gitignore` for `plz-out`, and added a minimal
  root `BUILD` file (no targets yet — each subpackage will define its
  own). Verified with `plz build //...` (succeeds, no targets).
  Committed + pushed (`e9f65af`).
- Tried two experiments to narrow the SIGHUP root cause per the
  Go-runtime-threading-vs-iSH-process-emulation theory: `GOMAXPROCS=1`
  and `numthreads = 1` in `.plzconfig`, 10 fresh-shell attempts each.
  Neither improved on baseline (0/10 each); neither was kept. Full
  detail, plus a process-leak hazard discovered mid-experiment and a
  new finding narrowing the hangup to Please's post-test results-file
  step specifically, in `docs/KNOWN_ISSUES.md`.
- Added `scripts/plz-retry.sh`: wraps any `plz`/`pleasew` invocation,
  retries up to 5 times (fresh subshell per attempt), only reports
  failure once exhausted. This is now the standing mitigation for the
  SIGHUP issue — see updated working rules above.

## In progress

- `shared/term.py` (rendering helpers: `clear_screen`, `pad_line`,
  `center_line`, `hr`), `shared/term_test.py`, and `shared/BUILD`
  (`python_library` + `python_test` targets) are written on disk.
  Committing these now as a deliberate, logged exception to the
  "test must pass first" rule — see `docs/KNOWN_ISSUES.md` for why,
  and for full details on the blocker below.

## BLOCKER: `plz` subprocess execution fails with `signal: hangup`

Full details, including everything tried and ruled out this session
(2026-07-26), now live in `docs/KNOWN_ISSUES.md` — read that first if
resuming this. Summary:

- It's a general Please build-action problem (reproduced with a bare
  `genrule`), not specific to Python or wheel fetching.
- It's flaky, not a hard wall — retrying the same command (fresh shell
  each time) succeeds a meaningful fraction of the time.
- The previously-recorded "pty wrapper fixes it" workaround was
  **wrong** — that was a cache hit, not a fix. Verified this session by
  forcing rebuilds (`--rebuild`) of a target already believed fixed by
  the pty wrapper (`//shared:_term#zip`) and watching it fail with the
  same `signal: hangup` under the same wrapper.
- Built `//tools/plz_test_runner` (a stdlib-only, dependency-free
  custom `python_test` runner, wired via `TestRunner`/`TestrunnerDeps`
  in the root `.plzconfig`) specifically to rule out "it's the
  xmlrunner/portalocker wheel fetch" as the cause. It wasn't — the
  plain zip step for this new dependency-free target hit the identical
  `signal: hangup`. Keeping this runner anyway since it's a reasonable
  simplification independent of this bug, but it does not unblock
  testing.

## Open question to resolve before/at next step

- How to get `//shared:term_test` (or any `python_test`) to actually
  return a passing exit code reliably under iSH-AOK. Root cause still
  not fixed (GOMAXPROCS/numthreads experiments ruled out, see
  `docs/KNOWN_ISSUES.md`), and root-causing this further is no longer
  the plan — `scripts/plz-retry.sh` is now the standing mitigation.
  Code correctness is no longer in question: multiple captured runs
  show the actual `unittest` suite completing with all 5 tests passing
  before Please's own results-file step hangs. A genuinely passing
  `plz test` exit code has not yet been captured this session despite
  ~45 attempts; keep retrying via `scripts/plz-retry.sh` when next
  picking this up, but don't block further work on it.
- Please's Python rules (`python_library`, `python_test`, etc.) — the
  plugin itself is already added (`aeba897`), so this question from
  before is resolved.

## Priority change from user (2026-07-26)

Build order for the actual projects, once `shared/` is unblocked:
1. **`board-games`** — do this one first.
2. `adventure-engine` and `world-events-tracker` — normal priority,
   order TBD.
3. **`weather-narrative`** and **`world-events-tracker`** — wait, see
   below — moved to LAST, treated as bonus/stretch projects, not core.

Corrected list, in order:
1. `shared/` (in progress, blocked — see above)
2. `board-games` (tictactoe, connect4, backgammon, go, chess)
3. `adventure-engine` (`stories/`: dungeon, train-mystery)
4. `weather-narrative` — bonus, do last
5. `world-events-tracker` — bonus, do last

## Next up (in order)

1. Start on `board-games` (stub folder + README + minimal BUILD + stub
   entrypoint), per the reordered priority above and per explicit
   user instruction (2026-07-26) to move on from the SIGHUP
   investigation regardless of outcome. Use `scripts/plz-retry.sh` for
   any `plz build`/`plz test` calls.
2. `shared/input.py` (single-keypress input helper) — same
   stub → test → commit pattern, whenever picked up. Same SIGHUP
   caveat likely applies; use `scripts/plz-retry.sh` and don't
   silently skip the test — log it same as `shared/term_test.py` if a
   clean pass isn't captured.
3. `//shared:term_test` still hasn't returned a passing `plz test` exit
   code this session (see `docs/KNOWN_ISSUES.md`) — worth another
   `scripts/plz-retry.sh test //shared:term_test` next time it's
   convenient, but not a blocker for the above.

## In progress (2026-07-26, later same day)

Device setting change: HLE Accel (arm64/riscv64) toggled ON, amd64 JIT
toggled OFF (irrelevant — we run native aarch64). Running a fresh
10-attempt `scripts/plz-retry.sh test //shared:term_test` batch to see
if HLE Accel affects the `signal: hangup` rate, per
`docs/KNOWN_ISSUES.md`. Confirmed no stray `plz`/`please` processes
before starting (`ps aux | grep -i please`, clean).

Note: the requested `--rebuild` flag doesn't exist for `plz test`
(confirmed via `./pleasew test --help`); using `--rerun` instead, which
is what prior batches in `docs/KNOWN_ISSUES.md` actually used for test
targets (`--rebuild` is a `plz build`-only flag).

**Result: HLE Accel does not fix it.** 0/10 batch (50 total underlying
invocations via `scripts/plz-retry.sh`'s internal retries), identical
`signal: hangup` / missing-results-file signature as before. Full
writeup in `docs/KNOWN_ISSUES.md`. Checked for any accessible
syscall/signal log to strengthen the draft issue — `/proc/ish/*` and
`dmesg` have nothing at that granularity, no `strace`/`ltrace`
installed, and the iSH-AOK app's own Diagnostics screen (if it has
anything useful) is a GUI feature this CLI session can't reach.
Committed and pushed (`abe3f54`, `73befdb`, `f948a25`).

With user confirmation, installed `strace` (`apk add strace`) and
tried to capture a live hangup via `strace -f`. Ruled out as
impractical: two attempts both failed to return in reasonable time
(one hit the tool's 5-minute ceiling, the other still hadn't returned
under a `timeout 60` wrapper), and the partial trace showed severe
overhead plus abnormal CPU-time accounting rather than a clean capture
of the hangup moment. No stray processes left behind either time.
Logged as circumstantial supporting evidence for the draft issue.
Committed and pushed (`2dab368`).

## Pending: draft upstream issue awaiting review

`docs/DRAFT_ISH_AOK_ISSUE.md` is a drafted GitHub issue for
`github.com/emkey1/ish-AOK`, based on the SIGHUP findings in
`docs/KNOWN_ISSUES.md` — environment details, a minimal `genrule`
repro, everything confirmed/ruled out, and the post-exit
results-file-step finding with terminal output. **This is a draft
only** — it has not been filed anywhere (no `gh`/GitHub API used) and
is pending the user's review before submission. Don't file it without
being explicitly asked to.

## In progress (2026-07-27): dogfooding `lirk` against `shared/term_test.py`

`lirk` (separate repo, cloned at `../lirk`, v1 complete: target
declarations, dependency graph, content-hash incremental builds, CLI
`build`/`test`, 42 passing tests) was built specifically to avoid the
Please SIGHUP saga above by using the simplest possible subprocess
model. This session dogfoods it against the exact target that never
returned a clean `plz test` exit code: `shared/term.py` /
`shared/term_test.py`.

Not touching the existing Please setup (`.plzconfig`, `shared/BUILD`,
`docs/KNOWN_ISSUES.md` stays as historical record) — adding
`shared/BUILD.lirk` alongside it. Invoking via `../lirk/bin/lirk`
(relative path) from the repo root.

- `../lirk/bin/lirk build //shared:term` — OK, first try.
- `../lirk/bin/lirk test //shared:term_test` — **fails, deterministically,
  every time.** 10/10 fresh-shell attempts, all identical:
  `ModuleNotFoundError: No module named 'shared'`.

Root cause (confirmed by reading `lirk/actions.py`): `run_test`
invokes `python3 -m unittest <module>` with `cwd=<package dir>` and no
`PYTHONPATH` adjustment, so the only things importable are modules
flat inside that package directory (`lirk`'s own test fixtures
confirm this is the intended model — `tests/fixtures/sample_repo/a/test_a.py`
does `from a import greet`, not a root-relative import). But
`shared/term_test.py` does `from shared import term` — a
root-relative import, matching the convention Please's `python_test`
rules use. This is not the SIGHUP-style flakiness (0/10 pass, but with
a single consistent deterministic cause, not a race) — it's an
import-model mismatch between what `lirk` v1 supports and how this
repo's existing test files are written. See `docs/KNOWN_ISSUES.md` for
the full writeup. Not fixing it here per plan — this is a `lirk` bug/gap
to take back to the `lirk` repo separately, not something to
work around or debug from this side.

Added `.lirk-cache.json`, `__pycache__/`, `*.pyc` to `.gitignore`
(lirk's own build-cache file and Python bytecode caches, generated by
running it — same reasoning as the existing `plz-out` entry above).

## Resolved (2026-07-27, later same day): `lirk` bug fixed upstream, `shared/term_test.py` genuinely green

The import-model bug found above was fixed in the `lirk` repo
(`428c517`, "Fix lirk test failing on root-relative imports" —
`run_test` now injects `PYTHONPATH=<repo root>` before invoking
`python3 -m unittest`) and reported fixed there (20/20 across two
independent batches, plus lirk's own suite still green). `FINDINGS.md`
(the handoff file dropped in `../lirk` last session) has been deleted
over there now that it's triaged.

Re-confirmed independently from this side, not just taking the other
session's word for it: `git -C ../lirk pull` (already up to date,
landed at `428c517`), then `lirk test //shared:term_test` 10 more
times, fresh shell per attempt, `.lirk-cache.json` deleted before each
run to force real re-execution. **10/10 passed.** Combined with the
`lirk` repo's own 20/20, that's 30/30 clean passes since the fix.

`docs/KNOWN_ISSUES.md` updated in place (both the `shared/term_test.py`
section and the `lirk` dogfooding section got append-only updates
noting the fix and the pass-rate comparison vs. Please's 0 clean exit
codes across ~45+ attempts) — none of the original history was deleted
or rewritten. `shared/term.py` and `shared/term_test.py` are unchanged
throughout this whole saga; only the tooling running them changed.

**`shared/` via `lirk` is the reference pattern going forward**: stub →
`BUILD.lirk` → `lirk test` confirmed via multiple fresh-shell runs →
commit.

**Correction:** the plan above assumed `shared/input.py` was already
written and just unconfirmed, same as `term.py` had been. Checked
before acting on that — it wasn't; only planned in a "Next up" note,
never actually created. Wrote it from scratch instead (see below)
rather than silently treating a plan as done code.

## Done (2026-07-27): `shared/input.py` — single-key input helper

New module, following the `term.py`/`lirk` pattern directly (no Please
BUILD entry — `shared/` is standardizing on `lirk` per the note
above): `normalize_key` (pure), `get_key`/`prompt_choice` (thin
wrappers around `input()`, tested via mocking `builtins.input`). Design
follows the original project constraint noted in this file's
Environment section — iOS on-screen keyboard only, so no raw
single-char reads or arrow/modifier-key chords; "single-key" here
means "type one character, hit Enter."

`shared/BUILD.lirk` extended with `input`/`input_test` targets.
`lirk test //shared:input_test`: **10/10** fresh-shell runs,
`.lirk-cache.json` cleared each time, all 8 tests passing every run.
Committed and pushed (`e714c45`).

`shared/` is now fully green under `lirk`: `term_test` and
`input_test` both confirmed reliably passing. Moving to `board-games`
next, starting with `tictactoe`, same pattern.

Also fixed `shared/README.md` (`e370290`): its `input.py` description
predated the actual implementation and claimed raw single-keypress
reads with no Enter, which isn't reliable via the iOS on-screen
keyboard and isn't what got built. Also updated to point at
`BUILD.lirk` as where `term`/`input` are now built and tested.

## Done (2026-07-27): `board-games/tictactoe` — first board-games target

`board-games/` didn't exist yet; created it plus `tictactoe/` as the
first game, per the reordered priority list below. Layout mirrors
`shared/`: pure logic + tests, thin I/O entrypoint.

- `board.py` — pure functions (`new_board`, `apply_move`, `winner`,
  `is_draw`), no I/O.
- `board_test.py` — 16 tests (row/column/diagonal wins, draws, invalid
  moves, no-mutation).
- `main.py` — terminal entrypoint, imports `shared.term` /
  `shared.input` (repo root added to `sys.path` at the top, since the
  script isn't run through `lirk`'s `PYTHONPATH` injection — that only
  applies to `lirk test` invocations). Manually verified end-to-end
  with a piped-input playthrough to a win (`X` on the diagonal),
  output rendered correctly.
- `BUILD.lirk` — `board` (library), `board_test` (test, deps `:board`),
  `main` (library, deps `:board`, `//shared:term`, `//shared:input` —
  first cross-package dependency this repo has exercised in `lirk`).

`lirk build //...`: all 7 targets across `shared/` and
`board-games/tictactoe/` build clean — confirms cross-package label
resolution works, not just single-package targets.
`lirk test //board-games/tictactoe:board_test`: **10/10** fresh-shell,
cache-cleared runs. Committed and pushed (`9e2bc95`).

## Done (2026-07-27): `board-games/connect4`

Same pattern as `tictactoe`: `board.py` (pure logic on a 6-row x
7-column grid — `new_board`, `valid_moves`, `apply_move` with gravity,
`winner` checking all 4 directions, `is_draw`), `board_test.py` (19
tests), `main.py` (entrypoint, manually verified end-to-end with a
piped-input playthrough to a horizontal win), `BUILD.lirk` (same
`board`/`board_test`/`main` shape, `main` depending on `//shared:term`
and `//shared:input`).

Caught a bug in my own `is_draw`-with-a-winner test during
development, not a `board.py` bug: filling the board with all `"O"`
before adding the `"X"` win line created spurious full-row `"O"` runs
that `winner()`'s row-major scan finds first, so the test asserted the
wrong mark. Fixed by not asserting *which* mark wins in that specific
test (already covered by the dedicated `WinnerTest` cases) — only that
`is_draw` is `False`. First 10-run batch: 0/10, all failing on that
one assertion; after the fix, re-ran clean.

`lirk build //...`: all 10 targets across `shared/`, `tictactoe/`, and
`connect4/` build clean. `lirk test //board-games/connect4:board_test`:
**10/10** fresh-shell, cache-cleared runs (after the test fix above).
Committed and pushed (`3cec08c`).

## Priority list status (2026-07-27)

Per the reordered list further down this file:

1. `shared/` — **done**, both `term`/`input` green under `lirk`.
2. `board-games` — **in progress**: `tictactoe`, `connect4` done;
   `backgammon`, `go`, `chess` still to come, same pattern.
3. `adventure-engine` — not started.
4. `weather-narrative`, `world-events-tracker` — bonus, still last.

## Next up

- `board-games/backgammon` (or whichever board-games entry is picked
  up next), same pattern: pure logic module + test, thin `main.py`
  entrypoint, `BUILD.lirk`, `lirk test` confirmed via multiple
  fresh-shell runs, commit.

## In progress (2026-07-27, new session): `board-games/backgammon`

Fresh session start: confirmed via `git log`/`git status` that the repo
is exactly where the prior session left it (nothing to resume), pulled
`../lirk` (already up to date at `428c517`, no new commits — the
separate "honest usage assessment" work in that repo, per
`../lirk/docs/LIRK_ASSESSMENT.md`, is being deferred per user decision
in favor of continuing to dogfood lirk against real targets here).

Starting `backgammon`, same `board.py` → `board_test.py` → `main.py` →
`BUILD.lirk` pattern as `tictactoe`/`connect4`. Explicit scope decision
this session: implementing full core rules (movement, hits, bar entry,
bearing off with the exact-or-overshoot rule, doubles-as-4-moves) but
**not** the doubling cube — that's a separate state machine (offer/
accept/decline, cube ownership, cube value) that adds significant
complexity for a local two-player terminal game and isn't needed for
the core ruleset to be correct and playable. Noting this explicitly
per the "whatever the actual ruleset needs" instruction rather than
silently dropping it.

Also, per explicit instruction this session, committing each file
separately (`board.py`, `board_test.py`, `BUILD.lirk`, `main.py`) as
its own commit+push, rather than one bundled commit per target the way
`tictactoe` (`9e2bc95`) and `connect4` (`3cec08c`) were actually done.

## Done (2026-07-27): `board-games/backgammon`

State representation: `{"points": [0]*25, "bar": {"X","O"}, "off":
{"X","O"}}`, points 1-24 (index 0 unused), positive = X count,
negative = O count. X moves 24→1 (home 1-6), O moves 1→24 (home
19-24), matching the standard mirrored starting layout.

- `board.py` — pure functions: `new_game`, movement (`can_move`/
  `move_checker`), hits (lone opposing checker sent to bar),
  mandatory bar re-entry (`can_enter_from_bar`/`enter_from_bar`, must
  clear the bar before any other move), bearing off
  (`can_bear_off`/`bear_off`, exact-die-or-overshoot-if-no-farther-
  checker rule, mirrored correctly for both players), `dice_to_moves`
  (doubles → 4 moves), `roll_dice` (takes an injectable rng),
  `legal_actions` (enumerates actions for a die — used by both
  `main.py` and the tests). Committed `d602ddc`.
- `board_test.py` — 60 tests, run directly via `python3 -m unittest`
  first (60/60 green) before wiring into `lirk`, same discipline as
  connect4's caught-a-test-bug lesson. Deliberately exercised the
  edge cases likely to hide bugs the way connect4's did: a blot
  (single opposing checker, not blocking) vs. a made point (2+,
  blocking) are different in `is_blocked`/`can_move`; a fully closed
  board (opponent holds all 6 entry points with 2+ each) blocks every
  die 1-6 for bar entry; the bear-off overshoot rule needs a checker
  actually farther from home to correctly forbid the shortcut, tested
  in both directions (mirrored for X and O, since their home ranges
  and pip-distance formulas are opposite). Committed `dab5c0f`.
- `main.py` — compact two-row terminal board (points 13-24 top,
  12-1 bottom, so home quadrants align vertically like a physical
  board), bar/off counts, numbered per-die action menu via
  `shared.input.prompt_choice`. Verified end-to-end differently than
  tictactoe/connect4: dice make an exact scripted win-path
  impractical, so piped 3000 lines of "always pick option 1" into a
  real run instead — completed cleanly (exit 0, no tracebacks, full
  game to "O wins!"), confirming rendering + input flow + board logic
  work together across a full real game. Committed `f6bc257`.
- `BUILD.lirk` — same `board`/`board_test`/`main` shape as
  tictactoe/connect4. Sanity-checked (`lirk build` on `:board` and
  `:main`, one `lirk test` pass) before committing. Committed
  `538c96b`.
- `README.md` (backgammon + updated `board-games/README.md`) —
  documents the deliberate no-doubling-cube scope decision. Committed
  `e1aa645`.

**Test rigor:** `lirk test //board-games/backgammon:board_test` —
**10/10** fresh-subshell runs, `.lirk-cache.json` deleted before each
to force genuine re-execution, same methodology as every prior
target. `lirk build //...`: all 13 targets across `shared/`,
`tictactoe/`, `connect4/`, and `backgammon/` build clean — full graph
still resolves correctly with the new cross-package deps
(`//shared:term`, `//shared:input`) added.

## Priority list status (2026-07-27, updated)

1. `shared/` — **done**.
2. `board-games` — **in progress**: `tictactoe`, `connect4`,
   `backgammon` done; `go`, `chess` still to come, same pattern.
3. `adventure-engine` — not started.
4. `weather-narrative`, `world-events-tracker` — bonus, still last.

## Next up

- `board-games/go` (or `chess`), same pattern: pure logic module +
  test, thin `main.py` entrypoint, `BUILD.lirk`, `lirk test`
  confirmed via multiple fresh-shell runs, commit per file per this
  session's instruction.

## In progress (2026-07-27, continued): `board-games/go`

Scope decision, logged before writing code: 9x9 board (standard
beginner/competitive size — 19x19 doesn't fit a ~30-40 col terminal
or a single-key+Enter coordinate-entry scheme reasonably). Full core
ruleset: stone placement, group/liberty tracking, captures, the
suicide rule (illegal to self-capture unless the move captures
opponent stones first — "snapback"-style moves are legal), simple ko
(can't immediately recreate the board position from just before the
opponent's last move). Scoring: area/Chinese-style (stones + fully-
surrounded empty territory) rather than Japanese territory scoring,
since the latter requires a dead-stone-removal negotiation phase
that's a UI/protocol problem more than a rules one — out of scope
here. Komi 5.5 (standard for 9x9, avoids score ties).

Given how bug-prone group/liberty/capture logic is, verifying tricky
fixtures (a snapback-style legal-suicide-that-captures scenario, and
a ko scenario) interactively via `python3` against the real
`board.py` functions before committing them to `board_test.py`,
rather than hand-deriving and hoping the by-hand liberty count is
right.

## Done (2026-07-27): `board-games/go`

- `board.py` — `group_and_liberties` (flood-fill), `apply_move`
  (placement, captures, suicide rule, optional simple-ko check via a
  `previous_board` arg), `is_legal_move` (try/except wrapper reusing
  `apply_move` rather than a second parallel rule implementation),
  `score`/`winner` (area/Chinese scoring, komi). Committed `8138406`.
- `board_test.py` — 31 tests. Verified the snapback (suicide-looking-
  but-legal-via-capture) and ko fixtures interactively against the
  real `board.py` via `python3` first, rather than hand-deriving —
  both matched exactly on the first construction. Caught one real bug
  while writing the territory-scoring test itself (not a `board.py`
  bug): the first version only placed black stones, so the *entire*
  rest of the empty board legitimately counted as black territory
  (correct engine behavior — one giant connected region touching only
  black), not the small isolated pocket the test meant to isolate;
  fixed by adding a distant white stone so the giant remainder reads
  as neutral. Ran directly via `python3 -m unittest` first (31/31
  green after the fix) before wiring into `lirk`. Committed `2a14aeb`.
- `main.py` — coordinates via two single-digit prompts (column, then
  row), `P` to pass, two consecutive passes end the game. Verified
  end-to-end via piped input, two scenarios: an illegal-move-then-
  pass-pass game showing correct scoring (neutral territory, komi
  applied only to white), and a real sequential capture (black fills
  white's corner stone's last liberty across two moves, confirmed
  removed from the rendered board). Both ran clean, exit 0, no
  tracebacks. Committed `650f42c`.
- `BUILD.lirk` — same shape as the other board-games targets.
  Sanity-checked before committing. Committed `442902a`.
- `README.md` (go + updated `board-games/README.md`) — documents the
  9x9/area-scoring/simple-ko scope decisions. Committed `456bf87`.

**Test rigor:** `lirk test //board-games/go:board_test` — **10/10**
fresh-subshell runs, `.lirk-cache.json` deleted before each. `lirk
build //...`: all 16 targets across `shared/`, `tictactoe/`,
`connect4/`, `backgammon/`, and `go/` build clean.

## Test-coverage review (2026-07-27): closed the main.py gap, spot-checked test quality

User asked whether test coverage was actually adequate, and pushed on
a real question: if tests pass every time, does that mean they're
good tests? Answer acted on: no, passing is necessary but not
sufficient — a test only means something if it's *capable* of
failing. Two things followed from that.

**1. Closed the biggest real gap: `main.py` had zero automated tests
in any of the four games.** All prior "manually verified end-to-end"
claims in this log were piped-input runs in the terminal, real but
not repeatable or checked by `lirk test`. Added `main_test.py` to
each game (subprocess-based: runs the real `main.py` with piped
stdin, same as a player typing), wired into `BUILD.lirk` as a new
`main_test` target (`deps = [":main"]`) per game:

- `tictactoe`: scripted win (top row) + full-board draw.
- `connect4`: scripted horizontal win + a full-column-rejected-then-
  continues-to-win scenario (exercises the `except ValueError:
  continue` retry path nothing else tested).
- `go`: the two scenarios already manually verified while building
  `main.py` (illegal-move-then-pass-pass with correct scoring; a real
  sequential corner capture), now committed and repeatable.
- `backgammon`: dice make an exact scripted outcome impractical, so
  this one only asserts a full game (always picking the first offered
  action) reaches a winner cleanly — guaranteed to terminate since
  every action strictly decreases total pips. Verified reliable
  across 16+ runs with genuinely different random dice each time
  (~2-4s standalone, ~9-12s through `lirk test`'s nested-subprocess
  overhead — noted so a future session doesn't mistake that for a
  hang, which is what it looked like on first glance during a
  combined multi-target batch that hit a Bash-tool timeout).

All committed and pushed per-file (test file, then `BUILD.lirk` edit,
per game — 8 commits). `lirk build //...`: 20 targets total, all
clean. Root `board-games/README.md`/per-game `README.md`s not updated
for this — the games' scope descriptions didn't change, only their
test coverage did.

**2. Mutation-testing spot check, to answer "are these tests actually
good" rather than just "do they pass."** Deliberately broke 4 real
rules in `go/board.py` and `backgammon/board.py`, one at a time, ran
the relevant `board_test.py`, confirmed a failure, reverted (backed up
originals first, diffed clean after each revert):

- go: disabled the ko check entirely (`if False and ...`) → 1 test
  failed (`test_ko_forbids_immediate_recapture`).
- go: disabled captures entirely → 7 tests failed/errored (captures
  are load-bearing for several other assertions too, e.g. the
  snapback test).
- backgammon: disabled the bear-off overshoot's farther-checker check
  → 3 tests failed.
- backgammon: weakened the blocking rule (`>= 2` → `> 2`, wrongly
  allowing a landing on a made 2-stack point) → 7 tests failed.

All 4 caught. This doesn't prove the suites are exhaustive, but it's
real evidence they're not tautological — they die when the rules
they claim to check actually break, which is the honest bar for "are
these good tests," not just green-every-time.

## Priority list status (2026-07-27, updated)

1. `shared/` — **done**.
2. `board-games` — **in progress**: `tictactoe`, `connect4`,
   `backgammon`, `go` done (now with `main.py` integration tests
   too); `chess` still to come, same pattern.
3. `adventure-engine` — not started.
4. `weather-narrative`, `world-events-tracker` — bonus, still last.

## Next up

- `board-games/chess` — last `board-games` entry, same pattern: pure
  logic module + test, thin `main.py` entrypoint, `main_test.py`
  (established this session as standard going forward, not just a
  one-off backfill), `BUILD.lirk`, `lirk test` confirmed via multiple
  fresh-shell runs, commit per file per this session's instruction.
  Chess has its own bug-prone areas worth verifying interactively
  before writing tests the same way go's snapback/ko fixtures were:
  check/checkmate/stalemate detection, castling (both sides, through-
  check and rook-moved/king-moved invalidation), en passant, and pawn
  promotion.

## In progress (2026-07-27, new session): `board-games/chess`

Fresh session start: confirmed via `git log`/`git status` that the repo
is exactly where the prior session left it (nothing to resume beyond
an unrelated uncommitted `.claude/settings.local.json` tweak, not
touched). Skimmed this file for context per session start instruction.

Starting `chess`, same `board.py` → `board_test.py` → `main.py` →
`main_test.py` → `BUILD.lirk` pattern as the other four games, per
explicit per-file commit+push discipline established with backgammon.

Design decisions made before writing code:
- Board: `board[row][col]`, row 0 = rank 1 (white's back rank), row 7
  = rank 8; col 0 = file a, col 7 = file h. Pieces are single letters,
  uppercase = white, lowercase = black (`P N B R Q K` / `p n b r q k`),
  `""` = empty — standard, compact, and matches the single-letter
  notation needed for the ~30-40 col terminal constraint.
- Game state is a dict: `board`, `turn`, `castling` (4 independent
  booleans `K`/`Q`/`k`/`q`), `en_passant` (target square or `None`,
  reset every move except immediately after a two-square pawn push).
- Move legality: pseudo-legal generation per piece, then filtered by
  simulating the move and checking the mover's own king isn't left in
  check — same "generate then filter by safety" shape as go's
  suicide-rule check, not a from-scratch pin-detection algorithm.
- Castling encoded as a two-square king move in pseudo-legal
  generation (checks rights, empty-between, not-currently-in-check,
  and king's path/landing squares not attacked); `apply_move` detects
  the two-square king move and relocates the rook. Castling rights
  invalidated on king move, rook move from its original square, or
  rook captured on its original square.
- En passant: diagonal pawn move onto the (empty) `en_passant` target
  square triggers removal of the passed pawn.
- Promotion: `apply_move` takes an explicit `promotion` param
  (`Q`/`R`/`B`/`N`); raises if a pawn reaches the last rank without one
  supplied, forcing `main.py` to prompt rather than silently defaulting
  to queen.
- Input scheme for `main.py`: file letter (a-h) + rank digit (1-8) per
  square, unlike go's plain column/row digits — algebraic notation is
  the natural fit for chess and still single-key+Enter compatible via
  `shared/input.py`'s `prompt_choice`.

Plan: verify castling-through-check, en passant, and promotion
interactively via `python3` against the real `board.py` first (same
discipline as go's snapback/ko fixtures), before encoding them into
`board_test.py`.

## In progress (2026-07-27, new session): resuming chess, lirk pulled post-review

New session start. Per explicit instruction: pulled `../lirk` first —
confirmed at `9611760` ("Close out the review-driven work in the
session log"), post architecture-review with 18 follow-up hardening
commits since the `428c517` this repo last used (unknown-key
rejection, no-srcs rejection, run-all-srcs-not-just-first-failure,
stdin=DEVNULL + timeout for test subprocesses, atomic incremental
cache saves, dot-directory skipping, label-syntax validation, and
more — full list in `../lirk/docs/dogfooding/2026-07-27-chess.md`).

Regression-checked the *existing* graph against the updated lirk
before touching chess further: `lirk build //...` — 20/20 targets
clean. `lirk test //...` — 10/10 tests passed, 3x fresh-shell with
`.lirk-cache.json` cleared each run. No regressions from the 18 fixes.

Found chess exactly where the prior session left it: `board.py`
committed (`839165e`), `board_test.py` (55 tests, covering check,
checkmate, stalemate, castling both sides + through/onto-check +
rights-invalidation, en passant, promotion) written but **uncommitted**
— matching the log's last note that verification was still pending.

Ran `board_test.py` standalone first (repo convention): **55/55
green.** Then, since the log flagged chess's bug-prone areas
explicitly (castling-through-check, en passant, promotion), did a
mutation-testing spot check on `board.py` before trusting the suite,
same discipline used for go/backgammon's coverage review — backed up
`board.py`, broke 4 real rules one at a time, confirmed each caused a
real test failure, reverted (diffed clean after each revert):

- Disabled en passant capture eligibility → 2 tests failed
  (`EnPassantTest`).
- Disabled the castling-through-check transit-square safety check →
  1 test failed (`test_castling_forbidden_through_attacked_square`).
  Notably, the *landing*-square variant (`..._onto_attacked_square`)
  did **not** fail under this same mutation — it's independently
  protected by `legal_moves`'s generic own-king-safety filter (landing
  in check is illegal for any move, not just castling), so the
  dedicated landing-square check in `_king_moves` is defense-in-depth,
  not the only guard. Confirmed this is by design, not a gap: a second
  mutation disabling the general king-safety filter entirely (see
  below) does catch the landing-square case too.
- Disabled the general own-king-safety filter in `legal_moves` (the
  "generate then filter" check shared with go's suicide-rule shape) →
  3 tests failed, including the pin-detection test and both the fools-
  mate checkmate test and the K+Q-vs-K stalemate test.
- Removed the mandatory-promotion-choice enforcement in `apply_move` →
  2 tests failed (`test_raises_without_promotion_choice`,
  `test_raises_on_invalid_promotion_choice`).

All 4 caught, `board.py` confirmed byte-identical to committed version
after all reverts. `board_test.py` committed.

Also started `../lirk/docs/dogfooding/2026-07-27-chess.md` (uncommitted
in the lirk repo, per the standing hand-off convention) — logging real
lirk usage experience as chess proceeds, separate from this file.

## Done (2026-07-27): `board-games/chess` complete — board-games priority item finished

- `main.py` — algebraic-notation entrypoint: squares entered as two
  single-key prompts each (file letter a-h, then rank digit 1-8),
  matching go's column/row split pattern. Promotion piece (q/r/b/n)
  prompted only when a pawn move actually reaches the last rank.
  Verified end-to-end via a piped Fool's Mate playthrough (f2-f3 e7-e5
  g2-g4 Qd8-h4#) — board rendered correctly (rank 8 on top, a-h file
  labels), checkmate detected, clean exit. Committed `42ef0a6`.
- `main_test.py` — 2 subprocess-based integration tests, both
  hand-verified live against the real script before encoding (same
  discipline as go's snapback/ko fixtures):
  - Illegal-move retry (a2-a5, rejected as a 3-square pawn jump) then
    Fool's Mate to checkmate.
  - A queenside pawn-storm promotion (a4, axb5, b6, b7, bxa8=Q —
    promoting by capturing black's own rook) followed by a standard
    Scholar's-Mate pattern on the kingside (e4, Bc4, Qh5, Qxf7#).
    Black's king never moves and stays boxed in by its own untouched
    d7/e7/f7/d8/f8 pieces the whole game (never touched by either
    side's scripted moves), so the final undefended check is
    immediately mate — verified this reasoning against the real engine
    interactively (via `board.py` directly) before committing to the
    full move list, rather than hand-deriving legality by memory.
  Both scenarios: exit 0, no tracebacks. Deliberately scoped to
  integration wiring only (rendering, prompt flow, illegal-move retry,
  promotion prompt, clean checkmate ending) — deep rule coverage
  (castling, en passant, promotion mechanics) stays in `board_test.py`'s
  55 tests, consistent with the effort level of the other 4 games'
  `main_test.py` files. Committed `0ab6909`.
- `BUILD.lirk` — same `board`/`board_test`/`main`/`main_test` shape as
  every other game, `main` depending on `//shared:term`/`//shared:input`.
  `lirk test //board-games/chess:board_test` and `:main_test`: **10/10**
  fresh-shell, cache-cleared runs each, no flakiness. Committed `59d58b5`.
- `README.md` (chess + updated `board-games/README.md`, removing the
  stale "planned next: chess" line since it's now done). Committed
  `888b2e1`.

**Full-repo confirmation:** `lirk build //...` — 24/24 targets clean.
`lirk test //...` — 12/12 tests pass.

**lirk dogfooding, closed out for this target:** appended final entries
to `../lirk/docs/dogfooding/2026-07-27-chess.md` (still uncommitted
there, per convention) — timed `board_test`/`main_test` through `lirk
test` vs standalone (lirk adds a flat ~2.7-3.2s per-invocation overhead
regardless of suite size, consistent with backgammon's earlier note;
not a correctness issue), and confirmed nothing about chess's added
complexity (55 tests, 8x8 stateful board, cross-package deps,
algebraic I/O) stressed lirk's model beyond what the simpler 4 games
already exercised. That file is a hand-off for a future lirk session,
not something to act on further from this side.

## Priority list status (2026-07-27, updated)

1. `shared/` — **done**.
2. `board-games` — **done**: `tictactoe`, `connect4`, `backgammon`,
   `go`, `chess` all complete, same pattern throughout (pure logic +
   `board_test.py`, thin `main.py` + `main_test.py`, `BUILD.lirk`,
   `README.md`), all green under `lirk`.
3. `adventure-engine` — not started.
4. `weather-narrative`, `world-events-tracker` — bonus, still last.

## Next up

- `adventure-engine` (`stories/`: dungeon, train-mystery) is next per
  the reordered priority list — board-games is fully done. No design
  decisions made yet for this; start fresh next session with a scope
  discussion the same way chess's castling/en passant/promotion scope
  was decided up front before writing code.

## In progress (2026-07-27, new session): starting `adventure-engine`

Fresh session start: confirmed via `git log`/`git status` that the repo
is exactly where the prior session left it (board-games fully done,
nothing to resume beyond the unrelated uncommitted
`.claude/settings.local.json` tweak, not touched). Pulled `../lirk`
(already up to date, nothing new since the chess session's `9611760`).

Noticed a stray untracked, empty `board-games/lirk/docs/` directory on
disk (not git-tracked, doesn't show in `git status` since it's empty) —
looks like debris from an earlier accidental invocation. Left alone,
not part of any tracked state.

Design decisions made before writing code (per explicit instruction to
propose the state model first, same as chess's up-front castling/en
passant/promotion decisions):

- State (save/resume-able): `{"scene": id, "inventory": [...],
  "flags": {...}, "visited": [...]}`. `inventory` is an order-
  preserving list, `flags` arbitrary story-defined booleans, `visited`
  an ordered scene-id history.
- Story data is a plain Python module per pack (e.g.
  `stories/dungeon/story.py`, `START` + `SCENES` dict), not JSON —
  keeps ASCII art as readable triple-quoted strings, stays consistent
  with the rest of the repo being pure Python, and still slots into
  `lirk` as an ordinary `python_library` target, same shape as
  `board.py`. No engine imports inside story data — genuinely just
  data, per the "engine runs either pack without code changes" scope
  requirement.
- A scene's `choices` list entries carry `requires_flags`,
  `requires_items`, `sets_flags`, `add_items`, `remove_items`. A scene
  with no *available* choices (empty, or all gated out) is an ending —
  no separate ending flag needed.
- `engine.py` is pure logic, no I/O, mirroring `board.py`'s
  testability shape: `new_state`, `available_choices`, `apply_choice`,
  `is_ending`, `save_state`/`load_state` (plain JSON, since state is
  already JSON-serializable).

Plan: `engine.py` + `engine_test.py` (fixture story, not real prose)
first, committed and confirmed via `lirk` before any story content.
Then `BUILD.lirk` for the engine, then `stories/dungeon`, then
`stories/train-mystery`, per-file commits per the established
discipline. Also starting
`../lirk/docs/dogfooding/2026-07-27-adventure-engine.md` (uncommitted
there, per the standing hand-off convention) to note whether lirk
handles this data-driven-content shape any differently than the board
games' rule-validation shape.

## Done (2026-07-27): `adventure-engine` core (`engine.py`, `runner.py`)

- `engine.py` — pure state machine per the design above: `new_state`,
  `available_choices` (flag/item gating), `apply_choice` (effects:
  `sets_flags`/`add_items`/`remove_items`, dedup on add, raises
  `IndexError` on an out-of-range index — index is relative to
  *available* choices, not the scene's raw choice list, so a gated-out
  choice can never be selected by stale positional index),
  `is_ending` (no available choices), `save_state`/`load_state` (plain
  JSON, state is already JSON-serializable). Committed `edfa874`.
- `engine_test.py` — 24 tests against a small fixture story (not real
  prose). Ran standalone first (24/24 green), then mutation-tested 4
  real rules (flag gating, item gating, add-item dedup, index-bounds
  check) one at a time — all 4 caught on the first pass, `engine.py`
  confirmed byte-identical after each revert. Committed `ff99f7b`.
- `runner.py` — the shared interactive loop every story pack's own
  thin `main.py` calls (`run(story, save_path)`): renders art+text via
  `shared.term`, numbered-choice prompts via `shared.input`, "s" to
  save-and-quit, resume-or-decline prompt when a save file exists.
  Committed `56dc0e6`.
- `runner_test.py` — 4 subprocess-based tests (same style as every
  board game's `main_test.py`) against a tiny fixture story: full
  playthrough to an ending, save-and-quit, resume-and-continue,
  decline-resume-starts-fresh. Mutation testing caught 2 of 3 breaks
  immediately (skipped save-file removal on ending; skipped the actual
  `save_state` call on quit) but the third — silently ignoring the
  resume y/n answer and always resuming — **slipped through** the
  original decline-resume test, because both a forced-resume and a
  genuine fresh start happened to reach "THE END" given the same input
  length; the test only checked for a successful ending, not which
  path was taken. Fixed by asserting the start scene's text actually
  renders (proof play began at `story.START`), reran the mutation,
  confirmed it's now caught. Worth remembering for any other
  session/choice-count-based test: passing doesn't mean the *specific*
  path claimed was actually taken — assert on distinguishing content,
  not just a shared downstream outcome. Committed `2571b37`.
- `BUILD.lirk` — `engine`/`engine_test`/`runner`/`runner_test`
  targets. `lirk test //adventure-engine:engine_test` and
  `:runner_test`: **10/10** fresh-shell, cache-cleared runs each
  (`runner_test` needed a longer-than-default Bash timeout — each
  `lirk test` invocation is ~10-12s due to its own nested-subprocess
  model, same overhead shape backgammon's `main_test` already
  surfaced). `lirk build //...`: 28/28 targets clean. Committed
  `ca5bec9`.

## Done (2026-07-27): `adventure-engine/stories/dungeon`

- Style-tested ASCII art at the narrow-terminal constraint before
  committing to real content: drafted candidate scenes in a scratch
  script, confirmed simple line-art (basic ASCII chars, no box-drawing
  unicode) fits comfortably at <=36 cols, then finalized 9 scene arts.
- `story.py` — 9 scenes, 3 endings (`escape_with_treasure`,
  `escape_plain`, `caught_again` [bad]). Exercises both
  `requires_items` (a rusty key gates the corridor door) and
  `requires_flags` (a self-looping "study the guard" choice in
  `corridor` sets `studied_guard`, which gates `vault_entrance`'s
  sneak option) — not just linear branching. Verified programmatically
  before committing: wrote a BFS over all reachable
  `(scene, inventory, flags)` states and confirmed all 9 scenes and
  all 3 endings are actually reachable, rather than trusting the
  hand-drawn scene map in the module docstring. Committed `d6acaee`.
- `main.py` — thin wrapper supplying the story module + a per-story
  save path to `runner.run()`. Manually verified end-to-end via piped
  playthroughs to all 3 endings and a save/resume cycle. Committed
  `ebb4691`.
- `main_test.py` — 5 subprocess-based integration tests (real story
  content, not a fixture): treasure-escape, plain-escape,
  shout-leads-to-bad-ending, vault-sneak-hidden-until-guard-studied,
  and a save/resume cycle across two separate process runs. One
  scenario's scripted input was wrong on the first attempt (assumed
  "Turn back" stayed at its raw choice-list position 2 at
  `vault_entrance`, but it renumbers to 1 once "Slip past" is gated
  out) — caught by the live hand-verification pass *before* encoding
  it, not after, same discipline as the engine/runner mutation-testing
  catches above. Committed `22af841`.
- `BUILD.lirk` — `story`/`main`/`main_test`, first cross-package deps
  for `adventure-engine` (`//adventure-engine:runner` consumed from a
  story pack). `lirk test
  //adventure-engine/stories/dungeon:main_test`: **10/10** fresh-shell,
  cache-cleared runs. Committed `df918b2`.

`lirk build //...`: **31/31** targets clean.

## Done (2026-07-27): `adventure-engine/stories/train-mystery`

- Design: hub-and-spoke shape (deliberately different from dungeon's
  linear-with-detours layout) — a corridor hub with three self-looping
  clue rooms (dining/sleeper/cargo car, one clue item each) and a
  confrontation scene where the correct accusation (the widow) is
  gated on a single `requires_items` list of all 3 clues — exercises a
  different engine feature than dungeon's single-flag gate.
- `story.py` — 8 scenes, 3 endings (`ending_solved`,
  `ending_wrong_conductor`, `ending_wrong_stranger`). Same BFS-
  reachability verification as dungeon before committing (all 8
  scenes, all 3 endings reachable). Committed `2af1b73`.
- `main.py` — thin wrapper, same shape as dungeon's. Manually verified
  end-to-end via piped playthroughs to all 3 endings and a save/resume
  cycle. Committed `6d7b77d`.
- `main_test.py` — 5 subprocess-based integration tests: full case
  solved, wrong-suspect endings (both), the widow-accusation option
  confirmed absent with zero clues, and — the most interesting one —
  a single run that reaches confrontation with only 2 of 3 clues
  (confirms "Accuse the widow" absent, and that "Keep investigating"
  has renumbered to key 3 not 4, the same gated-choice-renumbering
  gotcha dungeon's `vault_entrance` test hit), gathers the third clue,
  returns to confrontation, and confirms the option has now appeared
  in the *same run* — split on the repeated "Time to accuse someone."
  scene text to isolate the two visits' choice menus. One assertion
  needed a case-sensitivity fix (checked lowercase "the real killer"
  against a sentence-initial "The real killer..."), caught by the
  first standalone run. Committed `1765b35`.
- `BUILD.lirk` — same `story`/`main`/`main_test` shape as dungeon.
  `lirk test //adventure-engine/stories/train-mystery:main_test`:
  **10/10** fresh-shell, cache-cleared runs. Committed `723b3bb`.

**Full-repo confirmation:** `lirk build //...` — 34/34 targets clean.
`lirk test //...` — 16/16 tests pass (4 adventure-engine + 10 across
the 5 board games + 2 shared).

**Docs:** `adventure-engine/README.md`, `stories/dungeon/README.md`,
`stories/train-mystery/README.md` added (state model, gating/effect
fields, per-story scene/ending counts and which engine feature each
leans on). `.gitignore` updated for runtime-generated `save.json`
files. Root `README.md` already described `adventure-engine`
correctly from before this session, no change needed there.
Committed `0ffc00b`.

**lirk dogfooding, closed out for this target:** appended closing
notes to `../lirk/docs/dogfooding/2026-07-27-adventure-engine.md`
(still uncommitted there, per convention) — confirmed the "different
shape of content" question from the top of that file: lirk's
`library`/`test` target model handles a mostly-big-dict-literal source
file exactly like any other Python source, no friction. Also noted the
first 2-level cross-package fan-in in this repo (`stories/dungeon` and
`stories/train-mystery` both depending on `//adventure-engine:runner`,
which itself has its own cross-package deps) worked cleanly with no
diamond-dependency or cache-staleness issue across repeated
cache-cleared batches. No lirk bugs found this session.

## Priority list status (2026-07-27, updated)

1. `shared/` — **done**.
2. `board-games` — **done**.
3. `adventure-engine` — **done**: engine (`engine.py`/`runner.py`,
   mutation-verified) plus both planned story packs (`dungeon`,
   `train-mystery`), each with real branching content, ASCII art
   tested at the narrow-terminal width, BFS-verified scene/ending
   reachability, and subprocess-based integration tests.
4. `weather-narrative`, `world-events-tracker` — bonus, still last, in
   that order (per the original reordering). Neither started; no
   design decisions made yet for either.

## Next up

- `weather-narrative` (or `world-events-tracker`, order TBD — both are
  bonus/stretch per the standing priority list) — start fresh with a
  scope discussion before writing code, same as every prior project.
  No existing design decisions to build on for either.

## Open questions

- None beyond the SIGHUP blocker above (now tracked in
  `docs/KNOWN_ISSUES.md`, not just here) — that blocker is Please-specific
  and moot for any target now running under `lirk`.
