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
  (`python_library` + `python_test` targets) are all written on disk
  but **NOT YET COMMITTED** — per working rules, the test has to be run
  and confirmed passing first, and that's blocked (see below).

## BLOCKER: `plz` subprocess execution fails with `signal: hangup`

Discovered while trying to run `./pleasew test //shared:term_test`.
Every build action Please shells out to fails immediately:
`Error building target //shared:_term#zip: signal: hangup` — this is
not specific to Python or to this target; a bare `genrule` with
`cmd = "echo hi > $OUT"` fails the same way. Confirmed the underlying
command itself is fine when run directly (`python3 -S -m compileall`
works standalone).

Root cause (best working theory, not confirmed against Please's
source): Please is a multi-threaded Go binary, and when it isn't
attached to a controlling terminal (which it isn't in this session),
its fork/exec + process-group setup for build actions appears to race
with iSH-AOK's job-control emulation, and the child gets sent SIGHUP
before/right after exec.

**Workaround found:** wrapping the `plz` invocation in a real
pseudo-terminal fixes it for plain build actions:

```
python3 -c "import pty; pty.spawn(['./pleasew', '-p', 'test', '//shared:term_test'])"
```

Under this wrapper, `//shared:_term#zip` (the plain python_library zip
step) built successfully. **But** it did NOT fix everything: the
`python_test` target also depends on `///python//third_party/python:
_xmlrunner#wheel` (and `_portalocker#wheel`, `coverage`) — these are
`python_wheel` targets (fetched dependencies for the default
xmlrunner-based test reporter), and their "Repackaging..." build step
still fails with the same `signal: hangup`, pty or not, sequential
(`-n 1`) or not. Not yet root-caused. Network itself is reachable
(`ping 8.8.8.8` works) and `wget` is installed (no `curl`), so it's
probably not a plain connectivity issue — more likely the same
fork/exec problem hitting a different code path inside Please (maybe
its sandboxing wrapper for fetched/repackaged targets).

## Open question to resolve before/at next step

- How to get `//shared:term_test` (or any `python_test`) to actually
  run to completion under iSH-AOK. Options to try next:
  - Root-cause why the wheel-repackaging step still hangs-up under the
    pty wrapper when the plain zip step doesn't.
  - Check if Please has a way to avoid the xmlrunner-based test
    bootstrap (e.g. a plain/bare test runner) to sidestep the wheel
    fetch entirely, at least to unblock `shared/term`.
  - Worth asking upstream (Please or ish-AOK) if this is known.
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

1. Unblock the `plz test` SIGHUP issue above — this gates everything
   else, since the working rules require a passing test before any
   module is considered done.
2. Once unblocked: run `//shared:term_test`, confirm it passes, commit
   `shared/term.py` + `shared/term_test.py` + `shared/BUILD` as one
   commit, push.
3. `shared/input.py` (single-keypress input helper) — same
   stub → test → commit pattern.
4. Then start on `board-games` (stub folder + README + minimal BUILD +
   stub entrypoint), per the reordered priority above.

## Open questions

- None beyond the SIGHUP blocker above.
