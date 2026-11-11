# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #2: the responsive rule. The agreed wording is in CLAUDE.md (Hard
rules) and DESIGN.md Part 2, replacing "Layouts must work at 16:10 and 4:3";
the style guide's Rules section shows it; DECISIONS.md records the rule and
the owner's answers; the two agreed sentences on the Overview page follow it.

That the style guide was rebuilt from DESIGN.md is also checked by
tools/check_guide.py (scripts/test.sh). These tests read the files directly.

    scripts/test.sh unit tests.test_responsive_rule
"""
import html
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def section(text, heading):
    """The body of the markdown section that starts with `heading`."""
    m = re.search(r"^" + re.escape(heading) + r"[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        raise AssertionError(f"no section {heading!r}")
    return m.group(1)


CLAUDE_RULE = ("- No layout is tied to a screen size, a device or an aspect ratio. Layouts adapt to the "
               "space they are given, and breakpoints come from the content and are named by what they "
               "do. Devices are for testing, never targets. No file names a capture size or a device as the "
               "source of a value.")

DESIGN_RULES = [
    "No layout is tied to a screen size, a device or an aspect ratio. Nothing in tokens, components, "
    "examples or docs names one as a layout target.",
    "Layouts adapt to the space they are given: relative units, min(), max() and clamp(), intrinsic "
    "sizing, wrapping, and container queries, so a component responds to its own box rather than to "
    "the whole screen.",
    "Breakpoints, where needed, come from the content and are named by what they do (\"panels stack "
    "when they cannot both fit at their minimum width\"), never by a device.",
    "Devices are for testing, never targets.",
]

OLD_RULE = re.compile(r"16:10 and (?:at )?4:3")


class ClaudeMd(unittest.TestCase):
    def test_hard_rules_hold_the_agreed_rule(self):
        rules = section(read("CLAUDE.md"), "## Hard rules")
        lines = [l for l in rules.splitlines() if l.startswith("- ")]
        self.assertIn(CLAUDE_RULE, lines, "CLAUDE.md Hard rules: the responsive rule is missing or reworded")

    def test_rule_is_only_in_hard_rules(self):
        self.assertEqual(read("CLAUDE.md").count("No layout is tied to a screen size"), 1)


class DesignMd(unittest.TestCase):
    def test_part_2_holds_the_agreed_rules(self):
        rules = section(read("DESIGN.md"), "## Part 2: Rules")
        lines = [l[2:] for l in rules.splitlines() if l.startswith("- ")]
        for rule in DESIGN_RULES:
            self.assertIn(rule, lines, f"DESIGN.md Part 2 is missing: {rule[:50]}...")

    def test_old_aspect_ratio_rule_is_gone(self):
        self.assertIsNone(OLD_RULE.search(read("DESIGN.md")), "DESIGN.md still has the 16:10 and 4:3 rule")


class StyleGuideRules(unittest.TestCase):
    def test_token_reference_shows_the_rules(self):
        page = html.unescape(re.sub(r"<[^>]+>", "", read("docs", "index.html")))
        page = " ".join(page.split())
        for rule in DESIGN_RULES:
            self.assertIn(" ".join(rule.replace("`", "").split()), page,
                          f"style guide Rules section is missing: {rule[:50]}...")
        self.assertIsNone(OLD_RULE.search(page), "style guide still shows the 16:10 and 4:3 rule")


class Decisions(unittest.TestCase):
    def test_entry_records_rule_and_answers(self):
        text = read("DECISIONS.md")
        m = re.search(r"^## [^\n]*the responsive rule[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "DECISIONS.md has no entry for the responsive rule")
        body = m.group(1)
        self.assertIn("No layout is tied to a screen size, a device or an aspect ratio.", body)
        self.assertIn('replaces the rule "Layouts must work at 16:10 and 4:3."', body)
        self.assertIn("#2", body)
        # the five answers the rest of the series builds on
        for needle in ("rem", "100rem", "160rem",                     # text and spacing sizes
                       "gets taller",                                  # action bar
                       "20rem wide by 15rem tall",                     # smallest supported box
                       "Sources name no device",                       # where values come from (#19)
                       "The new check (#6) covers",                    # what the check covers
                       "Overview page"):                               # hand-written page
            self.assertIn(needle, body, f"DECISIONS.md entry does not record: {needle}")
        self.assertIn("no version bump", body)
        # it is newer than every entry before it (later issues add entries above it)
        older = re.search(r"^## [^\n]*toast fades out in place", text, re.M)
        self.assertIsNotNone(older, "DECISIONS.md has lost the 0.5.1 toast entry")
        self.assertLess(m.start(), older.start(), "the responsive rule entry is not above the older entries")


class OverviewSentences(unittest.TestCase):
    text = read("docs", "overview.html")

    def test_rule_sentence(self):
        rules = re.search(r'<ul class="rules">(.*?)</ul>', self.text, re.S).group(1)
        items = re.findall(r"<li>(.*?)</li>", rules)
        self.assertIn("Layouts adapt to the space they are given, never to a screen size, a device or an "
                      "aspect ratio.", items)
        self.assertIsNone(OLD_RULE.search(self.text), "Overview page still has the 16:10 and 4:3 rule")

    def test_measurements_sentence_names_no_device(self):
        space = re.search(r'<section class="part" id="space">(.*?)</section>', self.text, re.S).group(1)
        self.assertIn("<p>A small set of measurements.</p>", space)
        self.assertNotIn("Steam Deck", space)


if __name__ == "__main__":
    unittest.main()
