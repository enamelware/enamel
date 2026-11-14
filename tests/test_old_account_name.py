# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #11: nothing names the GitHub account by its old name.

The account was renamed to enamelware on 2026-10-27. GitHub forwards the old
addresses only until someone else takes the old name, so no file in the repo
may use it (in its text or its file name). The one exception is history: an
entry in DECISIONS.md or CHANGELOG.md dated before the rename stays as it was.

The old name comes from the public-text check (tools/release_check.py, #23),
where it is built from two parts, so neither file names it. That check also
looks for it in what is published; this test covers every file in the folder.

    scripts/test.sh unit tests.test_old_account_name
"""
import os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import release_check as rc  # noqa: E402

OLD = rc.OLD_ACCOUNT
NEW = rc.ACCOUNT
RENAMED_ON = "2026-10-27"
HISTORY = ("DECISIONS.md", "CHANGELOG.md")
SKIP_DIRS = {".git", "__pycache__"}

# An entry heading in either history file: "## 0.6.0, 2026-10-21 (visual)" or
# "## 2026-10-21, a release is ...". The date is the entry's date.
DATED = re.compile(r"^## (?:\d+\.\d+\.\d+, )?(\d{4}-\d{2}-\d{2})\b")


def mentions(text):
    """Line numbers that name the old account, in any letter case."""
    return [n for n, line in enumerate(text.splitlines(), 1) if OLD in line.lower()]


def allowed_lines(text):
    """Lines of a history file that sit in an entry dated before the rename."""
    allowed, date = set(), None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            m = DATED.match(line)
            date = m.group(1) if m else None
        if date and date < RENAMED_ON:
            allowed.add(n)
    return allowed


def problems(rel, text):
    """'path line N' for each mention outside old dated entries."""
    found = mentions(text)
    if rel in HISTORY:
        found = [n for n in found if n not in allowed_lines(text)]
    return [f"{rel} line {n}" for n in found]


def repo_files():
    """Every file in the repo folder, as a path relative to it."""
    for top, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield os.path.relpath(os.path.join(top, name), ROOT)


def read_text(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


class OldAccountName(unittest.TestCase):
    def test_no_file_uses_the_old_name(self):
        found = []
        for rel in repo_files():
            if OLD in rel.lower():
                found.append(f"{rel} (file name)")
            text = read_text(rel)
            if text is not None:
                found += problems(rel, text)
        self.assertEqual(found, [], f"the old account name is still used; it is now {NEW}")

    def test_it_reads_the_whole_repo(self):
        files = set(repo_files())
        for rel in ("README.md", "CLAUDE.md", "NOTICE.md", ".claude/board.json", "scripts/board.sh",
                    "tools/check_guide.py", "docs/overview.html", "tokens/enamel.css"):
            self.assertIn(rel, files)

    def test_the_board_settings_use_the_new_owner(self):
        text = read_text(".claude/board.json")
        self.assertIn(f'"owner": "{NEW}"', text)
        self.assertIn(f'"repo": "{NEW}/enamel"', text)
        self.assertIn(f"https://github.com/users/{NEW}/projects/1", text)

    def test_a_planted_mention_is_caught(self):
        for sentence in (f"See https://github.com/{OLD}/enamel.", f"git@github.com:{OLD}/enamel.git",
                         f"The {OLD.upper()} board.", f"Owned by {OLD.capitalize()}."):
            for rel in ("README.md", "scripts/board.sh", ".claude/board.json"):
                with self.subTest(rel=rel, sentence=sentence):
                    self.assertEqual(problems(rel, f"one\n{sentence}\nthree\n"), [f"{rel} line 2"])

    def test_old_dated_entries_stay_as_they_were(self):
        for rel in HISTORY:
            text = f"# Title\n\nIntro.\n\n## 2026-10-21, old entry\n\nIt was {OLD}.\n"
            self.assertEqual(problems(rel, text), [], rel)
            text = f"# Title\n\n## 0.6.0, 2026-10-21 (visual)\n\nIt was {OLD}.\n"
            self.assertEqual(problems(rel, text), [], rel)

    def test_new_entries_and_the_top_of_history_files_are_checked(self):
        for rel in HISTORY:
            with self.subTest(rel=rel):
                text = f"# Title\n\nNow {OLD}.\n\n## 2026-10-21, old\n\nfine\n"
                self.assertEqual(problems(rel, text), [f"{rel} line 3"])
                text = f"# Title\n\n## {RENAMED_ON}, new entry\n\nStill {OLD}.\n\n## 2026-10-21, old\n\nfine\n"
                self.assertEqual(problems(rel, text), [f"{rel} line 5"])
                text = f"# Title\n\n## 0.7.0, 2026-11-02 (breaking)\n\nStill {OLD}.\n"
                self.assertEqual(problems(rel, text), [f"{rel} line 5"])

    def test_other_files_get_no_history_exception(self):
        text = f"## 2026-10-21, an old-looking entry\n\n{OLD}\n"
        self.assertEqual(problems("README.md", text), ["README.md line 3"])

    def test_the_clone_uses_the_new_address(self):
        """The clone's own git settings (not tracked, so the walk above skips them)."""
        config = os.path.join(ROOT, ".git", "config")
        if not os.path.isfile(config):
            self.skipTest("not a plain clone (no .git/config)")
        with open(config, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(mentions(text), [], "the clone's GitHub address still uses the old account name")
        urls = re.findall(r"^\s*(?:push)?url\s*=\s*(\S+)", text, re.M)
        self.assertTrue(urls, "the clone has no GitHub address")
        for url in urls:
            self.assertIn(f"{NEW}/", url)

    def test_the_new_name_and_lookalikes_pass(self):
        for text in (f"https://github.com/users/{NEW}/projects/1", "SteamOS tools", "steamos-tools", "Steam tools"):
            self.assertEqual(mentions(text), [], text)


if __name__ == "__main__":
    unittest.main()
