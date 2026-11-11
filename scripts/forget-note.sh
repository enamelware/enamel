#!/usr/bin/env bash
# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
#
# Deletes one of Claude Code's own memory notes for this project.
#
#   scripts/forget-note.sh NAME.md
#
# The memory folder is worked out the way Claude Code names it: the repo's
# full path with every character that isn't a letter or digit turned into
# "-", under $HOME/.claude/projects/, then memory/. So it works on any
# device without a rule naming one. Only a plain .md file name directly in
# that folder is accepted; MEMORY.md is the index and is edited, never
# deleted here. Everything else that deletes files still asks first.

set -euo pipefail

fail() { echo "forget-note.sh: $*" >&2; exit 2; }

[ "$#" -eq 1 ] || fail "usage: scripts/forget-note.sh NAME.md"
name="$1"

[[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*\.md$ ]] || fail "not a plain .md file name: $name"
[[ "$name" != *..* ]] || fail "not a plain .md file name: $name"
[ "$name" != "MEMORY.md" ] || fail "MEMORY.md is the index: edit it, don't delete it"

[ -n "${HOME:-}" ] || fail "HOME is not set"
repo="$(cd "$(dirname "$0")/.." && pwd -P)"
folder="$HOME/.claude/projects/$(printf '%s' "$repo" | sed 's/[^A-Za-z0-9]/-/g')/memory"

[ -d "$folder" ] || fail "no memory folder for this project at $folder"
note="$folder/$name"
[ -e "$note" ] || [ -L "$note" ] || fail "no such note: $name"
[ -f "$note" ] && [ ! -L "$note" ] || fail "not a plain file: $name"

rm -- "$note"
echo "deleted memory note: $name"
echo "remember to take its line out of MEMORY.md"
