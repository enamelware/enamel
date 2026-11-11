# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #15: Steam baseline sizes, scaled from one root size (0.8.0).

Reads the files directly:
  - every size token and component variable has its Steam baseline value
    (Kettle Video's sizing report, both passes), naming no capture or device;
  - every size except text is a multiple of 4px at 16px per rem; px is kept
    only for lines (hairlines, the focus ring, corners), blur, shadows and the
    touch target;
  - one root size: --en-root-size on :root, applied as the page's root font
    size by the components stylesheet;
  - the components use the new sizes (rows with a control, buttons, the gap
    between an icon and its text, rows, shelves, the side menu);
  - DESIGN.md explains the scaling and has the rule that apps size their own
    layout with the same scale; DECISIONS.md and the 0.8.0
    changelog entry record it, old and new values side by side.

That the root size really scales every rem size in the browser, and leaves
the px ones alone, is checked by tests/root_size_check.py.

    scripts/test.sh unit tests.test_steam_baseline
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def root_block(css):
    return re.search(r":root\s*\{([^}]*)\}", strip_comments(css)).group(1)


def table(css):
    return {n: " ".join(v.split()) for n, v in re.findall(r"(--en-[a-z0-9-]+)\s*:\s*([^;]+);", root_block(css))}


def rule(css, selector):
    m = re.search(r"(?:^|\n|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", strip_comments(css))
    if not m:
        raise AssertionError(f"no rule for {selector}")
    return m.group(1)


TOKENS_CSS = read("tokens", "enamel.css")
COMPONENTS_CSS = read("components", "enamel-components.css")
TOKENS = table(TOKENS_CSS)
VARS = table(COMPONENTS_CSS)
ALL = {**TOKENS, **VARS}
NORMAL_PX = 16

# The Steam baseline at 16px per rem: (name, px). For a growing token it is
# its base, on pages up to 100rem wide.
BASELINE = [
    ("--en-size-row", 64), ("--en-size-row-control", 96), ("--en-c-picker-row", 72), ("--en-text-body", 24),
    ("--en-text-caps", 17), ("--en-size-button", 60), ("--en-size-bar", 60), ("--en-space-gutter-grid", 48),
    ("--en-space-gutter", 36), ("--en-size-tile-portrait", 200), ("--en-space-inset", 20),
    ("--en-c-picker-inset", 24), ("--en-c-button-padding", 36), ("--en-c-tab-padding", 28),
    ("--en-space-gap", 12), ("--en-space-icon", 16), ("--en-c-hint-gap", 28), ("--en-c-menu-item-height", 72),
    ("--en-c-menu-bar", 8), ("--en-c-menu-width", 360), ("--en-c-tile-large-max", 452), ("--en-c-shelf-gap", 20),
    ("--en-text-title", 33), ("--en-text-heading", 24), ("--en-text-small", 18.667),
]
# Text keeps its measured size; it is not rounded to 4.
TEXT = {"--en-text-title", "--en-text-heading", "--en-text-body", "--en-text-small", "--en-text-caps",
        "--en-c-glyph-text", "--en-c-text-detail"}
# Sizes kept in px on purpose: lines, corners, blur and the touch target.
PX_ALLOWED = {"--en-radius", "--en-radius-pill", "--en-focus-ring-width", "--en-focus-ring-offset",
              "--en-focus-ring-start", "--en-focus-affordance", "--en-size-target", "--en-c-icon-stroke",
              "--en-c-backdrop-blur", "--en-radius-face", "--en-radius-panel", "--en-focus-underside", "--en-lift",
              "--en-satin-edge", "--en-satin-shadow", "--en-lift-shadow", "--en-press-shadow", "--en-sunken",
              "--en-c-glyph-shoulder-radius", "--en-c-tab-padding", "--en-c-button-padding", "--en-c-progress-height",
              "--en-c-progress-thin", "--en-c-menu-bar", "--en-c-picker-inset", "--en-c-tile-glow", "--en-c-rise",
              "--en-c-satin-shadow", "--en-c-lift-shadow", "--en-c-press-shadow", "--en-c-focus-stroke"}
NEW_TOKENS = ["--en-root-size", "--en-size-button", "--en-size-row-control", "--en-size-tile-portrait",
              "--en-space-gutter-grid", "--en-space-icon"]
NEW_VARS = ["--en-c-menu-width", "--en-c-shelf-gap"]
REM = re.compile(r"(-?\d*\.?\d+)rem\b")


def base_px(value):
    """A size's px at 16px per rem: a plain rem value, or a growing clamp()'s base."""
    m = re.fullmatch(r"(-?\d*\.?\d+)rem", value)
    if m:
        return float(m.group(1)) * NORMAL_PX
    m = re.fullmatch(r"(\d+)px", value)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"clamp\((\d*\.?\d+)rem,[^,]*vw,\s*\d*\.?\d+rem\)", value)
    if m:
        return float(m.group(1)) * NORMAL_PX
    raise AssertionError(f"not a plain or growing rem size: {value}")


