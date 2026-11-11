# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""The helper agents' guard and the read-only Kettle Video script.

Every helper runs one plain command at a time, runs git from this repo's
folder (never `git -C`), and reads Kettle Video only through scripts/peek.sh.
peek.sh itself runs only read-only git commands and never writes a file.

    scripts/test.sh unit tests.test_agent_guard
"""
import fnmatch, json, os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(ROOT, ".claude", "hooks", "agent_guard.py")
PEEK = os.path.join(ROOT, "scripts", "peek.sh")
ROLES = ("reviewer", "test-checker", "test-writer", "refactor-scout")


def guard(role, command, cwd=None):
    call = {"tool_name": "Bash", "tool_input": {"command": command}}
    env = dict(os.environ)
    if cwd:
        call["cwd"] = cwd
        env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run([sys.executable, GUARD, role], input=json.dumps(call), capture_output=True,
                          text=True, env=env).returncode


def write(role, path, cwd):
    call = {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(cwd, path)}, "cwd": cwd}
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, GUARD, role], input=json.dumps(call), capture_output=True,
                          text=True, env=env).returncode


class AgentGuard(unittest.TestCase):
    def test_every_role_may_read_kettle_video_through_peek(self):
        for role in ROLES:
            for command in ("scripts/peek.sh log --oneline -5", "scripts/peek.sh show --stat HEAD",
                            "scripts/peek.sh status --short", "scripts/peek.sh tag", "scripts/peek.sh ls-files"):
                self.assertEqual(guard(role, command), 0, f"{role}: {command}")

    def test_unsafe_peek_and_git_minus_c_are_refused(self):
        for role in ROLES:
            for command in ("scripts/peek.sh push", "scripts/peek.sh diff --output=x", "scripts/peek.sh tag -d v1",
                            "git -C ../kettle-video log", "git log && git status", "git log ; ls", "git log | head"):
                self.assertEqual(guard(role, command), 2, f"{role}: {command}")

    def test_every_agent_file_states_the_command_rules(self):
        for role in ROLES:
            with open(os.path.join(ROOT, ".claude", "agents", role + ".md"), encoding="utf-8") as f:
                text = f.read()
            for words in ("scripts/peek.sh", "git -C", "&&"):
                self.assertIn(words, text, f"{role}.md does not mention {words}")


class ReviewerTidyUps(unittest.TestCase):
    """The reviewer fixes tidy-ups itself in a small commit, only on an issue branch,
    never in tokens, components or the style guide pages."""

    def repo(self, branch):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        subprocess.run(["git", "init", "-q", "-b", branch, folder], check=True)
        return folder

    def test_commits_tidy_ups_on_an_issue_branch(self):
        folder = self.repo("issue-21")
        for command in ("git add tests/test_x.py tools/build_design_md.py", "git add CHANGELOG.md",
                        'git commit -m "WIP issue-21: reviewer tidy-ups"', "scripts/test.sh"):
            self.assertEqual(guard("reviewer", command, folder), 0, command)
        self.assertEqual(write("reviewer", "tools/build_design_md.py", folder), 0)

    def test_never_on_main_nor_outside_its_areas(self):
        main, branch = self.repo("main"), self.repo("issue-21")
        self.assertEqual(guard("reviewer", 'git commit -m "WIP issue-21: reviewer tidy-ups"', main), 2)
        self.assertEqual(guard("reviewer", "git add tests/test_x.py", main), 2)
        for command in ("git add tokens/enamel.css", "git add components/enamel-components.css",
                        "git add docs/index.html", "git add -A", 'git commit -m "Refs #21: done"',
                        'git commit --amend -m "WIP issue-21: x"', "git push origin issue-21"):
            self.assertEqual(guard("reviewer", command, branch), 2, command)
        for path in ("tokens/enamel.css", "components/enamel-components.js", "docs/overview.html"):
            self.assertEqual(write("reviewer", path, branch), 2, path)

    def test_only_the_reviewer_commits(self):
        folder = self.repo("issue-21")
        for role in ("test-checker", "test-writer", "refactor-scout"):
            self.assertEqual(guard(role, 'git commit -m "WIP issue-21: x"', folder), 2, role)


class SharedSettings(unittest.TestCase):
    """A new ask or deny rule must never catch a read-only command (CLAUDE.md)."""

    READ_ONLY = ["git log --oneline -5", "git log -p -- tokens/enamel.css", "git show HEAD:CHANGELOG.md",
                 "git show --stat HEAD~1", "git status", "git status --short", "git diff main...issue-14",
                 "git diff --stat -- docs/", "gh issue view 14 --comments", "gh issue view 7 --json body,comments",
                 "gh issue list --state open --label gaps", "ls -la docs", "cat CLAUDE.md",
                 "grep -rn en-accent tokens/", "scripts/board.sh list", "scripts/peek.sh log --oneline -3",
                 "scripts/peek.sh diff --stat HEAD~1"]

    def rules(self, kind):
        with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as f:
            permissions = json.load(f)["permissions"]
        return [r[5:-1] for r in permissions.get(kind, []) if r.startswith("Bash(")]

    def test_no_ask_or_deny_rule_catches_a_read_only_command(self):
        for kind in ("ask", "deny"):
            for rule in self.rules(kind):
                for command in self.READ_ONLY:
                    self.assertFalse(fnmatch.fnmatchcase(command, rule) or fnmatch.fnmatchcase(command, rule.replace(" *", "*")),
                                     f"{kind} rule Bash({rule}) catches the read-only command {command!r}")

    def test_the_workflow_scripts_are_allowed(self):
        allow = self.rules("allow")
        for script in ("scripts/forget-note.sh", "scripts/peek.sh", "scripts/board.sh", "scripts/test.sh"):
            self.assertIn(script + " *", allow, script)


class Peek(unittest.TestCase):
    def peek(self, *args):
        return subprocess.run([PEEK, *args], capture_output=True, text=True)

    def test_refuses_anything_but_read_only_commands(self):
        for args in (["push"], ["commit"], ["checkout", "main"], ["reset", "--hard"], ["config", "x", "y"], []):
            self.assertEqual(self.peek(*args).returncode, 2, args)

    def test_refuses_writing_a_file(self):
        for arg in ("--output=out.txt", "--output"):
            self.assertEqual(self.peek("diff", arg).returncode, 2, arg)


if __name__ == "__main__":
    unittest.main()
