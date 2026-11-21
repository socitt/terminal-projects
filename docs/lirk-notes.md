# lirk notes: terminal-projects against lirk 1.0.1

Hand-off to the `lirk` repo, in the same shape as termrery's and
slingshot's `docs/lirk-notes.md`. Written 2026-11-21, after re-running
this repo — lirk's first and largest consumer, 66 targets — against
lirk 1.0.1 (`53fab38`). Everything before this was against 0.x; none of
the v1.x features (environment fingerprinting, `verify`, `fix`, `init`,
timings) had been used here.

Every finding below was reproduced on a throwaway copy before being
written down. Fixes on this side are on branch
`claude/terminal-lirk-hardening-bd85zc`.

## Summary

| # | Finding | Severity | Side | Status |
|---|---|---|---|---|
| 1 | Stale PASS: an edge loaded by file path (`importlib`) is invisible to the import check | High | both | fixed here; closed in lirk 1.1.0 |
| 2 | Tests deleted the player's real save, and failed when one existed | Medium | here | fixed |
| 3 | No `.lirk-root`, so running from a package dir broke the graph | Low | here | fixed |
| — | Everything else checked out — see "What held up" | — | — | — |

## 1. Stale PASS through a file-path load (high)

**What happened.** `furminal/runner.py` loads region-explorer's
`runner.py` and `data/washington.py` with
`importlib.util.spec_from_file_location` — it has to, because its own
module is also called `runner` and `region-explorer` isn't an
importable package name. `//furminal:runner` didn't declare either
edge, and lirk's import check (H1/H2) only follows `import` statements,
so nothing flagged it.

Result, on an unmodified checkout of `9786a9b`: break
`region-explorer/runner.py`'s `select_region`, run `lirk test //...`,
and `//furminal:main_test` reports `cached` and green. `--force` fails
it 4/4. The same holds for `region-explorer/engine.py` and
`data/washington.py`.

**This was live from Phase B (2026-07-30) until now**, across the v1.0
tag. TASKS.md criterion 2 records "zero cache-correctness bugs" on real
repos and the H1 rollout measured "terminal-projects, 66 targets, zero
false positives"; both were accurate about *imports*, but this repo had
a stale-PASS path the whole time that no import-based check could see.

**What caught it.** `lirk verify` reports it correctly, including the
hint about undeclared inputs:

```
  STALE  //furminal:main_test (tests): cached as passing, fails when re-run: 1 of 1 src files failed: main_test
lirk: an input these targets depend on is not in their fingerprint -- often a file read at runtime but not declared in `data`
```

So the safety net works — but only when someone runs it, and the
default path (`lirk test`) gives the wrong green.

**Fixed here** by declaring `//region-explorer:runner` and
`//region-explorer/data:washington` on `//furminal:runner` (`44d53d4`).

**How it was found.**
`scripts/lirk-stale-sweep.py` (`36822be`, since removed in favour of
`lirk verify --mutate`) did it systematically: in a
throwaway copy, for each `library` src, prepend a top-level `raise`,
run `lirk test //...`, and `--force` every test that stayed `cached`.
A FAIL there is a stale edge. On the pre-fix commit it exits 1 naming
exactly the three edges above; on the fixed tree it exits 0. ~1 minute
here for 34 library srcs.

