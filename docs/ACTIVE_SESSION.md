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
  run to completion reliably under iSH-AOK. Now believed to need one
  of:
  - A real fix/understanding of the fork/exec race (see
    `docs/KNOWN_ISSUES.md`) — possibly worth reporting upstream to
    Please and/or iSH-AOK.
  - A pragmatic retry wrapper around `plz`/`pleasew` invocations, since
    failures are racy rather than deterministic (~50-60% success per
    attempt was measured for a trivial target this session).
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

1. `shared/term.py` + `shared/term_test.py` + `shared/BUILD` are being
   committed this session as a logged exception (see
   `docs/KNOWN_ISSUES.md`) — test not yet confirmed passing due to the
   SIGHUP blocker. First thing on resume: try `plz test
   //shared:term_test` again (retry a few times, fresh shell per
   attempt, per the workaround in `docs/KNOWN_ISSUES.md`). If it
   passes, remove the "not yet confirmed passing" note from
   `docs/KNOWN_ISSUES.md`.
2. `shared/input.py` (single-keypress input helper) — same
   stub → test → commit pattern. Same SIGHUP caveat likely applies;
   don't silently skip the test again — log it same as above if hit.
3. Then start on `board-games` (stub folder + README + minimal BUILD +
   stub entrypoint), per the reordered priority above.
4. If the SIGHUP flakiness keeps costing time, consider writing a
   small retry wrapper script around `plz`/`pleasew` invocations
   (see `docs/KNOWN_ISSUES.md` for measured success rates) rather than
   re-diagnosing it from scratch each time.

## Open questions

- None beyond the SIGHUP blocker above (now tracked in
  `docs/KNOWN_ISSUES.md`, not just here).
