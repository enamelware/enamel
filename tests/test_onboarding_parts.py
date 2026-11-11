# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #16: five small components for onboarding (0.9.0).

Reads the files directly:
  - the step label, group band, badge, message in a row and numbered steps
    are in the components stylesheet, sized and coloured only from tokens
    and existing component variables (no new token or variable);
  - the badge only changes colour on a focused row or a selected tab, and the
    outlined band draws its line without a border, so neither changes size;
  - the message takes no space while empty, fades in, and not in reduced
    motion (both reduced-motion blocks);
  - the guide check knows every new state and colour pair, and the Resize
    page has each new part in a frame;
  - DESIGN.md describes each; the 0.9.0 changelog entry is marked visual,
    renames nothing and lists each class as new; MIGRATION.md leaves them out.

How they look and measure in the browser (sizes on focus, the message making
its row taller and never wider, bands, steps lining up) is checked by
tests/onboarding_parts_check.py.

    scripts/test.sh unit tests.test_onboarding_parts
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_guide  # noqa: E402
import resize_page  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


CSS = re.sub(r"/\*.*?\*/", "", read("components", "enamel-components.css"), flags=re.S)
CLASSES = ["en-steplabel", "en-band", "en-band--outline", "en-band__name", "en-band__count", "en-badge",
           "en-row__message", "en-steps"]
LENGTH = re.compile(r"(?<![\w.-])-?\d*\.?\d+(?:px|em|rem|vh|vw|pt|ch|cqi)\b")


def rules(selector_part):
    """[(selector, body)] for every rule whose selector names selector_part."""
    return [(" ".join(s.split()), b) for s, b in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS)
            if re.search(re.escape(selector_part) + r"(?![\w-])", s)]


def decls(body):
    return {p.strip(): v.strip() for p, v in re.findall(r"([-\w]+)\s*:\s*([^;]+)", body)}


class Stylesheet(unittest.TestCase):
    def test_every_new_class_is_styled(self):
        for cls in CLASSES:
            self.assertTrue(rules("." + cls), f".{cls} has no rule")

    def test_only_tokens_and_existing_variables(self):
        defined = set(re.findall(r"(--en-[a-z0-9-]+)\s*:", read("tokens", "enamel.css") + CSS))
        for cls in CLASSES:
            for sel, body in rules("." + cls):
                for prop, value in decls(body).items():
                    with self.subTest(selector=sel, prop=prop):
                        self.assertIsNone(LENGTH.search(value), f"{sel} {prop}: a fixed size ({value})")
                        for ref in re.findall(r"var\((--[\w-]+)\)", value):
                            self.assertIn(ref, defined)

    def test_no_new_component_variable(self):
        names = re.findall(r"(--en-c-[a-z0-9-]+)\s*:", CSS)
        for word in ("band", "badge", "step", "message"):
            self.assertFalse([n for n in names if word in n], f"a new component variable for the {word}")

    def test_badge_only_changes_colour(self):
        # rules that style the badge itself in a state (not its row or tab)
        changing = [(s, b) for s, b in rules(".en-badge") if s != ".en-badge" and s.endswith(".en-badge")]
        self.assertTrue(changing)
        for sel, body in changing:
            self.assertTrue(set(decls(body)) <= {"background", "background-color", "color"}, f"{sel}: {body}")
        self.assertIn("var(--en-surface-page)", "".join(b for _, b in changing))

    def test_a_badge_that_does_not_fit_moves_under_the_title(self):
        tab = decls(dict(rules(".en-badge"))[".en-tab:has(> .en-badge)"])
        self.assertEqual(tab["flex-wrap"], "wrap")
        row = decls(dict(rules(".en-badge"))[".en-row:has(> .en-row__message:not(:empty), > .en-badge)"])
        self.assertEqual(row["flex-wrap"], "wrap")

    def test_outlined_band_draws_its_line_without_a_border(self):
        outline = decls(rules(".en-band--outline")[0][1])
        self.assertNotIn("border", outline)
        self.assertEqual(outline["box-shadow"], "inset 0 0 0 var(--en-c-icon-stroke) var(--en-text-muted)")
        self.assertEqual(outline["background"], "none")
        self.assertEqual(decls(rules(".en-band")[0][1])["background-color"], "var(--en-surface-control)")

    def test_band_cannot_take_focus(self):
        for sel, _ in rules(".en-band"):
            self.assertNotRegex(sel, r"focus")

    def test_message_waits_empty_and_wraps_its_row(self):
        self.assertIn("display: none", dict(rules(".en-row__message"))[".en-row__message:empty"])
        wrap = decls(dict(rules(".en-row__message"))[".en-row:has(> .en-row__message:not(:empty), > .en-badge)"])
        self.assertEqual(wrap["flex-wrap"], "wrap")
        self.assertEqual(decls(dict(rules(".en-row__message"))[".en-row__message"])["flex-basis"], "100%")
        self.assertIn("color: var(--en-danger)", dict(rules(".en-row__message"))[".en-row__message .en-icon"])

    def test_message_turns_dark_on_a_focused_picker_row(self):
        picker = [b for s, b in rules(".en-row__message") if s.startswith(".en-picker__row:is(")]
        self.assertTrue(picker, "no rule for a message on a focused picker row")
        self.assertIn("color: var(--en-focus-fill-ink)", picker[0])
        self.assertIn(("Row message", "text, focused picker row", "--en-focus-fill-ink", "--en-focus-fill", "text"),
                      check_guide.PAIRS)

    def test_message_fade_is_cancelled_in_reduced_motion(self):
        self.assertIn("animation: en-fade-in var(--en-motion-fast)", dict(rules(".en-row__message"))[".en-row__message"])
        for prefix in (':root:not([data-en-motion="full"])', '[data-en-motion="reduced"]'):
            self.assertIn(f"{prefix} .en-row__message {{ animation: none; }}", read("components", "enamel-components.css"))

    def test_steps_number_is_a_glyph_sized_mark(self):
        mark = decls(dict(rules(".en-steps"))[".en-steps > li::before"])
        self.assertEqual(mark["width"], "var(--en-c-glyph-size)")
        self.assertEqual(mark["content"], "counter(en-step)")
        item = decls(dict(rules(".en-steps"))[".en-steps > li"])
        self.assertEqual(item["grid-template-columns"], "var(--en-c-glyph-size) minmax(0, 1fr)")


