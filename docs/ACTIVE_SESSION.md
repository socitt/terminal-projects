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

## Priority list status (2026-07-27)

Per the reordered list further down this file:

1. `shared/` — **done**, both `term`/`input` green under `lirk`.
2. `board-games` — **in progress**: `tictactoe` done; `connect4`,
   `backgammon`, `go`, `chess` still to come, same pattern.
3. `adventure-engine` — not started.
4. `weather-narrative`, `world-events-tracker` — bonus, still last.

## Next up

- `board-games/connect4` (or whichever board-games entry is picked up
  next), same pattern: pure logic module + test, thin `main.py`
  entrypoint, `BUILD.lirk`, `lirk test` confirmed via multiple
  fresh-shell runs, commit.

## Open questions

- None beyond the SIGHUP blocker above (now tracked in
  `docs/KNOWN_ISSUES.md`, not just here) — that blocker is Please-specific
  and moot for any target now running under `lirk`.
