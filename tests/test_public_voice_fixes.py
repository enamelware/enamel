# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #26, fixes from the "public voice" series review (#23, #24):

- CLAUDE.md's "Public writing" section states that instructions addressed to
  Claude Code, in CLAUDE.md and `.claude/`, may speak to it as "you";
- the Button description on the Components page is reworded, in its build
  script and on the generated page;
- the README says the release check allows a noreply address while the
  public-text check catches the commit form of it, with no contradiction;
- DECISIONS.md says, under #24, that the known list is empty and what the
  settings exception covers.

    scripts/test.sh unit tests.test_public_voice_fixes
"""
import os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def section(text, heading):
    return text.split(heading + "\n", 1)[1].split("\n## ", 1)[0]


class PublicVoiceFixes(unittest.TestCase):
    def test_claude_md_states_the_exception_for_instructions(self):
        rule = section(read("CLAUDE.md"), "## Public writing")
        self.assertIn('Never "I", "we", "you"', rule)
        self.assertIn('Instructions addressed to Claude Code, in CLAUDE.md and `.claude/`, may speak to it as "you".',
                      rule)

    def test_button_description_is_reworded(self):
        old = "Something pressed to do an action."
        new = "Something to press for an action. The primary button is the main action on a screen."
        for rel in ("tools/components_page.py", "docs/components.html"):
            with self.subTest(rel=rel):
                text = read(rel)
                self.assertIn(new, text)
                self.assertNotIn(old, text)

    def test_readme_release_check_line_reads_without_contradiction(self):
        line = next(l for l in read("README.md").splitlines() if "`release_check.py`" in l)
        self.assertNotIn("other than the GitHub noreply address", line)
        self.assertNotIn("commit email addresses", line)
        self.assertIn("it allows a GitHub noreply address", line)
        self.assertIn("the commit form of that noreply address", line)

    def test_decisions_says_the_known_list_is_empty(self):
        decisions = read("DECISIONS.md")
        heading = next(l for l in decisions.splitlines() if l.startswith("## ") and l.endswith("(#24)"))
        entry = section(decisions, heading)
        self.assertIn("The known list is empty.", entry)
        self.assertIn("covers only the deny rules for the secret folders", entry)
        self.assertLess(decisions.index(heading), decisions.index("(#23)"),
                        "the #24 entry is newer, so it comes first")


if __name__ == "__main__":
    unittest.main()
