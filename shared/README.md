# shared

Common helpers used by more than one tool/game in this repo, so each
tool doesn't reinvent narrow-terminal rendering or raw-keypress input.

- `term.py` — output helpers for narrow (~30-40 col) terminals: padding,
  centering, horizontal rules, screen clearing.
- `input.py` — single-key input: type one character, hit Enter. Not a
  raw keypress read — the iOS on-screen keyboard doesn't give terminal
  apps reliable access to that, so games/tools read a line and act on
  its first character instead.

Each module is its own `library` target with its own `test` target in
`shared/BUILD.lirk` (built and tested via `lirk`, see
`docs/ACTIVE_SESSION.md` for why — `term` also still has a `python_library`/
`python_test` pair in the older, Please-based `shared/BUILD`, kept as
historical record; `input` is `lirk`-only). Depend on targets
individually (e.g. `//shared:term`), not as one bundled target, so a
tool that only needs rendering doesn't pull in input handling.
