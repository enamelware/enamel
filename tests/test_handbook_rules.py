# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #28: where CLAUDE.md and the handbook disagreed, Enamel follows the handbook.

    scripts/test.sh unit tests.test_handbook_rules
"""
import os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = ("CLAUDE.md",)
NEXT = (".claude", "commands", "next.md")
DRAFT = (".claude", "commands", "draft.md")
REVIEWER = (".claude", "agents", "reviewer.md")
VISITORS = ("docs", "how-this-repo-is-built.md")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def line_with(text, needle):
    return next(line for line in text.splitlines() if needle in line)


class HardStops(unittest.TestCase):
    def test_every_list_of_hard_stops_points_to_the_handbook(self):
        for rel in (CLAUDE, NEXT, DRAFT, REVIEWER):
            with self.subTest(rel=rel):
                self.assertRegex(read(*rel), r"handbook's[^.]*decisions skill")

    def test_a_spec_read_two_ways_that_looks_different_is_a_stop(self):
        for rel in (CLAUDE, NEXT, REVIEWER):
            with self.subTest(rel=rel):
                self.assertRegex(read(*rel), r"read two ways[^.]*look different to the user")

    def test_enamel_keeps_its_own_additions(self):
        stops = {
            "CLAUDE.md": line_with(read(*CLAUDE), "Hard stops, the only reasons to stop"),
            "next.md": read(*NEXT).split("**Hard stops**", 1)[1].split("**Not stops:**", 1)[0],
        }
        for where, text in stops.items():
            for words in ("Valve", "outside the repo", "git revert can't undo", "contradicting each other"):
                with self.subTest(where=where, words=words):
                    self.assertIn(words, text)


class Questions(unittest.TestCase):
    def test_a_blocked_question_has_numbered_options_and_a_recommendation(self):
        self.assertIn("numbered options and a recommendation", line_with(read(*CLAUDE), "Hard stops, the only reasons to stop"))
        nxt = read(*NEXT)
        self.assertIn("one plain-language question, with numbered options and a recommendation", nxt)
        self.assertIn("at most 3 numbered options, your recommendation", nxt)


class SizeSLimits(unittest.TestCase):
    def test_data_formats_and_the_settings_format_make_an_s_an_m(self):
        places = {
            "CLAUDE.md S": line_with(read(*CLAUDE), "`size:S`:"),
            "CLAUDE.md upgrades": line_with(read(*CLAUDE), "**Upgrades are automatic.**"),
            "next.md": line_with(read(*NEXT), "**Upgrades, automatic.**"),
            "visitors": line_with(read(*VISITORS), "| S |"),
        }
        for where, line in places.items():
            for words in ("data formats", "settings format"):
                with self.subTest(where=where, words=words):
                    self.assertIn(words, line)


if __name__ == "__main__":
    unittest.main()
