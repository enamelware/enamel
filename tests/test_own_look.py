# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #18, Enamel's own look: the new tokens, the three new style guide rules
(the grid unit, no pattern on anything interactive, contrast by the speckle), the
speckle images, satin and corners on every raised surface, one focus style per
kind of element (only things you press rise and drop), the unit audit, the
guidelines and the notes. How it all looks and moves in a browser is checked by
tests/own_look_check.py.

    scripts/test.sh unit tests.test_own_look
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_speckle  # noqa: E402
import check_guide  # noqa: E402
import enamel_tokens as en  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


GUIDELINES = [
    "Satin, never gloss.",
    "Patterns live on the page ground and in progress fills only. Nothing you can select is ever patterned.",
    "One border per element: no rims inside rings, no lips inside outlines.",
    "One focus style per kind of element: cream on a coral underside for things you press, a coral ring for tiles, a lift for rows.",
    "Cream is a neutral; the accent stays the only colour.",
    "Only things you press move physically.",
    "Every size is a multiple of 4 in its own unit (0.25rem if it grows with text, 4px if it does not) unless a listed exception applies.",
    "Ask of every size: should it grow when the user makes text bigger? Yes is rem, no is px. Never set the root font size.",
]
TOKENS = {t["name"]: t for t in en.all_tokens(en.load())}
CSS = read("components", "enamel-components.css")
BARE = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)


def rule(selector):
    m = re.search(r"(?:^|\n|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", BARE)
    if not m:
        raise AssertionError(f"no rule for {selector}")
    return m.group(1)


class Tokens(unittest.TestCase):
    def test_values(self):
        for name, value in (("--en-cream", "#F2EBDA"), ("--en-cream-pressed", "#E6DDC8"), ("--en-radius-face", "8px"),
                            ("--en-radius-panel", "12px"), ("--en-focus-underside", "4px"), ("--en-lift", "4px"),
                            ("--en-focus-ring-width", "4px"), ("--en-focus-ring-offset", "4px"),
                            ("--en-focus-fill", "var(--en-cream)")):
            self.assertEqual(TOKENS[name]["value"], value, name)

    def test_the_new_ones_are_enamels_own(self):
        for name in ("--en-cream", "--en-cream-pressed", "--en-radius-face", "--en-radius-panel", "--en-satin-light",
                     "--en-satin-edge", "--en-satin-shadow", "--en-focus-underside", "--en-lift", "--en-speckle-fill",
                     "--en-speckle-page", "--en-speckle-page-accent"):
            self.assertEqual(TOKENS[name]["label"], "Enamel", name)

    def test_satin_is_never_gloss(self):
        """A very faint light: no stop in the light or the rim is stronger than a tenth."""
        for name in ("--en-satin-light", "--en-satin-edge"):
            for alpha in re.findall(r"rgba\(255, 255, 255, ([\d.]+)\)", TOKENS[name]["value"]):
                self.assertLessEqual(float(alpha), 0.1, name)

    def test_no_name_was_removed(self):
        for name in ("--en-root-size", "--en-radius", "--en-focus-fill", "--en-focus-fill-ink", "--en-shadow-2"):
            self.assertIn(name, TOKENS)


def css_rules(css):
    """[(selector, {property: value})] for every plain rule, those inside @media too."""
    out = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        decls = {}
        for part in body.split(";"):
            if ":" in part:
                prop, value = part.split(":", 1)
                decls[prop.strip()] = value.strip()
        out.append((" ".join(selector.split()), decls))
    return out


def selectors(group):
    """The selectors in a selector list, split only at its top-level commas."""
    return re.split(r",(?![^()]*\))", group)