class GuideCheck(unittest.TestCase):
    def test_every_new_state_is_required_on_the_components_page(self):
        required = {cls for cls, _, _ in check_guide.STATES}
        for cls in CLASSES:
            self.assertIn(cls, required)
        self.assertIn(("en-row__message", 'role="status"', "message in a row, announced"), check_guide.STATES)

    def test_every_new_colour_pair_is_checked(self):
        comps = {c for c, *_ in check_guide.PAIRS}
        for comp in ("Step label", "Group band", "Badge", "Row message", "Steps"):
            self.assertIn(comp, comps)
        pairs = {(fg, bg) for _, _, fg, bg, kind in check_guide.PAIRS if kind != "disabled"}
        self.assertIn(("--en-text-strong", "--en-surface-control"), pairs)   # message on a focused row
        self.assertIn(("--en-text-soft", "--en-surface-page"), pairs)        # badge on a focused row
        self.assertIn(("--en-focus-fill-ink", "--en-danger"), pairs)         # the error mark

    def test_resize_page_has_each_part_in_a_frame(self):
        markup = "".join(m for _, m, *_ in resize_page.BY_HAND)
        for cls in ("en-steplabel", "en-band--outline", "en-badge", "en-row__message", "en-steps"):
            self.assertIn(cls, markup)


class Docs(unittest.TestCase):
    def test_design_md_describes_each(self):
        part3 = read("DESIGN.md").split("## Part 3: Components", 1)[1]
        for title, cls in [("Step label", "en-steplabel"), ("Group band", "en-band"), ("Badge", "en-badge"),
                           ("Message in a row", "en-row__message"), ("Numbered steps", "en-steps")]:
            self.assertIn(f"### {title}\n", part3)
            section = part3.split(f"### {title}\n", 1)[1].split("\n### ", 1)[0]
            self.assertIn(f"`.{cls}`", section)
            self.assertIn("- Motion:", section)

    def test_changelog_entry(self):
        text = read("CHANGELOG.md")
        m = re.search(r"^## 0\.9\.0,[^\n]*\(visual\)\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "no 0.9.0 entry marked visual")
        body = m.group(1)
        self.assertIn("**Renamed or removed: none.**", body)
        self.assertIn("**Who should adopt it, and when:**", body)
        self.assertIn('"Bring in Enamel 0.9.0"', body)
        for cls in CLASSES:
            self.assertRegex(body, re.escape(f"`.{cls}`") + r"[^\n]*new")

    def test_version(self):
        self.assertGreaterEqual(tuple(map(int, read("VERSION").strip().split("."))), (0, 9, 0))

    def test_migration_leaves_new_classes_out(self):
        text = read("MIGRATION.md")
        for cls in CLASSES:
            self.assertNotIn(f"`{cls}`", text)


if __name__ == "__main__":
    unittest.main()
