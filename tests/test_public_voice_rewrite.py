# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #24, what tests/test_project_voice.py leaves out:

- the three wording points added to the issue from #20: the README says how
  anyone can open the style guide (serve the repo with tools/serve.py and open
  the page it prints) and why a double-clicked page shows up unstyled; the
  top of DECISIONS.md says what Kettle is; tools/serve.py and the README give
  the reason (a sandboxed Firefox, for example a Flatpak install) instead of
  describing one machine;
- the renamed CLAUDE.md sections ("How the work is done", "Reports to the
  designer") are what every workflow file and script points to, so no
  instruction points to a section that is gone;
- every release and decision keeps its version and date: each CHANGELOG
  heading and each DECISIONS.md date from the v0.13.0 tag is still there, in
  the same order.

    scripts/test.sh unit tests.test_public_voice_rewrite
"""
import os, re, subprocess, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEFORE = "v0.13.0"  # the last release before the rewrite; a pushed tag never moves


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def at_tag(rel):
    """The file as it was at the last release before the rewrite, or None if the tag isn't here."""
    try:
        out = subprocess.run(["git", "show", f"{BEFORE}:{rel}"], cwd=ROOT, capture_output=True,
                             text=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout


def readme_style_guide():
    text = read("README.md")
    start = text.index("## Style guide")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else len(text)]


def serve_note():
    text = read("tools/serve.py")
    m = re.match(r'\s*"""(.*?)"""', text, re.S)
    assert m, "tools/serve.py has no opening note"
    return m.group(1)


class AddedScope(unittest.TestCase):
    """The comment on #24 that added three points from #20."""

    def test_readme_says_how_anyone_can_open_the_style_guide(self):
        section = readme_style_guide()
        # Beyond the launcher: a command anyone with the repo can run.
        self.assertIn("python3 tools/serve.py", section,
                      "the README's Style guide part doesn't say how to serve the repo without the launcher")
        self.assertRegex(section, r"(?i)\bprints\b",
                         "the README doesn't say to open the page tools/serve.py prints")
        self.assertIn("unstyled", section, "the README no longer says why a double-clicked page looks unstyled")

    def test_the_reason_is_the_sandbox_not_the_machine(self):
        for where, text in (("README.md", readme_style_guide()), ("tools/serve.py", serve_note())):
            with self.subTest(where=where):
                self.assertNotIn("Firefox here", text)
                self.assertNotIn("Firefox on SteamOS is sandboxed", text)
                self.assertRegex(text, r"(?i)sandboxed Firefox")
                self.assertIn("Flatpak", text)

    def test_serve_note_still_describes_what_it_does(self):
        note = serve_note()
        for words in ("127.0.0.1", "--no-open", "Standard library only"):
            self.assertIn(words, note)

    def test_decisions_says_what_kettle_is(self):
        text = read("DECISIONS.md")
        intro = text[:text.index("\n## ")]
        self.assertIn("Kettle", intro.replace("Kettle Video", ""),
                      "the top of DECISIONS.md doesn't say what Kettle is")
        self.assertIn("Kettle Video", intro)
        self.assertRegex(intro, r"(?i)\bfirst\b", "the top of DECISIONS.md doesn't say Kettle Video is the first app")
        self.assertRegex(intro, r"(?i)\bapps\b")


WORKFLOW = [os.path.join(".claude", d, name)
            for d in ("commands", "agents") if os.path.isdir(os.path.join(ROOT, ".claude", d))
            for name in sorted(os.listdir(os.path.join(ROOT, ".claude", d))) if name.endswith(".md")]
POINTING = WORKFLOW + ["CLAUDE.md", "README.md", "docs/how-this-repo-is-built.md",
                       "scripts/board.sh", "scripts/test.sh"]


class SectionNames(unittest.TestCase):
    def test_claude_md_has_the_new_sections(self):
        headings = re.findall(r"^## (.+)$", read("CLAUDE.md"), re.M)
        for name in ("Who uses this", "How the work is done", "Hard rules", "Public writing",
                     "Reports to the designer"):
            self.assertIn(name, headings)
        self.assertNotIn("How we work", headings)
        self.assertNotIn("How to talk to me", headings)

    def test_nothing_points_to_an_old_section_name(self):
        self.assertGreaterEqual(len(WORKFLOW), 6)
        for rel in POINTING:
            with self.subTest(rel=rel):
                text = read(rel)
                self.assertNotIn("How we work", text)
                self.assertNotIn("How to talk to me", text)

    def test_every_quoted_claude_md_section_exists(self):
        """A section named next to CLAUDE.md (CLAUDE.md "X", or CLAUDE.md (..., "X", ...)) is a heading there."""
        headings = set(re.findall(r"^## (.+)$", read("CLAUDE.md"), re.M))
        # Bullet names inside "How the work is done" that the workflow also quotes.
        headings |= set(re.findall(r"^- \*\*(.+?)\.?\*\*", read("CLAUDE.md"), re.M))
        checked = 0
        for rel in POINTING:
            for line in read(rel).splitlines():
                for m in re.finditer(r"CLAUDE\.md[^.\n]{0,160}", line):
                    for name in re.findall(r'"([A-Z][A-Za-z ,\']{3,40})"', m.group(0)):
                        if name in ("Gaps found by the apps",) or name.startswith("Decided"):
                            continue
                        checked += 1
                        with self.subTest(rel=rel, name=name):
                            self.assertIn(name, headings, f"{rel} points to a CLAUDE.md section that isn't there")
        self.assertGreater(checked, 5)


class History(unittest.TestCase):
    def setUp(self):
        if at_tag("CHANGELOG.md") is None:
            self.skipTest(f"the {BEFORE} tag is not in this clone")

    def test_every_release_keeps_its_heading(self):
        head = re.compile(r"^## (\d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}.*)$", re.M)
        before = head.findall(at_tag("CHANGELOG.md"))
        now = head.findall(read("CHANGELOG.md"))
        self.assertGreater(len(before), 10)
        self.assertEqual(now[-len(before):], before, "a released version lost or changed its heading, or moved")

    def test_every_decision_keeps_its_date(self):
        date = re.compile(r"^## (\d{4}-\d{2}-\d{2}),", re.M)
        before = date.findall(at_tag("DECISIONS.md"))
        now = date.findall(read("DECISIONS.md"))
        self.assertGreater(len(before), 20)
        self.assertEqual(now[-len(before):], before, "a decision was dropped, added in the middle, or redated")


if __name__ == "__main__":
    unittest.main()
