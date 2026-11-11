# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #19: Enamel goes public with only its own work. These tests cover
what tests/test_release_rules.py does not:

  - nothing that would be published still points at the removed reference
    folder or the removed Steam tools;
  - README, DESIGN.md, the Overview, Tokens and Motion pages, and CLAUDE.md
    say nothing about taking values out of Steam, a debug connection or
    Steam's files, and the two old source labels are gone;
  - every example title in a row or tile is one of the made-up titles
    listed here (the owner's request during the build), so no real film or
    show title can slip into the examples;
  - the guide check really fails when the release check finds something;
  - the case-study page, where it exists next to this repo, opens on its
    own (nothing loaded from another file).

    scripts/test.sh unit tests.test_public_repo
"""
import contextlib, io, os, re, sys, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import release_check as rc  # noqa: E402
import check_guide as cg  # noqa: E402

SELF = "tests/test_public_repo.py"
# test_release_rules.py lists the removed tools to check they are gone, and
# the release check itself looks for a reference folder.
LISTS_THE_REMOVED_TOOLS = {SELF, "tests/test_release_rules.py", "tools/release_check.py"}


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def published_text():
    """[(path, text)] for every text file that would be published."""
    out = []
    for rel in rc.published_files():
        try:
            out.append((rel, read(rel)))
        except UnicodeDecodeError:
            pass
    return out


def hits(pattern, text):
    return [(n, m.group(0)) for n, line in enumerate(text.splitlines(), 1) for m in [pattern.search(line)] if m]


# The removed reference folder, its files, and the removed tools.
REMOVED = re.compile(
    r"(?<![\w./-])reference/|provenance\.md|steam-(?:motion|variables|reference)\.(?:json|html)"
    r"|\b(?:extract|extract_motion|extract_colours_pass2|build_page|build_motion_reference|css_vars|css_motion|cdp)\.py\b"
    r"|\bfrom cdp import\b|\bimport cdp\b")


class NothingPointsAtTheRemovedFiles(unittest.TestCase):
    def test_no_published_file_names_them(self):
        found = []
        for rel, text in published_text():
            if rel in LISTS_THE_REMOVED_TOOLS:
                continue
            found += [f"{rel} line {n}: {what!r}" for n, what in hits(REMOVED, text)]
        self.assertEqual(found, [], "these still point at the removed reference folder or Steam tools")

    def test_the_pattern_catches_each_kind(self):
        for line in ("see `reference/provenance.md`", "python3 tools/" + "extract_motion.py",
                     "from " + "cdp import Session", '<a href="../reference/steam-motion.html">'):
            self.assertTrue(REMOVED.search(line), line)
        for line in ("Token reference", "docs/index.html (the token reference)", "tools/browser_session.py"):
            self.assertFalse(REMOVED.search(line), line)


# Wording the issue rules out in the public docs (step 2).
WORDING = [
    ("taking values out of Steam", re.compile(r"extract", re.I)),
    ("a debug connection", re.compile(r"debug", re.I)),
    ("Steam's files or stylesheets", re.compile(
        r"Steam(?:'s| client's)? (?:own )?(?:files|stylesheets?)|Gaming Mode's (?:own )?stylesheets?", re.I)),
    ("Valve's names or values",re.compile(r"Valve's (?:own )?(?:var" + r"iables?|values|styles|animations?)", re.I)),
    ("a Steam client version", re.compile(r"client\s+\d{6,}", re.I)),
    # built from parts, so the release check does not catch this file
    ("the old source labels", re.compile(r"\b(?:" + "Extract" + "ed|Observed)\\b")),
]
PUBLIC_DOCS = ["README.md", "DESIGN.md", "NOTICE.md", "docs/overview.html", "docs/index.html", "docs/motion.html",
               "docs/components.html", "docs/resize.html", "tokens/enamel.css", "components/enamel-components.css"]


class Wording(unittest.TestCase):
    def test_public_docs_say_matched_not_extracted(self):
        for rel in PUBLIC_DOCS:
            text = read(rel)
            for what, pattern in WORDING:
                with self.subTest(file=rel, what=what):
                    self.assertEqual(hits(pattern, text), [], f"{rel} still mentions {what}")

    def test_claude_md_has_no_extraction_instructions(self):
        text = read("CLAUDE.md")
        self.assertEqual(hits(re.compile(r"extract", re.I), text), [])
        self.assertEqual(hits(re.compile(r"debug", re.I), text), [])

    def test_the_pages_name_the_new_source_labels(self):
        self.assertIn("<b>Steam baseline</b>", read("docs/index.html"))
        self.assertIn("<b>Steam baseline</b>", read("docs/motion.html"))
        self.assertIn("**Steam baseline** = matched to Steam's Gaming Mode", read("DESIGN.md"))


# The made-up titles the examples use. A row or tile label passes when its
# title (before " · " or ",") is one of these, when it is one of the
# interface labels, or when it is a folder path made of the folder names.
INVENTED_TITLES = {"Copper Tide Rising", "Driftwood", "Orchard Weather", "Lighthouse Keepers of the Long Winter",
                   "Lantern Street", "Quiet Harbour", "The Glasshouse Year", "North of the Orchard", "Ember"}
UI_LABELS = {"Keep screen awake", "Keep screen awake while a video is paused", "Library", "Videos"}
FOLDER_NAMES = {"SD card", "Internal storage", "Videos", "Films", "Films from the family", "Series", "Old"}
LABEL = re.compile(r'class="en-(?:row|tile__title)"[^>]*>([^<]*)<')


def label_is_allowed(raw):
    label = " ".join(re.split(r"['\"]", raw)[0].split())
    if not label or "{" in label:      # empty, or filled in by the page script
        return True
    if label in UI_LABELS:
        return True
    if " › " in label:
        return all(part in FOLDER_NAMES for part in label.split(" › "))
    return re.split(r" · |,", label)[0].strip() in INVENTED_TITLES


def labels(text):
    """[(line, label)] for every row and tile title in a file's text."""
    return [(text.count("\n", 0, m.start()) + 1, m.group(1)) for m in LABEL.finditer(text)]


class MadeUpTitles(unittest.TestCase):
    def test_every_example_title_is_made_up(self):
        found = []
        for rel, text in published_text():
            if rel == SELF:     # its own samples below include titles not on the list
                continue
            found += [f"{rel} line {n}: {label!r}" for n, label in labels(text) if not label_is_allowed(label)]
        self.assertEqual(found, [], "an example uses a title that is not on the made-up list")

    def test_the_check_reads_the_examples(self):
        seen = {" ".join(label.split()) for rel, text in published_text() if rel != SELF for _, label in labels(text)}
        for title in ("Copper Tide Rising", "Driftwood · Episode 5", "Orchard Weather · Part 1", "SD card › Films"):
            self.assertIn(title, seen)

    def test_a_title_not_on_the_list_is_caught(self):
        for markup in ('<div class="en-row">Some Real Film <span class="en-row__meta">1995</span></div>',
                       '<button class="en-row" data-focused="true">Another Film</button>',
                       '<div class="en-tile__title">A Series · Episode 2</div>',
                       '<div class="en-row">SD card › Someone Real</div>'):
            with self.subTest(markup=markup):
                self.assertFalse(all(label_is_allowed(label) for _, label in labels(markup)))
        for markup in ('<div class="en-row">Driftwood <span class="en-row__meta">1995</span></div>',
                       '<div class="en-tile__title">Orchard Weather · Part 1</div>',
                       '<div class="en-row">{e(t)}</div>', '<div class="en-row">Internal storage › Videos</div>'):
            with self.subTest(markup=markup):
                self.assertTrue(all(label_is_allowed(label) for _, label in labels(markup)))

    def test_the_examples_use_the_made_up_ones(self):
        for rel in ("docs/components.html", "docs/motion.html", "docs/resize.html", "docs/overview.html"):
            self.assertIn("Copper Tide Rising", read(rel), rel)


class GuideCheckFails(unittest.TestCase):
    """check_release as the guide check runs it: one failure per finding."""
    def run_check(self, found):
        saved = list(cg.failures)
        del cg.failures[:]
        try:
            with mock.patch.object(cg.release_check, "problems", return_value=(found, 60)), \
                    contextlib.redirect_stdout(io.StringIO()):
                cg.check_release()
            return list(cg.failures)
        finally:
            cg.failures[:] = saved

    def test_a_finding_fails_the_check(self):
        failures = self.run_check(["docs/page.html line 2: a home folder path ('x')"])
        self.assertEqual(len(failures), 1)
        self.assertIn("docs/page.html line 2: a home folder path", failures[0])

    def test_no_finding_no_failure(self):
        self.assertEqual(self.run_check([]), [])


CASE_STUDY = os.path.join(os.path.dirname(ROOT), "enamel-case-study", "index.html")


@unittest.skipUnless(os.path.exists(CASE_STUDY), "the case-study page lives only on the owner's device")
class CaseStudy(unittest.TestCase):
    def setUp(self):
        with open(CASE_STUDY, encoding="utf-8") as f:
            self.text = f.read()

    def test_it_holds_the_story(self):
        self.assertIn("From Steam to Enamel", self.text)
        self.assertIn("Before:", self.text)

    def test_it_opens_on_its_own(self):
        self.assertNotRegex(self.text, r"<link\b[^>]*\bhref=", "a stylesheet loaded from another file")
        self.assertNotRegex(self.text, r"<script\b[^>]*\bsrc=", "a script loaded from another file")
        self.assertNotRegex(self.text, r"<img\b[^>]*\bsrc=\"(?!data:)", "an image loaded from another file")
        self.assertNotRegex(self.text, r"url\(\s*[\"']?(?!data:|#)[^)\"']+", "a file loaded by the styles")

    def test_it_is_outside_the_repo(self):
        self.assertFalse(os.path.abspath(CASE_STUDY).startswith(ROOT + os.sep))


if __name__ == "__main__":
    unittest.main()
