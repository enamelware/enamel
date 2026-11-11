# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #10: every release has a git tag, and releasing means tagging.

The history starts again at 0.11.1 (#19: replaced by one first commit to go
public, with every older tag removed, agreed with "yes, rewrite"). So every
changelog version from 0.11.1 up to the one before the current version must
have a tag, and no older version has one. Each tag is annotated, carries the
version and its changelog date, and the files at the tag show that version;
every tag has a changelog entry. Also checks that every changelog entry says
who should adopt it and when, that CLAUDE.md and the /next release steps say
a version is released only when its entry is written and its tag is pushed
(one plain push per tag, never forced), and that the README has the section
for apps.

Reads the local git history only; never pushes or fetches.

    scripts/test.sh unit tests.test_release_tags
"""
import os, re, shutil, subprocess, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The first version of the replaced history (#19). Older versions keep their
# changelog entries but have no tags.
FIRST_TAGGED = "0.11.1"


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def git(*args):
    out = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
    return out.returncode, out.stdout.strip()


def vkey(v):
    return tuple(int(p) for p in v.split("."))


def changelog_entries():
    """{version: (date, body)} from CHANGELOG.md."""
    text = read("CHANGELOG.md")
    parts = re.split(r"^## (\d+\.\d+\.\d+), (\d{4}-\d{2}-\d{2})[^\n]*\n", text, flags=re.M)
    return {parts[i]: (parts[i + 1], parts[i + 2]) for i in range(1, len(parts), 3)}


HAVE_GIT = shutil.which("git") is not None and os.path.exists(os.path.join(ROOT, ".git"))


@unittest.skipUnless(HAVE_GIT, "not a git clone")
class Tags(unittest.TestCase):
    def setUp(self):
        self.entries = changelog_entries()
        _, out = git("tag", "--list", "v*")
        self.tags = set(out.split()) if out else set()

    def tagged_versions(self):
        """Changelog versions that must have a tag: from FIRST_TAGGED to the current one (if tagged yet)."""
        return [v for v in self.entries if vkey(v) >= vkey(FIRST_TAGGED) and "v" + v in self.tags]

    def test_they_are_annotated_with_version_and_changelog_date(self):
        for version in self.tagged_versions():
            with self.subTest(version=version):
                tag = "v" + version
                _, kind = git("cat-file", "-t", tag)
                self.assertEqual(kind, "tag", f"{tag} is a lightweight tag, not annotated")
                _, obj = git("cat-file", "-p", tag)
                message = obj.split("\n\n", 1)[1] if "\n\n" in obj else ""
                self.assertIn(version, message)
                self.assertIn(self.entries[version][0], message, f"{tag} message lacks its changelog date")

    def test_the_files_at_each_tag_show_its_version(self):
        for tag in sorted(self.tags):
            with self.subTest(tag=tag):
                code, version = git("show", tag + ":VERSION")
                self.assertEqual(code, 0)
                self.assertEqual("v" + version.strip(), tag)

    def test_no_tags_from_before_the_history_starts(self):
        for tag in self.tags:
            self.assertGreaterEqual(vkey(tag[1:]), vkey(FIRST_TAGGED), f"{tag} is older than the history")

    def test_every_tag_has_a_changelog_entry(self):
        for tag in self.tags:
            self.assertIn(tag[1:], self.entries, f"{tag} has no changelog entry")

    def test_every_older_changelog_version_is_tagged(self):
        current = read("VERSION").strip()
        for version in self.entries:
            if vkey(FIRST_TAGGED) <= vkey(version) < vkey(current):
                self.assertIn("v" + version, self.tags, f"{version} is older than {current} but has no tag")


class ChangelogSaysWhoAdopts(unittest.TestCase):
    def test_every_entry_says_who_should_adopt_it_and_when(self):
        entries = changelog_entries()
        self.assertIn("0.3.0", entries)
        for version, (_, body) in entries.items():
            with self.subTest(version=version):
                m = re.search(r"^\*\*Who should adopt it, and when:\*\* (.+)$", body, re.M)
                self.assertTrue(m, f"{version} does not say who should adopt it")
                self.assertIn("Kettle Video", m.group(1))

    def test_intro_says_released_means_tagged(self):
        intro = read("CHANGELOG.md").split("\n## ", 1)[0]
        self.assertIn("released only once its entry is written and its git tag", intro)


class ReleaseRules(unittest.TestCase):
    def test_claude_md(self):
        text = read("CLAUDE.md")
        self.assertIn("A version counts as released only when its `CHANGELOG.md` entry is written", text)
        self.assertIn("its tag is pushed", text)
        self.assertIn("annotated tag", text)
        self.assertIn("Work in progress on `main` never counts", text)
        self.assertIn("one plain `git push origin <tag>` per tag, never forced", text)
        self.assertIn("never moved or deleted", text)

    def test_next_md_release_steps(self):
        text = read(".claude", "commands", "next.md")
        self.assertIn("**Released means tagged.**", text)
        self.assertIn("only when its `CHANGELOG.md` entry is written and its tag is pushed", text)
        self.assertIn("says which apps should adopt it and when", text)
        step9 = text[text.index("git merge --squash issue-N"):]
        self.assertIn("**Tag the release**", step9)
        self.assertIn("git tag -a v<version>", step9)
        self.assertIn("one plain `git push origin v<version>`", step9)
        self.assertIn("never forced", step9)
        self.assertNotRegex(text, r"push[^\n]*(--force|-f\b)[^\n]*tag")
        # tagging comes after the merge is pushed, before clean-up
        self.assertLess(step9.index("git push origin main"), step9.index("**Tag the release**"))
        self.assertLess(step9.index("**Tag the release**"), step9.index("scripts/branch-done.sh"))


class ReadmeForApps(unittest.TestCase):
    def setUp(self):
        text = read("README.md")
        self.assertIn("## Versions and tags, for apps", text)
        self.section = text.split("## Versions and tags, for apps", 1)[1].split("\n## ", 1)[0]

    def test_files_at_a_tag(self):
        self.assertIn("git fetch --tags origin", self.section)
        self.assertRegex(self.section, r"git show v\d+\.\d+\.\d+:")
        self.assertRegex(self.section, r"git archive v\d+\.\d+\.\d+")

    def test_newest_tag(self):
        self.assertIn("git ls-remote --tags", self.section)
        self.assertIn("newest first", self.section)

    def test_what_an_apps_check_compares(self):
        self.assertIn("fails only when the copy differs from that tag", self.section)
        self.assertIn("at most warns", self.section)


if __name__ == "__main__":
    unittest.main()
