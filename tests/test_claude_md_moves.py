# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #34: CLAUDE.md holds only what every Enamel session needs.

The rules it no longer holds moved to the file that uses them, word for word
where it matters: how commands are run, permission rules, removing files,
memory notes and closing issues into /next; the reviewer's tidy-ups and the
resume rule were already there. CLAUDE.md keeps Enamel's own additions to the
handbook and points to the rest. Reads the files only.

    scripts/test.sh unit tests.test_claude_md_moves
"""
import os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def section(text, heading):
    m = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


CLAUDE = read("CLAUDE.md")
NEXT = read(".claude", "commands", "next.md")
STEP1 = NEXT[NEXT.index("1. **Board and tests.**"):NEXT.index("2. **Pick the issue.**")]


class MovedIntoNext(unittest.TestCase):
    def test_how_commands_are_run(self):
        for words in ("no `&&`, `;` or pipes", "to filter output, do it in a separate step or with the built-in tools",
                      "without `git -C`", "`scripts/peek.sh` (log, show, status, diff, tag, rev-parse, ls-files)",
                      "written into its own instructions"):
            with self.subTest(words=words):
                self.assertIn(words, STEP1)

    def test_permission_rules(self):
        self.assertIn("A new ask or deny rule must never catch a read-only command.", STEP1)
        self.assertIn("narrow any existing ask rule that catches one", STEP1)
        self.assertIn("`tests/test_agent_guard.py`", STEP1)

    def test_removing_files(self):
        self.assertIn("`git rm` on a file git tracks inside this repo needs no approval", STEP1)
        self.assertIn("`git clean`, and anything that deletes untracked files still ask first", STEP1)

    def test_memory_notes(self):
        self.assertIn("use `scripts/forget-note.sh`", STEP1)
        self.assertIn("never `rm`", STEP1)

    def test_issues_are_closed_only_by_the_housekeeping(self):
        step0 = NEXT[NEXT.index("## 0. Housekeeping"):NEXT.index("## Steps")]
        self.assertIn("Issues are closed only by this housekeeping, never otherwise.", step0)

    def test_no_interactive_prompt_and_the_time_limit(self):
        self.assertIn("never use the interactive question prompt", NEXT)
        self.assertIn("**Time limit:** if one problem takes more than about 30 minutes", NEXT)

    def test_resume_and_tidy_ups_were_already_there(self):
        self.assertIn("**Re-run the checking agents only if the code changed since they last passed**", NEXT)
        reviewer = read(".claude", "agents", "reviewer.md")
        self.assertIn("**Tidy-ups never fail a review.**", reviewer)
        self.assertIn("**Fail only for real problems**", reviewer)

    def test_every_agent_has_the_command_rules(self):
        for name in ("reviewer", "test-checker", "test-writer", "refactor-scout"):
            text = read(".claude", "agents", name + ".md")
            with self.subTest(agent=name):
                self.assertIn("never chain commands with `&&`, `;` or pipes", text)
                self.assertIn("without `git -C`", text)
                self.assertIn("`scripts/peek.sh`", text)


class ClaudeMdKeeps(unittest.TestCase):
    def test_its_sections(self):
        headings = re.findall(r"^## (.+)$", CLAUDE, re.M)
        self.assertEqual(headings, ["Who uses this", "How the work is done", "Hard rules", "Public writing",
                                    "Reports to the designer"])

    def test_enamel_s_additions_to_the_sizes(self):
        line = next(l for l in CLAUDE.splitlines() if l.startswith("- **Sizes**"))
        for words in ("handbook's operations skill", "a screen is a component or a style guide page",
                      "tokens, the style guide launcher and `tools/serve.py`",
                      "the ones the build scripts write", "`series: <name>` label"):
            with self.subTest(words=words):
                self.assertIn(words, line)

    def test_the_decided_comment_and_label(self):
        work = section(CLAUDE, "How the work is done")
        self.assertIn('"Decided: <what>. Why: <one line>. To change it, reply on this issue."', work)
        self.assertIn("the `decided` label", work)
        self.assertIn("Design system changes are expected", work)
        self.assertIn("Never hardcode a size a token provides", work)

    def test_the_board_and_checks_scripts(self):
        work = section(CLAUDE, "How the work is done")
        self.assertIn("Board changes only through `scripts/board.sh`", work)
        self.assertIn("Checks only through `scripts/test.sh`, in two modes", work)
        self.assertIn("`scripts/test.sh full` runs everything", work)

    def test_the_failed_phrase_is_a_rule_of_its_own(self):
        lines = [l for l in CLAUDE.splitlines() if '"#N failed: <what happened>"' in l]
        self.assertEqual(len(lines), 1)
        self.assertNotIn("close", lines[0])
        self.assertIn("moves it to More to do, without starting the fix", lines[0])

    def test_public_writing_points_to_the_handbook(self):
        rule = section(CLAUDE, "Public writing")
        self.assertIn("product skill (principle 7)", rule)
        self.assertIn("the hard stop on private details", rule)
        self.assertIn("MIGRATION.md", rule)

    def test_rules_now_kept_elsewhere_are_gone(self):
        for words in ("&&", "git rm", "forget-note", "close-done", "annotated tag", "Install nothing",
                      "No layout is tied to a screen size", "30 minutes", "interactive question prompt",
                      "Columns:", "Problem, Why it matters"):
            with self.subTest(words=words):
                self.assertNotIn(words, CLAUDE)


if __name__ == "__main__":
    unittest.main()