**Suggestions for lirk** (not implemented — lirk's call):

- **A build note for file-path loads.** When a src calls
  `importlib.util.spec_from_file_location`, `runpy.run_path`,
  `importlib.machinery.SourceFileLoader`, or mutates `sys.path` with a
  computed path, say that its deps can't be checked. Cheap: the AST is
  already parsed for the import check. Would have flagged
  `furminal/runner.py` on day one. (`sys.path.insert` is common here —
  every `main.py` does it — so that one may be too noisy; the three
  loader calls are not.)
- **The sweep as a lirk mode** (e.g. `lirk verify --mutate`). `verify`
  can only find a stale result after the inputs have *already* changed;
  a mutation sweep finds the missing edge before anyone edits
  anything. It's the one check that covers every way of reaching code
  — imports, file-path loads, subprocesses — without lirk having to
  understand any of them.
- **Criterion 2's record** should probably note this, in the same
  honest register as the self-hosting and termrery stale-PASS entries.

## 2. Tests deleted the player's real save (medium)

`furminal`, `dungeon` and `train-mystery` each had a `main_test.py`
that ran the real `main.py` against the real `save.json` next to it,
and unlinked it in `setUp`/`tearDown`. Verified on a copy with a save
in each:

- `lirk test //...` **deleted all three saves** — a player's
  in-progress game, gone without a word;
- and the two story tests **failed** while a save existed (the resume
  prompt shifted the scripted input), then passed on the next run once
  the first run had deleted the file. An order-dependent result that no
  fingerprint covers.

Fixed here (`c330f15`, `e1d4510`, `ee76ff9`): each `main.py` honours a
`TP_SAVE_PATH` override (default unchanged), each `main_test.py` points
it at a per-module temp dir. With real saves present: 32/32 green, all
three saves intact, no temp dirs left behind. Mutation-checked: with
the override ignored, all three tests fail.

**For lirk**, this is outside DESIGN §1's scope (no sandboxing, by
design) and isn't a lirk bug. If it's ever wanted, the cheap version is
a post-run note when a test target created or deleted files under its
own package directory — a before/after listing, no sandbox. It would
have caught this.

## 3. No `.lirk-root` (low)

This repo predates `lirk init` and never had a marker, so
`cd furminal && lirk test //...` treated `furminal/` as the root and
failed with `//:runner: dependency '//shared:term' does not exist`.
Added one (`8ebe0bb`); subdirectory runs now resolve the real root and
share the top-level cache. Not a lirk gap: lirk prints the "no
.lirk-root found" note, the docs cover it, and `lirk init` writes the
marker for new repos.

## What held up

- **Build/test:** 66/66 built, 32/32 tests, unchanged from 0.x.
- **Stability:** 10 consecutive `--force` runs of the whole suite, then
  3 more with the CPU oversubscribed 2×: 13/13 green. The timing-
  sensitive subprocess tests (region-explorer's runner_test, noted as
  "flaky under load" in its own source) held.
