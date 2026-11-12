# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #21: the destructive row. Without a browser:

  - both variants exist and take their face, text and icon colours from the
    error red and the strong white only, in every state, and red is never a
    text colour anywhere in the components;
  - focus raises the face onto the accent underside, a press drops it, and the
    two reduced-motion blocks stop the movement;
  - the contrast check holds white on the error red, and only that pair, to
    APCA Lc 60 instead of 4.5:1, fails it when it falls short, and the APCA
    measure gives the published values;
  - the Components page shows every state, DESIGN.md has the rules and the
    entry, the new names are recorded, and 0.12.0 has its visual entry.

    scripts/test.sh unit tests.test_destructive_row
"""
import contextlib, io, os, re, sys, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_migration  # noqa: E402
import check_guide as cg  # noqa: E402
import enamel_tokens as en  # noqa: E402

CLASSES = ("en-row--destructive", "en-picker__row--destructive")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


CSS = re.sub(r"/\*.*?\*/", "", read("components/enamel-components.css"), flags=re.S)


def rules(css, cls):
    """[(selector, body)] for every rule whose selector names cls."""
    return [(sel.strip(), body) for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
            if re.search(rf"\.{re.escape(cls)}(?![\w-])", sel)]


def selectors(sel):
    """A selector list split at its top-level commas (not those inside :is())."""
    out, depth, cur = [], 0, ""
    for ch in sel:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return out + [cur.strip()]


def declarations(body):
    return dict((k.strip(), v.strip()) for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+);", body))


class Styles(unittest.TestCase):
    def test_every_state_keeps_the_red_face_and_white_text(self):
        for cls in CLASSES:
            states = {"rest": f".{cls}", "focus": f'.{cls}:is(:focus-visible, [data-focused="true"])',
                      "press": f'.{cls}:is(:active, [data-pressed="true"])'}
            found = {sel: declarations(body) for sel, body in rules(CSS, cls)}
            for state, sel in states.items():
                with self.subTest(cls=cls, state=state):
                    decl = next((d for s, d in found.items() if sel in selectors(s)), None)
                    self.assertIsNotNone(decl, f"no rule for {sel}")
                    self.assertEqual(decl.get("background-color"), "var(--en-danger)")
                    self.assertEqual(decl.get("color"), "var(--en-text-strong)")

    def test_focus_rises_onto_the_underside_and_a_press_drops(self):
        for cls in CLASSES:
            body = next(d for s, d in rules(CSS, cls) if f'.{cls}:is(:focus-visible, [data-focused="true"])' in selectors(s))
            decl = declarations(body)
            self.assertIn("var(--en-focus-underside) 0 var(--en-focus-ring)", decl["box-shadow"])
            self.assertEqual(decl["transform"], "translateY(calc(-1 * var(--en-c-rise)))")
            body = next(d for s, d in rules(CSS, cls) if f'.{cls}:is(:active, [data-pressed="true"])' in selectors(s))
            self.assertEqual(declarations(body)["transform"], "translateY(0)")

    def test_meta_and_description_are_white_and_bold_and_the_text_keeps_its_size(self):
        small = [d for cls in CLASSES for s, d in rules(CSS, cls) if "__meta" in s or "__desc" in s]
        self.assertTrue(small)
        for body in small:
            decl = declarations(body)
            self.assertEqual(decl.get("color"), "var(--en-text-strong)")
            self.assertEqual(decl.get("font-weight"), "700")
        for cls in CLASSES:
            for sel, body in rules(CSS, cls):
                self.assertNotIn("font-size", declarations(body), f"{sel} changes the text size")

    def test_only_tokens(self):
        for cls in CLASSES:
            for sel, body in rules(CSS, cls):
                self.assertNotRegex(body, r"#[0-9A-Fa-f]{3,8}\b|rgba?\(", sel)
                for v in re.findall(r"(?<![\w.-])(\d+(?:\.\d+)?)(px|rem)\b", body):
                    self.fail(f"{sel} hard-codes a size: {''.join(v)}")

    def test_red_is_never_a_text_colour(self):
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS):
            if declarations(body).get("color") == "var(--en-danger)":
                self.assertTrue(sel.strip().endswith(".en-icon"), f"{sel.strip()} sets red text")

    def test_reduced_motion_stops_the_movement_in_both_blocks(self):
        media = CSS[CSS.index("@media (prefers-reduced-motion: reduce)"):]
        for prefix in (':root:not([data-en-motion="full"]) ', '[data-en-motion="reduced"] '):
            for cls in CLASSES:
                base = "en-picker__row" if cls.startswith("en-picker") else cls
                with self.subTest(prefix=prefix, cls=base):
                    m = re.search(re.escape(prefix + "." + base) + r"\s*\{([^}]*)\}", media)
                    self.assertTrue(m, f"no reduced-motion rule for .{base}")
                    self.assertEqual(declarations(m.group(1)).get("transform"), "none")


class Contrast(unittest.TestCase):
    def test_apca_gives_the_published_values(self):
        self.assertAlmostEqual(en.apca("#000000", "#FFFFFF"), 106.04, places=1)
        self.assertAlmostEqual(en.apca("#FFFFFF", "#000000"), 107.88, places=1)
        self.assertAlmostEqual(en.apca("#888888", "#888888"), 0.0)

    def test_white_on_the_error_red(self):
        red, white = cg.en.resolve(en.load(), "var(--en-danger)"), cg.en.resolve(en.load(), "var(--en-text-strong)")
        self.assertLess(en.contrast(white, red), 4.5)          # why it needs the exception
        self.assertGreaterEqual(en.contrast(white, red), 4.4)
        self.assertGreaterEqual(en.apca(white, red), cg.APCA_LARGE_OR_BOLD)

    def test_the_exception_is_one_pair(self):
        apca = [p for p in cg.PAIRS if p[4] == "apca"]
        self.assertEqual([(p[2], p[3]) for p in apca], [("--en-text-strong", "--en-danger")])
        self.assertEqual(cg.APCA_LARGE_OR_BOLD, 60)
        comps = {(c, w) for c, w, *_ in cg.PAIRS if c == "Destructive row"}
        self.assertGreaterEqual(len(comps), 5)

    def run_check(self, pairs):
        saved, saved_notes = list(cg.failures), list(cg.notes)
        del cg.failures[:]
        try:
            with mock.patch.object(cg, "PAIRS", pairs), contextlib.redirect_stdout(io.StringIO()):
                cg.check_contrast()
            return list(cg.failures), list(cg.notes)
        finally:
            cg.failures[:], cg.notes[:] = saved, saved_notes

    def test_the_check_passes_it_and_notes_why(self):
        failures, notes = self.run_check([("Destructive row", "text", "--en-text-strong", "--en-danger", "apca")])
        self.assertEqual(failures, [])
        self.assertTrue(any("APCA Lc 75" in n for n in notes), notes)

    def test_the_check_fails_a_pair_that_falls_short(self):
        failures, _ = self.run_check([("Destructive row", "text", "--en-text-muted", "--en-danger", "apca")])
        self.assertTrue(failures)
        self.assertIn("APCA", failures[0])


class Docs(unittest.TestCase):
    def test_the_components_page_has_every_state(self):
        page = read("docs/components.html")
        self.assertIn('<section id="destructive">', page)
        for cls, attr, what in cg.STATES:
            if "destructive" in cls:
                self.assertIn(cls, page, what)
        wanted = {(c, a) for c in CLASSES for a in (None, 'data-focused="true"', 'data-pressed="true"')}
        self.assertTrue(wanted <= {(c, a) for c, a, _ in cg.STATES})
        self.assertIn("narrow box", page[page.index('id="destructive"'):page.index("</section>", page.index('id="destructive"'))])

    def test_design_md(self):
        text = read("DESIGN.md")
        rules_ = "\n".join(en.read_rules(os.path.join(ROOT, "DESIGN.md")))
        self.assertIn("Red is a status colour like error, never a second accent", rules_)
        self.assertIn("used only for actions that close, remove or delete", rules_)
        self.assertIn("white on the error red in a destructive row is 4.44:1", rules_)
        self.assertIn("### Destructive row", text)
        for cls in CLASSES:
            self.assertIn(f"`.{cls}`", text)

    def test_names_recorded_and_version(self):
        self.assertEqual(build_migration.ADDED_SINCE["0.12.0"], list(CLASSES))
        self.assertEqual(read("VERSION").strip(), "0.12.0")
        self.assertIn("## 0.12.0, 2026-11-12 (visual)", read("CHANGELOG.md"))


if __name__ == "__main__":
    unittest.main()
