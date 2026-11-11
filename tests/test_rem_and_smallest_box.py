# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #4: text and spacing in rem, every other component sized from its
content and space, and the smallest supported box (0.6.0). These tests read
the files directly: the agreed base sizes and capped growth of the text and
spacing tokens, the sizes kept fixed in px, component sizes in rem and
heights as minimums, the smallest supported box written in DESIGN.md and the
same box used by the browser check, the measured values labelled Steam
baseline without naming a device (#19), no name changed, and the 0.6.0 changelog listing
every changed value.

How the components actually behave in Firefox at several frame sizes, at the
smallest supported box and with a larger browser font size is checked by
tools/browser_check.py (scripts/test.sh guide).

    scripts/test.sh unit tests.test_rem_and_smallest_box
"""
import ast
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_migration import old_name  # noqa: E402  (the 0.6.0 entry keeps the names it was written with, #12)
import enamel_tokens as en  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def variable(css, name):
    m = re.search(r"(?<![\w-])" + re.escape(name) + r"\s*:\s*([^;]+);", strip_comments(css))
    if not m:
        raise AssertionError(f"{name} is not defined")
    return " ".join(m.group(1).split())


def rule(css, selector):
    """The body of the first rule whose selector is exactly `selector`."""
    m = re.search(r"(?:^|\n|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", strip_comments(css))
    if not m:
        raise AssertionError(f"no rule for {selector}")
    return m.group(1)


def section(text, heading):
    m = re.search(r"^" + re.escape(heading) + r"[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        raise AssertionError(f"no section {heading!r}")
    return m.group(1)


TOKENS = read("tokens", "enamel.css")
CSS = read("components", "enamel-components.css")

# Agreed on #2: base size in rem (the old px / 16), growing evenly by a fifth
# between a page 100rem and 160rem wide. The bases are the Steam baseline
# since 0.8.0 (#15).
GROWING = {"--en-text-title": 2.0625, "--en-text-heading": 1.5, "--en-text-body": 1.5,
           "--en-text-small": 1.16667, "--en-text-caps": 1.0625,
           "--en-space-gutter": 2.25, "--en-space-gutter-grid": 3, "--en-space-inset": 1.25}
FLAT = {"--en-space-gap": "0.75rem", "--en-space-tight": "0.25rem", "--en-space-icon": "1rem",
        "--en-size-row": "4rem", "--en-size-row-control": "6rem", "--en-size-bar": "3.75rem",
        "--en-size-button": "3.75rem", "--en-size-tile-portrait": "12.5rem"}
# The sizes the audit kept fixed.
FIXED = {"--en-radius": "2px", "--en-radius-pill": "999px", "--en-focus-ring-width": "4px",
         "--en-focus-ring-offset": "4px", "--en-focus-ring-start": "12px",
         "--en-focus-affordance": "10px", "--en-size-target": "44px"}
# Component variables in px: lines and blur, and since 0.11.0 (#18) what should
# not grow with the user's text size: side padding that would squeeze text,
# corners, tracks, the menu bar, the tile's glow and the rise.
FIXED_C = {"--en-c-icon-stroke", "--en-c-backdrop-blur", "--en-c-glyph-shoulder-radius", "--en-c-tab-padding",
           "--en-c-button-padding", "--en-c-progress-height", "--en-c-progress-thin", "--en-c-menu-bar",
           "--en-c-picker-inset", "--en-c-tile-glow", "--en-c-rise", "--en-c-focus-stroke"}
# Token and component variable changes: (name, old value, new value).
TOKEN_CHANGES = [("--en-text-title", "30px"), ("--en-text-heading", "24px"), ("--en-text-body", "20px"),
                 ("--en-text-small", "15px"), ("--en-text-caps", "13px"), ("--en-space-gutter", "36px"),
                 ("--en-space-inset", "18px"), ("--en-space-gap", "12px"), ("--en-space-tight", "4px"),
                 ("--en-size-row", "56px"), ("--en-size-bar", "60px")]
COMPONENT_CHANGES = [("--en-c-hint-gap", "28px"), ("--en-c-glyph-size", "30px"), ("--en-c-glyph-text", "16px"),
                     ("--en-c-glyph-shoulder-width", "48px"), ("--en-c-glyph-shoulder-height", "36px"),
                     ("--en-c-tab-padding", "24px"), ("--en-c-dot-size", "10px"),
                     ("--en-c-tile-width", "256px"), ("--en-c-tile-width-large", "448px"),
                     ("--en-c-button-padding", "36px"), ("--en-c-toggle-width", "58px"),
                     ("--en-c-toggle-height", "34px"), ("--en-c-toggle-thumb", "28px"),
                     ("--en-c-menu-item-height", "62px"), ("--en-c-icon-size", "24px"),
                     ("--en-c-picker-row", "72px"), ("--en-c-picker-row-tall", "96px"),
                     ("--en-c-picker-inset", "21px"), ("--en-c-text-detail", "17px")]
# What 0.6.0 changed each of those to, as its changelog entry says.
V060 = {"--en-text-title": "clamp(1.875rem, 1.25rem + 0.625vw, 2.25rem)",
        "--en-text-heading": "clamp(1.5rem, 1rem + 0.5vw, 1.8rem)",
        "--en-text-body": "clamp(1.25rem, 0.83333rem + 0.41667vw, 1.5rem)",
        "--en-text-small": "clamp(0.9375rem, 0.625rem + 0.3125vw, 1.125rem)",
        "--en-text-caps": "clamp(0.8125rem, 0.54167rem + 0.27083vw, 0.975rem)",
        "--en-space-gutter": "clamp(2.25rem, 1.5rem + 0.75vw, 2.7rem)",
        "--en-space-inset": "clamp(1.125rem, 0.75rem + 0.375vw, 1.35rem)",
        "--en-space-gap": "0.75rem", "--en-space-tight": "0.25rem", "--en-size-row": "3.5rem",
        "--en-size-bar": "3.75rem", "--en-c-hint-gap": "1.75rem", "--en-c-glyph-size": "1.875rem",
        "--en-c-glyph-text": "1rem", "--en-c-glyph-shoulder-width": "3rem",
        "--en-c-glyph-shoulder-height": "2.25rem", "--en-c-tab-padding": "1.5rem", "--en-c-dot-size": "0.625rem",
        "--en-c-tile-width": "clamp(10rem, 40cqi, 16rem)",
        "--en-c-tile-width-large": "clamp(12rem, 75cqi, var(--en-c-tile-large-max))",
        "--en-c-button-padding": "2.25rem", "--en-c-toggle-width": "3.625rem", "--en-c-toggle-height": "2.125rem",
        "--en-c-toggle-thumb": "1.75rem", "--en-c-menu-item-height": "3.875rem", "--en-c-icon-size": "1.5rem",
        "--en-c-picker-row": "4.5rem", "--en-c-picker-row-tall": "6rem", "--en-c-picker-inset": "1.3125rem",
        "--en-c-text-detail": "calc(var(--en-text-small) * 17 / 15)"}
CLAMP = re.compile(r"clamp\(\s*([\d.]+)rem\s*,\s*([\d.]+)rem\s*\+\s*([\d.]+)vw\s*,\s*([\d.]+)rem\s*\)")


class TextAndSpacing(unittest.TestCase):
    def test_growing_tokens_have_the_agreed_base_and_cap(self):
        for name, base in GROWING.items():
            value = variable(TOKENS, name)
            m = CLAMP.fullmatch(value)
            self.assertIsNotNone(m, f"{name} is not clamp(rem, rem + vw, rem): {value}")
            low, start, slope, high = map(float, m.groups())
            self.assertAlmostEqual(low, base, places=4, msg=f"{name}: base is not {base}rem")
            self.assertAlmostEqual(high, base * 1.2, places=4, msg=f"{name}: cap is not a fifth above the base")
            # vw is a hundredth of the page, so at a page W rem wide the middle is start + slope * W / 100.
            self.assertAlmostEqual(start + slope * 1.0, base, places=3,
                                   msg=f"{name}: growth does not start at a page 100rem wide")
            self.assertAlmostEqual(start + slope * 1.6, base * 1.2, places=3,
                                   msg=f"{name}: growth does not reach its cap at 160rem")

    def test_flat_tokens_in_rem(self):
        for name, value in FLAT.items():
            self.assertEqual(variable(TOKENS, name), value, f"{name} is not {value}")

    def test_fixed_sizes_stay_in_px(self):
        for name, value in FIXED.items():
            self.assertEqual(variable(TOKENS, name), value, f"{name} was kept fixed at {value}")

    def test_no_text_or_space_token_in_px(self):
        for m in re.finditer(r"(--en-(?:text|space|size)-[\w-]+)\s*:\s*([^;]+);", strip_comments(TOKENS)):
            if m.group(1) == "--en-size-target":
                continue
            self.assertNotRegex(m.group(2), r"\d+px", f"{m.group(1)} is still in px, so it ignores the browser's font size")


class Components(unittest.TestCase):
    def test_component_sizes_in_rem(self):
        for m in re.finditer(r"(--en-c-[\w-]+)\s*:\s*([^;]+);", strip_comments(CSS)):
            if m.group(1) in FIXED_C:
                continue
            self.assertNotRegex(m.group(2), r"\d+px", f"{m.group(1)} is still in px: {m.group(2).strip()}")

    def test_heights_that_hold_text_are_minimums(self):
        for selector, var in ((".en-hintbar", "--en-size-bar"), (".en-tab", "--en-size-target"),
                              (".en-menu__item", "--en-c-menu-item-height")):
            body = rule(CSS, selector)
            self.assertRegex(body, r"min-height:\s*var\(" + re.escape(var) + r"\)", f"{selector} has no minimum height")
            self.assertNotRegex(body, r"(?<![-\w])height:", f"{selector} still has a fixed height")

    def test_icon_button_never_below_the_touch_target(self):
        body = rule(CSS, ".en-button--icon")
        self.assertIn("min-width: max(var(--en-size-target), var(--en-size-button))", body)
        self.assertIn("min-height: max(var(--en-size-target), var(--en-size-button))", body)
        self.assertNotRegex(body, r"(?<![-\w])(?:width|height):", "the icon button has a fixed size")

    def test_rows_of_things_wrap(self):
        for selector in (".en-hintbar", ".en-tabs", ".en-progress__head"):
            self.assertIn("flex-wrap: wrap", rule(CSS, selector), f"{selector} does not wrap")

    def test_tiles_take_their_width_from_the_shelf(self):
        shelf = rule(CSS, ".en-shelf")
        self.assertIn("container-type: inline-size", shelf, "the shelf is not a size container")
        self.assertIn("scroll-padding: var(--en-c-shelf-room)", shelf,
                      "a tile scrolled into view could have its ring cut off at the shelf's edge")
        self.assertIn("padding: var(--en-c-shelf-room)", shelf)
        self.assertRegex(variable(CSS, "--en-c-tile-width"), r"cqi", "a tile's width does not follow its shelf")
        self.assertRegex(variable(CSS, "--en-c-tile-width-large"), r"cqi")

    def test_style_guide_breakpoint_not_in_px(self):
        for m in re.finditer(r"@media[^{]*", strip_comments(read("docs", "site.css"))):
            self.assertNotIn("px", m.group(0), f"site.css has a px breakpoint: {m.group(0).strip()}")


class SmallestBox(unittest.TestCase):
    def test_design_md_states_it_as_a_content_rule(self):
        rules = section(read("DESIGN.md"), "## Part 2: Rules")
        line = next((l for l in rules.splitlines() if "smallest supported box" in l), None)
        self.assertIsNotNone(line, "DESIGN.md Part 2 does not state the smallest supported box")
        self.assertIn("20rem wide by 15rem tall", line)
        for needle in ("list row", "hint bar", "focus ring", "scrolls"):
            self.assertIn(needle, line, f"the smallest box rule does not mention {needle!r}")

    def test_browser_check_uses_the_same_box(self):
        tree = ast.parse(read("tools", "browser_check.py"))
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ("SMALLEST", "FRAMES", "LARGE_FONT_PX"):
                    found[node.targets[0].id] = ast.literal_eval(node.value)
        self.assertEqual(tuple(found.get("SMALLEST", ())), (20, 15), "the browser check's smallest box is not 20rem by 15rem")
        self.assertEqual(tuple(found["FRAMES"][0]), (20, 15), "the frame checks do not start at the smallest box")
        self.assertGreater(max(w for w, h in found["FRAMES"]), 100, "no frame wider than 100rem, where text grows")
        self.assertGreater(found.get("LARGE_FONT_PX", 0), 16, "no run with a larger browser font size")

    def test_style_guide_shows_it(self):
        page = " ".join(re.sub(r"<[^>]+>", "", read("docs", "index.html")).split())
        self.assertIn("The smallest supported box is 20rem wide by 15rem tall", page)


class Source(unittest.TestCase):
    def test_token_comments_name_no_capture_or_device(self):
        for m in re.finditer(r"(--en-(?:text|space|size)-[\w-]+)\s*:[^;]*;([^\n]*)", TOKENS):
            for needle in ("Steam Deck", "Gaming Mode", "screenshot", "1280"):
                self.assertNotIn(needle, m.group(2), f"{m.group(1)}'s comment still names {needle!r}")

    def test_every_measured_token_is_labelled_steam_baseline(self):
        labels = {t["name"]: t["label"] for t in en.all_tokens(en.load())}
        for name, _ in TOKEN_CHANGES + [("--en-size-target", "44px")]:
            if name == "--en-space-tight":
                continue  # Enamel's choice, not a measurement
            self.assertEqual(labels[name], "Steam baseline", f"{name} is not labelled Steam baseline")

    def test_design_md_source_label_names_no_device(self):
        design = read("DESIGN.md")
        self.assertIn("**Steam baseline** = matched to Steam's Gaming Mode", design)
        self.assertNotIn("Steam Deck Gaming Mode screenshots", design)
        self.assertNotIn("**Observed**", design)


class NoNameChanged(unittest.TestCase):
    CLASSES = [".en-hintbar", ".en-hint", ".en-glyph", ".en-glyph--shoulder", ".en-tabs", ".en-tab",
               ".en-tab__count", ".en-dot", ".en-rows", ".en-row", ".en-row__meta", ".en-shelf", ".en-tile",
               ".en-tile--large", ".en-tile__frame", ".en-tile__title", ".en-button", ".en-button--primary",
               ".en-button--icon", ".en-toggle", ".en-progress", ".en-progress--thin", ".en-progress__fill",
               ".en-progress__head", ".en-menu", ".en-menu__item"]

    def test_tokens_and_variables_still_there(self):
        for name, _ in TOKEN_CHANGES:
            variable(TOKENS, name)
        for name in FIXED:
            variable(TOKENS, name)
        for name, _ in COMPONENT_CHANGES:
            variable(CSS, name)
        for name in FIXED_C:
            variable(CSS, name)

    def test_classes_still_there(self):
        body = strip_comments(CSS)
        for name in self.CLASSES:
            self.assertRegex(body, re.escape(name) + r"(?![\w-])", f"class {name} is gone")


class Changelog(unittest.TestCase):
    def setUp(self):
        text = read("CHANGELOG.md")
        m = re.search(r"^## 0\.6\.0,[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "no 0.6.0 entry")
        self.body = m.group(1)

    def test_every_changed_token_old_and_new(self):
        for name, old in TOKEN_CHANGES:
            new = V060[name]
            self.assertRegex(self.body, re.escape(f"`{old_name(name)}` was `{old}`") + r", now "
                             + re.escape(f"`{old_name(new)}`"),
                             f"the 0.6.0 entry does not say {name} changed from {old} to {new}")

    def test_every_changed_component_variable_old_and_new(self):
        for name, old in COMPONENT_CHANGES:
            new = V060[name]
            self.assertRegex(self.body, re.escape(f"`{old_name(name)}` was `{old}`") + r", now "
                             + re.escape(f"`{old_name(new)}`"),
                             f"the 0.6.0 entry does not say {name} changed from {old} to {new}")


if __name__ == "__main__":
    unittest.main()
