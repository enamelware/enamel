# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #24, the existing text in the project voice: the main documents and
the style guide's own prose speak as the project explaining itself, with no
"I", "we" or "you" and nothing pointing to a private place; the reworded
guidelines read the same in DESIGN.md and on the Overview page; and the
wording change is released as the patch 0.13.1. The public-text check itself
is tested by tests/test_public_text.py.

    scripts/test.sh unit tests.test_project_voice
"""
import os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


PERSON = re.compile(r"\b(?:I|me|my|we|We|us|our|Our|you|You|your|Your|yours)\b")

DOCUMENTS = ["README.md", "DESIGN.md", "DECISIONS.md", "CHANGELOG.md", "MIGRATION.md",
             "docs/how-this-repo-is-built.md"]
PAGES = ["docs/overview.html", "docs/index.html", "docs/components.html", "docs/motion.html", "docs/resize.html"]

# Example copy inside the components' own examples: an invented app speaking to its user, not the project.
EXAMPLE_COPY = [
    "Scan my folders",
    "Which folder has your movies?",
    "Which folder has your TV shows and your home videos?",
    "Copy your videos in. Give each TV show its own folder.",
    "This folder is inside your movies folder, so pick a different one.",
]

PROSE = re.compile(r"<(p|li|h[1-6]|dd|dt|td|th|figcaption|summary)(\s[^>]*)?>(.*?)</\1>", re.S)


def page_prose(rel):
    """The text of each paragraph, list item and heading the page writes itself (not a component's own part)."""
    for m in PROSE.finditer(read(rel)):
        if re.search(r'class="[^"]*\ben-', m.group(2) or ""):
            continue
        text = " ".join(re.sub(r"<[^>]+>", " ", m.group(3)).split())
        for example in EXAMPLE_COPY:
            text = text.replace(example, "")
        yield text


class ProjectVoice(unittest.TestCase):
    def test_documents_speak_as_the_project(self):
        for rel in DOCUMENTS:
            with self.subTest(rel=rel):
                found = [line for line in read(rel).splitlines() if PERSON.search(line)]
                self.assertEqual(found, [])

    def test_style_guide_prose_speaks_as_the_project(self):
        for rel in PAGES:
            with self.subTest(rel=rel):
                found = [text for text in page_prose(rel) if PERSON.search(text)]
                self.assertEqual(found, [])

    def test_the_example_copy_is_still_example_copy(self):
        pages = "".join(read(rel) for rel in PAGES)
        for example in EXAMPLE_COPY:
            with self.subTest(example=example):
                self.assertIn(example, pages)

    def test_nothing_points_to_a_private_place(self):
        for rel in DOCUMENTS + PAGES:
            with self.subTest(rel=rel):
                text = read(rel)
                for words in ("the brief", "design canvas", "media-player#"):
                    self.assertNotIn(words, text)

    def test_reworded_guidelines_match(self):
        overview = read("docs/overview.html")
        design = read("DESIGN.md")
        for line in ("Nothing that can be selected is ever patterned.",
                     "cream on a coral underside for things that can be pressed",
                     "Only things that can be pressed move physically."):
            with self.subTest(line=line):
                self.assertIn(line, design)
                self.assertIn(line, overview)


class PatchRelease(unittest.TestCase):
    def test_version_and_entry(self):
        self.assertEqual(read("VERSION").strip(), "0.13.1")
        changelog = read("CHANGELOG.md")
        entry = changelog.split("## 0.13.1, 2026-11-17\n", 1)[1].split("\n## ", 1)[0]
        self.assertLess(changelog.index("## 0.13.1"), changelog.index("## 0.13.0"))
        self.assertIn("Wording only", entry)
        self.assertIn("**Renamed or removed: none.**", entry)
        self.assertIn("**Who should adopt it, and when:**", entry)
        self.assertIn("apps need to change nothing", entry)
        self.assertIn("currently 0.13.1", read("README.md"))

    def test_every_release_keeps_its_date(self):
        heads = re.findall(r"^## (\d+\.\d+\.\d+), (\d{4}-\d{2}-\d{2})", read("CHANGELOG.md"), re.M)
        self.assertIn(("0.11.1", "2026-11-11"), heads)
        self.assertIn(("0.12.0", "2026-11-12"), heads)
        self.assertIn(("0.13.0", "2026-11-14"), heads)


if __name__ == "__main__":
    unittest.main()