class Baseline(unittest.TestCase):
    def test_every_size_has_its_steam_baseline(self):
        for name, px in BASELINE:
            with self.subTest(name=name):
                self.assertAlmostEqual(base_px(ALL[name]), px, delta=0.01, msg=f"{name} is {ALL[name]}")

    def test_the_detail_text_is_the_small_text(self):
        self.assertEqual(VARS["--en-c-text-detail"], "var(--en-text-small)")

    def test_new_names_are_defined(self):
        for name in NEW_TOKENS:
            self.assertIn(name, TOKENS)
        for name in NEW_VARS:
            self.assertIn(name, VARS)


class MultiplesOfFour(unittest.TestCase):
    def test_every_rem_size_is_a_multiple_of_4px(self):
        checked = 0
        for name, value in ALL.items():
            if name in TEXT:
                continue
            m = re.fullmatch(r"clamp\((\d*\.?\d+)rem,[^,]*vw,[^)]*\)", value)
            numbers = [m.group(1)] if m else REM.findall(value)
            for n in numbers:
                px = float(n) * NORMAL_PX
                with self.subTest(name=name, value=n):
                    self.assertAlmostEqual(px / 4, round(px / 4), places=6,
                                           msg=f"{name}: {n}rem is {px:g}px, not a multiple of 4")
                checked += 1
        self.assertGreater(checked, 30)

    def test_px_only_for_lines_corners_blur_and_the_touch_target(self):
        for name, value in ALL.items():
            if name.startswith("--en-shadow"):
                continue
            if re.search(r"\d+px\b", value):
                self.assertIn(name, PX_ALLOWED, f"{name} is in px ({value}), so it ignores the root size")

    def test_the_kept_px_sizes(self):
        self.assertEqual(TOKENS["--en-size-target"], "44px")
        self.assertEqual(TOKENS["--en-focus-ring-width"], "4px")
        self.assertEqual(VARS["--en-c-icon-stroke"], "2px")


class OneRootSize(unittest.TestCase):
    def test_the_root_size_token(self):
        self.assertEqual(TOKENS["--en-root-size"], "100%")

    def test_the_components_apply_it_to_the_root(self):
        self.assertRegex(strip_comments(COMPONENTS_CSS), r":root\s*\{\s*zoom:\s*var\(--en-root-size\);\s*\}")

    def test_nothing_reads_the_screen(self):
        for name, css in (("tokens", TOKENS_CSS), ("components", COMPONENTS_CSS)):
            bare = strip_comments(css)
            self.assertNotRegex(bare, r"\d(?:vh|dvh|svh|lvh|vmin|vmax)\b", f"{name} sizes something from the screen's height")
            self.assertNotRegex(bare, r"@media[^{]*(?:height|aspect-ratio|resolution)", f"{name} has a screen query")