class Satin(unittest.TestCase):
    """Item 3: every raised surface is satin; item 1: their corners."""
    RAISED = (".en-row", ".en-button", ".en-tile__frame", '.en-tab[aria-selected="true"]', ".en-picker", ".en-toast",
              ".en-statpanel", ".en-band")

    def test_every_raised_surface_is_satin(self):
        for selector in self.RAISED:
            body = rule(selector)
            self.assertIn("background-image: var(--en-satin-light)", body, selector)
            self.assertRegex(body, r"box-shadow:\s*var\(--en-satin-edge\),\s*var\(--en-c-satin-shadow\)", selector)

    def test_the_round_marks_have_the_rim(self):
        for selector in (".en-steps > li::before",):
            self.assertIn("var(--en-satin-edge)", rule(selector), selector)

    def test_the_satin_is_a_rim_a_lip_and_a_short_shadow(self):
        edge = TOKENS["--en-satin-edge"]["value"]
        self.assertRegex(edge, r"inset 0 0 0 1px rgba\(255, 255, 255, [\d.]+\)", "the 1px soft rim all round")
        self.assertRegex(edge, r"(?:^|,\s*)0 1px 0 #[0-9A-Fa-f]{6}", "the 1px dark lip below")
        m = re.fullmatch(r"0 (\d+)px (\d+)px rgba\(0, 0, 0, ([\d.]+)\)", TOKENS["--en-satin-shadow"]["value"])
        self.assertTrue(m, "a single short soft shadow")
        self.assertLessEqual(int(m.group(1)), 4)
        self.assertLessEqual(int(m.group(2)), 8)
        self.assertLessEqual(float(m.group(3)), 0.3)

    def test_corners(self):
        for selector in (".en-row", ".en-button", ".en-tile__frame", ".en-tile::after", ".en-picker__row", ".en-band",
                         ".en-badge"):
            self.assertIn("border-radius: var(--en-radius-face)", rule(selector), selector)
        for selector in (".en-picker", ".en-statpanel", ".en-toast"):
            self.assertRegex(rule(selector), r"border-radius: var\(--en-radius-panel\)", selector)


class OneFocusStyle(unittest.TestCase):
    """Items 4, 7 and 8: one focus style per kind of element, and only things
    you press move physically."""

    def test_only_things_you_press_rise_or_drop(self):
        moving = []
        for selector, decls in css_rules(BARE):
            if "translateY" in decls.get("transform", "") or "--en-c-rise" in decls.get("transform", ""):
                moving.append(selector)
                for part in selectors(selector):
                    self.assertRegex(part, r"\.en-(button|picker__row)\b", selector)
        self.assertTrue(any(".en-button" in s for s in moving))
        self.assertTrue(any(".en-picker__row" in s for s in moving))

    def test_rows_tabs_toggles_and_the_menu_never_move(self):
        for selector, decls in css_rules(BARE):
            if re.match(r"\.en-(row|tab|toggle|menu__item)\b", selector) and not selector.startswith(".en-row > "):
                self.assertNotIn("transform", decls, selector)

    def test_the_underside_is_only_on_things_you_press(self):
        for selector, decls in css_rules(BARE):
            if "--en-focus-underside" in decls.get("box-shadow", ""):
                for part in selectors(selector):
                    self.assertRegex(part, r"\.en-(button|picker__row)\b", selector)

    def test_no_rim_inside_a_tabs_ring(self):
        self.assertRegex(BARE, r"\.en-tab:focus-visible\s*\{\s*box-shadow:\s*none;\s*\}")

    def test_a_badge_on_a_focused_picker_row_turns_to_the_page_colour(self):
        self.assertRegex(BARE, r'\.en-picker__row:is\(:focus-visible, \[data-focused="true"\]\) \.en-badge'
                               r'[^{]*\{\s*background: var\(--en-surface-page\);')

    def test_the_lighter_fallback_zeroes_what_it_drops(self):
        decls = dict(css_rules(BARE))['[data-en-lighter="true"]']
        self.assertEqual(decls["--en-c-rise"], "0px")
        for name in ("--en-c-satin-shadow", "--en-c-lift-shadow", "--en-c-press-shadow"):
            self.assertEqual(decls[name], "0 0 transparent", name)


