# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #1: the toast fades out in place (0.5.1), the picker sentence on the
Overview page, the "Gaps found by the apps" issue named in CLAUDE.md and
README.md, and the version and changelog that go with them.

The toast's fade, its removal after the fade and its instant removal in
reduced motion are also run in the device's Firefox by tools/browser_check.py
(scripts/test.sh guide). These tests read the files directly.

    scripts/test.sh unit tests.test_toast_fade
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def rule(css, selector):
    """The body of the first rule whose selector is exactly `selector`."""
    m = re.search(r"(?:^|\n|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not m:
        raise AssertionError(f"no rule for {selector}")
    return m.group(1)


def keyframes(css, name):
    m = re.search(r"@keyframes\s+" + re.escape(name) + r"\s*\{((?:[^{}]*\{[^}]*\})*)\s*\}", css)
    return m.group(1) if m else None


class ToastStylesheet(unittest.TestCase):
    css = read("components", "enamel-components.css")
    js = read("components", "enamel-components.js")

    def test_still_slides_in_from_the_right(self):
        body = rule(self.css, ".en-toast")
        self.assertRegex(body, r"animation:\s*en-slide-in\s+var\(--en-motion-slow\)\s+var\(--en-ease-enter\)")
        self.assertIn("translateX(100%)", keyframes(self.css, "en-slide-in"))

    def test_leaves_with_a_fade_in_place(self):
        body = rule(self.css, '.en-toast[data-closing="true"]')
        self.assertRegex(body, r"animation:\s*en-fade-out\s+var\(--en-motion-slow\)\s+var\(--en-ease-enter\)\s+forwards")
        self.assertNotIn("slide", body)
        self.assertNotIn("transform", body)
        fade = keyframes(self.css, "en-fade-out")
        self.assertIsNotNone(fade, "en-fade-out keyframes are missing")
        self.assertIn("opacity: 0", fade)
        self.assertNotIn("transform", fade, "the fade must not move the toast")

    def test_script_waits_for_the_same_token_the_fade_uses(self):
        # The script's fallback timer must match the fade's length, so the
        # toast is removed when the fade ends.
        self.assertRegex(self.js, r'leave\(el,\s*el,\s*"--en-motion-slow"')

    def test_reduced_motion_has_no_toast_animation(self):
        self.assertIn(':root:not([data-en-motion="full"]) .en-toast { animation: none; }', self.css)
        self.assertIn('[data-en-motion="reduced"] .en-toast { animation: none; }', self.css)

    def test_nothing_removed(self):
        self.assertIsNotNone(keyframes(self.css, "en-slide-out"), "en-slide-out keyframes were removed")
        for name in ("show", "update", "hide"):
            self.assertRegex(self.js, r"toast:\s*\{[^}]*\b" + name + r":")


class ToastWording(unittest.TestCase):
    def assertFadeWording(self, text, where):
        self.assertRegex(text, r"fad(?:es|ing) out where it is", f"{where} does not describe the toast's fade")
        self.assertNotIn("leaves the same way", text, f"{where} still says the toast slides out")

    def test_motion_page(self):
        for path in (("docs", "motion.html"), ("tools", "motion_page.py")):
            text = read(*path)
            m = re.search(r"A toast slides in(.*?)All of this", text, re.S)
            self.assertIsNotNone(m, f"{path[-1]}: toast sentence not found")
            self.assertFadeWording(m.group(1), path[-1])

    def test_components_page(self):
        for path in (("docs", "components.html"), ("tools", "components_page.py")):
            text = read(*path)
            m = re.search(r"Motion: it slides in from the right edge[^\n]*", text)
            self.assertIsNotNone(m, f"{path[-1]}: toast motion note not found")
            self.assertFadeWording(m.group(0), path[-1])

    def test_design_md(self):
        m = re.search(r"- Motion: it slides in from the right edge[^\n]*", read("DESIGN.md"))
        self.assertIsNotNone(m, "DESIGN.md: toast motion line not found")
        self.assertFadeWording(m.group(0), "DESIGN.md")

    def test_decision_entry(self):
        text = read("DECISIONS.md")
        m = re.search(r"^## [^\n]*toast fades out in place[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "DECISIONS.md has no entry for the toast fading out in place")
        self.assertIn("slides out, as briefed", m.group(1))
        self.assertIn("Steam's own toast fades out in place", m.group(1))


class OverviewPickerRule(unittest.TestCase):
    SENTENCE = ("a cream fill with dark text on a coral underside on buttons, fields and picker rows, "
                "and a lifted row in lists.")

    def test_focus_rule_has_the_picker_sentence(self):
        text = read("docs", "overview.html")
        rules = re.search(r'<ul class="rules">(.*?)</ul>', text, re.S).group(1)
        focus = [li for li in re.findall(r"<li>(.*?)</li>", rules) if li.startswith("Focus is ")]
        self.assertEqual(len(focus), 1)
        self.assertTrue(focus[0].endswith(" " + self.SENTENCE), focus[0])
        self.assertEqual(text.count(self.SENTENCE), 1)


class GapsIssueNamed(unittest.TestCase):
    def test_claude_md_and_readme_name_it(self):
        for name in ("CLAUDE.md", "README.md"):
            text = read(name)
            m = re.search(r'Gaps found while building an app[^\n]*', text)
            self.assertIsNotNone(m, f"{name}: the gaps line is missing")
            self.assertIn('"Gaps found by the apps"', m.group(0), name)
            self.assertIn("#7", m.group(0), name)
            self.assertIn("gaps", m.group(0), name)


class VersionAndChangelog(unittest.TestCase):
    def test_newest_changelog_entry_is_this_version(self):
        version = read("VERSION").strip()
        heads = re.findall(r"^## (\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M)
        self.assertTrue(heads)
        self.assertEqual(heads[0], version, "CHANGELOG's newest entry is not the VERSION")

    def test_0_5_1_entry(self):
        text = read("CHANGELOG.md")
        m = re.search(r"^## 0\.5\.1,[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "no 0.5.1 entry")
        self.assertIn("(visual)", text[m.start():text.index("\n", m.start())])
        self.assertRegex(m.group(1), r"No token, component class, state attribute[^\n]*renamed or removed")
        self.assertIn("fades out", m.group(1))


if __name__ == "__main__":
    unittest.main()
