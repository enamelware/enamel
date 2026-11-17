# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #24, wording only: the 0.13.1 rewrite in the project voice changes
words, never what apps get or what the style guide looks like. Compared with
the v0.13.0 tag (the last release before it, a pushed tag that never moves):

- the tokens, the components stylesheet and script, and the style guide's own
  styles and script are the same once comments and the version stamp are set
  aside, so no token value, rule, animation or behaviour moved;
- every style guide page has the same markup (every tag and attribute, every
  style and script block) once its text is set aside, so the hand-written
  Overview page was neither restyled nor regenerated and the generated pages
  only changed their words.

These hold while VERSION says 0.13.1; once a later version moves on, they
skip, since later issues may change the code on purpose.

    scripts/test.sh unit tests.test_wording_only
"""
import os, re, subprocess, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEFORE, NOW = "0.13.0", "0.13.1"

CODE = ["tokens/enamel.css", "components/enamel-components.css", "components/enamel-components.js"]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def at_tag(rel):
    """The file at the v0.13.0 tag, or None if the tag or the file isn't there."""
    try:
        out = subprocess.run(["git", "show", f"v{BEFORE}:{rel}"], cwd=ROOT, capture_output=True,
                             text=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout


def docs_at_tag():
    listing = at_tag("docs/")
    return [] if listing is None else [name for name in listing.splitlines()[1:] if name.strip()]


def code_only(text):
    """CSS or JavaScript without its comments and with the version stamp set aside, whitespace evened out."""
    text = text.replace(NOW, BEFORE)
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))
    return " ".join(text.split())


def markup_only(html):
    """Every tag with its attributes, and every style and script block whole, in order; no text."""
    html = html.replace(NOW, BEFORE)
    blocks = re.findall(r"<(style|script)\b[^>]*>(.*?)</\1>", html, re.S)
    html = re.sub(r"<(style|script)\b([^>]*)>.*?</\1>", r"<\1\2></\1>", html, flags=re.S)
    tags = [" ".join(t.split()) for t in re.findall(r"<[^>]+>", html)]
    return tags, [(kind, " ".join(body.split())) for kind, body in blocks]


class WordingOnly(unittest.TestCase):
    def setUp(self):
        if read("VERSION").strip() != NOW:
            self.skipTest(f"VERSION has moved on from {NOW}")
        if at_tag("VERSION") is None:
            self.skipTest(f"the v{BEFORE} tag is not in this clone")

    def test_tokens_components_and_script_are_unchanged(self):
        for rel in CODE:
            with self.subTest(rel=rel):
                self.assertEqual(code_only(read(rel)), code_only(at_tag(rel)),
                                 f"{rel} changed beyond its comments and version stamp")

    def test_the_style_guide_styles_and_script_are_unchanged(self):
        names = [n for n in docs_at_tag() if n.endswith((".css", ".js"))]
        self.assertTrue(names, "the style guide's own styles and script were not found at the tag")
        for name in names:
            rel = "docs/" + name
            with self.subTest(rel=rel):
                self.assertEqual(code_only(read(rel)), code_only(at_tag(rel)))

    def test_every_page_keeps_its_markup(self):
        pages = [n for n in docs_at_tag() if n.endswith(".html")]
        for expected in ("overview.html", "index.html", "components.html", "motion.html", "resize.html"):
            self.assertIn(expected, pages)
        for name in pages:
            rel = "docs/" + name
            with self.subTest(rel=rel):
                now_tags, now_blocks = markup_only(read(rel))
                old_tags, old_blocks = markup_only(at_tag(rel))
                self.assertEqual(now_blocks, old_blocks, f"{rel}: a style or script block changed")
                self.assertEqual(len(now_tags), len(old_tags), f"{rel}: elements were added or removed")
                changed = [(old, new) for old, new in zip(old_tags, now_tags) if old != new]
                self.assertEqual(changed, [], f"{rel}: a tag or attribute changed")


class TheComparisonCatchesChanges(unittest.TestCase):
    """The helpers above would notice a real change, not only pass."""

    def test_a_changed_value_is_caught_and_a_comment_is_not(self):
        css = "/* Enamel, version 0.13.0. */\n:root { --en-x: 4px; }\n"
        self.assertEqual(code_only(css.replace("version 0.13.0.", "version 0.13.1, reworded.")), code_only(css))
        self.assertNotEqual(code_only(css.replace("4px", "8px")), code_only(css))
        js = "// says hello\nfunction f() { return 1; }\n"
        self.assertEqual(code_only(js.replace("says hello", "greets")), code_only(js))
        self.assertNotEqual(code_only(js.replace("return 1", "return 2")), code_only(js))

    def test_a_changed_class_or_style_is_caught_and_text_is_not(self):
        page = '<style>p { color: red; }</style><p class="plain">Words you read.</p>'
        self.assertEqual(markup_only(page.replace("you read", "to read")), markup_only(page))
        self.assertNotEqual(markup_only(page.replace('"plain"', '"loud"')), markup_only(page))
        self.assertNotEqual(markup_only(page.replace("red", "blue")), markup_only(page))
        self.assertNotEqual(markup_only(page.replace("</p>", "</p><p></p>")), markup_only(page))


if __name__ == "__main__":
    unittest.main()