class GridRule(unittest.TestCase):
    def test_it_catches_a_size_off_the_grid(self):
        for css in ("a { padding: 6px; }", "a { margin: 0.3rem; }", ":root { --en-c-x: 10px; }", "a { width: 1.1rem; }"):
            self.assertTrue(check_guide.grid_problems(css), css)

    def test_it_allows_each_listed_exception(self):
        for css in ("a { border: 1px solid; }", "a { outline-width: 2px; }", "a { border-radius: 999px; }",
                    "a { font-size: 1.16667rem; }", ":root { --en-text-small: 1.16667rem; }",
                    ":root { --en-shadow-2: 0px 3px 6px 0px #0000003D; }", ":root { --en-focus-affordance: 10px; }",
                    ":root { --en-c-backdrop-blur: 3px; }", "a { width: clamp(1.25rem, 0.83333rem + 0.41667vw, 1.5rem); }",
                    "a { width: 8px; height: 0.25rem; }"):
            self.assertEqual(check_guide.grid_problems(css), [], css)

    def test_it_ignores_the_speckle_images(self):
        self.assertEqual(check_guide.grid_problems(':root { --en-speckle-fill: url("data:image/svg+xml,M3.5px"); }'), [])

    def test_the_stylesheets_pass(self):
        for path in (en.CSS, check_guide.COMPONENTS, check_guide.SITE_CSS):
            self.assertEqual(check_guide.grid_problems(read(path)), [], path)


class PatternRule(unittest.TestCase):
    def test_it_catches_a_pattern_on_anything_else(self):
        for css in (".en-button { background-image: var(--en-speckle-fill); }",
                    ".en-row { background: var(--en-speckle-page); }",
                    '.en-tile { background-image: url("a.png"); }',
                    ".en-tab { background: repeating-linear-gradient(90deg, red 0 1px); }"):
            self.assertTrue(check_guide.pattern_problems(css), css)

    def test_it_allows_the_page_and_the_progress_fill(self):
        css = ".en-progress__fill { background-image: var(--en-speckle-fill); } .en-speckle { background-image: var(--en-speckle-page); }"
        self.assertEqual(check_guide.pattern_problems(css), [])

    def test_the_components_pass(self):
        self.assertEqual(check_guide.pattern_problems(CSS), [])


class Contrast(unittest.TestCase):
    def test_text_by_the_speckle_and_a_badge_on_cream_are_checked(self):
        kinds = {(c, w) for c, w, *_ in check_guide.PAIRS}
        self.assertIn(("Speckle", "muted text, by a cream fleck"), kinds)
        self.assertIn(("Speckle", "muted text, by an accent fleck"), kinds)
        self.assertIn(("Badge", "on the cream focus fill"), kinds)

    def test_the_accent_fleck_strength_matches_what_is_checked(self):
        self.assertIn(f"--en-c-speckle-accent: {build_speckle.ACCENT_STRONGEST:g};", BARE)

    def test_no_page_fleck_is_stronger_than_what_is_checked(self):
        for size, count, opacity in build_speckle.IMAGES["--en-speckle-page"][4]:
            self.assertLessEqual(opacity, build_speckle.PAGE_STRONGEST)


