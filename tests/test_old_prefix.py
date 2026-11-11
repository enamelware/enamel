# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issues #12 and #13: the old names are gone, and MIGRATION.md lists every one.

The design system's names moved from the "kt" prefix to "en", its main files
took the new name, and the old product name went too. tools/old_names.py
finds any old name left (check_guide.py runs it on every change) and says
where they may stay. MIGRATION.md is written by tools/build_migration.py from
the names the system has now, so it matches them all and rebuilding it
changes nothing.

The old names are built from parts here, so this file doesn't use them.

    scripts/test.sh unit tests.test_old_prefix
"""
import os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_migration  # noqa: E402
from old_names import (KT, KETTLE, RENAMED_ON, HISTORY, mentions, problems,  # noqa: E402
                       read_text, repo_files, scan)


class OldNamesGone(unittest.TestCase):
    def test_no_file_uses_an_old_name(self):
        count, found = scan()
        self.assertGreater(count, 50)
        self.assertEqual(found, [], "an old name is still used; MIGRATION.md has the new one")

    def test_the_main_files_have_the_new_names(self):
        files = set(repo_files())
        for old, new in build_migration.FILES:
            self.assertIn(new, files)
            self.assertNotIn(old, files)

    def test_old_names_are_caught(self):
        for sentence in (f"var(--{KT}-accent)", f'class="{KT}-row"', f".{KT}-tab:focus", f"[data-{KT}-motion]",
                         f'"{KT}-select"', f"el.__{KT}Turn", f"window.{KETTLE.capitalize()}UI",
                         f"tokens/{KETTLE}.css", f"components/{KETTLE}-components.js", f"import {KETTLE}_tokens",
                         f"# {KETTLE.capitalize()} UI", f"the {KETTLE}-ui repo", f"github.com/enamelware/{KETTLE}-ui.git",
                         f"{KETTLE.upper()} UI", f"for {KETTLE}-ui's checks"):
            for rel in ("README.md", "docs/overview.html", "components/enamel-components.js"):
                with self.subTest(rel=rel, sentence=sentence):
                    self.assertEqual(problems(rel, f"one\n{sentence}\nthree\n"), [f"{rel} line 2"])

    def test_kt_inside_other_words_and_the_new_names_pass(self):
        for text in ("Steam Deck Desktop", "--en-accent", "data-en-motion", ".en-row", "window.EnamelUI",
                     "tokens/enamel.css", "markt-x", f"{KETTLE.capitalize()} Video", f"the {KETTLE.capitalize()} board",
                     f"its `vendor/{KETTLE}-ui/` folder", f"<!-- {KETTLE}-progress -->"):
            self.assertEqual(mentions(text), [], text)

    def test_old_dated_entries_stay_but_new_ones_are_checked(self):
        for rel in HISTORY:
            with self.subTest(rel=rel):
                old = f"# Title\n\n## 0.6.0, 2026-10-21 (visual)\n\nUses --{KT}-accent.\n"
                self.assertEqual(problems(rel, old), [])
                new = f"# Title\n\n## 0.7.0, {RENAMED_ON} (breaking)\n\nUses --{KT}-accent.\n"
                self.assertEqual(problems(rel, new), [f"{rel} line 5"])
                top = f"# Title\n\nUses --{KT}-accent.\n\n## 2026-10-21, old\n"
                self.assertEqual(problems(rel, top), [f"{rel} line 3"])


class Migration(unittest.TestCase):
    def test_rebuilding_changes_nothing(self):
        self.assertEqual(read_text("MIGRATION.md"), build_migration.page(),
                         "MIGRATION.md is out of date: run python3 tools/build_migration.py")

    def test_every_new_name_is_listed_with_its_old_name(self):
        text = read_text("MIGRATION.md")
        css = read_text("tokens/enamel.css") + read_text("components/enamel-components.css")
        js = read_text("components/enamel-components.js")
        everything = css + js + "".join(read_text(f"docs/{p}") for p in ("index.html", "components.html"))
        word = r"[a-z0-9]+(?:-[a-z0-9]+)*(?![a-z0-9-])"  # a whole name, not the prefix alone in a comment
        new_names = (set(re.findall(rf"--en-{word}", css)) | set(re.findall(rf"data-en-{word}", css))
                     | set(re.findall(r'class="(en-[a-z0-9_-]+)', everything))
                     | set(re.findall(r"@keyframes (en-[a-z0-9-]+)", css))
                     | set(re.findall(r"\b(__en[A-Z]\w*)", js))
                     | {"EnamelUI", "en-select", "en-cancel"})
        self.assertGreater(len(new_names), 100)
        self.assertTrue(any(n.startswith("__en") for n in new_names), "the script's element properties were not found")
        for name in sorted(new_names - build_migration.ADDED):
            old = name.replace("EnamelUI", f"{KETTLE.capitalize()}UI")
            old = re.sub(r"^__en([A-Z])", rf"__{KT}\1", old)
            old = re.sub(r"^(--|data-)?en-", rf"\g<1>{KT}-", old)
            with self.subTest(name=name):
                self.assertIn(f"| `{old}` | `{name}` |", text)
        for old, new in build_migration.FILES:
            self.assertIn(f"| `{old}` | `{new}` |", text)

    def test_names_added_since_the_rename_are_left_out(self):
        """#15, #16: a name added after 0.7.0 (a token, a variable or a class) never had an old
        name, so MIGRATION.md doesn't list one."""
        text = read_text("MIGRATION.md")
        css = read_text("tokens/enamel.css") + read_text("components/enamel-components.css")
        self.assertTrue(build_migration.ADDED)
        for name in sorted(build_migration.ADDED):
            if name.startswith("--"):
                defined = re.escape(name) + r"\s*:"
            elif name.startswith("data-"):
                defined = r"\[" + re.escape(name) + r"[=\]]"
            else:
                defined = r"\." + re.escape(name) + r"(?![\w-])"
            with self.subTest(name=name):
                self.assertRegex(css, defined, f"{name} is listed as added but not defined")
                self.assertNotIn(f"`{name}`", text)

    def test_old_name_reverses_the_rules(self):
        for name in ("--en-c-toast-width", "data-en-accent", "en-picker__row", "__enTurn", "EnamelUI",
                     "components/enamel-components.css", "tools/enamel_tokens.py"):
            new = build_migration.old_name(name)
            for pattern, replacement in build_migration.RULES:
                new = re.sub(pattern, replacement, new)
            self.assertEqual(new, name)


if __name__ == "__main__":
    unittest.main()
