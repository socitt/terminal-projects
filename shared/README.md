# shared

Common helpers used by more than one tool/game in this repo, so each
tool doesn't reinvent narrow-terminal rendering or raw-keypress input.

- `term.py` — output helpers for narrow (~30-40 col) terminals: padding,
  centering, horizontal rules, screen clearing.
- `input.py` — single-keypress input, so games/tools can read one key
  at a time without waiting for Enter.

Each module is its own `python_library` target with its own
`python_test` target in `shared/BUILD`. Depend on them individually
(e.g. `//shared:term`), not as one bundled target, so a tool that only
needs rendering doesn't pull in input handling.
