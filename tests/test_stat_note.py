# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #17: the stat panel, stat pair and note (0.10.0).

Reads the files directly:
  - every new class is in the components stylesheet, sized and coloured only
    from tokens and component variables, with no fixed size;
  - no accent, success, warning or error colour, and no state of any kind
    (hover, focus, data-focused);
  - the pair is a container that wraps, with no media or container query;
  - its minimum width and the notes' gap are multiples of 4 at 16px per rem;
  - the guide check knows every new state and colour pair, and the Resize page
    has each part in a frame;
  - DESIGN.md describes each; the 0.10.0 changelog entry is marked visual,
    renames nothing and lists each class as new; MIGRATION.md leaves them out;
  - VERSION is at least 0.10.0, and against the v0.9.0 tag (local git history
    only) no token is added, nothing is renamed or removed, and the only new
    names are the ones this issue lists.

How they measure in the browser (stacking, focus, hover, spacing, overflow,
multiples of 4) is checked by tests/stat_note_check.py.

    scripts/test.sh unit tests.test_stat_note
"""
import os
import re
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_guide  # noqa: E402
import components_page  # noqa: E402
import resize_page  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


CSS = re.sub(r"/\*.*?\*/", "", read("components", "enamel-components.css"), flags=re.S)
CLASSES = ["en-statpair", "en-statpanel", "en-statpanel__counts", "en-statpanel__count", "en-statpanel__number",
           "en-statpanel__path", "en-statpanel__notset", "en-note"]
LENGTH = re.compile(r"(?<![\w.-])-?\d*\.?\d+(?:px|em|rem|vh|vw|pt|ch|cqi)\b")


def rules(selector_part):
    """[(selector, body)] for every rule whose selector names selector_part."""
    return [(" ".join(s.split()), b) for s, b in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS)
            if re.search(re.escape(selector_part) + r"(?![\w-])", s)]


def decls(body):
    return {p.strip(): v.strip() for p, v in re.findall(r"([-\w]+)\s*:\s*([^;]+)", body)}


class Stylesheet(unittest.TestCase):
    def test_every_class_has_a_rule(self):
        for cls in CLASSES:
            self.assertTrue(rules("." + cls), f".{cls} has no rule")

    def test_only_tokens_and_variables(self):
        defined = set(re.findall(r"(--en-[a-z0-9-]+)\s*:", read("tokens", "enamel.css") + CSS))
        for cls in CLASSES:
            for sel, body in rules("." + cls):
                for prop, value in decls(body).items():
                    with self.subTest(selector=sel, prop=prop):
                        self.assertIsNone(LENGTH.search(value), f"{sel} {prop}: a fixed size ({value})")
                        for ref in re.findall(r"var\((--[\w-]+)\)", value):
                            self.assertIn(ref, defined)

    def test_no_accent_or_status_colour(self):
        for cls in CLASSES:
            for sel, body in rules("." + cls):
                self.assertNotRegex(body, r"--en-(accent|success|warning|danger|green|yellow|red|focus)", sel)

    def test_no_state_of_any_kind(self):
        for cls in CLASSES:
            for sel, _ in rules("." + cls):
                self.assertNotRegex(sel, r":hover|:focus|:active|data-focused|aria-", sel)

    def test_no_motion(self):
        for cls in CLASSES:
            for sel, body in rules("." + cls):
                self.assertNotRegex(body, r"\b(transition|animation)", sel)

    def test_no_row_style_reaches_a_note(self):
        for sel, _ in rules(".en-note"):
            self.assertNotIn("en-row", sel)

    def test_the_pair_wraps_without_a_query(self):
        pair = decls(dict(rules(".en-statpair"))[".en-statpair"])
        self.assertEqual(pair["display"], "flex")
        self.assertEqual(pair["flex-wrap"], "wrap")
        in_pair = decls(dict(rules(".en-statpanel"))[".en-statpair > .en-statpanel"])
        self.assertEqual(in_pair["flex"], "1 1 var(--en-c-statpanel-min)")
        panel = decls(dict(rules(".en-statpanel"))[".en-statpanel"])
        self.assertNotIn("flex", panel, "outside a pair, a column parent would turn its minimum width into a height")
        self.assertEqual(panel["min-width"], "0")
        for block in re.findall(r"@(?:media|container)[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", CSS):
            self.assertNotRegex(block, r"en-(statp|note)")

    def test_panel_is_a_raised_surface(self):
        panel = decls(dict(rules(".en-statpanel"))[".en-statpanel"])
        self.assertEqual(panel["background-color"], "var(--en-surface-raised)")
        self.assertEqual(panel["border-radius"], "var(--en-radius-panel)")

    def test_text_colours_and_sizes(self):
        got = {c: decls(dict(rules(c))[c]) for c in (".en-statpanel__number", ".en-statpanel__path",
                                                     ".en-statpanel__notset", ".en-note")}
        self.assertEqual(got[".en-statpanel__number"]["font-size"], "var(--en-text-title)")
        self.assertEqual(got[".en-statpanel__path"]["color"], "var(--en-text-soft)")
        self.assertEqual(got[".en-statpanel__notset"]["color"], "var(--en-text-muted)")
        self.assertEqual(got[".en-note"]["font-size"], "var(--en-text-small)")
        self.assertEqual(got[".en-note"]["color"], "var(--en-text-soft)")

    def test_new_sizes_are_multiples_of_4(self):
        for name in ("--en-c-statpanel-min", "--en-c-note-gap"):
            m = re.search(re.escape(name) + r"\s*:\s*([\d.]+)rem", CSS)
            self.assertIsNotNone(m, f"{name} is not in rem")
            self.assertEqual(float(m.group(1)) * 16 % 4, 0, name)

    def test_stacked_notes_are_8px_apart(self):
        self.assertRegex(CSS, r"--en-c-note-gap:\s*0\.5rem")
        self.assertEqual(decls(dict(rules(".en-note"))[".en-note + .en-note"])["margin-top"], "var(--en-c-note-gap)")


class Markup(unittest.TestCase):
    def test_a_panel_names_its_counts_and_path(self):
        one = components_page.stat_panel([(124, "movies")], "SD card › Films")
        self.assertIn('aria-label="124 movies, SD card › Films"', one)
        two = components_page.stat_panel([(18, "TV shows"), (240, "episodes")], "Internal storage › Videos")
        self.assertIn('aria-label="18 TV shows, 240 episodes, Internal storage › Videos"', two)

    def test_not_set_panels_can_be_told_apart(self):
        movies = components_page.stat_panel(None, "Movies")
        self.assertIn(">Not set<", movies)
        self.assertIn('aria-label="Movies, not set"', movies)
        self.assertNotIn("en-statpanel__number", movies)
        shows = components_page.stat_panel(None, "TV shows")
        self.assertIn('aria-label="TV shows, not set"', shows)
        # By eye too: the visible second line says which kind it is.
        self.assertIn('<span class="en-statpanel__path">Movies</span>', movies)
        self.assertIn('<span class="en-statpanel__path">TV shows</span>', shows)

    def test_the_note_icon_is_optional_and_hidden(self):
        self.assertNotIn("en-icon", components_page.note("Plain"))
        self.assertIn('aria-hidden="true"', components_page.note("With", icon=True))

    def test_the_note_icon_is_neutral_and_drawn_with_the_text_colour(self):
        icon = components_page.note("With", icon=True)
        self.assertIn('stroke="currentColor"', icon)
        self.assertNotRegex(icon, r"#[0-9A-Fa-f]{3,8}\b|\b(?:rgb|hsl)a?\(|<image|<use|href=")
        for sel, body in rules(".en-note"):
            self.assertNotRegex(body, r"\b(?:stroke|fill)\s*:", sel)


class GuideCheck(unittest.TestCase):
    def test_every_new_state_is_required_on_the_components_page(self):
        required = {cls for cls, _, _ in check_guide.STATES}
        for cls in CLASSES:
            self.assertIn(cls, required)
        self.assertIn(("en-statpanel", 'role="img"', "stat panel, one item for screen readers"), check_guide.STATES)

    def test_every_new_colour_pair_is_checked(self):
        pairs = {(comp, fg, bg) for comp, _, fg, bg, _ in check_guide.PAIRS}
        for fg in ("--en-text-strong", "--en-text", "--en-text-soft", "--en-text-muted"):
            self.assertIn(("Stat panel", fg, "--en-surface-raised"), pairs)
        self.assertIn(("Note", "--en-text-soft", "--en-surface-page"), pairs)

    def test_resize_page_has_each_part_in_a_frame(self):
        markup = "".join(m for _, m, *_ in resize_page.BY_HAND)
        for cls in ("en-statpair", "en-statpanel__notset", "en-note"):
            self.assertIn(cls, markup)


class Docs(unittest.TestCase):
    def test_design_md_describes_each(self):
        part3 = read("DESIGN.md").split("## Part 3: Components", 1)[1]
        for title, names in [("Stat panel", [c for c in CLASSES if c != "en-note"]), ("Note", ["en-note"])]:
            self.assertIn(f"### {title}\n", part3)
            section = part3.split(f"### {title}\n", 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]
            for cls in names:
                self.assertIn(f"`.{cls}`", section)
            self.assertIn("- Motion:", section)

    def test_changelog_entry(self):
        m = re.search(r"^## 0\.10\.0,[^\n]*\(visual\)\n(.*?)(?=^## )", read("CHANGELOG.md"), re.S | re.M)
        self.assertIsNotNone(m, "no 0.10.0 entry marked visual")
        body = m.group(1)
        self.assertIn("**Renamed or removed: none.**", body)
        self.assertIn("**Who should adopt it, and when:**", body)
        self.assertIn('"Bring in Enamel 0.10.0"', body)
        for cls in CLASSES:
            self.assertRegex(body, re.escape(f"`.{cls}`"))

    def test_migration_leaves_new_names_out(self):
        text = read("MIGRATION.md")
        for name in CLASSES + ["--en-c-statpanel-min", "--en-c-note-gap"]:
            self.assertNotIn(f"`{name}`", text)

    def test_version_is_at_least_this_release(self):
        self.assertGreaterEqual(tuple(map(int, read("VERSION").strip().split("."))), (0, 10, 0))


HAVE_GIT = shutil.which("git") is not None and os.path.exists(os.path.join(ROOT, ".git"))


def at_tag(tag, path):
    """A file as it was at a release tag; None if it can't be read here."""
    out = subprocess.run(["git", "-C", ROOT, "show", f"{tag}:{path}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def without_stamp(text):
    """The file without its header line naming the version."""
    return "\n".join(line for line in text.split("\n") if not re.search(r"version \d+\.\d+\.\d+", line))


@unittest.skipUnless(HAVE_GIT, "not a git clone")
class NothingRenamed(unittest.TestCase):
    """Compares this release with the one before it, so it only means something
    while VERSION is 0.10.0; a later release may add names of its own."""

    def setUp(self):
        if read("VERSION").strip() != "0.10.0":
            self.skipTest("about the 0.10.0 release only")
        self.old_css = at_tag("v0.9.0", "components/enamel-components.css")
        if self.old_css is None:
            self.skipTest("the v0.9.0 tag can't be read here")

    def test_no_token_changes(self):
        self.assertEqual(without_stamp(read("tokens", "enamel.css")), without_stamp(at_tag("v0.9.0", "tokens/enamel.css")))

    def test_the_script_does_not_change(self):
        self.assertEqual(without_stamp(read("components", "enamel-components.js")),
                         without_stamp(at_tag("v0.9.0", "components/enamel-components.js")))

    def names(self, pattern, css):
        return set(re.findall(pattern, re.sub(r"/\*.*?\*/", "", css, flags=re.S)))

    def test_classes(self):
        pattern = r"\.(en-[A-Za-z0-9_-]+)"
        old, new = self.names(pattern, self.old_css), self.names(pattern, CSS)
        self.assertEqual(old - new, set(), "a component class was renamed or removed")
        self.assertEqual(new - old, set(CLASSES), "the new component classes are not the ones this issue lists")

    def test_component_variables(self):
        pattern = r"(--en-c-[a-z0-9-]+)\s*:"
        old, new = self.names(pattern, self.old_css), self.names(pattern, CSS)
        self.assertEqual(old - new, set(), "a component variable was renamed or removed")
        self.assertEqual(new - old, {"--en-c-statpanel-min", "--en-c-note-gap"})

    def test_state_attributes_and_animations(self):
        for pattern in (r"\[([a-z-]+)[\]=]", r"@keyframes\s+([\w-]+)"):
            self.assertEqual(self.names(pattern, self.old_css) - self.names(pattern, CSS), set(), pattern)
            self.assertEqual(self.names(pattern, CSS) - self.names(pattern, self.old_css), set(), pattern)


if __name__ == "__main__":
    unittest.main()
