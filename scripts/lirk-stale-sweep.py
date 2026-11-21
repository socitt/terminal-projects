#!/usr/bin/env python3
"""Hunt for stale-PASS edges: deps a test really has that lirk can't see.

lirk's import check only follows `import` statements. This repo also
loads code by file path (`importlib`, in furminal/runner.py) and runs
scripts as subprocesses from tests, and an undeclared edge of that kind
leaves a test `cached` and green after the code it runs has changed.

Method, against a throwaway copy of the repo (the working tree is never
touched):

1. warm the cache with `lirk test //...` (must be all green);
2. for each `library` src in any BUILD.lirk, prepend a top-level
   `raise`, run `lirk test //...`, and force-rerun every test that
   stayed `cached`;
3. any of those that FAIL is a stale edge: `src -> test`.

Exit 0 if no stale edges, 1 if any, 2 if the cache won't warm.
Takes ~1 minute here; much longer on-device. Needs `lirk` importable
(`pip install lirk`, or PYTHONPATH pointing at a lirk checkout).

    python3 scripts/lirk-stale-sweep.py [repo root, default: this repo]

Limitation: a raise at import time only exposes edges whose code is
*loaded* by the test. A file read as data (open/read_text) won't fail
that way; declare those under `data` by hand.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", "*.pyc", ".lirk-cache.json", "plz-out", "save.json"
)
CACHED_TEST = re.compile(r"^\s+cached\s+(//\S+)\s*$", re.M)
FAILED = re.compile(r"^\s+FAIL\s+(//\S+)", re.M)


def lirk(root, *args):
    return subprocess.run(
        [sys.executable, "-m", "lirk", *args],
        cwd=root, capture_output=True, text=True,
    )


def test_labels(root):
    labels = set()
    for build in root.rglob("BUILD.lirk"):
        pkg = build.parent.relative_to(root).as_posix()
        for t in tomllib.loads(build.read_text()).get("target", []):
            if t["type"] == "test":
                labels.add(f"//{pkg}:{t['name']}")
    return labels


def library_srcs(root):
    for build in sorted(root.rglob("BUILD.lirk")):
        for t in tomllib.loads(build.read_text()).get("target", []):
            if t["type"] == "library":
                yield from (build.parent / s for s in t["srcs"])


def sweep(root):
    tests = test_labels(root)
    warm = lirk(root, "test", "//...")
    if warm.returncode != 0:
        print(warm.stdout + warm.stderr)
        print("lirk-stale-sweep: `lirk test //...` is not green; fix that first")
        return 2

    stale = {}
    for src in library_srcs(root):
        rel = src.relative_to(root).as_posix()
        original = src.read_text()
        src.write_text("raise RuntimeError('lirk-stale-sweep')\n" + original)
        try:
            out = lirk(root, "test", "//...").stdout
            cached = [c for c in CACHED_TEST.findall(out) if c in tests]
            bad = []
            if cached:
                bad = FAILED.findall(lirk(root, "test", "--force", *cached).stdout)
            if bad:
                stale[rel] = bad
            print(f"  {rel}: {len(cached)} test(s) stayed cached,"
                  f" {len(bad)} stale", flush=True)
        finally:
            src.write_text(original)
            lirk(root, "test", "//...")  # re-warm what the break invalidated

    if not stale:
        print("lirk-stale-sweep: no stale edges")
        return 0
    print("lirk-stale-sweep: STALE EDGES (declare these in BUILD.lirk):")
    for rel, bad in stale.items():
        print(f"  {rel} -> {', '.join(bad)}")
    return 1


def main():
    src_root = Path(sys.argv[1] if len(sys.argv) > 1 else
                    Path(__file__).resolve().parent.parent).resolve()
    with tempfile.TemporaryDirectory(prefix="lirk-sweep-") as tmp:
        root = Path(tmp) / "repo"
        shutil.copytree(src_root, root, ignore=IGNORE)
        return sweep(root)


if __name__ == "__main__":
    sys.exit(main())
