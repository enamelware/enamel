# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #6: nothing names a device, an aspect ratio or a screen size.

tools/check_guide.py (check_no_screens, part of the quick checks, no browser)
reads tokens/, components/, every style guide page and its styles in docs/,
DESIGN.md and README.md, as agreed on #2. These tests plant each kind of
mention in a token comment, a component, an example page and DESIGN.md and
see it caught; see that the real files pass; that the provenance file and the
history are left alone; and that contrast ratios, font weights, times and the
tile frame's 16:9 picture shape are not mistaken for one.

    scripts/test.sh unit tests.test_no_screens
"""
import contextlib, io, os, sys, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_guide as cg


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


# Where to plant, and how: (file, text to find, what to put before it).
PLACES = {
    "a token comment": ("tokens/enamel.css", "  /* Group C: Semantic", "  /* {} */\n"),
    "a component": ("components/enamel-components.css", ".en-tile__frame {", "/* {} */\n"),
    "an example page": ("docs/components.html", "</main>", "<p>{}</p>\n"),
    "DESIGN.md": ("DESIGN.md", "### Group C", "{}\n\n"),
}

PLANTED = [
    ("device", "Made for the Steam Deck."),
    ("device", "Matches the Deck's screen."),
    ("device", "Checked on the Nova."),
    ("device", "Sized for a handheld."),
    ("aspect ratio", "Works at 16:10."),
    ("aspect ratio", "Also fits a 4:3 screen."),
    ("aspect ratio", "A 16:9 screen."),
    ("screen size", "Measured at 1280 by 800."),
    ("screen size", "Fits 1280x800."),
    ("screen size", "Fits 1024 × 768 px."),
    ("screen size", "320px at 1280."),
    ("screen size", "Looks right in 1080p."),
    ("screen size", "A 7-inch screen."),
]

NOT_SCREENS = [
    "Text needs 4.5:1; graphics need 3:1. The accent is 7.50:1.",  # contrast ratios
    "font-weight: 800; font-weight: 700;",  # font weights
    "RESUME AT 19:15. Starts again from 0:00. Ends at 1:05:30 or 4:30.",  # times
    "--en-c-text-detail: calc(var(--en-text-small) * 17 / 15); grid-row: 1 / 3;",  # fractions
    "20rem wide by 15rem tall (320px wide and 240px tall at the browser's normal font size).",  # the smallest box
    "100rem (1600px) wide; 56.25rem; 20rem wide (320px).",  # widths in rem with their pixels
    "Enamel is not affiliated with Valve. Steam and Steam Deck are trademarks of Valve Corporation.",
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "TV shows; Movies; the kettle-video repo at `~/Development/kettle-video`.",
    "<li>Vertical layouts and layered UI (Gaming Mode).</li>",
]


def plant(where, sentence):
    path, anchor, wrap = PLACES[where]
    text = read(path)
    if anchor not in text:
        raise AssertionError(f"{path} no longer contains {anchor!r}; update the test's planting places")
    return text.replace(anchor, wrap.format(sentence) + anchor, 1)


class NoScreens(unittest.TestCase):
    def test_the_real_files_pass(self):
        for path in cg.screen_files():
            self.assertEqual(cg.screen_mentions(read(path)), [], os.path.relpath(path, ROOT))

    def test_it_reads_the_agreed_files(self):
        files = {os.path.relpath(p, ROOT) for p in cg.screen_files()}
        for f in ("tokens/enamel.css", "components/enamel-components.css", "components/enamel-components.js",
                  "docs/site.css", "docs/site.js", "DESIGN.md", "README.md") + tuple(f"docs/{p}" for p in cg.PAGES):
            self.assertIn(f, files)

    def test_it_leaves_the_history_and_workflow_files_alone(self):
        files = {os.path.relpath(p, ROOT) for p in cg.screen_files()}
        self.assertFalse([f for f in files if f.startswith((".claude/", "scripts/", "tools/"))])
        for f in ("CHANGELOG.md", "DECISIONS.md", "CLAUDE.md", "NOTICE.md"):
            self.assertNotIn(f, files)

    def test_a_planted_mention_is_caught_everywhere(self):
        for where in PLACES:
            for kind, sentence in PLANTED:
                with self.subTest(where=where, sentence=sentence):
                    found = cg.screen_mentions(plant(where, sentence))
                    self.assertTrue(found, f"{sentence!r} in {where} was not caught")
                    self.assertIn(kind, {k for _, k, _ in found})

    def test_it_says_which_line(self):
        found = cg.screen_mentions("one\ntwo\nAt 16:10 and 4:3.\n")
        self.assertEqual([(line, kind) for line, kind, _ in found], [(3, "aspect ratio"), (3, "aspect ratio")])

    def test_css_tied_to_a_screen_is_caught(self):
        for css in ("@media (min-aspect-ratio: 16/10) { .x { color: red } }",
                    "@media (max-width: 1280px) { .x { display: none } }",
                    "@media (max-width: 767.98px) { .x { display: none } }",
                    "@media (orientation: portrait) { .x { display: none } }",
                    "@media (device-width: 800px) { .x { display: none } }",
                    ".en-row { aspect-ratio: 16 / 10; }", ".en-row { aspect-ratio: 4/3; }",
                    ".en-row { aspect-ratio: 1.6; }", ".en-row { aspect-ratio: 16 / 9; }"):
            with self.subTest(css=css):
                self.assertTrue(cg.screen_mentions(css))

    def test_no_false_alarms(self):
        for text in NOT_SCREENS:
            with self.subTest(text=text):
                self.assertEqual(cg.screen_mentions(text), [])
        for css in ("@media (prefers-reduced-motion: reduce) { .x { animation: none } }",
                    "@media (max-width: 56.25rem) { .x { display: block } }"):
            self.assertEqual(cg.screen_mentions(css), [], css)

    def test_the_tile_frame_keeps_its_16_9_picture_shape(self):
        self.assertIn("aspect-ratio: 16 / 9;", read("components", "enamel-components.css"))
        for text in (".en-tile__frame {\n  display: flex;\n  aspect-ratio: 16 / 9;\n}",
                     "The tile frame has a 16:9 picture shape."):
            self.assertEqual(cg.screen_mentions(text), [], text)

    def test_it_is_part_of_the_quick_checks(self):
        source = read("tools", "check_guide.py")
        main = source[source.index("def main():"):]
        self.assertLess(main.index("check_no_screens()"), main.index('if "--no-browser" not in args'))


class CheckFails(unittest.TestCase):
    """check_no_screens itself, as the guide check runs it: it reads every
    agreed file and records a failure naming the file and the line, and
    records none on the real repo."""
    def run_check(self, planted=None):
        real_read = cg.read

        def fake_read(path):
            text = real_read(path)
            if planted and os.path.relpath(path, ROOT) == planted[0]:
                text = plant(planted[1], planted[2])
            return text
        saved = list(cg.failures)
        del cg.failures[:]
        try:
            with mock.patch.object(cg, "read", fake_read), contextlib.redirect_stdout(io.StringIO()):
                cg.check_no_screens()
            return list(cg.failures)
        finally:
            cg.failures[:] = saved

    def test_passes_on_the_real_repo(self):
        self.assertEqual(self.run_check(), [])

    def test_fails_on_a_planted_mention_in_each_place(self):
        for where, (path, _, _) in PLACES.items():
            for _, sentence in (PLANTED[0], PLANTED[4], PLANTED[7]):
                with self.subTest(where=where, sentence=sentence):
                    failures = self.run_check((path, where, sentence))
                    self.assertTrue(failures, f"{sentence!r} in {where} did not fail the guide check")
                    self.assertTrue(all(f.startswith(path + " line ") for f in failures), failures)



class ReleaseEntry(unittest.TestCase):
    """#6 ships 0.6.0: the entry is finished, dated, and says what apps do."""
    def setUp(self):
        import re
        text = read("CHANGELOG.md")
        self.head, self.body = re.search(r"^## (0\.6\.0,[^\n]*)\n(.*?)(?=^## )", text, re.S | re.M).groups()

    def test_version_and_heading(self):
        # 0.6.0 shipped; later versions follow it
        self.assertGreaterEqual(tuple(map(int, read("VERSION").split("."))), (0, 6, 0))
        self.assertRegex(self.head, r"^0\.6\.0, \d{4}-\d{2}-\d{2} \(visual\)$")
        self.assertNotIn("2026-10-19", self.head, "the entry should carry the release date, not #3's")

    def test_finished_not_in_progress(self):
        self.assertNotIn("being built in steps", self.body)
        self.assertNotIn("only once #6 is done", self.body)
        self.assertNotIn("stay on 0.5.1", self.body)

    def test_says_what_apps_must_do_and_what_was_renamed(self):
        self.assertIn("**Renamed or removed: none.**", self.body)
        self.assertIn("**What each app must do to pick it up:**", self.body)
        self.assertIn("Re-sync", self.body)
        self.assertIn("relied on the old fixed sizes", self.body)
        self.assertIn("Kettle Video, now", self.body)

    def test_names_the_new_check(self):
        self.assertIn("from #6", self.body)
        part = self.body.split("from #6", 1)[1]
        self.assertIn("device name, an aspect ratio or a screen size", part)
        self.assertIn("The history and workflow files are not checked.", part)


if __name__ == "__main__":
    unittest.main()
