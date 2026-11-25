# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #36: decisions follow the handbook's three levels.

Only a "decide and flag" choice gets the "Decided:" comment and the `decided`
label; a plain "decide" gets neither, and escalating means the hard stops.
CLAUDE.md, /next, the batch builder's prompt and the public workflow page say
the same, and point to the handbook instead of restating its table. Reads the
files only.

    scripts/test.sh unit tests.test_decision_levels
"""
import os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMENT = "Decided: <what>. Why: <one line>. To change it, reply on this issue."


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


CLAUDE = read("CLAUDE.md")
NEXT = read(".claude", "commands", "next.md")
DECIDE_OR_BLOCK = NEXT[NEXT.index("## Decide or block"):NEXT.index("**Hard stops**")]
DOCS = read("docs", "how-this-repo-is-built.md")


class ThreeLevels(unittest.TestCase):
    def test_claude_md_points_to_the_handbook_and_keeps_the_format_and_label(self):
        line = next(l for l in CLAUDE.splitlines() if "three levels" in l)
        self.assertIn('decisions skill, "Three levels"', line)
        self.assertIn('Only a "decide and flag" choice gets', line)
        self.assertIn(COMMENT, line)
        self.assertIn("the `decided` label", line)
        self.assertIn('a plain "decide" gets neither', line)

    def test_claude_md_does_not_repeat_the_handbook_table(self):
        for words in ("code structure", "test cases", "equivalent approaches", "a default the spec didn't give"):
            with self.subTest(words=words):
                self.assertNotIn(words, CLAUDE)

    def test_decide_or_block_names_the_three_levels(self):
        self.assertIn('decisions skill, "Three levels"', DECIDE_OR_BLOCK)
        for level in ("- **Decide** (", "- **Decide and flag** (", "- **Escalate**: the hard stops"):
            with self.subTest(level=level):
                self.assertIn(level, DECIDE_OR_BLOCK)

    def test_a_plain_decision_gets_no_comment_or_label(self):
        decide = DECIDE_OR_BLOCK[DECIDE_OR_BLOCK.index("- **Decide** ("):DECIDE_OR_BLOCK.index("- **Decide and flag**")]
        self.assertIn("No comment and no label", decide)
        self.assertNotIn("scripts/board.sh label", decide)

    def test_only_the_flagged_level_comments_and_labels(self):
        flag = DECIDE_OR_BLOCK[DECIDE_OR_BLOCK.index("- **Decide and flag**"):DECIDE_OR_BLOCK.index("- **Escalate**")]
        self.assertIn("These, and only these", flag)
        self.assertIn(COMMENT, flag)
        self.assertIn("`scripts/board.sh label N add decided`", flag)
        self.assertEqual(DECIDE_OR_BLOCK.count("label N add decided"), 1)

    def test_the_rest_of_next_md_says_the_same(self):
        self.assertIn('with the comment and the `decided` label only when it is a "decide and flag" one', NEXT)
        self.assertIn('only a "decide and flag" choice gets the comment "Decided: ..." and the decided label', NEXT)
        self.assertNotIn('(comment "Decided: ...", add the decided label)', NEXT)
        self.assertIn("one line per flagged decision you made on this round", NEXT)
        self.assertIn("each flagged decision made without asking", NEXT)
        self.assertIn("one line per flagged decision made without asking", NEXT)

    def test_the_public_page_says_the_same(self):
        self.assertIn("three levels of the Enamelware handbook", DOCS)
        self.assertIn("are simply made", DOCS)
        self.assertNotIn("so the designer can review all of them together", DOCS)

    def test_no_agent_labels_every_decision(self):
        agents = os.path.join(ROOT, ".claude", "agents")
        for name in sorted(os.listdir(agents)):
            text = read(".claude", "agents", name)
            with self.subTest(agent=name):
                self.assertIsNone(re.search(r"every (choice|decision)[^.\n]*decided", text, re.I))


if __name__ == "__main__":
    unittest.main()
