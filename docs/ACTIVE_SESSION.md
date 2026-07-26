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

## Open questions

- None beyond the SIGHUP blocker above (now tracked in
  `docs/KNOWN_ISSUES.md`, not just here).
