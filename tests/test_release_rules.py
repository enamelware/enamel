# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #19: the release check keeps anything taken from Steam's files and
anything personal out of what is published.

tools/release_check.py (run by tools/check_guide.py in the quick checks)
reads every file that would be published. These tests plant each kind of
problem in a throwaway git folder and see it caught, see that ordinary
Enamel text is not mistaken for one, and see that the real repo passes.
Planted values are built from parts, so this file passes the check itself.

    scripts/test.sh unit tests.test_release_rules
"""
import os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import release_check as rc  # noqa: E402
import check_guide as cg  # noqa: E402

AT = "@"
PLANTED = [
    ("Steam's variable names", "color: var(--" + "gp" + "Color-Dark);"),
    ("Steam's variable names", "--" + "gp-system-font: x;"),
    ("Steam's variable names", "g" + "pSystem" + "Dark"),
    ("words for taking values out of Steam's files", "These values were " + "extract" + "ed from Steam."),
    ("words for taking values out of Steam's files", "copied from " + "Valve's" + " variables"),
    ("a Steam client version", "Big Picture Mode, Steam " + "client 1791415817"),
    ("a Steam client version", "build" + "id=1794266161"),
    ("a debug connection to the Steam client", 'urlopen("http://127.0.0.1:' + "8080" + '/json")'),
    ("a debug connection to the Steam client", "--remote-debugging-" + "address=127.0.0.1"),
    ("a debug connection to the Steam client", 's.call("' + "CSS" + '.getStyleSheetText")'),
    ("a home folder path", "/" + "home/someone/Videos"),
    ("a home folder path", "/run/" + "media/SDCARD/films"),
    ("a Steam ID or Steam user folder", "7656119" + "8000000001"),
    ("a Steam ID or Steam user folder", "~" + "/.local/share/" + "Steam/userdata/" + "12345/config"),
    ("a device's own login name", "deck" + AT + "steam" + "deck"),
    ("something that looks like a secret", "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2"),
    ("something that looks like a secret", "-----BEGIN OPENSSH " + "PRIVATE KEY-----"),
    ("something that looks like a secret", 'pass' + 'word = "' + 'hunter2hunter2"'),
    ("an image written into a page", '<img src="data:image/' + 'png;base64,iVBORw0KGgo">'),
    ("an email address", "write to someone" + AT + "example.org"),
]

NOT_PROBLEMS = [
    'data-token="--en-motion-fast"',                             # a design token, not a secret
    "335260252+enamelware" + AT + "users.noreply.github.com",    # the GitHub noreply address
    "git" + AT + "github.com:enamelware/enamel.git",              # an SSH address, not an email
    'f"--remote-debugging-port={self.port}"',                    # the browser check's own Firefox
    'self.s.call("browsingContext.navigate", context=ctx)',     # Firefox's protocol, not Steam's debugger
    "if (CSS.supports('container-type: inline-size')) {}",
    '"Edit(//run/media/**)"',                                    # a rule about any drive, no drive named
    "The neutral palette is matched to Steam's Gaming Mode (Steam baseline).",
    "~" + "/Development/kettle-video",
]


class Folder:
    """A throwaway git folder with an empty README."""

    def __enter__(self):
        self.root = tempfile.mkdtemp(prefix="enamel-release-")
        subprocess.run(["git", "init", "-q", self.root], check=True)
        self.write("README.md", "# Enamel\n")
        return self

    def write(self, rel, text, binary=False):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb" if binary else "w") as f:
            f.write(text)

    def problems(self):
        return rc.problems(self.root)[0]

    def __exit__(self, *exc):
        shutil.rmtree(self.root, ignore_errors=True)


class Planted(unittest.TestCase):
    def test_each_kind_is_caught(self):
        for what, line in PLANTED:
            with self.subTest(line=line), Folder() as d:
                d.write("docs/page.html", f"<p>fine</p>\n{line}\n")
                found = d.problems()
                self.assertTrue(any(what in f and "docs/page.html line 2" in f for f in found),
                                f"{line!r} was not caught as {what}: {found}")

    def test_ordinary_text_passes(self):
        for line in NOT_PROBLEMS:
            with self.subTest(line=line), Folder() as d:
                d.write("tools/x.py", line + "\n")
                self.assertEqual(d.problems(), [])

    def test_a_reference_folder_fails(self):
        with Folder() as d:
            d.write("reference/notes.md", "values\n")
            self.assertIn("reference/: the reference folder must not be published", d.problems())

    def test_screenshots_and_other_images_fail(self):
        for name in ("docs/shot.png", "capture.JPG", "docs/icon.svg"):
            with self.subTest(name=name), Folder() as d:
                d.write(name, b"\x89PNG\r\n", binary=True)
                self.assertTrue(any(name in f and "image" in f for f in d.problems()))

    def test_a_tracked_local_claude_file_fails(self):
        for rel in rc.LOCAL_FILES:
            with self.subTest(rel=rel), Folder() as d:
                d.write(rel, "{}\n")
                subprocess.run(["git", "add", "-f", rel], cwd=d.root, check=True)
                self.assertTrue(any(f.startswith(f"{rel}: a local Claude Code file") for f in d.problems()))

    def test_ignored_files_are_not_published(self):
        with Folder() as d:
            d.write(".gitignore", "notes/\n")
            d.write("notes/private.md", "/" + "home/someone\n")
            self.assertEqual(d.problems(), [])

    def test_the_speckle_is_allowed_only_in_the_tokens(self):
        speckle = '--en-speckle: url("data:image/svg+xml,%3Csvg%3E");\n'
        with Folder() as d:
            d.write("tokens/enamel.css", speckle)
            self.assertEqual(d.problems(), [])
        with Folder() as d:
            d.write("tokens/enamel.css", '--x: url("data:image/' + 'png;base64,AAAA");\n')
            self.assertTrue(d.problems())


class TheRepo(unittest.TestCase):
    def test_the_repo_passes(self):
        found, count = rc.problems()
        self.assertEqual(found, [])
        self.assertGreater(count, 50)

    def test_the_steam_tools_are_gone(self):
        self.assertFalse(os.path.isdir(os.path.join(ROOT, "reference")))
        for name in ("extract.py", "extract_motion.py", "extract_colours_pass2.py", "build_page.py",
                     "build_motion_reference.py", "css_vars.py", "css_motion.py", "cdp.py"):
            self.assertFalse(os.path.exists(os.path.join(ROOT, "tools", name)), name)

    def test_the_style_guide_check_runs_it(self):
        self.assertTrue(callable(getattr(cg, "check_release", None)))
        with open(os.path.join(ROOT, "tools", "check_guide.py"), encoding="utf-8") as f:
            main = f.read().split("def main():", 1)[1]
        self.assertIn("check_release()", main)

    def test_notice_and_claude_md_say_what_was_agreed(self):
        with open(os.path.join(ROOT, "NOTICE.md"), encoding="utf-8") as f:
            notice = f.read()
        self.assertIn("The neutral palette, spacing and motion are designed to match Steam's Gaming Mode. Enamel "
                      "includes no Valve code, class names, icons, logos or fonts. Enamel and Kettle are not affiliated "
                      "with Valve. Steam and Steam Deck are trademarks of Valve Corporation. The MIT licence grants no "
                      "rights to the Enamel or Kettle names or the Kettle wordmark.", notice)
        with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as f:
            claude = f.read()
        self.assertIn("Never add anything taken from the Steam client's files. Steam baseline values are recorded "
                      "under Enamel's own names only.", claude)
        self.assertIn("Case-study and portfolio material never goes in this repo; it lives in "
                      "~" + "/Development/enamel-case-study/.", claude)


if __name__ == "__main__":
    unittest.main()
