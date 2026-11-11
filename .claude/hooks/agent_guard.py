#!/usr/bin/env python3
# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT

"""Keep the project agents inside their lanes.

Claude Code runs this before each tool call of the agents in
.claude/agents/ (see the hooks in each .md file). It reads the tool call as
JSON on stdin and exits with 2 to refuse it; the message on stderr goes back
to the agent.

  reviewer        Bash: read-only git and gh issue view, running the tests,
                  and committing its own tidy-ups on an issue branch
                  (git add <files>, git commit -m "WIP issue-N: ...").
                  Write/Edit: tests/, tools/, scripts/, the workflow's
                  commands and agents, and the hand-written docs; never
                  tokens/, components/ or docs/.
  test-checker    Bash: the same, plus running the tests (scripts/test.sh).
                  Write/Edit: only files inside tests/.
  test-writer     Bash: the same as test-checker, plus gh issue list.
                  Write/Edit: only tests/, README.md and DESIGN.md.
  refactor-scout  Bash: read-only git, gh issue view and gh issue list.
                  No file writes: /tidy files its proposals as issues.

Read-only git is an allow-list: `git status|diff|log|show` with only the
options in SAFE_GIT_OPTIONS. Anything else, such as `--output=<file>`
(writes a file) or `--ext-diff` (runs another program), is refused. Every
agent may read Kettle Video the same way through scripts/peek.sh (also
`tag`, `rev-parse` and `ls-files` there); `git -C` is never allowed.

Copied from Kettle Video's guard, with Enamel's write areas. What it
can and can't enforce is in DECISIONS.md (2026-10-14, delivery workflow).

Usage: agent_guard.py reviewer|test-checker|test-writer|refactor-scout
"""

import json
import os
import re
import shlex
import subprocess
import sys

GIT_SUBCOMMANDS = {"status", "diff", "log", "show"}

# What scripts/peek.sh may run in the other Kettle repo, with the same options.
PEEK_SUBCOMMANDS = GIT_SUBCOMMANDS | {"tag", "rev-parse", "ls-files"}

# Options that only change what git prints. Exact spellings only: git also
# accepts abbreviations (`--out` for `--output`), so nothing is matched by
# prefix.
SAFE_GIT_FLAGS = {
    "-p", "-u", "-n", "--patch", "-s", "--no-patch", "-w", "-b", "-z", "-M",
    "--stat", "--shortstat", "--numstat", "--summary", "--name-only",
    "--name-status", "--cached", "--staged", "--no-ext-diff", "--no-color",
    "--ignore-all-space", "--ignore-space-change", "--word-diff",
    "--find-renames", "--oneline", "--graph", "--decorate", "--all",
    "--reverse", "--follow", "--first-parent", "--merges", "--no-merges",
    "--abbrev-commit", "--short", "--branch", "--porcelain", "--long",
    "--ignored", "--full-diff", "--source",
}

# Options that take a value after "=" (for example --format=%h).
SAFE_GIT_VALUE_OPTIONS = {
    "--format", "--pretty", "--unified", "--max-count", "--since",
    "--until", "--after", "--before", "--author", "--grep",
    "--diff-filter", "--untracked-files", "--stat", "--color", "--date",
    "--decorate", "--word-diff", "--find-renames", "--abbrev",
}

# Short options with a number glued on: -3, -n5, -U10.
SAFE_GIT_NUMBERED = re.compile(r"-(\d+|n\d+|U\d+)")

# Fields agents may ask `gh issue view N --json` for.
SAFE_ISSUE_FIELDS = {"title", "body", "comments", "labels", "state"}

# What `gh issue list` may filter on and print (test-writer and
# refactor-scout check open issues for overlap and duplicates).
SAFE_LIST_FIELDS = {"number", "title", "body", "labels", "state"}
SAFE_LIST_STATES = {"open", "closed", "all"}
LABEL_NAME = re.compile(r"[A-Za-z0-9:_.-]+")

RUN_TESTS = [
    # scripts/test.sh checks its own arguments (only tests/ modules and checks).
    r"scripts/test\.sh( (quick|full|--again|unit|check|checks|guide|all)( [\w.-]+)*)?",
    r"python3 -m unittest( .*)?",
    r"python3 -m tests\.\w+( .*)?",
    r"python3 tests/\w+\.py( .*)?",
]

ROLES = ("reviewer", "test-checker", "test-writer", "refactor-scout")

# Who may run the tests, list issues, and write where.
RUNS_TESTS = {"reviewer", "test-checker", "test-writer"}
LISTS_ISSUES = {"test-writer", "refactor-scout"}
WRITE_AREAS = {
    "test-checker": ("tests",),
    "test-writer": ("tests", "README.md", "DESIGN.md"),
    "reviewer": ("tests", "tools", "scripts", ".claude/commands", ".claude/agents",
                 "README.md", "CHANGELOG.md", "DECISIONS.md", "DESIGN.md"),
}

# Who may commit, and only work-in-progress commits on an issue branch.
COMMITS = {"reviewer"}
WIP_MESSAGE = re.compile(r"WIP issue-\d+: [^\n]+")

