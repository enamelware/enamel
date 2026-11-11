#!/usr/bin/env bash
# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
#
# The one way to run Enamel's automated checks, so a single narrow
# permission rule covers them (see CLAUDE.md, "How we work").
#
#   scripts/test.sh [quick] [--again]  the quick suite, run on every issue: the
#                                    unit tests in tests/, then
#                                    tools/check_guide.py --quick (tokens parse,
#                                    generated pages and DESIGN.md up to date,
#                                    colours and sizes only from tokens, every
#                                    component state shown, contrast, accents,
#                                    motion, and the device's Firefox on the
#                                    style guide pages the change touches, in
#                                    full and reduced motion)
#   scripts/test.sh full [--again]   everything, run before any VERSION bump and
#                                    at the end of /next all: the unit tests,
#                                    the complete style guide check in the
#                                    device's Firefox (every page, four motion
#                                    modes, the frame checks, a larger font),
#                                    then every tests/*_check.py
#   scripts/test.sh unit MODULE...   only these modules, e.g. tests.test_generated
#   scripts/test.sh check NAME       one slower check: tests/NAME.py
#   scripts/test.sh checks           every tests/*_check.py, one after another
#   scripts/test.sh guide            only the complete style guide check
#   scripts/test.sh all              the same as full
#
# A pass of quick or full is remembered against the exact code (the commit's
# file tree, only when nothing is uncommitted), in git's own folder, never in
# the repo. Running the same mode again on the same code says it already
# passed instead of running again; a full pass also counts for quick.
# --again runs it anyway. Nothing here changes a file in the repo. Exits
# non-zero if anything failed.

set -u
cd "$(dirname "$0")/.." || exit 1

RESULTS="$(git rev-parse --git-common-dir)/enamel-test-results"

# The exact code, or nothing if anything is uncommitted (then nothing is reused).
code_key() {
    [ -z "$(git status --porcelain)" ] || return 0
    git rev-parse 'HEAD^{tree}'
}

# Says so and succeeds if one of the named modes already passed on this code.
already_passed() {
    local key="$1" mode
    shift
    [ -n "$key" ] || return 1
    for mode in "$@"; do
        if [ -f "$RESULTS/$mode-$key" ]; then
            echo "Already passed on this exact code: $(cat "$RESULTS/$mode-$key")"
            echo "Not run again. scripts/test.sh $1 --again runs it anyway."
            return 0
        fi
    done
    return 1
}

remember() {
    local mode="$1" key="$2"
    [ -n "$key" ] || return 0
    mkdir -p "$RESULTS"
    echo "scripts/test.sh $mode, $(date '+%Y-%m-%d %H:%M'), commit $(git rev-parse --short HEAD)" > "$RESULTS/$mode-$key"
}

unit() {
    if [ "$#" -eq 0 ]; then
        python3 -m unittest discover -s tests -t .
        return
    fi
    for module in "$@"; do
        if ! [[ "$module" =~ ^tests\.[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$ ]]; then
            echo "test.sh: not a test module: $module" >&2
            return 2
        fi
    done
    python3 -m unittest "$@"
}

check() {
    local name="$1"
    if ! [[ "$name" =~ ^[a-z0-9_]+$ ]] || [[ "$name" == test_* ]] || [ ! -f "tests/$name.py" ]; then
        echo "test.sh: no check named $name in tests/" >&2
        return 2
    fi
    python3 "tests/$name.py"
}

checks() {
    local failed=0 file
    for file in tests/*_check.py; do
        [ -e "$file" ] || continue
        echo "== $file"
        check "$(basename "$file" .py)" || failed=1
    done
    return "$failed"
}

# quick or full, with the result remembered; $2 is empty or --again.
run_mode() {
    local mode="$1" again="${2:-}" key status=0
    if [ -n "$again" ] && [ "$again" != "--again" ]; then
        echo "usage: scripts/test.sh $mode [--again]" >&2
        return 2
    fi
    key="$(code_key)"
    if [ -z "$again" ]; then
        if [ "$mode" = quick ]; then
            already_passed "$key" quick full && return 0
        else
            already_passed "$key" full && return 0
        fi
    fi
    unit || status=1
    if [ "$mode" = quick ]; then
        python3 tools/check_guide.py --quick || status=1
    else
        python3 tools/check_guide.py || status=1
        checks || status=1
    fi
    # Only remember a pass if the code didn't change while the checks ran.
    if [ "$status" -eq 0 ] && [ "$key" = "$(code_key)" ]; then
        remember "$mode" "$key"
    fi
    return "$status"
}

case "${1:-}" in
    ""|--again) run_mode quick "${1:-}" ;;
    quick) run_mode quick "${2:-}" ;;
    full|all) run_mode full "${2:-}" ;;
    unit) shift; unit "$@" ;;
    check)
        if [ "$#" -ne 2 ]; then echo "usage: scripts/test.sh check NAME" >&2; exit 2; fi
        check "$2" ;;
    checks) checks ;;
    guide) python3 tools/check_guide.py ;;
    *)
        echo "usage: scripts/test.sh [quick | full] [--again] | unit MODULE... | check NAME | checks | guide" >&2
        exit 2 ;;
esac