- **Python versions:** 32/32 on 3.11, 3.12 (the device's version) and
  3.13.
- **R1, environment fingerprinting:** switching interpreter reruns all
  32 tests rather than reusing another interpreter's green; staying on
  one keeps all 32 cached. (One cache slot per target, so switching
  back reruns again — expected.)
- **`verify`:** 98 cached results verified, 0 stale on the fixed tree;
  correctly reported finding 1 on the broken one.
- **`fix`:** no-op (0 deps added) — correct, since every *import* edge
  was already declared.
- **`init`, from zero BUILD files:** drafted 13 files / 25 targets with
  no hand fixes, and that graph went 12/12 green. Coarser than the
  hand-written graph (one library + one test per package, so wider
  invalidation), and it misses finding 1's edge for the same reason
  the import check does — but as a starting point for a repo this size
  it works out of the box.
- **Undeclared `.py` files:** only `scripts/lirk-stale-sweep.py` and
  the Please-era `tools/plz_test_runner/runner.py`, both tooling that
  no target imports.

## Update: lirk 1.1.0 (2026-11-21)

Both lirk-side suggestions from finding 1 shipped in v1.1.0
(`e09c6fd`), and TASKS.md's criterion 2 now carries a correction for
the broken zero-cache-bug record. Checked here against both commits:

- **Build note:** `lirk build` flags `furminal/runner.py`'s
  `spec_from_file_location`. It shows on the fixed tree too, as
  intended (a declared load looks the same).
- **`lirk verify --mutate`:** on `9786a9b` (pre-fix) it reports exactly
  the three edges and exits 1 (984 test runs, ~2 min here); on this
  branch, 0 edges, exit 0. It replaces `scripts/lirk-stale-sweep.py`,
  which has been deleted.
- 66/66 build, 32/32 test on 1.1.0.

**Still open on the lirk side** (requests sent back, see below):

1. **`--mutate` is far too slow for the device.** It isn't incremental:
   every run breaks every library src and reruns every test that
   doesn't claim the edge. 984 runs here at ~2 min; on iSH, where one
   test subprocess is ~2-4s, that's plausibly 30-60 min. Ask: remember
   which (src, test) pairs were checked against which fingerprints and
   skip them next time, or a `--changed` scope that only breaks srcs
   edited since the last clean run.
2. **The subdirectory error still doesn't point at the cause.** Without
   `.lirk-root`, from `furminal/`: `//:runner: dependency
   '//shared:term' does not exist`. The "no .lirk-root found" note is
   printed separately, two lines up. Ask: when a dep is missing *and*
   no marker was found, say so in the error itself ("no .lirk-root, so
   the root is furminal/; run from the repo root or add one").
3. **Tests that write into the source tree (finding 2).** Still
   undetected. Ask (optional, fits DESIGN §1): after a test target
   runs, note any file created or deleted under its package directory
   (a before/after listing; no sandbox). That would have caught the
   save-file deletion here, and it's the data-file blind spot
   `--mutate` documents.
4. **A way to quiet a checked note.** Minor: the file-path note fires
   on every rebuild of `//furminal:runner` even though its deps are now
   right. Something like recording that `--mutate` last passed for the
   target would let the note go quiet until the src changes.

## Round 3: stress test with new shapes (2026-11-21, lirk 1.1.0)

Rounds 1–2 kept finding bugs only when the repo had a *new shape*, not
from more invocations. So this round added two sub-projects chosen for
the lirk features this repo had never used, then probed each one:

- **Nemo** (`nemo/`, plus `nemo_adapter.py` in every board game): a
  computer opponent for all five games. Gives the repo nested packages
  (`nemo` → `nemo.search`, `nemo.cam`), an ancestor `__init__.py`
  that matters, and wide fan-in (13 tests downstream of one file).
- **furminal Phase C**: tuning moved into `furminal/data/*.json`, read
  at runtime and declared as `data`, the first in this repo.

The graph went from 66 targets / 32 tests to **85 / 41**, all green;
full `lirk test //...` from a cold cache takes 11s here.

### Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| R3-1 | Stale `.pyc` gives a wrong PASS that `test`, `--force` and `verify` all confirm | **High** | open, lirk |
| R3-2 | L7 hit on a natural shape, and `verify --mutate` can't see it | Medium | open, lirk |
| R3-3 | `verify --mutate` cost grows fast and prints no progress | Medium | open, lirk |
| R3-4 | `--fail-fast` summary counts unrun tests as not passed | Low | open, lirk |
| R3-5 | Raid tests hard-coded numbers that live in a data table | — | fixed here |

### R3-1: a stale `.pyc` makes lirk report and cache a wrong PASS (high)

lirk runs test subprocesses without `PYTHONDONTWRITEBYTECODE` or `-B`,
so Python writes and reads `__pycache__` in the repo as normal. Python
decides whether a `.pyc` is current by the source's **mtime (whole
seconds) and size**, not its content. lirk decides whether to rerun by
content hash. When the two disagree, lirk reruns the test against old
bytecode and caches the result under the new fingerprint.

Repro (scratch repo, one library and one test):

1. `lib.py` is `LIMIT = 1`; the test asserts `LIMIT == 1`.
   `lirk test //...`: PASS, and `__pycache__/lib.*.pyc` is written.
2. Rewrite `lib.py` as `LIMIT = 2` (same size) and keep its mtime
   (`touch -d @<old mtime>`). That's what `tar`, `cp -p`, `rsync -t` and
   unzip do, and what any two same-size edits within one second do.
3. `lirk test //...` sees the new fingerprint and reruns: **PASS**.
   `--force`: **PASS**. `lirk verify`: **0 stale**.
4. Delete `__pycache__` and rerun: **FAIL**, the true answer.

So the wrong result is cached as if it were fresh, and both ways to
double-check it agree with it. This is the same "green you can't
believe" class as H1/H2, and worse, because no declaration fixes it.

It was found by accident: Nemo's mutation testing changed `if wins:` to
`if False:`, which is the same length, within the same second as the
previous run, and the mutant "survived". It only failed once bytecode
writing was off.

**Suggested fix:** in `run_test`'s child environment, set
`PYTHONDONTWRITEBYTECODE=1` **and** point `PYTHONPYCACHEPREFIX` at an
empty lirk-owned directory. Both are needed: the first alone still
*reads* the repo's existing `__pycache__` (`-B` behaves the same, as I
found when my own "truth" check passed with `-B`). The cost is
recompiling imports on every run, which is small next to process
start-up. Bump `ACTION_VERSION`, since past greens may be stale.

