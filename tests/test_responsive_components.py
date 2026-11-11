# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #3: the picker, the toast and the action bar size themselves from
the space they are given (0.6.0). These tests read the files directly: no
screen-based units or device-sized breakpoints in the stylesheets, the
measured values naming no capture or device, no name changed, the
docs say "the space it is given" rather than "the screen", and the 0.6.0
changelog entry lists every changed value.

How the components actually behave at several frame sizes (the picker
between a quarter and two thirds of its space, the toast hugging its text
above the hint bar, the action bar wrapping) is run in the device's Firefox
by tools/browser_check.py (scripts/test.sh guide).

    scripts/test.sh unit tests.test_responsive_components
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_migration import old_name  # noqa: E402  (the 0.6.0 entry keeps the names it was written with, #12)


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def comments(css):
    return " ".join(re.findall(r"/\*(.*?)\*/", css, flags=re.S))


def rule(css, selector):
    """The body of the first rule whose selector is exactly `selector`."""
    m = re.search(r"(?:^|\n|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not m:
        raise AssertionError(f"no rule for {selector}")
    return m.group(1)


def variable(css, name):
    m = re.search(re.escape(name) + r"\s*:\s*([^;]+);", strip_comments(css))
    if not m:
        raise AssertionError(f"{name} is not defined")
    return m.group(1).strip()


CSS = read("components", "enamel-components.css")
TOKENS = read("tokens", "enamel.css")

# Values for the picker and toast matched to Steam's Gaming Mode (the Steam baseline).
MEASURED = ["--en-c-picker-row", "--en-c-picker-row-tall", "--en-c-picker-inset", "--en-c-text-detail",
            "--en-c-picker-min", "--en-c-picker-max", "--en-c-toast-width"]


class SizedFromTheirSpace(unittest.TestCase):
    def test_no_screen_units_in_the_components(self):
        # vw, vh, vmin and vmax size a component from the whole screen.
        found = re.findall(r"\b\d*\.?\d+(?:d|s|l)?v(?:w|h|i|b|min|max)\b", strip_comments(CSS))
        self.assertEqual(found, [], "the components stylesheet still sizes something from the screen")

    def test_picker_limits_follow_the_dialog(self):
        for name in ("--en-c-picker-min", "--en-c-picker-max"):
            self.assertRegex(variable(CSS, name), r"cqi$", f"{name} is not measured from the dialog's own space")
        self.assertIn("container-type: inline-size", rule(CSS, ".en-dialog"),
                      "the dialog is not a size container, so the picker's limits fall back to the screen")
        picker = rule(CSS, ".en-picker")
        self.assertIn("min-width: var(--en-c-picker-min)", picker)
        self.assertIn("max-width: var(--en-c-picker-max)", picker)
        self.assertIn("width: fit-content", picker)

    def test_toast_hugs_its_text_up_to_a_limit(self):
        self.assertRegex(variable(CSS, "--en-c-toast-width"), r"rem$", "the toast's limit is not in rem")
        toast = rule(CSS, ".en-toast")
        self.assertRegex(toast, r"(?<![-\w])width:\s*fit-content", "the toast is not as wide as its text")
        self.assertRegex(toast, r"max-width:\s*min\(var\(--en-c-toast-width\)",
                         "the toast's widest size is not --en-c-toast-width")

    def test_action_bar_wraps_instead_of_overflowing(self):
        bar = rule(CSS, ".en-actionbar")
        self.assertIn("flex-wrap: wrap", bar)
        self.assertNotIn("text-overflow", bar)
        self.assertNotIn("nowrap", rule(CSS, ".en-button"), "button labels cannot wrap")

    def test_no_device_sized_breakpoints(self):
        for name, css in (("components", CSS), ("tokens", TOKENS)):
            for m in re.finditer(r"@(?:media|container)[^{]*", strip_comments(css)):
                self.assertNotRegex(m.group(0), r"width|height|aspect-ratio|orientation|resolution",
                                    f"{name}: a breakpoint tied to a screen size: {m.group(0).strip()}")


class Source(unittest.TestCase):
    def test_stylesheet_names_no_capture_size_or_device(self):
        for needle in ("1280", "800px", "Steam Deck", "Deck"):
            self.assertNotIn(needle, comments(CSS), f"the components stylesheet still names {needle!r}")

    def test_every_measured_value_is_still_a_variable(self):
        for name in MEASURED:
            self.assertTrue(variable(CSS, name), f"{name} is not defined")


class NoNameChanged(unittest.TestCase):
    CLASSES = [".en-actionbar", ".en-icon", ".en-dialog", ".en-picker", ".en-picker__title", ".en-picker__rows",
               ".en-picker__row", ".en-picker__desc", ".en-picker__cancel", ".en-toast", ".en-toast__icon"]
    # .en-toast__text is a markup-only class (never styled), so it is checked in the script instead.

    def test_classes_and_variables_still_there(self):
        body = strip_comments(CSS)
        for name in self.CLASSES:
            self.assertRegex(body, re.escape(name) + r"(?![\w-])", f"class {name} is gone")
        for name in MEASURED:
            variable(CSS, name)

    def test_state_attributes_still_styled(self):
        body = strip_comments(CSS)
        for state in ('.en-dialog[open]', '.en-dialog[data-closing="true"]', '.en-toast[hidden]',
                      '.en-toast[data-closing="true"]', '.en-picker__row[aria-current="true"]'):
            self.assertIn(state, body, f"state {state} is no longer styled")

    def test_script_functions_still_there(self):
        js = read("components", "enamel-components.js")
        self.assertIn("en-toast__text", js, "the script no longer builds a toast's text")
        for group, names in (("picker", ("open", "close")), ("toast", ("show", "update", "hide"))):
            for name in names:
                self.assertRegex(js, group + r":\s*\{[^}]*\b" + name + r":", f"EnamelUI.{group}.{name} is gone")


class Wording(unittest.TestCase):
    def test_design_md(self):
        design = read("DESIGN.md")
        picker = re.search(r"^### Picker dialog\n(.*?)(?=^### )", design, re.S | re.M).group(1)
        self.assertNotIn("two thirds of the screen", picker)
        self.assertIn("two thirds of the space its dialog gives it", picker)
        toast = re.search(r"^### Toast\n(.*?)(?=^### )", design, re.S | re.M).group(1)
        self.assertIn("as wide as its text", toast)
        bar = re.search(r"^### Action bar\n(.*?)(?=^### )", design, re.S | re.M).group(1)
        self.assertIn("the bar gets taller", bar)

    def test_components_page(self):
        for path in (("docs", "components.html"), ("tools", "components_page.py")):
            text = " ".join(read(*path).split())
            self.assertNotIn("two thirds of the screen", text, path[-1])
            self.assertIn("between a quarter and two thirds of the space it is given", text, path[-1])
            self.assertIn("as wide as its text, up to a limit", text, path[-1])
            self.assertIn("they wrap onto another and the bar gets taller", text, path[-1])


class VersionAndChangelog(unittest.TestCase):
    def test_version_is_at_least_0_6_0(self):
        version = tuple(int(x) for x in read("VERSION").strip().split("."))
        self.assertGreaterEqual(version, (0, 6, 0))

    def test_0_6_0_entry(self):
        text = read("CHANGELOG.md")
        m = re.search(r"^## 0\.6\.0,[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertIsNotNone(m, "no 0.6.0 entry")
        self.assertIn("(visual)", text[m.start():text.index("\n", m.start())])
        body = m.group(1)
        self.assertRegex(body, r"No token, component class, state attribute[^\n]*renamed or removed")
        # #6 finished the entry: Kettle Video adopts it now (until then it was "only once #6 is done")
        self.assertRegex(body, r"Who should adopt it, and when:\*\* Kettle Video, now")
        for name, old, new in (("--en-c-picker-min", "25vw", "25cqi"),
                               ("--en-c-picker-max", "66.667vw", "66.667cqi"),
                               ("--en-c-toast-width", "35vw", "28rem")):
            self.assertRegex(body, re.escape(f"`{old_name(name)}` was `{old}`") + r"[^;`]*?, now " + re.escape(f"`{new}`"),
                             f"the entry does not say {name} changed from {old} to {new}")
            self.assertEqual(variable(CSS, name), new, f"{name} in the stylesheet differs from the changelog")


if __name__ == "__main__":
    unittest.main()
