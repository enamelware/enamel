# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #15: the token reference shows every size at the measuring point.

The issue asks for the style guide to show sizes at the measuring point (16px
per rem); the decision on the issue replaced a device preview with the pixels
written after each size on the token reference. This reads docs/index.html
and checks that every size card in rem shows its pixels at 16px per rem (a
growing size "from" its base), that sizes kept in px show nothing extra, and
that the root size is on the page.

    scripts/test.sh unit tests.test_baseline_on_page
"""
import html
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_styleguide  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


PAGE = read("docs", "index.html")
CARDS = {name: html.unescape(value) for name, value in
         re.findall(r'<code class="tok">(--en-[a-z0-9-]+)</code><code class="val">([^<]*)</code>', PAGE)}

# (token, what the card must end with) at 16px per rem.
EXPECTED = {
    "--en-size-row": "4rem (64px)", "--en-size-row-control": "6rem (96px)", "--en-size-button": "3.75rem (60px)",
    "--en-size-bar": "3.75rem (60px)", "--en-size-tile-portrait": "12.5rem (200px)",
    "--en-space-icon": "1rem (16px)", "--en-space-gap": "0.75rem (12px)", "--en-space-tight": "0.25rem (4px)",
    "--en-space-inset": "(from 20px)", "--en-space-gutter": "(from 36px)", "--en-space-gutter-grid": "(from 48px)",
    "--en-text-body": "(from 24px)", "--en-text-caps": "(from 17px)", "--en-text-title": "(from 33px)",
    "--en-text-small": "(from 18.67px)",
}
KEPT_PX = ["--en-size-target", "--en-radius", "--en-focus-ring-width", "--en-focus-ring-offset",
           "--en-focus-affordance", "--en-focus-ring-start"]


class TokenReference(unittest.TestCase):
    def test_sizes_show_their_pixels_at_the_measuring_point(self):
        for name, ending in EXPECTED.items():
            with self.subTest(name=name):
                self.assertIn(name, CARDS, f"{name} has no card on the token reference")
                self.assertTrue(CARDS[name].endswith(ending), f"{name} shows {CARDS[name]!r}, not ending {ending!r}")

    def test_sizes_kept_in_px_show_no_extra_pixels(self):
        for name in KEPT_PX:
            with self.subTest(name=name):
                self.assertNotIn("(", CARDS[name], f"{name} is in px but shows {CARDS[name]!r}")

    def test_every_rem_card_shows_pixels(self):
        found = 0
        for name, value in CARDS.items():
            if re.fullmatch(r"-?[\d.]+rem", value.split(" (")[0]) or value.startswith("clamp("):
                found += 1
                self.assertRegex(value, r"\((?:from )?[\d.]+px\)$", f"{name} ({value}) shows no pixels")
        self.assertGreater(found, 12)

    def test_the_root_size_is_on_the_page(self):
        self.assertEqual(CARDS.get("--en-root-size"), "100%")
        text = " ".join(re.sub(r"<[^>]+>", "", PAGE).split())
        self.assertIn("16px per rem", text)

    def test_at_normal(self):
        self.assertEqual(build_styleguide.at_normal("4rem"), " (64px)")
        self.assertEqual(build_styleguide.at_normal("clamp(1.5rem, 1rem + 0.5vw, 1.8rem)"), " (from 24px)")
        self.assertEqual(build_styleguide.at_normal("44px"), "")
        self.assertEqual(build_styleguide.at_normal("100%"), "")


if __name__ == "__main__":
    unittest.main()
