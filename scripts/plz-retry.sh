#!/bin/sh
# Retry wrapper for `plz`/`pleasew` invocations.
#
# iSH-AOK's process emulation intermittently fails Please build actions
# with `signal: hangup` (racy, not deterministic — see
# docs/KNOWN_ISSUES.md). Retrying the same command in a fresh subshell
# recovers most of the time, so route plz build/test calls through this
# instead of calling ./pleasew directly.
#
# Usage:
#   scripts/plz-retry.sh test //shared:term_test
#   scripts/plz-retry.sh build //shared:term
#
# Only reports failure once every attempt has been exhausted.

set -u

MAX_ATTEMPTS=5
SLEEP_SECS=2

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
PLEASEW="${REPO_ROOT}/pleasew"

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <plz args...>" >&2
    exit 2
fi

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
    ( cd "$REPO_ROOT" && sh -c 'cmd="$1"; shift; exec "$cmd" "$@"' _ "$PLEASEW" "$@" )
    rc=$?
    if [ "$rc" -eq 0 ]; then
        exit 0
    fi
    echo "plz-retry: attempt ${attempt}/${MAX_ATTEMPTS} failed (rc=${rc})" >&2
    if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
        sleep "$SLEEP_SECS"
    fi
    attempt=$((attempt + 1))
done

echo "plz-retry: all ${MAX_ATTEMPTS} attempts failed, giving up" >&2
exit 1
