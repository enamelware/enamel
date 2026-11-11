# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #5: the Resize page (docs/resize.html) adds no dependencies and its
live demos are wired to the same behaviour script as the Motion page.

The frames, labels, menu and look are checked by tools/check_guide.py; the
live demos are run in Firefox by tests/resize_live_check.py. These tests read
the files directly.

    scripts/test.sh unit tests.test_resize_page
"""
import html.parser
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class Refs(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts, self.links, self.ids, self.attrs = [], [], set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "script":
            self.scripts.append(a.get("src"))
        if tag == "link":
            self.links.append(a.get("href"))
        self.attrs.append(a)

    handle_startendtag = handle_starttag


def refs(page):
    p = Refs()
    p.feed(read("docs", page))
    return p


class NoNewDependencies(unittest.TestCase):
    def test_only_the_repos_own_files_are_loaded(self):
        text = read("docs", "resize.html")
        self.assertNotRegex(text, r'(?:src|href)="(?:https?:)?//', "the page loads something from the network")
        self.assertNotRegex(text, r"@import|url\(\s*['\"]?https?:", "the page loads something from the network")
        p = refs("resize.html")
        for ref in p.scripts + p.links:
            self.assertIsNotNone(ref, "an inline script on the page")
            path = os.path.normpath(os.path.join(DOCS, ref))
            self.assertTrue(path.startswith(ROOT + os.sep) and os.path.isfile(path), f"{ref} is not a file in this repo")

    def test_same_scripts_and_stylesheets_as_the_motion_page(self):
        resize, motion = refs("resize.html"), refs("motion.html")
        self.assertEqual(sorted(resize.scripts), sorted(motion.scripts))
        self.assertIn("../components/enamel-components.js", resize.scripts)
        self.assertIn("site.js", resize.scripts)
        self.assertEqual(sorted(resize.links), sorted(motion.links))


class LiveDemosWired(unittest.TestCase):
    p = refs("resize.html")

    def test_every_picker_button_opens_a_picker_on_the_page(self):
        openers = [a["data-open-picker"] for a in self.p.attrs if "data-open-picker" in a]
        self.assertGreaterEqual(len(openers), 3)
        text = read("docs", "resize.html")
        for did in openers:
            self.assertIn(did, self.p.ids, f"no picker with id {did}")
            m = re.search(r'<dialog class="en-dialog" id="%s"[^>]*>(.*?)</dialog>' % re.escape(did), text, re.S)
            self.assertIsNotNone(m, f"{did} is not a picker dialog")
            self.assertIn("en-picker__row", m.group(1))

    def test_toast_buttons_drive_the_toast_in_its_frame(self):
        actions = [a["data-toast"] for a in self.p.attrs if "data-toast" in a]
        self.assertEqual(sorted(actions), ["hide", "show", "update"])
        targets = [a["data-toast-element"] for a in self.p.attrs if "data-toast-element" in a]
        self.assertEqual(len(targets), 1)
        self.assertIn(targets[0], self.p.ids)
        text = read("docs", "resize.html")
        frame = re.search(r'<div class="site-resize[^"]*">((?:(?!<div class="site-resize).)*?id="%s".*?)</figure>'
                          % re.escape(targets[0]), text, re.S)
        self.assertIsNotNone(frame, "the demo toast is not inside a resizable frame")
        self.assertIn('class="en-toast"', frame.group(1))


if __name__ == "__main__":
    unittest.main()
