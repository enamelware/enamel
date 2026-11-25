# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issues #29 and #35: the checks script's verdict and its memory of a pass.

#29: a failed step fails the checks script and is never remembered as a pass.
#35: a remembered pass follows the exact code. After a recorded pass, an edited,
new or deleted file (committed or not) makes the checks run again instead of
answering "already passed". Files git ignores are not part of the code, and two
commits with the same files are the same code, so those reuse the pass. Every
run names the commit it checked, for the builder's report.

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

    # Issue #35: the memory of a pass follows the exact code.

    def pass_once(self):
        """Commits, runs the quick suite once and checks the pass was recorded."""
        self.commit()
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.remembered()), 1, out)

    def assert_ran_again(self):
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertNotIn("Already passed", out)
        self.assertEqual(self.last_line(out), PASSED, out)
        return out

    def assert_reused(self):
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertIn("Already passed on this exact code", out)

    def test_an_uncommitted_edit_after_a_pass_runs_again(self):
        self.pass_once()
        self.write("tests/test_ok.py", PASSING_TEST + "# edited\n")
        out = self.assert_ran_again()
        self.assertIn("plus uncommitted changes", out)
        # Uncommitted code is never remembered, so it keeps running.
        self.assertEqual(len(self.remembered()), 1)
        self.assert_ran_again()

    def test_an_uncommitted_edit_that_breaks_the_code_is_caught(self):
        self.pass_once()
        self.write("tests/test_ok.py", FAILING_TEST)
        code, out = self.run_script()
        self.assertNotIn("Already passed", out)
        self.assertNotEqual(code, 0, out)
        self.assertTrue(self.last_line(out).startswith("FAILED:"), out)

    def test_a_new_untracked_file_after_a_pass_runs_again(self):
        self.pass_once()
        self.write("tests/test_new.py", PASSING_TEST)
        self.assert_ran_again()

    def test_a_deleted_file_after_a_pass_runs_again(self):
        self.write("tests/test_extra.py", PASSING_TEST)
        self.pass_once()
        os.remove(os.path.join(self.dir, "tests", "test_extra.py"))
        self.assert_ran_again()

    def test_a_staged_edit_after_a_pass_runs_again(self):
        self.pass_once()
        self.write("tests/test_ok.py", PASSING_TEST + "# staged\n")
        self.git("add", "-A")
        self.assert_ran_again()

    def test_a_commit_with_different_files_runs_again(self):
        self.pass_once()
        self.write("tests/test_ok.py", PASSING_TEST + "# committed\n")
        self.commit()
        self.assert_ran_again()
        self.assertEqual(len(self.remembered()), 2)

    def test_a_commit_with_the_same_files_reuses_the_pass(self):
        self.pass_once()
        self.git("commit", "-q", "--allow-empty", "-m", "same files")
        self.assert_reused()

    def test_an_ignored_file_is_not_part_of_the_code(self):
        self.write(".gitignore", "__pycache__/\nscratch.txt\n")
        self.pass_once()
        self.write("scratch.txt", "kept out of version control")
        self.assert_reused()

    def test_every_run_names_the_commit_it_checked(self):
        self.commit()
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=self.dir, env=self.env,
                              stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
        expected = "Code checked: commit %s, nothing uncommitted." % head
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertIn(expected, out)
        # The reused answer names the commit too, and so does a failed run.
        code, out = self.run_script()
        self.assertIn(expected, out)
        self.write("tests/test_planted.py", FAILING_TEST)
        self.commit()
        code, out = self.run_script()
        self.assertNotEqual(code, 0, out)
        self.assertIn("Code checked: commit ", out)
        self.assertNotIn(expected, out)

    def test_the_real_style_guide_check_does_not_claim_every_check(self):
        """It runs after the unit tests, so its own last line must not read as the whole run's."""
        with open(os.path.join(ROOT, "tools", "check_guide.py"), encoding="utf-8") as f:
            self.assertNotIn(PASSED, f.read())


if __name__ == "__main__":
    unittest.main()
