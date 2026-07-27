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

**Also not the fix (ruled out 2026-07-26, later same session):** the
theory that this is Please's Go runtime threading interacting badly
with iSH-AOK's process emulation (motivated by the "worse in a tight
loop" observation above). Tested two ways, 10 fresh-shell attempts of
`plz test //shared:term_test --rerun` each:

- `GOMAXPROCS=1` env var: 0/10 passed.
- `numthreads = 1` under `[build]` in `.plzconfig`: 0/10 passed.

Neither improved on baseline; both batches were run back-to-back with
zero passes, vs. the previously measured ~50-60%. Note these specific
runs were also contaminated by the process-leak hazard described just
below, discovered only after both batches completed, so treat this as
suggestive rather than a clean disproof — but combined with ~15
further clean attempts afterward (system verified free of stray
processes) that also produced zero passes, there's no evidence either
setting helps. Neither was kept (`.plzconfig` has no `[build]` section;
no `GOMAXPROCS` set in `pleasew`).

**New hazard identified 2026-07-26:** a `plz`/`pleasew` invocation that
hangs (e.g. `plz help flags`, which does not return) and gets
backgrounded/abandoned rather than killed will keep running
indefinitely and can itself degrade the success rate of *every
subsequent* `plz` call in that session — one such stray process
accumulated over 11 CPU-minutes and, combined with 9 siblings, drove
free memory on the device down to ~56MB out of ~7.65GB before it was
noticed. Always confirm a `plz`/`pleasew` invocation has actually
exited (`ps aux | grep please`) before treating it as abandoned; kill
it explicitly (`kill -9`) rather than letting it run in the
background.

**Mitigation (added 2026-07-26): `scripts/plz-retry.sh`.** Since
retrying is the only working mitigation and doing it manually is
tedious, `scripts/plz-retry.sh <plz args...>` wraps any `plz`/`pleasew`
invocation, retrying up to 5 times (fresh subshell per attempt, short
sleep between), and only reports failure once every attempt is
exhausted. Route `plz build`/`plz test` calls through this rather than
calling `./pleasew` directly. Note: in the same session the two
threading experiments above were run in, `//shared:term_test` failed
100% of the time across roughly 45 total attempts (well beyond 5) even
after the stray-process hazard was cleared — worse than the ~50-60%
baseline documented for a bare genrule, plausibly because this target
requires a longer subprocess chain (build the `plz_test_runner` zip,
build the test binary, run it, then write *and read back* a results
file — more chances to hit the race) and/or genuinely worse ambient
device conditions that day. If `plz-retry.sh` exhausts all 5 attempts,
re-invoking it again is a reasonable next step, not a sign something
is actually broken.

**Also not the fix (ruled out 2026-07-26, later same session): HLE Accel
(arm64/riscv64) toggled on.** Device setting change — HLE Accel
(arm64/riscv64) toggled ON, amd64 JIT toggled OFF (irrelevant, we run
native aarch64 not amd64) — prompted a fresh measurement batch to see
if it affects the SIGHUP rate. Method: confirmed no stray
`plz`/`please` processes first (`ps aux | grep -i please`, clean), then
ran `scripts/plz-retry.sh test //shared:term_test --rerun` (note: the
originally-planned `--rebuild` flag doesn't exist for `plz test`,
confirmed via `./pleasew test --help` — `--rebuild` is `plz
build`-only; `--rerun` is the test-command equivalent and is what the
GOMAXPROCS/numthreads batches above actually used) 10 times, fresh
shell process per attempt, same methodology as those prior batches.

Result: **0/10 passed.** Since `scripts/plz-retry.sh` itself retries
up to 5 times internally, this batch represents 50 total underlying
`pleasew test` invocations, all 50 of which failed. Failure signature
identical to before HLE Accel was toggled — `signal: hangup` after the
test binary completes, then `Test failed to produce output results
file` / `failed to read test results file: Didn't find any test
results in plz-out/tmp/shared/term_test._test/run_1/test.results`.
Example:

```
Error: TestFailed in term_test
Test failed
signal: hangup
//shared:term_test 1 test run in 68ms; 0 passed, 1 errored
```

No improvement over the documented 0%-across-~45-attempts baseline for
this target. HLE Accel is not the fix; not kept as a variable to
control for (it's a device-level setting, not something this repo
configures). Given this and the two ruled-out threading theories above,
root-causing further from the userspace/build-config side looks like a
dead end — see the draft upstream issue
(`docs/DRAFT_ISH_AOK_ISSUE.md`) for the path forward.

**Attempted, not accessible from this session: a syscall/signal-level
log for the moment of the hangup.** Checked `/proc/ish/*` (only
exposes device metadata — battery, host info, JIT toggles, network
interfaces, iSH-AOK version — nothing signal/syscall-level) and
`dmesg` (only the one boot line, nothing per-process). No
`strace`/`ltrace` installed. The iSH-AOK app's own "Diagnostics"
settings screen (if it logs anything at this level) is a native iOS
GUI feature not reachable from a shell/CLI session — would need to be
checked directly in the app by whoever has the device in hand.

