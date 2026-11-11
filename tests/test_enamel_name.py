# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #13: the design system is called Enamel, and 0.7.0 ships the rename.

tests/test_old_prefix.py checks that no old name is left. These tests check
the other side: that the new name and its notes are in place (the one
description, word for word, in README.md, DESIGN.md and the changelog; every
style guide page's title, menu and footer; NOTICE.md, DECISIONS.md and
CLAUDE.md), that 0.7.0 is written up as a breaking release pointing to
MIGRATION.md, that nothing looks or moves differently from v0.6.0 (the
styles, scripts and page structure match it once the #12 rename is applied;
reads the local git history only), that the clone uses the new GitHub
address, that the Desktop launcher is called "Enamel style guide" and runs
tools/serve.py (read only; skipped where there is no Desktop), and that the style
guide checker really stops when an old name is planted (in a temporary
folder, never in the repo).

The old names are built from parts here, so this file doesn't use them.

    scripts/test.sh unit tests.test_enamel_name
"""
import contextlib, io, os, re, shutil, subprocess, sys, tempfile, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_migration  # noqa: E402
import check_guide as cg  # noqa: E402
import enamel_tokens  # noqa: E402
import old_names  # noqa: E402

KETTLE = "kett" + "le"
DESCRIPTION = ("Enamel is a design system for controller-first apps that feel at home in Steam's Gaming Mode: "
               "Steam's own baseline with one accent colour on top, like a thin coat of enamel over steel.")
PAGES = ["overview.html", "index.html", "components.html", "motion.html", "resize.html"]


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def entry(text, heading_re):
    """(heading, body) of the first '## ' entry whose heading matches."""
    m = re.search(rf"^## ({heading_re}[^\n]*)\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.groups() if m else (None, None)


class Description(unittest.TestCase):
    def test_the_same_description_everywhere(self):
        for rel in ("README.md", "DESIGN.md", "CHANGELOG.md"):
            with self.subTest(rel=rel):
                self.assertIn(DESCRIPTION, read(rel))

    def test_it_opens_the_readme_and_design_md(self):
        for rel in ("README.md", "DESIGN.md"):
            with self.subTest(rel=rel):
                lines = [l for l in read(rel).splitlines() if l.strip()]
                self.assertTrue(lines[0].startswith("# Enamel"), lines[0])
                self.assertTrue(lines[1].startswith(DESCRIPTION), "the description should come first")


class StyleGuidePages(unittest.TestCase):
    def test_every_page_says_enamel(self):
        for page in PAGES:
            with self.subTest(page=page):
                text = read("docs", page)
                title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
                self.assertTrue(title.startswith("Enamel "), title)
                self.assertIn('<div class="site-menu__brand"><strong>Enamel</strong>', text)
                self.assertRegex(text, r"<footer[^>]*>Enamel is not affiliated with Valve\.")
                self.assertNotRegex(text, rf"<title>{KETTLE.capitalize()}\b")

    def test_the_menu_shows_the_new_version(self):
        version = read("VERSION").strip()
        for page in PAGES:
            with self.subTest(page=page):
                self.assertIn(f"<strong>Enamel</strong><span>Version {version}</span>", read("docs", page))

    def test_the_source_label_is_enamel(self):
        labels = {t["label"] for g in enamel_tokens.load() for t in g["tokens"]}
        self.assertEqual(labels, {"Steam baseline", "Enamel"})
        self.assertNotIn(f"| {KETTLE.capitalize()} |", read("DESIGN.md"))


class Notes(unittest.TestCase):
    def test_notice_keeps_both_names_out_of_the_licence(self):
        text = read("NOTICE.md")
        self.assertIn("The MIT licence grants no rights to the Enamel or Kettle names or the Kettle wordmark.", text)
        self.assertIn("Enamel and Kettle are not affiliated with Valve.", text)

    def test_decisions_records_the_rename(self):
        head, body = entry(read("DECISIONS.md"), r"\d{4}-\d{2}-\d{2}, renamed to Enamel for the public launch")
        self.assertIsNotNone(head, "DECISIONS.md has no entry for the rename to Enamel")
        self.assertGreaterEqual(head[:10], old_names.RENAMED_ON)
        self.assertIn("thin coat of colour over a solid base", body)
        self.assertRegex(body, r"prefix changed now[^\n]*while one app uses it")

    def test_claude_md_says_kettle_video_keeps_the_old_names(self):
        text = read("CLAUDE.md")
        self.assertTrue(text.startswith("# Enamel\n"))
        part = text.split("## Who uses this", 1)[1].split("\n## ", 1)[0]
        self.assertRegex(part, r"Kettle Video keeps the old names[^\n]*until its own switch issue[^\n]*MIGRATION\.md")
        self.assertIn("Enamel style guide", text)


class Release(unittest.TestCase):
    """0.7.0 shipped the rename; later versions (0.8.0, #15) follow it."""

    def test_version_is_0_7_0_or_later(self):
        version = tuple(int(n) for n in read("VERSION").strip().split("."))
        self.assertGreaterEqual(version, (0, 7, 0))

    def test_the_main_files_carry_the_version(self):
        version = read("VERSION").strip()
        for rel, name in (("tokens/enamel.css", "Enamel design tokens"),
                          ("components/enamel-components.css", "Enamel components"),
                          ("components/enamel-components.js", "Enamel components behaviour")):
            with self.subTest(rel=rel):
                self.assertIn(f"{name}, version {version}.", read(rel))

    def test_changelog_entry_is_breaking_and_points_to_migration(self):
        text = read("CHANGELOG.md")
        heads = re.findall(r"^## ([^\n]*)", text, re.M)
        rename = [h for h in heads if h.startswith("0.7.0, ")]
        self.assertEqual(len(rename), 1, "CHANGELOG.md should have one 0.7.0 entry")
        self.assertRegex(rename[0], r"^0\.7\.0, \d{4}-\d{2}-\d{2} \(breaking\)$")
        _, body = entry(text, r"0\.7\.0, ")
        self.assertIn("(MIGRATION.md)", body, "the entry should link MIGRATION.md")
        self.assertRegex(body, r"Kettle Video, through its own switch issue")
        self.assertTrue(text.startswith("# Changelog\n\nEach version of Enamel,"))


def git_show(rev, rel):
    if shutil.which("git") is None or not os.path.exists(os.path.join(ROOT, ".git")):
        return None
    out = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{rel}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def renamed(text):
    for pattern, replacement in build_migration.RULES:
        text = re.sub(pattern, replacement, text)
    return text


def code_only(text):
    """Styles or script without comments or blank space, so only what runs is compared."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(?m)^\s*//.*$", "", text)
    return [" ".join(line.split()) for line in text.splitlines() if line.strip()]


BEFORE = "v0.6.0"
THIS_RELEASE = read("VERSION").strip() == "0.7.0"


@unittest.skipUnless(git_show(BEFORE, "VERSION") is not None, f"no git history with the {BEFORE} tag")
@unittest.skipUnless(THIS_RELEASE, "only 0.7.0 promises no change from 0.6.0; later versions change things on purpose")
class NothingLooksOrMovesDifferently(unittest.TestCase):
    """0.7.0 against v0.6.0 with the #12 rename applied: the styles and scripts are the same, comments aside."""

    def test_styles_and_scripts_are_unchanged(self):
        pairs = [(o, n) for o, n in build_migration.FILES if not n.endswith(".py")]
        pairs += [("docs/site.css", "docs/site.css"), ("docs/site.js", "docs/site.js")]
        self.assertGreaterEqual(len(pairs), 5)
        for old, new in pairs:
            with self.subTest(file=new):
                before = git_show(BEFORE, old)
                self.assertIsNotNone(before, f"{old} is missing at {BEFORE}")
                self.assertEqual(code_only(read(new)), code_only(renamed(before)),
                                 f"{new} changed more than its names since {BEFORE}")

    def test_page_styles_are_unchanged(self):
        for page in PAGES:
            with self.subTest(page=page):
                before = git_show(BEFORE, f"docs/{page}")
                self.assertIsNotNone(before)
                style = lambda t: [code_only(b) for b in re.findall(r"<style[^>]*>(.*?)</style>", t, re.S)]
                attrs = lambda t: re.findall(r'\sstyle="([^"]*)"', t)
                self.assertEqual(style(read("docs", page)), style(renamed(before)))
                self.assertEqual(attrs(read("docs", page)), attrs(renamed(before)))

    def test_the_page_structure_is_unchanged(self):
        """Same elements, classes and attributes in the same order on every page; only text differs."""
        tags = lambda t: re.findall(r"<[a-zA-Z][^>]*>", re.sub(r"<!--.*?-->", "", t, flags=re.S))
        for page in PAGES:
            with self.subTest(page=page):
                now, before = tags(read("docs", page)), tags(renamed(git_show(BEFORE, f"docs/{page}")))
                # the only tag allowed to differ is the version in the menu, and descriptive labels
                diff = [(a, b) for a, b in zip(before, now) if a != b]
                self.assertEqual(len(now), len(before))
                for a, b in diff:
                    self.assertEqual(re.sub(r'aria-label="[^"]*"', "", a), re.sub(r'aria-label="[^"]*"', "", b))


class Clone(unittest.TestCase):
    def test_the_clone_uses_the_new_repo_address(self):
        config = os.path.join(ROOT, ".git", "config")
        if not os.path.isfile(config):
            self.skipTest("not a plain clone (no .git/config)")
        with open(config, encoding="utf-8") as f:
            urls = re.findall(r"^\s*(?:push)?url\s*=\s*(\S+)", f.read(), re.M)
        self.assertTrue(urls, "the clone has no GitHub address")
        for url in urls:
            self.assertRegex(url, r"enamelware/enamel(?:\.git)?/?$", url)

    def test_the_board_settings_use_the_new_repo(self):
        self.assertIn('"repo": "enamelware/enamel"', read(".claude", "board.json"))


DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")


def launchers():
    """{file name: {key: value}} for every Desktop launcher that runs this repo's tools/serve.py (read only)."""
    found, serve = {}, os.path.join(ROOT, "tools", "serve.py")
    for name in sorted(os.listdir(DESKTOP)):
        if not name.endswith(".desktop"):
            continue
        try:
            with open(os.path.join(DESKTOP, name), encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        entry = dict(re.findall(r"^([A-Za-z]+)=(.*)$", text, re.M))
        if serve in entry.get("Exec", ""):
            found[name] = entry
    return found


@unittest.skipUnless(os.path.isdir(DESKTOP), "no Desktop folder here (the launcher lives on the device's Desktop)")
class Launcher(unittest.TestCase):
    """The one Desktop launcher for the style guide is called "Enamel style guide" and runs tools/serve.py."""

    def test_the_launcher_is_called_enamel_style_guide(self):
        found = launchers()
        self.assertEqual(list(found), ["Enamel style guide.desktop"],
                         "there should be exactly one style guide launcher, named Enamel style guide")
        entry = found["Enamel style guide.desktop"]
        self.assertEqual(entry.get("Name"), "Enamel style guide")
        self.assertNotIn(KETTLE.capitalize() + " style guide", entry.get("Comment", ""))

    def test_the_launcher_opens_the_style_guide(self):
        entry = launchers().get("Enamel style guide.desktop")
        self.assertIsNotNone(entry, "no Enamel style guide launcher on the Desktop")
        exec_line = entry["Exec"].split()
        self.assertEqual(exec_line[-1], os.path.join(ROOT, "tools", "serve.py"))
        self.assertNotIn("--no-open", exec_line, "the launcher should open the page in the browser")
        self.assertEqual(entry.get("Terminal"), "true", "the launcher needs its window, which stops the server")

    def test_no_launcher_keeps_the_old_name(self):
        self.assertFalse(os.path.exists(os.path.join(DESKTOP, KETTLE.capitalize() + " style guide.desktop")))


class CheckerStopsOnOldNames(unittest.TestCase):
    """The style guide checker itself, with an old name planted in a temporary folder."""

    def run_checker(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                path = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            others = {n: (lambda *a, **k: None) for n in dir(cg)
                      if n.startswith("check_") and n != "check_old_names" and callable(getattr(cg, n))}
            out = io.StringIO()
            with mock.patch.object(old_names, "ROOT", tmp), mock.patch.multiple(cg, **others), \
                    mock.patch.object(cg, "failures", []), mock.patch.object(cg, "notes", []), \
                    mock.patch.object(sys, "argv", ["check_guide.py", "--no-browser"]), \
                    contextlib.redirect_stdout(out):
                try:
                    cg.main()
                    code = 0
                except SystemExit as ex:
                    code = ex.code
        return code, out.getvalue()

    def test_a_planted_old_name_fails_the_check(self):
        for sentence in (f"# {KETTLE.capitalize()} UI", f"Clone {KETTLE}-ui first.", f"var(--{'k' + 't'}-accent)"):
            with self.subTest(sentence=sentence):
                code, out = self.run_checker({"README.md": f"# Enamel\n\n{sentence}\n"})
                self.assertEqual(code, 1, out)
                self.assertIn("README.md line 3: uses an old name", out)

    def test_an_old_file_name_fails_the_check(self):
        code, out = self.run_checker({f"tokens/{KETTLE}.css": ":root {}\n"})
        self.assertEqual(code, 1, out)
        self.assertIn("(file name)", out)

    def test_the_allowed_places_pass(self):
        code, out = self.run_checker({
            "README.md": f"# Enamel\n\nKettle Video keeps its copy in `vendor/{KETTLE}-ui/`.\n",
            "CHANGELOG.md": f"# Changelog\n\n## 0.6.0, 2026-10-21 (visual)\n\n{KETTLE.capitalize()} UI.\n",
            "MIGRATION.md": f"| `tokens/{KETTLE}.css` | `tokens/enamel.css` |\n",
        })
        self.assertEqual(code, 0, out)
        self.assertIn("All checks passed.", out)


if __name__ == "__main__":
    unittest.main()
