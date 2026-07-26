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
- Created this file.

## In progress

- Nothing yet — about to commit this file.

## Next up (in order)

1. Commit + push this file. (current step)
2. Root README (purpose, constraints, Please-not-Bazel rationale).
3. Please build config / root BUILD file.
4. `shared/` library stub (terminal rendering + single-keypress input
   helpers).
5. Stub folder + README + minimal BUILD + stub entrypoint, each as its
   own committed piece, for:
   - `weather-narrative`
   - `board-games` (subfolders: tictactoe, connect4, backgammon, go,
     chess)
   - `adventure-engine` (`stories/`: dungeon, train-mystery)
   - `world-events-tracker`

## Open questions

- None yet.
