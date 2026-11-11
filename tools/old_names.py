# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Find the design system's old names left in the repo (#12, #13).

The system was renamed to Enamel: its names moved from the "kt" prefix to
"en", its main files took the new name, and the old product name (in both its
spellings, see OLD) went too. No file may still use an old name or be called by one,
except:
  - history: entries in DECISIONS.md or CHANGELOG.md dated before the rename;
  - MIGRATION.md, and tools/build_migration.py, which holds the rename's rules;
  - Kettle Video's own folder for its copy (vendor/ plus the old product
    name), which keeps its name until Kettle Video's switch issue.
"Kettle" alone stays: Kettle Video, the Kettle board and the Kettle wordmark.

The old names are built from parts here, so this file doesn't use them.
Used by check_guide.py and tests/test_old_prefix.py. Standard library only.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KT, KETTLE = "k" + "t", "kett" + "le"
RENAMED_ON = "2026-10-27"
HISTORY = ("DECISIONS.md", "CHANGELOG.md")
RECORD = ("MIGRATION.md", "tools/build_migration.py")
SKIP_DIRS = {".git", "__pycache__"}

OLD = re.compile("|".join([
    rf"(?<![A-Za-z0-9_-])(?:--|data-)?{KT}-",       # tokens, classes, state attributes, events
    rf"__{KT}[A-Z]",                                 # element properties set by the script
    rf"\b{KETTLE.capitalize()}UI\b",                 # the script's global
    rf"\b{KETTLE}(?:\.css|-components|_tokens)\b",   # the main files and the tokens module
    rf"(?<!vendor/)\b{KETTLE}-ui\b",                 # the old product name, except Kettle Video's folder
    rf"\b{KETTLE} UI\b",
]), re.I)

# An entry heading in either history file: "## 0.6.0, 2026-10-21 (visual)" or
# "## 2026-10-21, a release is ...". The date is the entry's date.
DATED = re.compile(r"^## (?:\d+\.\d+\.\d+, )?(\d{4}-\d{2}-\d{2})\b")


def mentions(text):
    """Line numbers that use an old name."""
    return [n for n, line in enumerate(text.splitlines(), 1) if OLD.search(line)]


def allowed_lines(text):
    """Lines of a history file that sit in an entry dated before the rename."""
    allowed, date = set(), None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            m = DATED.match(line)
            date = m.group(1) if m else None
        if date and date < RENAMED_ON:
            allowed.add(n)
    return allowed


def problems(rel, text):
    """'path line N' for each old name outside the allowed places."""
    if rel in RECORD:
        return []
    found = mentions(text)
    if rel in HISTORY:
        found = [n for n in found if n not in allowed_lines(text)]
    return [f"{rel} line {n}" for n in found]


def repo_files():
    """Every file in the repo folder, as a path relative to it."""
    for top, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield os.path.relpath(os.path.join(top, name), ROOT)


def read_text(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def scan():
    """(files read, problems) for the whole repo, file names included."""
    found, count = [], 0
    for rel in sorted(repo_files()):
        if OLD.search(rel):
            found.append(f"{rel} (file name)")
        text = read_text(rel)
        if text is not None:
            count += 1
            found += problems(rel, text)
    return count, found
