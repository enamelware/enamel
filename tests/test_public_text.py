# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #23: the public-writing rule and its check.

The public-text check in tools/release_check.py (run by tools/check_guide.py
in the quick checks) reads every file that would be published. These tests
plant each kind of finding in a throwaway git folder and see it caught, see
that ordinary Enamel text and the public repo's own address pass, see that
the few explained exceptions hold only where they are listed, see that a
finding beyond the known list fails while the known ones (cleared by #24)
do not, and see that CLAUDE.md, the reviewer, /draft and the README carry
the rule. Planted values are built from parts, so this file passes the
check itself.

    scripts/test.sh unit tests.test_public_text
"""
import contextlib, io, os, re, sys, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import release_check as rc  # noqa: E402
import check_guide as cg  # noqa: E402
from tests.test_release_rules import Folder  # noqa: E402

AT = "@"
HOME = "~" + "/"
THE_OWNER = "the " + "own" + "er"
PLANTED = [
    (rc.HOME_PATH, "Kettle Video lives at " + HOME + "Development/kettle-video."),
    (rc.HOME_PATH, "cp tokens/enamel.css " + HOME + "Videos/"),
    (rc.OWNER_WORDING, "Chosen by " + THE_OWNER + " on #9."),
    (rc.OWNER_WORDING, "The " + "Own" + "er's answers."),
    ("the old account name", "https://github.com/" + rc.OLD_ACCOUNT + "/enamel"),
    ("the old account name", "Owned by " + rc.OLD_ACCOUNT.capitalize() + "."),
    ("a commit email address", "335260252+" + rc.ACCOUNT + AT + "users.noreply.github.com"),
    ("a claude.ai link", "See https://" + "claude" + ".ai/" + "chat/0123abcd for the brief."),
    ("a claude.ai link", "the canvas at " + "claude" + ".ai/" + "design/x"),
    (rc.PRIVATE_REPO, "https://github.com/" + rc.ACCOUNT + "/media-player/issues/4"),
    (rc.PRIVATE_REPO, "git" + AT + "github.com:" + rc.ACCOUNT + "/enamel-archive.git"),
    (rc.PRIVATE_REPO, "its GitHub repo is still `" + rc.ACCOUNT + "/media-player`"),
    (rc.BOARD_LINK, "https://github.com/" + "users/" + rc.ACCOUNT + "/projects/1"),
]

NOT_FINDINGS = [
    "https://github.com/" + rc.ACCOUNT + "/enamel",                 # the public repo
    "https://github.com/" + rc.ACCOUNT + "/enamel/issues/7.",
    "git" + AT + "github.com:" + rc.ACCOUNT + "/enamel.git",
    '"repo": "' + rc.ACCOUNT + '/enamel"',
    '"' + "own" + 'er": "' + rc.ACCOUNT + '"',                       # a settings key, not the wording
    "Kettle Video copies Enamel's files into its vendor/enamel/ folder.",
    "The designer chose coral; Enamel uses it as the default accent.",
    "a~/b and https://example.org/~/",                               # not a home folder path
    "Claude Code is Anthropic's coding agent.",
    "--en-gap: 8px; /* var(--en-space-2) */",
]


def planted_findings(rel, line):
    with Folder() as d:
        d.write(rel, f"fine\n{line}\n")
        return rc.public_text(d.root, known={})[0]


class Planted(unittest.TestCase):
    def test_each_kind_is_caught(self):
        for what, line in PLANTED:
            for rel in ("README.md", "docs/how-this-repo-is-built.md", "CLAUDE.md", ".claude/commands/next.md"):
                with self.subTest(rel=rel, line=line):
                    found = planted_findings(rel, line)
                    self.assertTrue(any(f.startswith(f"{rel} line 2: {what} (") for f in found),
                                    f"{line!r} in {rel} was not caught as {what}: {found}")

    def test_every_kind_is_planted(self):
        kinds = {what for what, _ in rc.PUBLIC_TEXT} | {rc.PRIVATE_REPO}
        self.assertEqual(kinds, {what for what, _ in PLANTED})

    def test_ordinary_text_passes(self):
        for line in NOT_FINDINGS:
            with self.subTest(line=line):
                self.assertEqual(rc.public_text_findings("README.md", line), [])

    def test_ignored_files_are_not_read(self):
        with Folder() as d:
            d.write(".gitignore", "notes.md\n")
            d.write("notes.md", "Chosen by " + THE_OWNER + ".\n")
            self.assertEqual(rc.public_text(d.root, known={})[0], [])


class Exceptions(unittest.TestCase):
    def test_each_exception_holds_only_in_its_own_file(self):
        samples = {rc.HOME_PATH: '"Read(' + HOME + '.ssh/**)"',
                   rc.BOARD_LINK: '"projectUrl": "https://github.com/' + "users/" + rc.ACCOUNT + '/projects/1"'}
        self.assertEqual({what for _, what in rc.PUBLIC_TEXT_ALLOWED}, set(samples))
        for (rel, what), why in rc.PUBLIC_TEXT_ALLOWED.items():
            with self.subTest(rel=rel):
                self.assertGreater(len(why), 40, "each exception says why it is needed")
                self.assertEqual(planted_findings(rel, samples[what]), [])
                self.assertTrue(planted_findings("README.md", samples[what]), "the same text elsewhere is caught")

    def test_an_exception_covers_only_its_own_kind(self):
        found = planted_findings(".claude/settings.json", "Chosen by " + THE_OWNER + ".")
        self.assertTrue(any(rc.OWNER_WORDING in f for f in found))

    def test_the_exceptions_are_few_and_in_use(self):
        self.assertLessEqual(len(rc.PUBLIC_TEXT_ALLOWED), 3)
        for rel, what in rc.PUBLIC_TEXT_ALLOWED:
            with self.subTest(rel=rel):
                with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                    text = f.read()
                pattern = dict(rc.PUBLIC_TEXT)[what]
                self.assertTrue(pattern.search(text), f"{rel} no longer needs its exception")

    def test_the_tests_naming_the_old_account_pass(self):
        """The old-name test and this one name what is searched for only in parts."""
        for rel in ("tests/test_old_account_name.py", "tests/test_public_text.py", "tests/test_release_rules.py",
                    "tools/release_check.py"):
            with self.subTest(rel=rel), open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                self.assertEqual(rc.public_text_findings(rel, f.read()), [])


class KnownList(unittest.TestCase):
    def test_one_more_than_known_fails(self):
        with Folder() as d:
            d.write("DECISIONS.md", "Chosen by " + THE_OWNER + ".\nAsked " + THE_OWNER + ".\n")
            new, within, _ = rc.public_text(d.root, known={("DECISIONS.md", rc.OWNER_WORDING): 2})
            self.assertEqual(new, [])
            self.assertEqual(within, {("DECISIONS.md", rc.OWNER_WORDING): 2})
            new, within, _ = rc.public_text(d.root, known={("DECISIONS.md", rc.OWNER_WORDING): 1})
            self.assertEqual(len(new), 2, "every finding of that kind in that file is listed")
            self.assertEqual(within, {})

    def test_known_counts_hold_only_for_their_file_and_kind(self):
        with Folder() as d:
            d.write("README.md", "Chosen by " + THE_OWNER + ".\n")
            self.assertEqual(len(rc.public_text(d.root, known={("DECISIONS.md", rc.OWNER_WORDING): 5})[0]), 1)
            self.assertEqual(len(rc.public_text(d.root, known={("README.md", rc.HOME_PATH): 5})[0]), 1)

    def test_the_new_page_has_no_known_findings(self):
        self.assertFalse([key for key in rc.PUBLIC_TEXT_KNOWN if key[0] == "docs/how-this-repo-is-built.md"])


class TheRepo(unittest.TestCase):
    def test_the_repo_has_no_new_findings(self):
        new, within, count = rc.public_text()
        self.assertEqual(new, [], "new text breaks CLAUDE.md \"Public writing\"")
        self.assertGreater(count, 50)

    def test_it_reads_claude_md_and_the_workflow_files(self):
        files = set(rc.published_files())
        for rel in ("CLAUDE.md", ".claude/commands/next.md", ".claude/agents/reviewer.md", ".claude/settings.json",
                    "README.md", "docs/how-this-repo-is-built.md", "DECISIONS.md", "CHANGELOG.md"):
            self.assertIn(rel, files)


class GuideCheck(unittest.TestCase):
    """check_public_text as the quick checks run it."""
    def run_check(self, new, within):
        saved = list(cg.failures)
        del cg.failures[:]
        out = io.StringIO()
        try:
            with mock.patch.object(cg.release_check, "public_text", return_value=(new, within, 80)), \
                    contextlib.redirect_stdout(out):
                cg.check_public_text()
            return list(cg.failures), out.getvalue()
        finally:
            cg.failures[:] = saved

    def test_a_new_finding_fails(self):
        failures, _ = self.run_check(["README.md line 3: a claude.ai link ('x')"], {})
        self.assertEqual(len(failures), 1)
        self.assertIn("README.md line 3: a claude.ai link", failures[0])

    def test_known_findings_are_listed_not_failed(self):
        failures, out = self.run_check([], {("CLAUDE.md", rc.HOME_PATH): 4})
        self.assertEqual(failures, [])
        self.assertIn("CLAUDE.md: 4 x a home folder path", out)

    def test_it_runs_in_the_quick_checks(self):
        with open(os.path.join(ROOT, "tools", "check_guide.py"), encoding="utf-8") as f:
            main = f.read().split("def main():", 1)[1]
        self.assertIn("check_public_text()", main)
        self.assertLess(main.index("check_public_text()"), main.index("check_browser("))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


class TheRule(unittest.TestCase):
    def test_claude_md_has_the_section(self):
        rule = section(read("CLAUDE.md"), "Public writing")
        self.assertTrue(rule, "CLAUDE.md has no \"Public writing\" section")
        for words in ('"Enamel uses…"', '"Chosen because…"', '"I", "we", "you"', "Steam Deck (SteamOS)",
                      "Retroid Pocket Nova (Armada)", "Example content is always invented",
                      "Problem, Why it matters, Proposal, Done when", "Manual checks on the reference devices",
                      "Testing comments and reports", "Past commits are never rewritten",
                      "docs/how-this-repo-is-built.md", "tools/release_check.py", "The reviewer checks every change"):
            self.assertIn(words, rule)

    def test_the_reviewer_points_to_it(self):
        text = read(".claude/agents/reviewer.md")
        self.assertIn('**Public writing.**', text)
        self.assertIn('`CLAUDE.md` "Public writing"', text)

    def test_draft_writes_public_tickets(self):
        text = read(".claude/commands/draft.md")
        self.assertIn('CLAUDE.md "Public writing"', text)
        for heading in ("**Problem**", "**Why it matters**", "**Proposal**", "**Done when**",
                        "**Manual checks on the reference devices**"):
            self.assertIn(heading, text)

    def test_the_readme_links_the_page(self):
        self.assertIn("(docs/how-this-repo-is-built.md)", read("README.md"))

    def test_the_page_explains_the_workflow(self):
        page = read("docs/how-this-repo-is-built.md")
        for words in ("Claude Code", "designer", "The board itself is private", "**Drafted**", "**Ready for dev**",
                      "**Building**", "**More to do**", "**Ready for testing**", "**Done**", "**/draft**",
                      "**/next**", "**/tidy**", "**reviewer**", "**test-checker**", "**test-writer**",
                      "**refactor-scout**", "| S |", "| M |", "| L |", "DECISIONS.md"):
            self.assertIn(words, page)

    def test_the_page_links_only_to_public_places(self):
        page = read("docs/how-this-repo-is-built.md")
        for link in re.findall(r"\]\(([^)]+)\)", page):
            with self.subTest(link=link):
                if link.startswith("http"):
                    self.assertTrue(link.startswith("https://www.anthropic.com/"), link)
                else:
                    self.assertTrue(os.path.exists(os.path.normpath(os.path.join(ROOT, "docs", link))), link)


if __name__ == "__main__":
    unittest.main()