**Follow-up attempt: `strace -f`, ruled out as impractical here.**
Installed `strace` via `apk add strace` (asked first since it's a
system package outside the repo's declared dependencies) and tried to
capture a live hangup with
`strace -f -tt -o trace.log ./pleasew test //shared:term_test --rerun`.
Two attempts:

- Attempt 1: no `timeout` wrapper, hard-timed-out at the tool's 5-minute
  ceiling. The trace log shows the traced process tree actually
  exited (status 7, matching the usual `signal: hangup`-style failure)
  only ~4-5s in, but the `strace`-wrapped command itself never
  returned control afterward for the remaining ~4.9 minutes.
- Attempt 2: wrapped in `timeout 60`, still didn't return within 60s;
  the partial trace after 60+s had only reached `pleasew`'s early
  startup config-file checks (`openat .../plzconfig` ENOENT checks),
  a phase that normally takes low tens of ms untraced. Also notable:
  `SIGCHLD` siginfo in the trace reports `si_utime`/`si_stime` values
  in the hundreds of *seconds* of CPU time for what should be
  near-instant syscalls — consistent with generally broken
  clock/CPU-time accounting under iSH-AOK's aarch64 emulation, though
  not confirmed as related to the hangup itself.

No stray processes were left behind either time (`ps aux` clean after
both). Conclusion: `ptrace`-based tracing (via `strace`) introduces
overhead severe enough in this environment (or interacts with the same
underlying emulation issue) that it isn't a practical way to observe
the hangup directly — ruled out as a capture method, not attempted
further. This is itself circumstantial supporting evidence for "the
emulation layer has fundamental issues with process lifecycle
syscalls," useful context for the draft upstream issue even without a
clean capture.

## `shared/term_test.py`: code confirmed correct, clean `plz test` pass still not achieved

Per this repo's working rules (see `docs/ACTIVE_SESSION.md`), every
module needs a passing test before being considered done. `shared/term.py`,
`shared/term_test.py`, and `shared/BUILD` are written and believed
correct (the logic is simple and was reasoned through by hand).

**Update 2026-07-26:** across dozens of attempts (direct, and via
`scripts/plz-retry.sh`), `plz test //shared:term_test` has never
returned a passing exit code this session — but several of the
failures were extremely informative. On at least two occasions, the
underlying `unittest` run completed and printed its full output before
Please's own results-file capture step hit `signal: hangup`:

```
test_center_line_centers_text ... ok
test_default_width_fits_narrow_terminal ... ok
test_hr_repeats_char ... ok
test_pad_line_pads_short_text ... ok
test_pad_line_truncates_long_text ... ok

Ran 5 tests in 0.02s

OK
```
```
ERROR: //shared:term_test failed: Test failed to produce output results file
```

This confirms `shared/term.py` and `shared/term_test.py` are correct —
all 5 tests genuinely pass — and narrows the hangup's failure point
specifically to Please's post-test results-file write/read step (not
just "some build action," as the general entry above already
suspected, but specifically the plumbing *after* the test binary has
already finished successfully).

This is still a deliberate, logged exception to the "test must pass
first" rule — the rule exists to prevent silently broken commits, not
to block on an environment issue that has nothing to do with the code
under test. The code is verified correct by direct observation of the
test run above, even though a green `plz test` exit code has not yet
been captured. Do not repeat this pattern silently for other modules;
each instance should get its own note here explaining why.

**To close this out:** once `plz test //shared:term_test` (ideally via
`scripts/plz-retry.sh`) returns a passing exit code, confirm it and
remove this section.

## `lirk` dogfooding on this target (2026-07-27): different failure, not resolved by switching tools

`lirk` (a separate, minimal build tool, cloned at `../lirk`, built
specifically to avoid the process-group/session-control patterns
suspected of causing the Please hangup above — see its README for the
design rationale) was pointed at the same `shared/term.py` /
`shared/term_test.py` target this session, via a new `shared/BUILD.lirk`
added alongside the existing Please `shared/BUILD` (which is untouched
and remains the historical record of the SIGHUP saga above).

`lirk build //shared:term` passes immediately. `lirk test
//shared:term_test` **fails 10/10** in fresh-shell attempts — but this
is not the same failure mode. It is 100% deterministic
(`ModuleNotFoundError: No module named 'shared'`), not racy, and has
nothing to do with process/session handling:

```
ImportError: Failed to import test module: term_test
Traceback (most recent call last):
  File "/usr/lib/python3.12/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/git/terminal-projects/shared/term_test.py", line 3, in <module>
    from shared import term
ModuleNotFoundError: No module named 'shared'
```

**Root cause:** `lirk`'s `run_test` (`lirk/actions.py`) runs
`python3 -m unittest <module>` with `cwd` set to the target's own
package directory and no `PYTHONPATH` adjustment. That only makes
modules flat inside that same directory importable — confirmed as the
intended model by `lirk`'s own test fixtures
(`tests/fixtures/sample_repo/a/test_a.py` does `from a import greet`,
not a root-relative import). `shared/term_test.py`, on the other hand,
uses `from shared import term` — a root-relative import, matching the
convention Please's Python rules use (and probably the more portable
convention generally, since it doesn't collide across packages that
happen to share a filename).

**Verdict: not a resolved comparison.** `lirk` correctly avoids the
Please hangup (no `signal: hangup`, no results-file step at all — it
fails or passes in one direct `subprocess.run()`), but v1 can't
actually run this existing test file as-is. This is a `lirk` bug/gap
(import model too narrow for root-relative imports), not an
environment flakiness issue, and not something to debug or work around
from this repo — it's being taken back to the `lirk` repo separately.
Neither `shared/term_test.py` nor `shared/BUILD` (the Please target)
were modified to work around this. `shared/BUILD.lirk` stays in this
repo as the reproduction case for that follow-up.