# Anything that could chain a second command or redirect output.
SHELL_TRICKS = re.compile(r"[;&|<>`\n]|\$\(")

# Anything the shell could expand into a different word, smuggling in an
# option the checks below never saw: variables, braces, wildcards, escapes.
SHELL_EXPANSION = re.compile(r"[$\\{}*?\[\]]")


def refuse(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def git_option_ok(word):
    if word in SAFE_GIT_FLAGS or SAFE_GIT_NUMBERED.fullmatch(word):
        return True
    name, equals, _ = word.partition("=")
    return bool(equals) and name in SAFE_GIT_VALUE_OPTIONS


def read_only_git_ok(words, subcommands=GIT_SUBCOMMANDS):
    if len(words) < 2 or words[0] != "git" or words[1] not in subcommands:
        return False
    for word in words[2:]:
        if word == "--":
            return True  # everything after "--" is a file path, not an option
        if word.startswith("-") and not git_option_ok(word):
            return False
    return True


def peek_ok(words):
    if not words or words[0] != "scripts/peek.sh":
        return False
    return read_only_git_ok(["git", *words[1:]], PEEK_SUBCOMMANDS)


def issue_view_ok(words):
    if words[:3] != ["gh", "issue", "view"] or len(words) < 4:
        return False
    if not words[3].isdigit():
        return False
    rest = words[4:]
    if rest in ([], ["--comments"]):
        return True
    if len(rest) == 2 and rest[0] == "--json":
        fields = rest[1].split(",")
        return all(f in SAFE_ISSUE_FIELDS for f in fields)
    return False


def issue_list_ok(words):
    if words[:3] != ["gh", "issue", "list"]:
        return False
    rest = words[3:]
    if len(rest) % 2:
        return False  # every option takes exactly one value
    for option, value in zip(rest[::2], rest[1::2]):
        if option == "--json":
            if not all(f in SAFE_LIST_FIELDS for f in value.split(",")):
                return False
        elif option == "--state":
            if value not in SAFE_LIST_STATES:
                return False
        elif option == "--label":
            if not LABEL_NAME.fullmatch(value):
                return False
        elif option == "--limit":
            if not value.isdigit():
                return False
        else:
            return False
    return True


def current_branch(project):
    try:
        out = subprocess.run(["git", "branch", "--show-current"], cwd=project,
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip()


def commit_ok(role, words, project):
    """git add <files in the write areas>, or git commit -m "WIP issue-N: ...",
    only on an issue-N branch."""
    if role not in COMMITS or words[:1] != ["git"] or len(words) < 3:
        return False
    if not re.fullmatch(r"issue-\d+", current_branch(project)):
        return False
    if words[1] == "add":
        paths = words[2:]
        if any(p.startswith("-") for p in paths):
            return False
        for path in paths:
            check_write(role, path, project)  # refuses anything outside the areas
        return True
    if words[1] == "commit":
        return len(words) == 4 and words[2] == "-m" and bool(WIP_MESSAGE.fullmatch(words[3]))
    return False


def check_bash(role, command, project="."):
    command = command.strip()
    if SHELL_TRICKS.search(command):
        refuse(f"{role}: one plain command at a time, no ; && | > or $(...).")
    if SHELL_EXPANSION.search(command):
        refuse(f"{role}: no $ variables, braces, wildcards or backslashes.")
    if role in RUNS_TESTS and any(re.fullmatch(p, command) for p in RUN_TESTS):
        return
    try:
        words = shlex.split(command)
    except ValueError:
        refuse(f"{role}: could not read this command: {command}")
    if read_only_git_ok(words) or peek_ok(words) or issue_view_ok(words):
        return
    if role in LISTS_ISSUES and issue_list_ok(words):
        return
    if commit_ok(role, words, project):
        return
    refuse(
        f"{role}: command not allowed: {command}\n"
        "Allowed: git status|diff|log|show with plain display options (from "
        "this repo's folder, never git -C), scripts/peek.sh for Kettle Video, "
        "and gh issue view N [--comments | --json body,comments]."
    )


def check_write(role, path, project):
    areas = WRITE_AREAS.get(role)
    if not areas:
        refuse(f"{role}: read-only, no file changes.")
    target = os.path.realpath(os.path.join(project, path)) if path else ""
    for area in areas:
        allowed = os.path.realpath(os.path.join(project, area))
        if target and os.path.commonpath([allowed, target]) == allowed:
            return
    where = ", ".join(a if "." in a else a + "/" for a in areas)
    refuse(f"{role}: may only write in {where}, not {path}")


def main():
    role = sys.argv[1] if len(sys.argv) > 1 else ""
    if role not in ROLES:
        refuse(f"agent_guard: unknown role {role!r}")
    call = json.load(sys.stdin)
    tool = call.get("tool_name", "")
    args = call.get("tool_input", {}) or {}
    project = os.environ.get("CLAUDE_PROJECT_DIR") or call.get("cwd") or "."
    if tool == "Bash":
        check_bash(role, args.get("command", ""), project)
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = args.get("file_path") or args.get("notebook_path") or ""
        check_write(role, path, project)


if __name__ == "__main__":
    main()
