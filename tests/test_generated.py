# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Generated files match what their scripts would write, so running a build
script again changes nothing.

    scripts/test.sh unit tests.test_generated
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_design_md  # noqa: E402
import enamel_tokens  # noqa: E402


class DesignMdTokenTables(unittest.TestCase):
    def test_part_1_matches_enamel_css(self):
        with open(build_design_md.DESIGN, encoding="utf-8") as f:
            text = f.read()
        start, end = build_design_md.START, build_design_md.END
        self.assertEqual(text.count(start), 1)
        self.assertEqual(text.count(end), 1)
        current = text.split(start)[1].split(end)[0]
        expected = "\n" + build_design_md.tables(enamel_tokens.load()) + "\n"
        self.assertEqual(current, expected,
                         "DESIGN.md Part 1 is out of date: run python3 tools/build_design_md.py")


if __name__ == "__main__":
    unittest.main()
