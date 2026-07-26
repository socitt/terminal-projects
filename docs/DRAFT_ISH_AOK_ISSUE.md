# Please build actions intermittently fail with `signal: hangup`, isolated to post-exit results-file step

## Summary

Please (https://please.build, a Bazel-like build tool, single static Go
binary, no JVM) intermittently fails build and test actions under
iSH-AOK with `signal: hangup`. This reproduces with the simplest
possible build action (a `genrule` that just does `echo hi > $OUT`),
so it isn't specific to Please's Python rules or any particular
dependency fetch. It's racy (roughly 50-60% success per attempt in one
measured batch, not a hard wall), gets worse when invocations are run
in a tight loop within one shell session, and — most specifically —
for a Python `python_test` target, the actual test binary has been
observed to run to completion and print a full passing result before
the hangup happens in Please's own post-test results-file write/read
step. Terminal output for that case is included below.

Not sure yet whether this is a Please-side bug, an iSH-AOK-side bug,
or an interaction between the two — filing here first since the
symptom (`signal: hangup` reaching a userspace process) looks like it
could originate in iSH-AOK's process/job-control emulation, but happy
to move or cross-file this if it turns out to be Please-side.

## Environment

- iSH-AOK version: `1.3 (543)` (from `/proc/ish/version`)
- Kernel string: `Linux localhost 5.20.66-ish_aok iSH-AOK 2026-07-26 12:13 aarch64 Linux`
- Distro: Alpine Linux 3.23.3 (`/etc/os-release`), native aarch64 (not
  emulated x86 — this is iSH-AOK's native aarch64 mode)
- Device: iPhone 15 Pro Max (`iPhone16,2`), iOS 26.5.2
- Host (for reference): Darwin 25.5.0 (xnu-12377.122.8~1/RELEASE_ARM64_T8122), arm64e (A17 Pro)
- Please version: `17.31.2` (pinned via `.plzconfig`, installed via the
  standard `pleasew` wrapper script)
- No JVM involved anywhere in this build — that's the whole reason
  this project uses Please instead of Bazel under iSH-AOK.

## Minimal reproduction

This does not require Python or any external dependency — a bare
`genrule` reproduces it.

1. In an empty directory, create `.plzconfig`:

   ```ini
   [please]
   version = 17.31.2
   ```

2. Create a root `BUILD` file:

   ```python
   genrule(
       name = "hello",
       outs = ["hello.txt"],
       cmd = "echo hi > $OUT",
   )
   ```

3. Run the build repeatedly, forcing a real rebuild each time (so
   cache hits don't mask failures), with each attempt in a **fresh
   shell process** (not a loop within one interactive shell):

   ```sh
   for i in $(seq 1 10); do
     sh -c './pleasew build //:hello --rebuild'
   done
   ```

4. Observe that a meaningful fraction of attempts (see below) fail
   with:

   ```
   Error building target //:hello: signal: hangup
   ```

   while others succeed normally with no code change between attempts.

## Confirmed behavior

These are stated as directly observed facts from this session's
testing, not theories:

- **Not Python/dependency-specific.** The bare `genrule` above (no
  Python, no wheel fetch, no external dependency) fails with the exact
  same `signal: hangup` as a `python_test` target did. A separate,
  dependency-free `python_library` zip-packaging step
  (`//tools/plz_test_runner:_runner#zip`) also failed the same way
  when tested directly.
- **Racy, not deterministic.** Repeated `--rebuild` attempts of the
  same trivial `genrule` target, each in a fresh shell process,
  succeeded roughly 50-60% of the time in one measured batch (5/8).
- **Worse in a tight loop.** Running multiple Please invocations
  back-to-back within a single shell process (rather than each getting
  a fresh shell) pushes the failure rate noticeably higher, closer to
  100%, than spacing invocations out as separate fresh-shell processes.
- **A pseudo-tty wrapper does not fix it — ruled out, was a false
  lead.** An earlier belief that wrapping `plz`/the launcher script in
  a real pty (`python3 -c "import pty; pty.spawn([...])"`) fixed plain
  build/zip steps turned out to be based on a cache hit, not an actual
  fix. Forcing rebuilds (`--rebuild`) of a target previously believed
  fixed by the pty wrapper reproduced the identical `signal: hangup`
  under the same wrapper, at the same rate as without it. Worth
  flagging explicitly so others don't spend time on the same false
  lead.
- **`GOMAXPROCS=1` does not fix it — ruled out.** Motivated by a
  hypothesis that this is Please's Go runtime threading interacting
  badly with iSH-AOK's process emulation. 10 fresh-shell attempts of a
  `python_test` target with `GOMAXPROCS=1` set: 0/10 passed. No
  improvement over baseline.
- **`numthreads = 1` (Please's own build-concurrency setting) does not
  fix it — ruled out.** Same hypothesis, tested via Please's own
  concurrency control instead of the Go runtime's. 10 fresh-shell
  attempts with `numthreads = 1` under `[build]` in `.plzconfig`: 0/10
  passed. No improvement over baseline.

## Further findings: isolates the failure to a specific post-exit step

The most concrete evidence comes from a `python_test` target (a small
`unittest`-based test, run via a custom stdlib-only test runner wired
through Please's `TestRunner`/`TestrunnerDeps` config — included for
completeness, though the bare `genrule` case above is the minimal
repro and doesn't require any of this Python-specific setup).

On at least two occasions, the actual test process ran to completion
and printed a fully passing result, and the `signal: hangup` happened
**afterward**, in Please's own step that writes and reads back the
test's results file — not in the test process itself. Terminal output
(from `plz test //shared:term_test`, wrapped through a plain 5x retry
script — see below):

```
test_center_line_centers_text (shared.term_test.TermTest.test_center_line_centers_text) ... ok
test_default_width_fits_narrow_terminal (shared.term_test.TermTest.test_default_width_fits_narrow_terminal) ... ok
test_hr_repeats_char (shared.term_test.TermTest.test_hr_repeats_char) ... ok
test_pad_line_pads_short_text (shared.term_test.TermTest.test_pad_line_pads_short_text) ... ok
test_pad_line_truncates_long_text (shared.term_test.TermTest.test_pad_line_truncates_long_text) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.020s

OK

//shared:term_test 1 test run in 6.613s; 0 passed, 1 errored
```

```
18:53:23.346 WARNING: failed to read test results file: Didn't find any test results in plz-out/tmp/shared/term_test._test/run_1/test.results
18:53:23.349   ERROR: //shared:term_test failed: Test failed to produce output results file
```

The code under test is verifiably correct (all 5 assertions pass, per
the captured `Ran 5 tests ... OK` output) — Please itself reports the
target as failed only because it couldn't find/read the results file
its own test runner should have just written. This was reproducible
across a large number of attempts in one session: for this
particular target, `plz test` failed 100% of the time across roughly
45 total attempts that day, noticeably worse than the ~50-60%
genrule-level baseline above — plausibly because this target's build
graph is a longer subprocess chain (build a helper library's zip step,
build the test binary, run it, then write *and* read back a results
file), giving the underlying race more chances to hit.

## Working theory (unconfirmed hypothesis)

Given the timing — the hangup in the Python-test case happens right
after the test process has already exited successfully, during
Please's own follow-up file I/O — one hypothesis is a race in
session/controlling-terminal or process-group teardown handling: when
a child process Please forked exits, something in iSH-AOK's
job-control emulation may occasionally deliver or mishandle `SIGHUP`
to a process (or a subsequent fork) that shouldn't receive it,
particularly around process-group/session boundaries. This is a
hypothesis based on the observed timing, not a confirmed root cause —
we have not instrumented iSH-AOK or Please internals to verify it.

## Open question: where does this belong?

Genuinely unclear whether this is:

- A Please-side issue (something about how its Go fork/exec /
  process-group handling behaves under an emulated job-control layer), or
- An iSH-AOK-side issue (something in the aarch64 process/signal
  emulation that surfaces specifically around child-process exit and
  the fork/exec calls Please issues immediately after), or
- An interaction between the two that wouldn't reproduce with either
  one in isolation on a different OS/kernel.

Filing here first given the `signal: hangup` symptom, but flagging
this uncertainty explicitly in case it's better suited to (or also
worth filing against) Please's own issue tracker.

## Workaround in use

Since failures are racy rather than deterministic, retrying the same
command (fresh shell process per attempt, not a tight in-process loop)
recovers within a handful of attempts most of the time. We've wrapped
this in a small retry script (`scripts/plz-retry.sh` in our repo:
https://github.com/socitt/terminal-projects) that retries a
`plz`/`pleasew` invocation up to 5 times before reporting failure —
happy to share it if useful for reproducing this.
