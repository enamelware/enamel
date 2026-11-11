# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #9: the picker's layer and the toast always clear the hint bar,
however tall it is (0.6.0).

The placement itself is run in the device's Firefox by tools/browser_check.py
(scripts/test.sh guide): one-line and two-line hint bars, in frames from the
smallest supported box to very wide, in full and reduced motion and with a
larger browser font, and on the Resize page. These tests read the files.

    scripts/test.sh unit tests.test_hintbar_clearance
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import resize_page  # noqa: E402
from build_migration import old_name  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def rule(css, selector):
    m = re.search(r"(?:^|\n|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not m:
        raise AssertionError(f"no rule for {selector}")
    return m.group(1)


CSS = strip_comments(read("components", "enamel-components.css"))
JS = read("components", "enamel-components.js")


class Stylesheet(unittest.TestCase):
    def test_variable_defaults_to_the_bar_minimum(self):
        # Without the behaviour script, both stop where they always did.
        self.assertRegex(rule(CSS, ":root"), r"--en-c-hintbar-height:\s*var\(--en-size-bar\);")

    def test_dialog_and_toast_stop_at_the_variable(self):
        self.assertRegex(rule(CSS, ".en-dialog"), r"inset:\s*0 0 var\(--en-c-hintbar-height\) 0;")
        self.assertRegex(rule(CSS, ".en-toast"), r"(?<![-\w])bottom:\s*var\(--en-c-hintbar-height\);")
        for sel in (".en-dialog", ".en-toast"):
            self.assertNotIn("--en-size-bar)", re.sub(r"min-height:[^;]*;", "", rule(CSS, sel)),
                             f"{sel} still stops one fixed bar height above the bottom")

    def test_no_token_added(self):
        self.assertNotIn("hintbar-height", read("tokens", "enamel.css"))


class Script(unittest.TestCase):
    def test_keeps_the_variable_at_the_bars_real_height(self):
        self.assertIn('"--en-c-hintbar-height"', JS)
        self.assertIn("new ResizeObserver(", JS)
        self.assertRegex(JS, r"bar\.parentElement")
        # #18: measured after zoom, written in the page's own units.
        self.assertRegex(JS, r"var height = bar\.getBoundingClientRect\(\)\.height / \(scope\.currentCSSZoom \|\| 1\);")
        self.assertRegex(JS, r"if \(height > 0\) scope\.style\.setProperty\(BAR_HEIGHT,\s*height \+ \"px\"\)")

    def test_hidden_bar_keeps_the_one_bar_gap(self):
        # A hidden bar (0 tall) takes the variable off its parent, so the
        # picker's layer and the toast fall back to --en-size-bar.
        self.assertRegex(JS, r"else scope\.style\.removeProperty\(BAR_HEIGHT\)")
        self.assertNotIn("counts as 0 tall", JS)

    def test_finds_hint_bars_added_later(self):
        self.assertIn("new MutationObserver(", JS)
        self.assertRegex(JS, r"\.observe\(root,\s*\{\s*childList:\s*true,\s*subtree:\s*true\s*\}\)")

    def test_api_unchanged(self):
        for name in ("open: open", "close: close", "select: select", "cancel: cancel", "isOpen:",
                     "show: showToast", "update: updateToast", "hide: hideToast"):
            self.assertIn(name, JS)

    def test_documented(self):
        design = read("DESIGN.md")
        self.assertIn("`--en-c-hintbar-height`", design)
        self.assertIn("however tall it is", design)


class ResizePage(unittest.TestCase):
    def test_narrowest_frame_has_a_two_line_bar_with_select_and_cancel(self):
        smallest = resize_page.fixed(resize_page.WIDTHS[0])
        self.assertIn(resize_page.HINTS_TWO_LINES, smallest)
        self.assertIn("Select", resize_page.HINTS_TWO_LINES)
        self.assertIn("Cancel", resize_page.HINTS_TWO_LINES)
        for width in resize_page.WIDTHS[1:]:
            self.assertNotIn(resize_page.HINTS_TWO_LINES, resize_page.fixed(width))
        self.assertIn(resize_page.HINTS_TWO_LINES, read("docs", "resize.html"))


class Changelog(unittest.TestCase):
    def test_in_the_060_entry_and_says_no_name_changed(self):
        log = read("CHANGELOG.md")
        entry = log.split("\n## 0.6.0", 1)[1].split("\n## ", 1)[0]
        self.assertIn("from #9", entry)
        part = entry.split("from #9", 1)[1]
        self.assertRegex(part, r"No token, component class, state attribute[^\n]*renamed or removed")
        # the entry keeps the names it was written with (#12)
        self.assertIn(f"`{old_name('--en-c-hintbar-height')}`", part)
        self.assertRegex(part, r"hidden[^\n]*one-bar gap")
        # 0.6.0 shipped; later versions follow it
        self.assertGreaterEqual(tuple(map(int, read("VERSION").split("."))), (0, 6, 0))


if __name__ == "__main__":
    unittest.main()
