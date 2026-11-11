# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""The quick check picks the style guide pages a change touches.

scripts/test.sh (quick) runs the device's Firefox only on those pages; this
checks the rules in tools/check_guide.py (touched_pages) that pick them.

    scripts/test.sh unit tests.test_quick_pages
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import check_guide as cg


class TouchedPages(unittest.TestCase):
    def test_nothing_on_the_pages_skips_the_browser(self):
        self.assertEqual(cg.touched_pages(["README.md", "CHANGELOG.md", "tests/test_generated.py"]), ([], False))

    def test_a_changed_page_is_checked_alone(self):
        self.assertEqual(cg.touched_pages(["docs/index.html"]), (["index.html"], False))

    def test_a_page_builder_checks_its_page(self):
        self.assertEqual(cg.touched_pages(["tools/motion_page.py"]), (["motion.html"], False))

    def test_the_resize_page_brings_the_frame_checks(self):
        self.assertEqual(cg.touched_pages(["tools/resize_page.py", "docs/resize.html"]), (["resize.html"], True))

    def test_tokens_and_components_check_both_component_pages_and_frames(self):
        for f in ("tokens/enamel.css", "components/enamel-components.css", "components/enamel-components.js",
                  "docs/site.css"):
            self.assertEqual(cg.touched_pages([f]), (["components.html", "motion.html"], True), f)

    def test_a_change_to_the_check_itself_checks_everything(self):
        self.assertEqual(cg.touched_pages(["tools/browser_check.py"]), (cg.PAGES, True))

    def test_every_page_has_a_rule(self):
        for page in cg.PAGES:
            self.assertEqual(cg.touched_pages([f"docs/{page}"])[0], [page])


if __name__ == "__main__":
    unittest.main()