### R3-2: L7 on a real shape, and `--mutate` can't see it (medium)

TASKS.md keeps L7 (an undeclared *ancestor* `__init__.py` is never
fingerprinted) open "until a real repo hits it". Nemo's layout is that
shape: `nemo/cam/avatar_test.py` only imports `nemo.cam`, so
`nemo/__init__.py` is reached only as an ancestor.

Seeded on a copy (the real BUILD files declare it correctly): leave
`nemo/__init__.py` undeclared and imported directly by nothing, run,
then break it. `//nemo/cam:avatar_test` stays **cached and green**;
`--force` fails it. `minimax_test` was caught only because it happens
to `import nemo` directly.

`lirk verify --mutate` reports **0 undeclared dependencies** on that
state. It only breaks *declared* sources, so an undeclared file is
never broken, and L7 can't be found by the tool meant to find hidden
edges. Either fix L7 (collect ancestor `__init__.py` files and require
them declared), or have `--mutate` also break the undeclared `.py`
files that declared imports reach.

### R3-3: `verify --mutate` cost and silence (medium)

| Graph | Sources broken | Test runs | Time here |
|---|---|---|---|
| Round 2: 66 targets | 34 | 984 | ~2 min |
| Round 3 Nemo checkpoint: 83 targets | 45 | 1,615 | **413 s** |

That's 25% more targets for 3.5× the time. Runs scale with sources ×
tests, and the new tests are subprocess-heavy. On iSH that's plausibly
hours, so the incremental mode asked for last round matters more now.
Separately, it prints its two header lines and then **nothing** for the
whole run. On a phone a seven-minute (or two-hour) silent command looks
hung. A one-line progress note per source would fix that.

The result itself was right: 0 undeclared edges on the new Nemo graph.

### R3-4: `--fail-fast` summary (low)

With `shared/term.py` broken, `--fail-fast` stopped after one test
(1s vs 4s) and said `78 target(s) not run`, then `lirk: 0/41 tests
passed`. 40 of those never ran. "0/1 run, 40 not run" would be
accurate.

### R3-5: fixed here

The data-file probe (a raid's size −2 → −3 in `border.json`) correctly
reran exactly `//furminal:tables`' five dependents, and `game_test`
went red. That was a bug in my tests, not lirk: they hard-coded −2, so
a pure rebalance (the whole point of the data layer) broke them. They
now read the size from the table.

### What held up

- **Nested packages:** `//nemo:nemo` → `//nemo/search:minimax` →
  `//nemo/cam:avatar` built and tested cleanly. Dropping minimax's dep
  on `//nemo:nemo` was caught by H1 with a precise message.
- **`lirk fix` on a real change:** after adding `//furminal:tables`, it
  added exactly the two missing deps (`camp` → `:tables`,
  `tables_test` → `:cats`), `--dry-run` first, nothing else touched.
- **`data` directories:** a declared JSON edit reran exactly the five
  dependents. An undeclared one gave a cached PASS that `--mutate`
  missed beforehand and plain `verify` caught afterwards, exactly as
  documented.
- **Fan-in:** one comment in `nemo/__init__.py` reran exactly the 13
  tests downstream of it.
- **v1.1 features:** cache pruning dropped a renamed target's old entry;
  `timeout = 1` in `.lirk-root` timed out exactly the three tests
  slower than 1s; the file-path build note still flags
  `furminal/runner.py`.
