#!/usr/bin/env bash
# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
#
# Reads the other Kettle repo (Kettle Video) without changing it, so a
# single narrow permission rule covers it and `git -C` can keep asking.
#
#   scripts/peek.sh log|show|status|diff|tag|rev-parse|ls-files [ARGS...]
#
# The other repo is found next to this one: the folder kettle-video, or
# media-player, its name before 2026-10-28. Only the read-only git commands
# above are run, never a pager. `tag` always lists (git refuses to create
# or delete a tag while listing), any argument that writes a file
# (--output) is refused, and `status` takes no lock on the index.

set -euo pipefail

fail() { echo "peek.sh: $*" >&2; exit 2; }

[ "$#" -ge 1 ] || fail "usage: scripts/peek.sh log|show|status|diff|tag|rev-parse|ls-files [ARGS...]"
cmd="$1"
shift

case "$cmd" in
    log|show|status|diff|tag|rev-parse|ls-files) ;;
    *) fail "only log, show, status, diff, tag, rev-parse and ls-files are allowed, not: $cmd" ;;
esac

for arg in "$@"; do
    case "$arg" in
        --output|--output=*) fail "writing a file is not allowed: $arg" ;;
    esac
done

here="$(cd "$(dirname "$0")/.." && pwd -P)"
other=""
for name in kettle-video media-player; do
    if [ -d "$(dirname "$here")/$name/.git" ]; then
        other="$(dirname "$here")/$name"
        break
    fi
done
[ -n "$other" ] || fail "no kettle-video (or media-player) repo next to $here"

if [ "$cmd" = tag ]; then
    set -- --list "$@"
fi
GIT_OPTIONAL_LOCKS=0 exec git --no-pager -C "$other" "$cmd" "$@"