class Speckle(unittest.TestCase):
    def points(self, name):
        return [tuple(map(float, p)) for p in re.findall(r"M(-?[\d.]+) (-?[\d.]+)h0", build_speckle.svg(name))]

    def test_the_tokens_hold_what_the_script_makes(self):
        """Running the script again changes nothing."""
        for name in build_speckle.IMAGES:
            self.assertEqual(TOKENS[name]["value"], build_speckle.value(name), name)

    def test_no_grid_or_repeat(self):
        """Flecks are not lined up: hardly any share a row or a column, and they
        reach every part of the image."""
        for name, (_, width, height, _, _) in build_speckle.IMAGES.items():
            points = self.points(name)
            self.assertGreater(len(points), 15, name)
            self.assertGreater(len({round(x) for x, _ in points}), len(points) * 0.6, name)
            self.assertGreater(len({round(y) for _, y in points}), len(points) * 0.3 if height < 64 else len(points) * 0.6, name)
            for left, right in ((0, width / 2), (width / 2, width)):
                self.assertTrue(any(left <= x < right for x, _ in points), name)

    def test_an_edge_fleck_is_drawn_again_opposite_so_it_tiles(self):
        import random
        path = build_speckle.flecks(random.Random(1), 100, 100, 2, 400)
        self.assertRegex(path, r"M-[\d.]+ ")
        self.assertRegex(path, r"M10[01]\.\d ")

    def test_nothing_animates(self):
        for selector in (".en-speckle", ".en-speckle::before", ".en-progress__fill"):
            self.assertNotIn("animation", rule(selector), selector)

    def test_it_never_names_an_accent(self):
        """The accent flecks are a mask filled with the active accent."""
        self.assertNotIn("EE8A72", TOKENS["--en-speckle-page-accent"]["value"].upper())
        self.assertNotIn("EE8A72", TOKENS["--en-speckle-fill"]["value"].upper())
        self.assertIn("background-color: var(--en-accent)", rule(".en-speckle::before"))

    def test_they_need_no_new_file(self):
        self.assertIn('url("data:image/svg+xml,', TOKENS["--en-speckle-fill"]["value"])


class Units(unittest.TestCase):
    def test_enamel_never_sets_the_root_font_size(self):
        sheets = [read("tokens", "enamel.css"), CSS, read("docs", "site.css")]
        # The style guide pages' own <style> blocks too: an `html, body` rule
        # there made the Components and Motion pages half as big again.
        for page in sorted(os.listdir(os.path.join(ROOT, "docs"))):
            if page.endswith(".html"):
                sheets += re.findall(r"<style>(.*?)</style>", read("docs", page), flags=re.S)
        for css in sheets:
            bare = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
            for selector, body in re.findall(r"([^{}]*)\{([^{}]*)\}", bare):
                if re.search(r"(^|,)\s*(:root|html)\s*(,|$)", selector):
                    self.assertNotIn("font-size", body, selector)
        self.assertRegex(BARE, r":root\s*\{\s*zoom:\s*var\(--en-root-size\);\s*\}")

    def test_px_for_what_should_not_grow(self):
        for name in ("--en-c-button-padding", "--en-c-tab-padding", "--en-c-picker-inset", "--en-c-progress-height",
                     "--en-c-progress-thin", "--en-c-menu-bar", "--en-c-glyph-shoulder-radius"):
            self.assertRegex(BARE, re.escape(name) + r":\s*\d+px;", name)

    def test_progress_heights(self):
        self.assertIn("--en-c-progress-height: 12px;", BARE)
        self.assertIn("--en-c-progress-thin: 8px;", BARE)

    def test_things_that_hold_text_have_a_minimum_height(self):
        for selector in (".en-row", ".en-button", ".en-tab", ".en-picker__row", ".en-toast", ".en-hintbar"):
            self.assertIn("min-height", rule(selector), selector)
            self.assertNotRegex(rule(selector), r"(?<![-\w])height:", selector)

    def test_breakpoints_are_in_rem(self):
        for css in (CSS, read("docs", "site.css")):
            for query in re.findall(r"@media[^{]*", css):
                self.assertNotRegex(query, r"\dpx", query)


