# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #31: the commands, agents and CLAUDE.md follow the handbook's size table.
Since #34, CLAUDE.md only points to the handbook and keeps Enamel's additions; since
#37, next.md no longer repeats the limits either, and points to the handbook for them.

    scripts/test.sh unit tests.test_size_rules
"""
import os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOT_COUNTED = ("tests", "DECISIONS.md", "CHANGELOG.md", "VERSION", "regenerate")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def line_with(text, needle):
    return next(line for line in text.splitlines() if needle in line)


class WhatCountsTowardsAnS(unittest.TestCase):
    def test_next_leaves_the_limits_to_the_handbook(self):
        """#37: next.md no longer repeats the limits, so it can't leave out a different list."""
        line = line_with(read(".claude", "commands", "next.md"), "**Upgrades, automatic.**")
        self.assertIn('the handbook\'s (its operations skill, "Sizes"', line)
        for word in NOT_COUNTED:
            with self.subTest(word=word):
                self.assertNotIn(word, line)

    def test_claude_md_says_which_files_are_regenerated(self):
        line = line_with(read("CLAUDE.md"), "**Sizes**")
        self.assertIn("regenerated files are the ones the build scripts write", line)

    def test_a_new_component_or_page_makes_an_s_an_m(self):
        self.assertIn("a screen is a component or a style guide page", line_with(read("CLAUDE.md"), "**Sizes**"))

    def test_the_sizes_point_to_the_handbook(self):
        for rel in (("CLAUDE.md",), (".claude", "commands", "next.md"), (".claude", "commands", "draft.md")):
            with self.subTest(rel=rel):
                self.assertIn("handbook's operations skill", read(*rel))


class TheFullCheckRunsOnce(unittest.TestCase):
    def test_test_checker_never_runs_it(self):
        text = read(".claude", "agents", "test-checker.md")
        runs = [line for line in text.splitlines() if "test.sh full" in line]
        self.assertEqual(len(runs), 1, runs)
        self.assertIn("Never run the full check", runs[0])
        self.assertNotRegex(text.split("\n---", 2)[1], r"runs the quick suite \(and the full check")

    def test_next_runs_it_once_in_step_9(self):
        text = read(".claude", "commands", "next.md")
        step6 = text[text.index("**Version and changelog.**"):text.index("8. **Independent checks**")]
        step9 = text[text.index("9. **Merge into main**"):text.index("10. **Move to Ready for testing**")]
        self.assertNotIn("run `scripts/test.sh full`", step6)
        self.assertIn("the full check runs once, in step 9", step6)
        self.assertIn("**The full check**, on a `size:L` issue or when the change bumps `VERSION`", step9)
        self.assertIn("run `scripts/test.sh full` once", step9)
        # It runs before the squash merge, on the branch's final code.
        self.assertLess(step9.index("**The full check**"), step9.index("git merge --squash issue-N"))

    def test_next_says_when_it_runs(self):
        """#34: moved from CLAUDE.md; next.md's size table and the release check say the same."""
        text = read(".claude", "commands", "next.md")
        self.assertIn("`scripts/test.sh full` once, run by you before merging", line_with(text, "| L |"))
        self.assertIn("The full check also runs before any `VERSION` bump", text)
        self.assertIn("Every issue runs quick before it is merged; quick aims to finish in under 2 minutes", text)
        release = text[text.index("**Release check**"):text.index("**Idle work**")]
        self.assertIn("if anything was merged", release)
        self.assertIn("no `VERSION` may be bumped until full passes again", release)


class SeriesFollowUps(unittest.TestCase):
    def test_a_series_review_follow_up_goes_straight_to_ready_for_dev(self):
        text = read(".claude", "commands", "next.md")
        fail = line_with(text, "**FAIL:** file one small follow-up issue in the same series")
        self.assertIn('scripts/board.sh status F "Ready for dev"', fail)

    def test_a_series_with_an_l_gets_the_full_check(self):
        text = read(".claude", "commands", "next.md")
        series = text[text.index("### Series"):text.index("## Safe to interrupt")]
        self.assertIn("**A series that holds a `size:L` issue** also gets the full check", series)


class BatchRuns(unittest.TestCase):
    def test_a_failed_full_check_goes_back_through_the_checks(self):
        text = read(".claude", "commands", "next.md")
        step4 = line_with(text, "4. **All PASS**: send the builder the final verdicts")
        self.assertIn("FULL CHECK FAILED: #N title", step4)
        self.assertIn("run the path's agents again", step4)


if __name__ == "__main__":
    unittest.main()
