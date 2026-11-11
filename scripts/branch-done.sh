#!/usr/bin/env bash
# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
#
# Deletes a finished issue-N branch, locally and on GitHub, but only when
# main (as pushed to GitHub) already holds exactly the same files.
#
#   scripts/branch-done.sh N
#
# /next squashes each branch into one commit on main, so git's own safe
# delete (`git branch -d`) never sees it as merged. This is the safe check
# instead; `git branch -D` itself still asks for approval.

set -euo pipefail
cd "$(dirname "$0")/.."

fail() { echo "branch-done.sh: $*" >&2; exit 2; }

[ "$#" -eq 1 ] && [[ "$1" =~ ^[0-9]+$ ]] || fail "usage: scripts/branch-done.sh N"
branch="issue-$1"

git fetch --quiet origin
[ "$(git rev-list --count origin/main..main)" -eq 0 ] || fail "main has commits not on GitHub yet; push main first"

if git rev-parse --verify --quiet "refs/heads/$branch" >/dev/null; then
    git diff --quiet origin/main "$branch" || fail "$branch differs from main; not deleting"
    [ "$(git branch --show-current)" != "$branch" ] || git switch --quiet main
    git branch -D "$branch"
else
    echo "$branch: no local branch"
fi

if git rev-parse --verify --quiet "refs/remotes/origin/$branch" >/dev/null; then
    git diff --quiet origin/main "origin/$branch" || fail "origin/$branch differs from main; not deleting"
    git push --quiet origin --delete "$branch"
    echo "$branch: deleted on GitHub"
else
    echo "$branch: not on GitHub"
fi
