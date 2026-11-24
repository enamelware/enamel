# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #29: a failed step fails the checks script and is never remembered as a pass.

scripts/test.sh is copied into a temporary folder, never the repo, next to a
small stand-in for the style guide check and planted tests, including a
deliberately failing unit test that only ever exists in that folder. Each run
must end with one summary line: "All checks passed." only when every step
passed, otherwise "FAILED:" naming the failed checks, with a failing exit and
no pass remembered for that code.

    scripts/test.sh unit tests.test_test_sh
"""
import os, shutil, subprocess, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSED = "All checks passed."

PASSING_TEST = "import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
FAILING_TEST = ("import unittest\n\nclass T(unittest.TestCase):\n"
                "    def test_planted_failure(self):\n        self.fail('planted on purpose')\n")
GUIDE = "import sys\nprint('\\nStyle guide checks passed.')\n"
GUIDE_FAILING = "import sys\nprint('\\nFAILED:\\n  planted')\nsys.exit(1)\n"
SLOW_CHECK_FAILING = "import sys\nsys.exit(1)\n"

GIT = ["git", "-c", "user.name=Enamel tests", "-c", "user.email=", "-c", "commit.gpgsign=false",
       "-c", "core.hooksPath=/dev/null"]


class ChecksScript(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="enamel-test-sh-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        # Nothing from a surrounding git run leaks into the temporary repo.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        os.makedirs(os.path.join(self.dir, "scripts"))
        os.makedirs(os.path.join(self.dir, "tests"))
        os.makedirs(os.path.join(self.dir, "tools"))
        shutil.copy(os.path.join(ROOT, "scripts", "test.sh"), os.path.join(self.dir, "scripts", "test.sh"))
        # As in the repo, so running the planted tests leaves the code unchanged
        # and a pass could be remembered: a missing record then means "not remembered".
        self.write(".gitignore", "__pycache__/\n")
        self.write("tests/__init__.py", "")
        self.write("tests/test_ok.py", PASSING_TEST)
        self.write("tools/check_guide.py", GUIDE)

    def write(self, path, text):
        with open(os.path.join(self.dir, path), "w", encoding="utf-8") as f:
            f.write(text)

    def git(self, *args):
        subprocess.run(GIT + list(args), cwd=self.dir, env=self.env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def commit(self):
        """Commits everything, so the script can remember a pass against this exact code."""
        if not os.path.isdir(os.path.join(self.dir, ".git")):
            self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "planted")

    def run_script(self, *args):
        result = subprocess.run(["bash", "scripts/test.sh", *args], cwd=self.dir, env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
        return result.returncode, result.stdout

    def remembered(self):
        folder = os.path.join(self.dir, ".git", "enamel-test-results")
        return os.listdir(folder) if os.path.isdir(folder) else []

    def last_line(self, out):
        return out.strip().splitlines()[-1]

    def assert_failed(self, code, out, *names):
        self.assertNotEqual(code, 0, out)
        self.assertNotIn(PASSED, out)
        last = self.last_line(out)
        self.assertTrue(last.startswith("FAILED:"), out)
        for name in names:
            self.assertIn(name, last)
        self.assertEqual(self.remembered(), [], "a failed run was remembered as a pass")

    def test_a_failing_unit_test_fails_the_quick_suite(self):
        self.write("tests/test_planted.py", FAILING_TEST)
        self.commit()
        code, out = self.run_script()
        self.assertIn("planted on purpose", out)
        self.assert_failed(code, out, "unit tests")
        self.assertNotIn("style guide check", self.last_line(out))
        # The failure is not hidden on the next run either.
        code, out = self.run_script()
        self.assertNotIn("Already passed", out)
        self.assert_failed(code, out, "unit tests")

    def test_a_failing_unit_test_fails_the_full_suite(self):
        self.write("tests/test_planted.py", FAILING_TEST)
        self.commit()
        code, out = self.run_script("full")
        self.assert_failed(code, out, "unit tests")

    def test_a_failing_style_guide_check_is_named(self):
        self.write("tools/check_guide.py", GUIDE_FAILING)
        self.commit()
        code, out = self.run_script()
        self.assert_failed(code, out, "style guide check")
        self.assertNotIn("unit tests", self.last_line(out))

    def test_a_failing_slower_check_is_named(self):
        self.write("tests/planted_check.py", SLOW_CHECK_FAILING)
        self.commit()
        code, out = self.run_script("full")
        self.assert_failed(code, out, "slower checks", "planted_check")

    def test_every_failed_step_is_named(self):
        self.write("tests/test_planted.py", FAILING_TEST)
        self.write("tools/check_guide.py", GUIDE_FAILING)
        self.commit()
        code, out = self.run_script()
        self.assert_failed(code, out, "unit tests", "style guide check")

    def test_a_clean_run_passes_and_is_remembered(self):
        self.commit()
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.last_line(out), PASSED)
        self.assertEqual(len(self.remembered()), 1)
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertIn("Already passed on this exact code", out)

    def test_the_real_style_guide_check_does_not_claim_every_check(self):
        """It runs after the unit tests, so its own last line must not read as the whole run's."""
        with open(os.path.join(ROOT, "tools", "check_guide.py"), encoding="utf-8") as f:
            self.assertNotIn(PASSED, f.read())


if __name__ == "__main__":
    unittest.main()
