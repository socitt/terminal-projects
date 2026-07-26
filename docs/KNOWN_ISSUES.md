# Known Issues

## `plz`/`pleasew` build actions intermittently fail with `signal: hangup`

**Status:** Open, unresolved. Root cause not confirmed. Deliberately not
blocking work — see "Working around it" below.

**Symptom:** Any Please build action that forks a subprocess (not just
Python-specific ones) can fail with:

```
Error building target //some:target: signal: hangup
```

**Confirmed scope, from direct testing on 2026-07-26:**

- It is **not** specific to Python, `python_test`, or wheel
  fetching/repackaging. A bare `genrule` with `cmd = "echo hi > $OUT"`
  fails the exact same way.
- It is **not** fixed by wrapping `plz`/`pleasew` in a real pseudo-tty
  (`python3 -c "import pty; pty.spawn([...])"`). A prior session
  believed this fixed plain build/zip steps; re-testing with forced
  rebuilds (`--rebuild`) showed that belief was based on a cache hit,
  not an actual fix — forced rebuilds of the same target fail under
  the pty wrapper just as often as without it.
- It **is** flaky/racy, not a hard 100%-reproducible wall. Repeated
  `--rebuild` attempts of the same trivial genrule target, each in a
  fresh shell process, succeeded roughly 50-60% of the time in one
  measured batch (5/8).
- It appears to get **worse** (closer to 100% failure) when multiple
  `plz`/pty-wrapped invocations run in a tight loop within a single
  shell process, vs. each invocation getting a fresh shell. Not
  root-caused, but consistent with the original theory: some kind of
  race between Please's Go fork/exec + process-group handling and
  iSH-AOK's job-control emulation, possibly worsened by leftover
  pty/fd state from a prior `pty.spawn` in the same parent process.

**Working theory (unconfirmed):** a race condition in Please's
fork/exec path under iSH-AOK's (native aarch64 Alpine, emulated on
iPhone) job-control emulation, not something fixable from userspace
in this repo. Worth reporting upstream to Please and/or iSH-AOK if it
keeps blocking real work.

**Working around it:**

- Retry. Since failures are racy rather than deterministic, re-running
  the same `plz build`/`plz test` command (ideally as a fresh shell
  invocation each time, not in a tight in-process loop) has a decent
  chance of succeeding within a handful of attempts.
- Do NOT treat one success as proof of a fix (see the pty-wrapper false
  lead above) — a cached target will "succeed" without re-exercising
  the actual subprocess path. Use `--rebuild` when trying to verify a
  fix is real.

**Not the fix (ruled out 2026-07-26):** a custom `python_test` runner
(`//tools/plz_test_runner`) was added, wired via `TestRunner` /
`TestrunnerDeps` in the root `.plzconfig`, specifically to avoid
Please's built-in `unittest` runner pulling in the `xmlrunner` and
`portalocker` wheels (see git history around this file for the
original hypothesis). It's still a reasonable thing to keep — it
means `python_test` targets never need those wheels — but it does
**not** unblock `plz test`, because the hangup is a general build-action
problem, not specific to wheel fetching. `//tools/plz_test_runner:_runner#zip`
(a plain, dependency-free `python_library` zip step) failed with the
same `signal: hangup` as everything else when tested directly.

## `shared/term_test.py` not yet confirmed passing

Per this repo's working rules (see `docs/ACTIVE_SESSION.md`), every
module needs a passing test before being considered done. `shared/term.py`,
`shared/term_test.py`, and `shared/BUILD` are written and believed
correct (the logic is simple and was reasoned through by hand), but
`plz test //shared:term_test` has not been confirmed to actually run
to completion, because of the issue above.

This is a deliberate, logged exception to the "test must pass first"
rule — the rule exists to prevent silently broken commits, not to
block on an environment issue that has nothing to do with the code
under test. Do not repeat this pattern silently for other modules;
each instance should get its own note here (or a new entry) explaining
why the test couldn't be run.

**To close this out:** once `plz test //shared:term_test` can be run
reliably (or even once, with `--rebuild`, to prove it's not a stale
cache hit), confirm it passes and remove this section.