class Components(unittest.TestCase):
    def test_rows_with_a_control_are_taller(self):
        self.assertIn("min-height: var(--en-size-row-control)", rule(COMPONENTS_CSS, ".en-row:has(> .en-toggle, > .en-button)"))
        self.assertIn("min-height: var(--en-size-row)", rule(COMPONENTS_CSS, ".en-row"))

    def test_rows_are_a_gap_apart(self):
        self.assertIn("gap: var(--en-space-gap)", rule(COMPONENTS_CSS, ".en-rows"))

    def test_buttons_are_button_height_never_below_the_touch_target(self):
        self.assertIn("min-height: max(var(--en-size-target), var(--en-size-button))", rule(COMPONENTS_CSS, ".en-button"))

    def test_an_icon_sits_an_icon_gap_from_its_text(self):
        for selector in (".en-hint", ".en-button", ".en-toast"):
            self.assertIn("gap: var(--en-space-icon)", rule(COMPONENTS_CSS, selector), selector)

    def test_shelf_and_menu(self):
        self.assertIn("gap: var(--en-c-shelf-gap)", rule(COMPONENTS_CSS, ".en-shelf"))
        self.assertIn("width: min(var(--en-c-menu-width), 100%)", rule(COMPONENTS_CSS, ".en-menu"))

    def test_bigger_parts_still_fit_a_narrow_space(self):
        """Two hints share a line, a long tab wraps its label, and a one-line
        action bar is as tall as its buttons need, in the smallest supported box
        (tools/browser_check.py measures these in Firefox)."""
        self.assertIn("padding: var(--en-space-tight) min(var(--en-space-gutter), 5%)", rule(COMPONENTS_CSS, ".en-hintbar"))
        tab = rule(COMPONENTS_CSS, ".en-tab")
        self.assertIn("overflow-wrap: anywhere", tab)
        self.assertNotIn("white-space: nowrap", tab)
        self.assertIn("min-height: calc(max(var(--en-size-target), var(--en-size-button)) + 2 * var(--en-space-tight))",
                      rule(COMPONENTS_CSS, ".en-actionbar"))

    def test_toggle_thumb_fits_its_track(self):
        rem = lambda n: float(VARS[n].removesuffix("rem"))
        self.assertAlmostEqual(rem("--en-c-toggle-thumb") + 2 * rem("--en-c-toggle-padding"),
                               rem("--en-c-toggle-height"))


class Docs(unittest.TestCase):
    def test_design_md_explains_the_scaling_and_the_rule(self):
        design = read("DESIGN.md")
        rules = re.search(r"^## Part 2: Rules\n(.*?)(?=^## )", design, re.S | re.M).group(1)
        self.assertRegex(rules, r"Apps size their own layout with the same scale[^\n]*never[^\n]*pixels")
        self.assertIn("## Scaling", design)
        scaling = design.split("## Scaling", 1)[1].split("\n## ", 1)[0]
        for needle in ("--en-root-size", "<html>", "multiple of 4", "px"):
            self.assertIn(needle, scaling)

    def test_the_baseline_names_no_capture_or_device(self):
        both = read("tokens", "enamel.css") + read("components", "enamel-components.css")
        for name, _ in BASELINE:
            line = re.search(r"^\s*" + re.escape(name) + r"\s*:[^\n]*", both, re.M)
            self.assertIsNotNone(line, f"{name} is not defined")
            for needle in ("Deck", "screenshot", "capture", "1280"):
                self.assertNotIn(needle, line.group(0), f"{name}'s line names {needle!r}")

    def test_decisions_dated(self):
        text = read("DECISIONS.md")
        self.assertIn("## 2026-10-29, Gaming Mode measured larger than Enamel's old sizes", text)
        self.assertIn("## 2026-10-29, the interface scales from one root size", text)

    def test_changelog_lists_old_and_new(self):
        text = read("CHANGELOG.md")
        m = re.search(r"^## 0\.8\.0,[^\n]*\(visual\)\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "no 0.8.0 entry marked visual")
        body = m.group(1)
        self.assertIn("**Renamed or removed: none.**", body)
        self.assertIn("**Who should adopt it, and when:**", body)
        for name, _ in BASELINE:
            self.assertIn(f"`{name}`", body)
        for name in NEW_TOKENS + NEW_VARS:
            self.assertRegex(body, re.escape(f"`{name}`") + r"[^\n]*(?:added|new)", f"{name} is not listed as added")


if __name__ == "__main__":
    unittest.main()
