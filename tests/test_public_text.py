# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issues #23 and #24: the public-writing rule and its check.

The public-text check in tools/release_check.py (run by tools/check_guide.py
in the quick checks) reads every file that would be published. These tests
plant each kind of finding in a throwaway git folder and see it caught, see
that ordinary Enamel text and the public repo's own address pass, see that
the few explained exceptions hold only for the exact lines their reason
covers (#24 narrowed them), see that every finding fails now that the
rewrite in the project voice (#24) has cleared the old text, and see that
CLAUDE.md, the reviewer, /draft and the README carry the rule. Planted
values are built from parts, so this file passes the check itself.

    scripts/test.sh unit tests.test_public_text
"""
import contextlib, io, json, os, re, sys, unittest
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
        return rc.public_text(d.root)[0]


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
            self.assertEqual(rc.public_text(d.root)[0], [])


SETTINGS = {"permissions": {
    "allow": ["Read(./**)", "Bash(git log *)"],
    "deny": ["Bash(sudo *)", "Read(" + HOME + ".ssh/**)", "Edit(" + HOME + ".ssh/**)", "Read(" + HOME + ".config/gh/**)",
             "Read(" + HOME + ".claude/.credentials.json)", "Read(" + HOME + ".git-credentials)",
             "Read(" + HOME + ".netrc)", "Read(" + HOME + ".gnupg/**)"]}}
BOARD = {"owner": rc.ACCOUNT, "repo": rc.ACCOUNT + "/enamel", "projectNumber": 1,
         "projectUrl": "https://github.com/" + "users/" + rc.ACCOUNT + "/projects/1"}


def json_findings(rel, data):
    with Folder() as d:
        d.write(rel, json.dumps(data, indent=2) + "\n")
        return rc.public_text(d.root)[0]


class Exceptions(unittest.TestCase):
    def test_each_exception_says_why(self):
        self.assertEqual(set(rc.PUBLIC_TEXT_ALLOWED), {(".claude/settings.json", rc.HOME_PATH),
                                                     (".claude/board.json", rc.BOARD_LINK)})
        for key, (why, lines) in rc.PUBLIC_TEXT_ALLOWED.items():
            with self.subTest(key=key):
                self.assertGreater(len(why), 40, "each exception says why it is needed")
                self.assertTrue(callable(lines))

    def test_the_secret_folder_deny_rules_pass(self):
        self.assertEqual(json_findings(".claude/settings.json", SETTINGS), [])

    def test_the_board_address_passes(self):
        self.assertEqual(json_findings(".claude/board.json", BOARD), [])

    def test_the_same_text_elsewhere_is_caught(self):
        for rel in ("README.md", ".claude/commands/next.md", ".claude/board.json", "docs/how-this-repo-is-built.md"):
            with self.subTest(rel=rel):
                self.assertEqual(len(json_findings(rel, SETTINGS)), 7, "every deny rule is a home folder path")
        self.assertEqual(len(json_findings(".claude/settings.json", BOARD)), 1)

    def test_other_home_folder_paths_in_the_settings_are_caught(self):
        """#24: the settings exception covers only the deny rules for the secret folders."""
        for where, rule in (("allow", "Read(" + HOME + "Videos/**)"),
                            ("deny", "Read(" + HOME + "Development/kettle-video/**)"),
                            ("ask", "Edit(" + HOME + ".ssh/**)"),
                            ("deny", "Bash(cat " + HOME + ".ssh/id_rsa)")):
            with self.subTest(where=where, rule=rule):
                data = json.loads(json.dumps(SETTINGS))
                data["permissions"].setdefault(where, []).append(rule)
                found = json_findings(".claude/settings.json", data)
                self.assertEqual(len(found), 1, found)
                self.assertIn(rc.HOME_PATH, found[0])
        with Folder() as d:
            d.write(".claude/settings.json", json.dumps(SETTINGS, indent=2) + "\n// see " + HOME + "notes.md\n")
            self.assertEqual(len(rc.public_text(d.root)[0]), 8, "a file that isn't valid settings allows nothing")

    def test_other_board_links_in_the_board_settings_are_caught(self):
        data = dict(BOARD, notes="https://github.com/" + "users/" + rc.ACCOUNT + "/projects/2")
        found = json_findings(".claude/board.json", data)
        self.assertEqual(len(found), 1, found)
        self.assertIn(rc.BOARD_LINK, found[0])

    def test_an_exception_covers_only_its_own_kind(self):
        found = planted_findings(".claude/settings.json", "Chosen by " + THE_OWNER + ".")
        self.assertTrue(any(rc.OWNER_WORDING in f for f in found))

    def test_the_exceptions_are_in_use(self):
        for (rel, what), (_, lines) in rc.PUBLIC_TEXT_ALLOWED.items():
            with self.subTest(rel=rel):
                text = read(rel)
                self.assertTrue(lines(text), f"{rel} no longer needs its exception")
                pattern = dict(rc.PUBLIC_TEXT)[what]
                self.assertTrue(all(pattern.search(text.splitlines()[n - 1]) for n in lines(text)))

    def test_the_tests_naming_the_old_account_pass(self):
        """The old-name test and this one name what is searched for only in parts."""
        for rel in ("tests/test_old_account_name.py", "tests/test_public_text.py", "tests/test_release_rules.py",
                    "tools/release_check.py"):
            with self.subTest(rel=rel):
                self.assertEqual(rc.public_text_findings(rel, read(rel)), [])


class EveryFindingFails(unittest.TestCase):
    """#24 cleared the text written before the rule, so there is no known list any more."""
    def test_no_known_list(self):
        self.assertFalse(hasattr(rc, "PUBLIC_TEXT_KNOWN"))

    def test_one_finding_is_reported(self):
        with Folder() as d:
            d.write("DECISIONS.md", "Fine.\nChosen by " + THE_OWNER + ".\n")
            self.assertEqual(rc.public_text(d.root)[0],
                             ["DECISIONS.md line 2: " + rc.OWNER_WORDING + " ('" + THE_OWNER + "')"])


class TheRepo(unittest.TestCase):
    def test_the_repo_has_no_findings(self):
        found, count = rc.public_text()
        self.assertEqual(found, [], "text breaks CLAUDE.md \"Public writing\"")
        self.assertGreater(count, 50)

    def test_it_reads_claude_md_and_the_workflow_files(self):
        files = set(rc.published_files())
        for rel in ("CLAUDE.md", ".claude/commands/next.md", ".claude/agents/reviewer.md", ".claude/settings.json",
                    "README.md", "docs/how-this-repo-is-built.md", "DECISIONS.md", "CHANGELOG.md"):
            self.assertIn(rel, files)


class GuideCheck(unittest.TestCase):
    """check_public_text as the quick checks run it."""
    def run_check(self, found):
        saved = list(cg.failures)
        del cg.failures[:]
        out = io.StringIO()
        try:
            with mock.patch.object(cg.release_check, "public_text", return_value=(found, 80)), \
                    contextlib.redirect_stdout(out):
                cg.check_public_text()
            return list(cg.failures), out.getvalue()
        finally:
            cg.failures[:] = saved

    def test_a_finding_fails(self):
        failures, _ = self.run_check(["README.md line 3: a claude.ai link ('x')"])
        self.assertEqual(len(failures), 1)
        self.assertIn("README.md line 3: a claude.ai link", failures[0])

    def test_no_findings_pass(self):
        failures, out = self.run_check([])
        self.assertEqual(failures, [])
        self.assertIn("Public text: nothing private", out)

    def test_it_runs_in_the_quick_checks(self):
        main = read("tools/check_guide.py").split("def main():", 1)[1]
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