class Fallback(unittest.TestCase):
    def test_it_drops_the_soft_shadows_and_movement_only(self):
        body = rule('[data-en-lighter="true"]')
        for name in ("--en-c-rise", "--en-c-satin-shadow", "--en-c-lift-shadow", "--en-c-press-shadow"):
            self.assertIn(name, body)
        self.assertNotIn("background", body)
        self.assertNotIn("speckle", body)
        self.assertNotIn("underside", body)

    def test_it_is_documented_and_shown(self):
        self.assertIn('data-en-lighter="true"', read("DESIGN.md"))
        self.assertIn('data-en-lighter="true"', read("docs", "components.html"))


class Guidelines(unittest.TestCase):
    def test_same_wording_in_design_md_and_on_the_overview(self):
        rules = en.read_rules(os.path.join(ROOT, "DESIGN.md"))
        overview = read("docs", "overview.html")
        for line in GUIDELINES:
            self.assertIn(line, rules)
            self.assertIn(f"<li>{line}</li>", overview)

    def test_the_accent_rule_names_the_underside_and_speckle(self):
        rule_text = next(r for r in en.read_rules(os.path.join(ROOT, "DESIGN.md")) if r.startswith("The accent appears"))
        self.assertIn("underside", rule_text)
        self.assertIn("speckle", rule_text)

    def test_white_focus_is_gone_from_the_rules(self):
        focus = next(r for r in en.read_rules(os.path.join(ROOT, "DESIGN.md")) if r.startswith("Focus:"))
        self.assertNotIn("white", focus)

    def test_design_md_lists_the_exceptions(self):
        scaling = read("DESIGN.md").split("## Scaling", 1)[1].split("\n## ", 1)[0]
        for needle in ("hairlines", "999px", "speckle", "ratios", "durations", "text sizes", "--en-shadow-",
                       "--en-focus-affordance", "backdrop blur", "upper limit", "never sets the root font size"):
            self.assertIn(needle, scaling)


class Overview(unittest.TestCase):
    # #19: the before-and-after story is case-study material and lives outside
    # the repo; the guidelines it ended with stay, under Rules.
    def test_the_case_study_is_not_in_the_repo(self):
        text = read("docs", "overview.html")
        for needle in ('id="steam-to-enamel"', 'href="#steam-to-enamel"', "What stays Steam", "Before:", "was-row"):
            self.assertNotIn(needle, text)

    def test_the_guidelines_stay_under_rules(self):
        text = read("docs", "overview.html")
        rules = text[text.index('id="rules"'):text.index('<footer class="end">')]
        self.assertIn("The guidelines", rules)
        for line in GUIDELINES:
            self.assertIn(f"<li>{line}</li>", rules)


class Release(unittest.TestCase):
    def test_version_changelog_and_decisions(self):
        version = read("VERSION").strip()
        self.assertGreaterEqual(tuple(map(int, version.split("."))), (0, 11, 0))
        self.assertRegex(read("CHANGELOG.md"), r"## 0\.11\.0, \d{4}-\d{2}-\d{2} \(visual\)")
        decisions = read("DECISIONS.md")
        self.assertIn("## 2026-11-06, Enamel's own look", decisions)
        self.assertIn("kitchenware", decisions)

    def test_no_name_was_removed_since_the_last_release(self):
        r = subprocess.run(["git", "show", "v0.10.0:components/enamel-components.css"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            self.skipTest("the v0.10.0 tag can't be read here")
        names = lambda css: set(re.findall(r"\.(en-[A-Za-z0-9_-]+)|(--en-c-[a-z0-9-]+)\s*:|\[(data-[a-z-]+)[\]=]",
                                           re.sub(r"/\*.*?\*/", "", css, flags=re.S)))
        self.assertEqual(names(r.stdout) - names(CSS), set())
        t = subprocess.run(["git", "show", "v0.10.0:tokens/enamel.css"], cwd=ROOT, capture_output=True, text=True)
        old = set(re.findall(r"(--en-[a-z0-9-]+)\s*:", t.stdout))
        self.assertEqual(old - set(TOKENS), set())


if __name__ == "__main__":
    unittest.main()
