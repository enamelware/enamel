# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #38: the style guide is published as a website with GitHub Pages,
serving the repo root from main at enamelware.github.io/enamel. These tests
check what can be checked before the site is live:

  - an empty .nojekyll file at the root, so GitHub serves the files as they are;
  - a small index.html at the root that sends visitors to the Overview page;
  - every link, stylesheet and script on the style guide pages and the root
    page is relative, names a file that exists with exactly that spelling
    (the site's server cares about upper and lower case), and loads nothing
    from any other address;
  - served under /enamel/, as the site will be, the root page and every style
    guide page, stylesheet and script load;
  - the README gives the site's address (added once the live site was checked)
    and still sends people working on Enamel to the launcher.

    scripts/test.sh unit tests.test_site
"""
import html.parser, http.server, os, re, threading, unittest, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "/enamel/"
PAGES = ["index.html", "docs/overview.html", "docs/index.html", "docs/components.html",
         "docs/motion.html", "docs/resize.html"]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


class Links(html.parser.HTMLParser):
    """Every href and src on a page, with the tag it is on."""

    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value is not None:
                self.found.append((tag, value))


def links(rel):
    parser = Links()
    parser.feed(read(rel))
    return parser.found


def exists_exactly(path):
    """True if path exists under ROOT with exactly this spelling."""
    here = ROOT
    for part in os.path.relpath(path, ROOT).split(os.sep):
        if part not in os.listdir(here):
            return False
        here = os.path.join(here, part)
    return True


def local_targets(rel):
    """The files a page links to or loads, resolved from its own folder."""
    out = []
    for tag, value in links(rel):
        target = value.split("#", 1)[0].split("?", 1)[0]
        if not target:
            continue
        out.append((tag, value, os.path.normpath(os.path.join(ROOT, os.path.dirname(rel), target))))
    return out


class RootFiles(unittest.TestCase):
    def test_nojekyll_is_empty(self):
        path = os.path.join(ROOT, ".nojekyll")
        self.assertTrue(os.path.isfile(path), ".nojekyll is missing at the root")
        self.assertEqual(os.path.getsize(path), 0)

    def test_root_page_sends_visitors_to_overview(self):
        page = read("index.html")
        self.assertRegex(page, r'<meta http-equiv="refresh" content="0; url=docs/overview\.html">')
        self.assertIn('href="docs/overview.html"', page)

    def test_root_page_uses_only_tokens_for_colour(self):
        style = re.search(r"<style>(.*?)</style>", read("index.html"), re.S).group(1)
        self.assertNotRegex(style, r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


class Links_(unittest.TestCase):
    def test_every_link_is_relative_and_exists(self):
        for rel in PAGES:
            for tag, value, path in local_targets(rel):
                with self.subTest(page=rel, link=value):
                    self.assertFalse(value.startswith("/"),
                                     "starts from the top of the address; breaks under /enamel/")
                    self.assertNotRegex(value, r"^[a-z]+:", "points at another address")
                    self.assertTrue(path.startswith(ROOT + os.sep), "points outside the repo")
                    self.assertTrue(exists_exactly(path), "no file with exactly this spelling")

    def test_stylesheets_load_nothing_from_elsewhere(self):
        for rel in ("tokens/enamel.css", "components/enamel-components.css", "docs/site.css"):
            css = read(rel)
            with self.subTest(file=rel):
                self.assertNotIn("@import", css)
                for url in re.findall(r"url\(\s*['\"]?([^'\")]{0,40})", css):
                    self.assertTrue(url.startswith("data:"), url)

    def test_scripts_fetch_nothing(self):
        for rel in ("components/enamel-components.js", "docs/site.js"):
            js = read(rel)
            with self.subTest(file=rel):
                self.assertNotRegex(js, r"\bfetch\(|XMLHttpRequest|\bimport\(|https?://")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves the repo under /enamel/ only, as the published site does."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        if not path.startswith(PREFIX):
            return os.path.join(ROOT, "no-such-file")
        return super().translate_path("/" + path[len(PREFIX):])

    def log_message(self, *args):
        pass


class UnderSiteAddress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}{PREFIX}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def status(self, url):
        try:
            with urllib.request.urlopen(url) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    def test_every_page_and_what_it_loads(self):
        for rel in PAGES:
            page_url = urllib.parse.urljoin(self.base, rel)
            with self.subTest(page=rel):
                self.assertEqual(self.status(page_url), 200)
            for tag, value in links(rel):
                if value.startswith("#"):
                    continue
                with self.subTest(page=rel, link=value):
                    self.assertEqual(self.status(urllib.parse.urljoin(page_url, value)), 200)

    def test_the_site_root_opens(self):
        self.assertEqual(self.status(self.base), 200)


class Readme(unittest.TestCase):
    def test_readme_gives_the_address_and_keeps_the_launcher(self):
        section = read("README.md").split("## Style guide", 1)[1].split("\n## ", 1)[0]
        self.assertIn("https://enamelware.github.io/enamel/", section)
        self.assertIn("Enamel style guide launcher", section)


if __name__ == "__main__":
    unittest.main()
