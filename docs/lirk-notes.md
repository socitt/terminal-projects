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
| 1 | Stale PASS: an edge loaded by file path (`importlib`) is invisible to the import check | High | both | fixed here; lirk gap open |
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

**How it was found, and a standing check.**
`scripts/lirk-stale-sweep.py` (`36822be`) does it systematically: in a
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
