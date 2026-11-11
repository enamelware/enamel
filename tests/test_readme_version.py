# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #8: every place that names the current version agrees with VERSION:
the README ("Using it in an app"), the headers of the tokens, components and
script files, and the newest CHANGELOG entry.

    scripts/test.sh unit tests.test_readme_version
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_styleguide as sg  # noqa: E402


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


class ReadmeVersion(unittest.TestCase):
    def test_using_it_in_an_app_names_the_version_in_VERSION(self):
        version = read("VERSION").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$", "VERSION should hold one version number")
        readme = read("README.md")
        section = readme.split("## Using it in an app", 1)
        self.assertEqual(len(section), 2, "README has no 'Using it in an app' section")
        section = section[1].split("\n## ", 1)[0]
        named = re.findall(r"currently (\d+\.\d+\.\d+)", section)
        self.assertEqual(named, [version],
                         f"README 'Using it in an app' should say 'currently {version}' once, "
                         f"found {named}")

    def test_every_place_that_names_a_version_agrees_with_VERSION(self):
        version = read("VERSION").strip()
        # The stamped files and their header line come from the build script
        # (the same check tools/check_guide.py runs), so a file added there is
        # covered here too.
        self.assertGreaterEqual(len(sg.STAMPED), 3, "build_styleguide.STAMPED lost a file")
        for path, prefix in sg.STAMPED:
            name = os.path.relpath(path, ROOT)
            try:
                old, new = sg.stamp_version(path, prefix, version)
            except SystemExit as ex:
                self.fail(str(ex))
            self.assertEqual(old, new, f"{name} header should say '{prefix}, version {version}.'")
            named = re.findall(r"version (\d+\.\d+\.\d+)", old[:400])
            self.assertEqual(named, [version],
                             f"{name} header should name version {version} once, found {named}")
        newest = re.search(r"^## (\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M)
        self.assertIsNotNone(newest, "CHANGELOG.md has no version entry")
        self.assertEqual(newest.group(1), version,
                         "the newest CHANGELOG.md entry should be for the version in VERSION")


if __name__ == "__main__":
    unittest.main()
