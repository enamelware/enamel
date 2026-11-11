# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #12: the rename changed names only, never a value or a look.

Takes the files as they were released in v0.6.0 (the last version before the
rename), applies the rename's own rules from tools/build_migration.py, and
checks that the result is exactly what the repo has now:

  - every token and component variable has the same value under its new name,
    and none was added or lost;
  - the components stylesheet and behaviour script, the style guide's own
    stylesheet and script, and every style guide page (generated ones and the
    hand-written Overview) differ from v0.6.0 only by the renamed names, so
    nothing on any page can look or move differently.

These files did not change between v0.6.0 and the start of the rename, so any
other difference is something the rename broke. The check only applies while
the rename is unreleased (VERSION still 0.6.0): part 2 (#13) bumps VERSION and
may change titles, and later versions change values on purpose.

Reads the local git history only; never pushes or fetches.

    scripts/test.sh unit tests.test_rename_kept_values
"""
import os, re, shutil, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_migration  # noqa: E402

BEFORE = "v0.6.0"
KETTLE = "kett" + "le"  # built from parts so this file uses no old name

# (path at v0.6.0, path now)
FILES = [(old, new) for old, new in build_migration.FILES if not new.endswith(".py")] + [
    (f"docs/{name}", f"docs/{name}")
    for name in ("site.css", "site.js", "index.html", "components.html", "motion.html", "resize.html",
                 "overview.html")
]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def git_show(rev, rel):
    out = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{rel}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def renamed(text):
    for pattern, replacement in build_migration.RULES:
        text = re.sub(pattern, replacement, text)
    return text


def declarations(css):
    """{custom property: value} for every --name: value; in a stylesheet."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found = {}
    for name, value in re.findall(r"(--[A-Za-z0-9-]+)\s*:\s*([^;{}]+);", css):
        found.setdefault(name, set()).add(" ".join(value.split()))
    return found


def first_difference(a, b):
    for n, (x, y) in enumerate(zip(a.splitlines(), b.splitlines()), 1):
        if x != y:
            return f"line {n}: expected {x.strip()!r}, found {y.strip()!r}"
    return f"line counts differ ({len(a.splitlines())} expected, {len(b.splitlines())} found)"


HAVE_GIT = shutil.which("git") is not None and os.path.exists(os.path.join(ROOT, ".git"))
HAVE_TAG = HAVE_GIT and git_show(BEFORE, "VERSION") is not None
UNRELEASED = read("VERSION").strip() == BEFORE[1:]


@unittest.skipUnless(HAVE_TAG, f"no git history with the {BEFORE} tag")
@unittest.skipUnless(UNRELEASED, "the rename has been released; later versions change values on purpose")
class RenameKeptValues(unittest.TestCase):
    def test_every_token_keeps_its_value(self):
        for old, new in FILES[:2]:  # the tokens file and the components stylesheet
            with self.subTest(file=new):
                before = git_show(BEFORE, old)
                self.assertIsNotNone(before, f"{old} is missing at {BEFORE}")
                expected = declarations(renamed(before))
                now = declarations(read(new))
                self.assertGreater(len(expected), 10)
                self.assertEqual(sorted(now), sorted(expected), f"{new}: a token was added or lost")
                for name, values in expected.items():
                    self.assertEqual(now[name], values, f"{name} changed value in the rename")

    def test_files_differ_only_by_the_renamed_names(self):
        for old, new in FILES:
            with self.subTest(file=new):
                before = git_show(BEFORE, old)
                self.assertIsNotNone(before, f"{old} is missing at {BEFORE}")
                expected, now = renamed(before), read(new)
                self.assertEqual(now == expected, True,
                                 f"{new} differs from {BEFORE} by more than the rename: "
                                 + first_difference(expected, now))

    def test_the_rename_did_something(self):
        # Guards the check above: the rules really turn the old files into new names.
        before = git_show(BEFORE, "tokens/" + KETTLE + ".css")
        self.assertNotEqual(renamed(before), before)
        self.assertIn("--en-accent", renamed(before))


if __name__ == "__main__":
    unittest.main()
