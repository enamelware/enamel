"""Check the style guide and the components. Standard library only.

Serves the repo on 127.0.0.1 for the duration of the check and fetches every
style guide page, stylesheet and script. Then checks that:
  - every stylesheet has balanced braces;
  - the generated pages and version stamps are up to date with the build
    script (so nothing generated was edited by hand);
  - each page's menu is the one the build script writes for that page: its
    own page marked aria-current="page", only its own sections listed, and
    every section link pointing at an id that exists;
  - no colour appears in components/ or docs/ outside the tokens (a pasted
    copy of a token with the same value counts as the token; the keyword
    transparent is allowed, as DESIGN.md Part 2 says);
  - enamel-components.css has no size outside its --en-c- variables, and
    site.css none outside its --site- layout widths (allowed by DESIGN.md);
  - the Components page shows every component in every state, and every
    "HTML to copy" block is exactly the HTML of live examples on the page;
  - the Resize page has every component in a frame resized by hand, and a
    row of fixed frames labelled by width only, from the smallest supported
    box up, at the widths the browser check uses;
  - every token appears on the token reference and in DESIGN.md Part 1 with
    the same value;
  - nothing in tokens/, components/, the style guide pages and styles in
    docs/, DESIGN.md or README.md names a device, an aspect ratio or a screen
    size (check_no_screens; the history is left alone, as agreed on #2);
  - no file uses a name from before the rename to Enamel (check_old_names,
    see old_names.py for the few places they may stay);
  - nothing that would be published holds anything taken from Steam's files
    or anything personal (check_release, see release_check.py);
and prints the contrast of every text and background pair the components use,
once per named accent. It also runs the accent check on every named accent
(see DESIGN.md, Accents) and checks that no component or page other than the
token reference names a specific accent.

Motion, read from the stylesheet:
  - every duration and curve in components/ is a motion token (Group D);
  - the focus pulse ends between four and six seconds after focus arrives;
  - the two reduced-motion blocks (device setting and data-en-motion) are
    identical, and together they cancel every animation, every transform
    and every transition that is not a colour fade.
Motion, in the device's Firefox (tools/browser_check.py): every page in full
and reduced motion, by attribute and by device setting; focus visible and
identical in all of them; no animation or transform left in reduced motion;
every component in frames from the smallest supported box to very wide
(sizes from their space, no overflow, overlap or cut-off label, every focus
ring visible, toast above the hint bar); the smallest supported box itself,
measured; the Resize page's frames (none scrolls sideways, nothing overlaps,
every focus ring visible, the resizable ones at the smallest box's width too);
and all of it again with a larger browser font size.
Exits non-zero if anything fails.

    python3 tools/check_guide.py [--screenshots FOLDER] [--no-browser | --quick]

--quick is the per-issue check (scripts/test.sh): everything above that
needs no browser, then the device's Firefox only on the style guide pages
the change touches (see touched_pages), in full and reduced motion, in one
browser. With no option it runs everything (scripts/test.sh full).
"""
import functools, glob, html, html.parser, http.server, os, re, subprocess, sys, threading, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enamel_tokens as en
import build_styleguide as sg
from serve import Handler
import old_names
import release_check
import build_speckle as speckle

DOCS = os.path.join(en.ROOT, "docs")
COMPONENTS = os.path.join(en.ROOT, "components", "enamel-components.css")
SITE_CSS = os.path.join(DOCS, "site.css")
PAGES = ["overview.html", "index.html", "components.html", "motion.html", "resize.html"]
FETCH = [f"docs/{p}" for p in PAGES] + ["docs/site.css", "docs/site.js", "components/enamel-components.js",
                                         "components/enamel-components.css", "tokens/enamel.css"]

# Every component and state the Components page must show:
# (class the element has, attribute that must be on it or None, what it is).
STATES = [
    ("en-hintbar", None, "hint bar"), ("en-hint", None, "hint"), ("en-glyph", None, "glyph"),
    ("en-glyph--shoulder", None, "shoulder glyph"),
    ("en-tab", 'aria-selected="true"', "tab, selected"), ("en-tab", 'aria-selected="false"', "tab, not selected"),
    ("en-tab", 'data-demo="focus-visible"', "tab, keyboard focus"),
    ("en-tab__count", None, "tab count"), ("en-dot", None, "new dot"),
    ("en-rows", None, "stacked rows"), ("en-row", None, "row"), ("en-row", 'data-focused="true"', "row, focused"),
    ("en-row__meta", None, "row meta"),
    ("en-shelf", None, "shelf"), ("en-tile", None, "tile"), ("en-tile", 'data-focused="true"', "tile, focused"),
    ("en-tile--large", None, "large tile"), ("en-tile__frame", None, "tile frame"), ("en-tile__title", None, "tile title"),
    ("en-button", None, "button"), ("en-button", 'data-focused="true"', "button, focused"),
    ("en-button", "disabled", "button, disabled"), ("en-button--primary", None, "primary button"),
    ("en-button--primary", 'data-focused="true"', "primary button, focused"),
    ("en-button--icon", None, "icon button"), ("en-button--icon", 'data-focused="true"', "icon button, focused"),
    ("en-toggle", 'aria-pressed="false"', "toggle, off"), ("en-toggle", 'aria-pressed="true"', "toggle, on"),
    ("en-toggle", 'data-focused="true"', "toggle, focused"),
    ("en-progress", "style", "progress with --value"), ("en-progress__fill", None, "progress fill"),
    ("en-progress--thin", None, "thin progress"), ("en-progress__head", None, "progress head line"),
    ("en-menu", None, "side menu"), ("en-menu__item", None, "menu item"),
    ("en-menu__item", 'aria-current="page"', "menu item, current"),
    ("en-menu__item", 'data-focused="true"', "menu item, focused"),
    ("en-actionbar", None, "action bar"), ("en-icon", None, "drawn icon"),
    ("en-dialog", "open", "picker dialog, open over a screen"), ("en-picker", None, "picker panel"),
    ("en-picker__title", None, "picker question"), ("en-picker__rows", None, "picker rows"),
    ("en-picker__row", None, "picker row"), ("en-picker__row", 'data-focused="true"', "picker row, focused"),
    ("en-picker__row", 'aria-current="true"', "picker row, current choice"),
    ("en-picker__desc", None, "picker row description"), ("en-picker__cancel", None, "picker Cancel row"),
    ("en-toast", None, "toast"), ("en-toast__icon", None, "toast icon"), ("en-toast__text", None, "toast text"),
    ("en-steplabel", None, "step label"),
    ("en-band", None, "group band"), ("en-band--outline", None, "group band, outlined"),
    ("en-band__name", None, "group band name"), ("en-band__count", None, "group band count"),
    ("en-badge", None, "badge"),
    ("en-row__message", None, "message in a row"), ("en-row__message", 'role="status"', "message in a row, announced"),
    ("en-steps", None, "numbered steps"),
    ("en-statpair", None, "stat pair"), ("en-statpanel", None, "stat panel"),
    ("en-statpanel", 'role="img"', "stat panel, one item for screen readers"),
    ("en-statpanel__counts", None, "stat panel counts"), ("en-statpanel__count", None, "stat panel count"),
    ("en-statpanel__number", None, "stat panel number"), ("en-statpanel__path", None, "stat panel path"),
    ("en-statpanel__notset", None, "stat panel, not set"),
    ("en-note", None, "note"),
    ("en-button", 'data-pressed="true"', "button, pressed"),
    ("en-picker__row", 'data-pressed="true"', "picker row, pressed"),
    ("en-speckle", None, "page speckle"),
]

# Text (or graphic) on background, for every pair the components use.
# A background of ("glow", base) is --en-accent-glow laid over base; one of
# ("fleck", colour) is the page with its strongest speckle fleck in that colour.
PAIRS = [
    ("Hint bar", "label", "--en-text-strong", "--en-surface-bar", "text"),
    ("Hint bar", "glyph letter", "--en-focus-fill-ink", "--en-focus-fill", "text"),
    ("Hint bar", "glyph on the bar", "--en-focus-fill", "--en-surface-bar", "graphic"),
    ("Tabs", "tab", "--en-text", "--en-surface-page", "text"),
    ("Tabs", "count", "--en-text-muted", "--en-surface-page", "text"),
    ("Tabs", "selected tab", "--en-text-strong", "--en-surface-control", "text"),
    ("Tabs", "selected count", "--en-text-soft", "--en-surface-control", "text"),
    ("Tabs", "new dot", "--en-accent", "--en-surface-page", "graphic"),
    ("Tabs", "keyboard focus ring", "--en-focus-ring", "--en-surface-page", "graphic"),
    ("Tabs", "new dot, selected tab", "--en-accent", "--en-surface-control", "graphic"),
    ("List row", "title", "--en-text", "--en-surface-raised", "text"),
    ("List row", "meta", "--en-text-muted", "--en-surface-raised", "text"),
    ("List row", "focused title", "--en-text-strong", "--en-surface-control", "text"),
    ("List row", "focused meta", "--en-text-soft", "--en-surface-control", "text"),
    ("Tile", "frame label", "--en-text-muted", "--en-surface-raised", "text"),
    ("Tile", "title", "--en-text-soft", "--en-surface-page", "text"),
    ("Tile", "focus ring", "--en-focus-ring", "--en-surface-page", "graphic"),
    ("Button", "label", "--en-text", "--en-surface-control", "text"),
    ("Button", "focused label", "--en-focus-fill-ink", "--en-focus-fill", "text"),
    ("Button", "primary label", "--en-accent-ink", "--en-accent", "text"),
    ("Button", "pressed label", "--en-focus-fill-ink", "--en-cream-pressed", "text"),
    ("Button", "focus underside, on a row", "--en-focus-ring", "--en-surface-raised", "graphic"),
    ("Button", "disabled label", "--en-text-muted", "--en-surface-control", "disabled"),
    ("Toggle", "off thumb", "--en-cream", "--en-surface-control", "graphic"),
    ("Toggle", "on thumb", "--en-accent-ink", "--en-accent", "graphic"),
    ("Toggle", "on track, on a row", "--en-accent", "--en-surface-raised", "graphic"),
    ("Toggle", "focus ring, on a row", "--en-focus-ring", "--en-surface-raised", "graphic"),
    ("Progress", "fill on track", "--en-accent", "--en-surface-bar", "graphic"),
    ("Progress", "head value", "--en-text-strong", "--en-surface-page", "text"),
    ("Progress", "head status, on the page", "--en-accent", "--en-surface-page", "text"),
    ("Progress", "head status, on a row", "--en-accent", "--en-surface-raised", "text"),
    ("Side menu", "item, on a raised panel", "--en-text-soft", "--en-surface-raised", "text"),
    ("Side menu", "item, on the page", "--en-text-soft", "--en-surface-page", "text"),
    ("Side menu", "current item, on a raised panel", "--en-text-strong", ("glow", "--en-surface-raised"), "text"),
    ("Side menu", "current item, on the page", "--en-text-strong", ("glow", "--en-surface-page"), "text"),
    ("Side menu", "focused item", "--en-text-strong", "--en-surface-control", "text"),
    ("Side menu", "focus bar", "--en-accent", "--en-surface-control", "graphic"),
    ("Action bar", "button label", "--en-text", "--en-surface-control", "text"),
    ("Action bar", "focused button on the bar", "--en-focus-fill", "--en-surface-bar", "graphic"),
    ("Picker", "question, over the darkened page", "--en-text-strong", "--en-surface-bar", "text"),
    ("Picker", "row title", "--en-text", "--en-surface-raised", "text"),
    ("Picker", "row description", "--en-text-muted", "--en-surface-raised", "text"),
    ("Picker", "current choice title", "--en-text-strong", "--en-surface-control", "text"),
    ("Picker", "current choice description", "--en-text-soft", "--en-surface-control", "text"),
    ("Picker", "focused row title", "--en-focus-fill-ink", "--en-focus-fill", "text"),
    ("Picker", "focused row description", "--en-focus-fill-ink", "--en-focus-fill", "text"),
    ("Toast", "text", "--en-text-strong", "--en-surface-page", "text"),
    ("Toast", "icon", "--en-text-strong", "--en-surface-page", "graphic"),
    ("Step label", "label", "--en-text-muted", "--en-surface-page", "text"),
    ("Group band", "name, filled", "--en-text-strong", "--en-surface-control", "text"),
    ("Group band", "count, filled", "--en-text-soft", "--en-surface-control", "text"),
    ("Group band", "icon, filled", "--en-text-strong", "--en-surface-control", "graphic"),
    ("Group band", "name, outlined", "--en-text-strong", "--en-surface-page", "text"),
    ("Group band", "count, outlined", "--en-text-soft", "--en-surface-page", "text"),
    ("Group band", "outline", "--en-text-muted", "--en-surface-page", "graphic"),
    ("Badge", "text", "--en-text-soft", "--en-surface-control", "text"),
    ("Badge", "text, focused row or selected tab", "--en-text-soft", "--en-surface-page", "text"),
    ("Badge", "on the cream focus fill", "--en-surface-page", "--en-focus-fill", "graphic"),
    ("Row message", "text", "--en-text-strong", "--en-surface-raised", "text"),
    ("Row message", "text, focused row", "--en-text-strong", "--en-surface-control", "text"),
    ("Row message", "mark on its red disc", "--en-focus-fill-ink", "--en-danger", "graphic"),
    ("Row message", "text, focused picker row", "--en-focus-fill-ink", "--en-focus-fill", "text"),
    ("Row message", "red disc, focused picker row", "--en-danger", "--en-focus-fill", "graphic"),
    ("Steps", "step", "--en-text", "--en-surface-page", "text"),
    ("Steps", "number", "--en-text-strong", "--en-surface-control", "text"),
    ("Stat panel", "number", "--en-text-strong", "--en-surface-raised", "text"),
    ("Stat panel", "word", "--en-text", "--en-surface-raised", "text"),
    ("Stat panel", "path", "--en-text-soft", "--en-surface-raised", "text"),
    ("Stat panel", "not set", "--en-text-muted", "--en-surface-raised", "text"),
    ("Note", "text", "--en-text-soft", "--en-surface-page", "text"),
    ("Note", "icon", "--en-text-soft", "--en-surface-page", "graphic"),
    # Text that stands directly on the page ground, beside the page speckle.
    ("Speckle", "tab, by a cream fleck", "--en-text", ("fleck", "--en-cream"), "text"),
    ("Speckle", "muted text, by a cream fleck", "--en-text-muted", ("fleck", "--en-cream"), "text"),
    ("Speckle", "muted text, by an accent fleck", "--en-text-muted", ("fleck", "--en-accent"), "text"),
    ("Speckle", "soft text, by a cream fleck", "--en-text-soft", ("fleck", "--en-cream"), "text"),
    ("Speckle", "accent status text, by a cream fleck", "--en-accent", ("fleck", "--en-cream"), "text"),
]

NAMED = ("aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet "
         "brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue "
         "darkgray darkgrey darkgreen darkred darkorange gold goldenrod gray grey green greenyellow hotpink "
         "indigo ivory khaki lavender lightblue lightgray lightgrey lightgreen lime linen magenta maroon navy "
         "olive orange orchid pink plum purple red salmon sienna silver skyblue snow tan teal thistle tomato "
         "turquoise violet wheat white whitesmoke yellow currentcolor").split()
COLOUR_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\b|\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\(|\b(?:%s)\b"
                       % "|".join(NAMED), re.I)

failures, notes = [], []


def fail(msg):
    failures.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def declarations(css):
    """Yield (property, value) for every declaration in a stylesheet."""
    for m in re.finditer(r"([-\w]+)\s*:\s*([^;{}]+)", strip_comments(css)):
        yield m.group(1).strip(), m.group(2).strip()


def css_of_page(text):
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S)
    attrs = [f"x{{{v}}}" for v in re.findall(r'\sstyle="([^"]*)"', text)]
    return blocks + attrs


def check_fetch():
    class Quiet(Handler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=en.ROOT)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/"
    try:
        for path in FETCH:
            try:
                with urllib.request.urlopen(base + path, timeout=10) as r:
                    body = r.read()
                if r.status != 200 or not body:
                    fail(f"{path}: status {r.status}, {len(body)} bytes")
            except Exception as ex:
                fail(f"{path}: could not load ({ex})")
            # every local stylesheet and script a page links must load too
            if path.endswith(".html"):
                for ref in re.findall(r'(?:href|src)="([^"#:]+\.(?:css|js))"', body.decode()):
                    url = urllib.parse.urljoin(base + path, ref)
                    try:
                        urllib.request.urlopen(url, timeout=10).read()
                    except Exception as ex:
                        fail(f"{path} links {ref}, which does not load ({ex})")
    finally:
        server.shutdown()
    print(f"Loaded over http: {len(FETCH)} files")


def check_braces():
    for path in [COMPONENTS, SITE_CSS, en.CSS]:
        bare = strip_comments(read(path))
        depth = 0
        for ch in bare:
            depth += (ch == "{") - (ch == "}")
            if depth < 0:
                break
        if depth != 0:
            fail(f"{os.path.relpath(path, en.ROOT)}: unbalanced braces")
    en.load()
    print("Stylesheets: braces balance; tokens parse")


def check_generated():
    page, _, version = sg.build()
    expected = [(sg.OUT, page)] + sg.other_pages(version)
    for path, text in expected:
        if read(path) != text:
            fail(f"{os.path.relpath(path, en.ROOT)} is out of date or edited by hand; run build_styleguide.py")
    for path, prefix in sg.STAMPED:
        old, new = sg.stamp_version(path, prefix, version)
        if old != new:
            fail(f"{os.path.relpath(path, en.ROOT)}: header version is not {version}")
    print(f"Generated: token reference, Components, Motion and Resize pages up to date; both stylesheets and the script say version {version}")


def check_menu():
    version = read(sg.VERSION).strip()
    for p in PAGES:
        text = read(os.path.join(DOCS, p))
        blocks = re.findall(re.escape(sg.MENU_START) + r".*?" + re.escape(sg.MENU_END), text, flags=re.S)
        if len(blocks) != 1:
            fail(f"docs/{p}: expected one menu block, found {len(blocks)}")
            continue
        block = blocks[0]
        if block != sg.menu(version, p):
            fail(f"docs/{p}: menu is not the one the build script writes for this page")
        current = re.findall(r'<a class="en-menu__item" href="([^"]*)" aria-current="page"', block)
        if current != [p]:
            fail(f"docs/{p}: menu marks {current} as the current page")
        if block.count("site-menu__sub") != 1:
            fail(f"docs/{p}: menu should list one page's sections")
        for sid in re.findall(r'href="#([^"]+)"', block):
            if not re.search(rf'\sid="{re.escape(sid)}"', text):
                fail(f"docs/{p}: menu links to #{sid}, which is not on the page")
    print(f"Menu: on all {len(PAGES)} pages, each marks its own page and lists only its sections; every link target exists")


def check_colours():
    tokens = {t["name"]: t["value"] for t in en.all_tokens(en.load())}
    norm = lambda v: re.sub(r"\s+", "", v).lower()
    sources = [(os.path.relpath(p, en.ROOT), [read(p)]) for p in
               sorted(glob.glob(os.path.join(en.ROOT, "components", "*.css")) + glob.glob(os.path.join(DOCS, "*.css")))]
    sources += [(os.path.relpath(p, en.ROOT), css_of_page(read(p))) for p in sorted(glob.glob(os.path.join(DOCS, "*.html")))]
    count = 0
    for name, sheets in sources:
        for css in sheets:
            for prop, value in declarations(css):
                if prop.startswith("--en-") and not prop.startswith("--en-c-"):
                    if prop not in tokens:
                        fail(f"{name}: defines {prop}, which is not a token")
                    elif norm(value) != norm(tokens[prop]):
                        fail(f"{name}: {prop} is {value}, but enamel.css has {tokens[prop]}")
                    continue
                bare = re.sub(r"var\([^)]*\)", "", value)
                for m in COLOUR_RE.finditer(bare):
                    fail(f"{name}: colour {m.group(0)!r} outside the tokens, in {prop}: {value}")
                count += len(re.findall(r"\btransparent\b", bare))
    print(f"Colours: checked {len(sources)} files; none outside the tokens "
          f"('transparent', which is allowed, is used {count} times)")


def check_sizes():
    size = re.compile(r"(?<![\w.-])-?\d*\.?\d+(?:px|em|rem|vh|vw|pt)\b")
    for path, allowed in [(COMPONENTS, "--en-c-"), (SITE_CSS, "--site-")]:
        css = strip_comments(read(path))
        css = re.sub(r"@media[^{]*", "", css)
        for prop, value in declarations(css):
            if prop.startswith(allowed):
                continue
            if size.search(re.sub(r"var\([^)]*\)", "", value)):
                fail(f"{os.path.relpath(path, en.ROOT)}: size outside the tokens in {prop}: {value}")
    print("Sizes: none outside tokens and declared variables")


class Elements(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        self.found.append(dict(attrs))


def check_states():
    text = read(os.path.join(DOCS, "components.html"))
    main = text.split('<main', 1)[1]  # the examples, not the site menu
    parser = Elements()
    parser.feed(main)
    for cls, attr, what in STATES:
        ok = False
        for a in parser.found:
            if cls not in (a.get("class") or "").split():
                continue
            if attr is None:
                ok = True
            elif "=" in attr:
                k, v = attr.split("=", 1)
                ok = a.get(k) == v.strip('"')
            elif attr == "style":
                ok = "--value" in (a.get("style") or "")
            else:
                ok = attr in a
            if ok:
                break
        if not ok:
            fail(f"Components page is missing: {what}")
    live = main.split('<pre class="site-code">')
    live_html = "".join(part.split("</pre>", 1)[-1] for part in live)
    blocks = re.findall(r'<pre class="site-code"><code>(.*?)</code></pre>', main, flags=re.S)
    pieces = [piece for b in blocks for piece in html.unescape(b).split("\n\n")]
    for piece in pieces:
        if piece not in live_html:
            fail(f"Components page: HTML to copy does not match a live example: {piece[:60]!r}...")
    print(f"Components page: checked {len(STATES)} components and states; "
          f"{len(pieces)} copy snippets in {len(blocks)} sections all match live examples")


class Frames(html.parser.HTMLParser):
    """The classes used inside each resizable frame, and the label of each
    row of fixed frames with the widths set on its frames."""
    VOID = {"br", "img", "input", "meta", "link", "hr", "source", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack, self.resizable, self.fixed = [], [], []
        self.caption = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag in self.VOID:
            return
        self.stack.append((tag, classes))
        names = [c for _, cs in self.stack for c in cs]
        if "site-resize" in classes:
            self.resizable.append(set())
        elif "site-resize" in names:
            self.resizable[-1].update(classes)
        if "site-frame" in classes:
            self.fixed.append(["", []])
        if "site-fixed" in classes:
            self.fixed[-1][1].append(a.get("style", ""))
        if tag == "figcaption" and "site-frame" in names:
            self.caption = self.fixed[-1]

    def handle_startendtag(self, tag, attrs):
        if self.stack and any("site-resize" in cs for _, cs in self.stack):
            self.resizable[-1].update((dict(attrs).get("class") or "").split())

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        if tag == "figcaption":
            self.caption = None

    def handle_data(self, data):
        if self.caption is not None:
            self.caption[0] += data


def check_resize():
    """The Resize page: every component in a resizable frame, and fixed frames
    labelled by width only, at the browser check's widths from the smallest
    supported box up, each as wide as its label says."""
    import browser_check
    parser = Frames()
    parser.feed(read(os.path.join(DOCS, "resize.html")).split("<main", 1)[1])
    components = sorted({cls for cls, _, _ in STATES if "__" not in cls and "--" not in cls})
    used = set().union(*parser.resizable) if parser.resizable else set()
    for cls in components:
        if cls not in used:
            fail(f"Resize page: {cls} is in no resizable frame")
    widths = []
    for caption, styles in parser.fixed:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)rem wide \((\d+)px\)", caption.strip())
        if not m:
            fail(f"Resize page: the frame label {caption.strip()!r} does not name a width only")
            continue
        rem, px, normal = float(m.group(1)), float(m.group(2)), sg.resize_page.NORMAL_PX
        if px != rem * normal:
            fail(f"Resize page: {caption.strip()!r}: {rem:g}rem is {rem * normal:g}px at the normal font size")
        if not styles or any(st != f"width: {rem:g}rem" for st in styles):
            fail(f"Resize page: the frames labelled {caption.strip()!r} are not set to that width ({styles})")
        widths.append(rem)
    expected = [w for w, _ in browser_check.FRAMES]
    if widths != expected:
        fail(f"Resize page: fixed frames are {widths} rem wide, not the browser check's {expected}")
    if not widths or widths[0] != browser_check.SMALLEST[0]:
        fail(f"Resize page: the narrowest frame is not the smallest supported box ({browser_check.SMALLEST[0]:g}rem)")
    print(f"Resize page: all {len(components)} components in {len(parser.resizable)} resizable frames; "
          f"{len(widths)} fixed widths ({', '.join(f'{w:g}' for w in widths)}rem) labelled by width only, "
          "the narrowest the smallest supported box")


def check_tokens():
    groups = en.load()
    index = read(os.path.join(DOCS, "index.html"))
    design = read(os.path.join(en.ROOT, "DESIGN.md"))
    import html as h
    for t in en.all_tokens(groups):
        if f'<code class="tok">{t["name"]}</code><code class="val">{h.escape(t["value"])}' not in index:
            fail(f"index.html: {t['name']} missing or has a different value")
        if f"| `{t['name']}` | `{t['value'].replace('|', chr(92) + '|')}`" not in design:
            fail(f"DESIGN.md: {t['name']} missing or has a different value")
    print(f"Tokens: all {len(en.all_tokens(groups))} on the token reference and in DESIGN.md with the same value")


def blend(over, alpha, base):
    o, b = en.hex_rgb(over), en.hex_rgb(base)
    return "#%02X%02X%02X" % tuple(round(alpha * x + (1 - alpha) * y) for x, y in zip(o, b))


def check_contrast():
    """Every component pair, once per named accent."""
    groups = en.load()
    base = lambda n: en.resolve(groups, f"var({n})")
    strength = re.search(r"(\d+(?:\.\d+)?)%", base("--en-accent-glow"))
    if not strength:
        fail("--en-accent-glow: no strength percentage found")
        return
    strength = float(strength.group(1)) / 100
    for a in en.accents(groups):
        active = {"--en-accent": base(a["token"]), "--en-focus-ring": base(a["token"]),
                  "--en-accent-ink": base(a["ink"])}
        colour = lambda n: active.get(n) or base(n)
        print(f"\nContrast with the {a['name']} accent (text needs 4.5:1, graphics 3:1, "
              "disabled controls have no minimum):")
        for comp, what, fg, bg, kind in PAIRS:
            if isinstance(bg, tuple) and bg[0] == "fleck":
                alpha = speckle.ACCENT_STRONGEST if bg[1] == "--en-accent" else speckle.PAGE_STRONGEST
                b = blend(colour(bg[1]), alpha, colour("--en-surface-page"))
                bg_name = f"page, {bg[1]} fleck"
            elif isinstance(bg, tuple):
                b = blend(colour("--en-accent"), strength, colour(bg[1]))
                bg_name = f"glow over {bg[1]}"
            else:
                b, bg_name = colour(bg), bg
            r = en.contrast(colour(fg), b)
            need = {"text": 4.5, "graphic": 3.0, "disabled": None}[kind]
            if need is None:
                verdict = "below 4.5, allowed (disabled)" if r < 4.5 else "pass"
                note = f"{comp}, {what}: {r:.2f}:1, below 4.5:1 but disabled controls are exempt"
                if r < 4.5 and note not in notes:
                    notes.append(note)
            else:
                verdict = "pass" if r >= need else "FAIL"
                if r < need:
                    fail(f"contrast with {a['name']}: {comp}, {what}: {r:.2f}:1 (needs {need}:1)")
            print(f"  {comp:10} {what:32} {fg:20} on {bg_name:32} {r:5.2f}:1  {kind:8} {verdict}")


def check_accents():
    """The accent check for every named accent, and no component or page
    naming a specific accent."""
    groups = en.load()
    named = en.accents(groups)
    print(f"\nAccent check (distance is CIE76 Delta E, at least {en.ACCENT_MIN_DISTANCE} from each status colour):")
    for a in named:
        tag = " (default)" if a["default"] else ""
        print(f"  {a['name']}{tag}: {a['value']}, ink {a['ink_value']}")
        for what, value, need, ok in en.accent_checks(groups, a):
            v = f"{value:5.1f}  " if what.startswith("distance") else f"{value:5.2f}:1"
            print(f"    {what:40} {v}  needs {need:g}  {'pass' if ok else 'FAIL'}")
            if not ok:
                fail(f"accent check: {a['name']}, {what}: {value:.2f} (needs {need:g})")
    named_re = re.compile(r"--en-accent-(?:%s)\b" % "|".join(re.escape(a["name"]) for a in named))
    paths = [COMPONENTS, SITE_CSS] + [os.path.join(DOCS, p) for p in ("overview.html", "components.html", "resize.html")]
    for path in paths:
        for m in named_re.finditer(read(path)):
            fail(f"{os.path.relpath(path, en.ROOT)} names a specific accent: {m.group(0)}")
    text = read(os.path.join(DOCS, "components.html"))
    for m in re.finditer(r"coral", text, re.I):
        line = text.count("\n", 0, m.start()) + 1
        notes.append(f"docs/components.html line {line}: the word {m.group(0)!r} "
                     f"in ...{text[max(0, m.start() - 50):m.end() + 20].strip()}...")
    print(f"  No component or style guide page names a specific accent ({len(paths)} files checked)")


# No device, aspect ratio or screen size (CLAUDE.md and DESIGN.md: no layout
# is tied to one). What is checked and what is left alone was agreed on #2:
# tokens/, components/, every style guide page and its styles in docs/ (the
# Overview page included), DESIGN.md and README.md are checked; the history,
# the workflow files and NOTICE.md are not. The trademark line and the tile frame's 16:9
# picture shape are always allowed. The patterns look for screen sizes and
# ratios, not any number: a contrast ratio (4.5:1), a font weight (800), a
# time (19:15, 0:00) or a fraction in calc() (17 / 15) is not one.
SCREEN_FILES = ["tokens/*", "components/*", "docs/*", "DESIGN.md", "README.md"]
TRADEMARK = "Steam and Steam Deck are trademarks of Valve Corporation"
SCREEN_RATIOS = {(4, 3), (3, 2), (5, 4), (16, 9), (16, 10), (21, 9), (32, 9), (18, 9), (19.5, 9), (20, 9),
                 (64, 27), (43, 18), (256, 135)}
SCREEN_RATIOS |= {(b, a) for a, b in SCREEN_RATIOS}  # portrait
# Common screen widths and heights in px, for media queries and "at 1280".
SCREEN_DIMENSIONS = {320, 360, 375, 390, 393, 412, 414, 428, 480, 540, 600, 640, 720, 768, 800, 810, 820, 834,
                     900, 1024, 1080, 1112, 1180, 1200, 1280, 1366, 1440, 1536, 1600, 1680, 1920, 2048, 2160,
                     2560, 2880, 3440, 3840}
NUM = r"\d+(?:\.\d+)?"
SCREEN_PATTERNS = [
    ("device", None, re.compile(r"\b(?:steam\s+deck|nova|handhelds?|rog\s+ally|legion\s+go|steam\s+machine|"
                          r"ipads?|iphones?|smartphones?|phones?|tablets?|laptops?)\b", re.I)),
    ("device", None, re.compile(r"(?<![/\w])Deck\b")),
    ("aspect ratio", "ratio", re.compile(r"(?<![\d.:])(" + NUM + r")\s*:\s*(" + NUM + r")(?![\d:]|\.\d)")),
    ("aspect ratio", "ratio", re.compile(r"(?<![\w-])aspect-ratio\s*:\s*(" + NUM + r")(?:\s*/\s*(" + NUM + r"))?")),
    ("screen query", None, re.compile(r"(?:min-|max-)(?:device-)?aspect-ratio\b|\bdevice-(?:width|height|aspect-ratio)"
                                r"\s*:|\borientation\s*:\s*(?:portrait|landscape)\b")),
    ("screen size", None, re.compile(r"(?<![\w.#-])(\d{3,4})\s*(?:px\s*)?(?:x|×|by)\s*(\d{3,4})(?:\s*px)?(?!\w|\.\d)", re.I)),
    ("screen size", None, re.compile(r"\b(?:480|576|720|1080|1440|2160|4320)[pi]\b|\b(?:4K|5K|8K|Full HD|QHD|WQHD|UHD|"
                               r"WXGA|XGA|SVGA|VGA)\b")),
    ("screen size", None, re.compile(r"\b" + NUM + r"\s*-?\s*inch(?:es)?\b|\b" + NUM + r"(?:\"|″)\s*(?:screens?|displays?)",
                               re.I)),
    ("screen size", None, re.compile(r"\b\d{3,4}\s*(?:px|pixels?)?[- ](?:wide\s+|tall\s+|high\s+)?(?:screens?|displays?|"
                               r"monitors?|viewports?|resolutions?)\b", re.I)),
    ("screen size", "dimension", re.compile(r"\b(?:at|for)\s+(?:a\s+)?(\d{3,4})(?:\s*px)?\b(?!\s*(?:rem|em|ms|%)|\w|\.\d)", re.I)),
    ("screen query", "dimension", re.compile(r"@media[^{]*?\b(?:min-|max-)?(?:width|height)\s*:\s*(" + NUM + r")px")),
]


def enclosing_selector(text, pos):
    """The CSS selector whose block `pos` is in, or "" outside any block."""
    before = text[:pos]
    opening = before.rfind("{")
    if opening < 0 or before.rfind("}") > opening:
        return ""
    start = max(before.rfind("}", 0, opening), before.rfind(">", 0, opening), before.rfind(";", 0, opening))
    return " ".join(before[start + 1:opening].split())


def tile_frame_shape(text, m, value):
    """The tile frame's 16:9 picture shape, always allowed: in a rule for the
    tile frame, or on a line that is about the tile frame."""
    if value != (16, 9):
        return False
    line_start = text.rfind("\n", 0, m.start()) + 1
    line_end = text.find("\n", m.end())
    line = text[line_start:line_end if line_end >= 0 else len(text)].lower()
    return "tile__frame" in enclosing_selector(text, m.start()) or "tile__frame" in line or "tile frame" in line


def screen_mentions(text):
    """[(line, kind, what)] for every device name, aspect ratio or screen
    size in `text`, leaving out what is always allowed."""
    text = text.replace(TRADEMARK, " " * len(TRADEMARK))
    found = []
    for kind, test, pattern in SCREEN_PATTERNS:
        for m in pattern.finditer(text):
            groups = [float(g) for g in m.groups() if g is not None]
            if test == "ratio":  # only a screen's shape, not a contrast ratio or a time
                if len(groups) == 1:  # aspect-ratio: 1.6
                    value = next((r for r in SCREEN_RATIOS if abs(r[0] / r[1] - groups[0]) < 0.005), None)
                else:
                    value = tuple(int(g) if g.is_integer() else g for g in groups)
                    if value not in SCREEN_RATIOS:
                        value = None
                if value is None or tile_frame_shape(text, m, value):
                    continue
            elif test == "dimension":  # "at 1280", or a px media query, at a common screen width or height
                if round(groups[0]) not in SCREEN_DIMENSIONS and round(groups[0] + 0.02) not in SCREEN_DIMENSIONS:
                    continue
            found.append((text.count("\n", 0, m.start()) + 1, kind, " ".join(m.group(0).split())))
    return sorted(set(found))


def screen_files():
    paths = []
    for pattern in SCREEN_FILES:
        paths += sorted(p for p in glob.glob(os.path.join(en.ROOT, pattern)) if os.path.isfile(p))
    return paths


# The grid unit rule: every size is a multiple of 4 in its own unit, 0.25rem if
# it grows with text, 4px if it does not. These are the only exceptions.
GRID_NAMES = {
    "--en-text-": "text sizes keep Steam's sizes",
    "--en-c-glyph-text": "text size",
    "--en-c-text-detail": "text size",
    "--en-shadow-": "Steam baseline shadows",
    "--en-focus-affordance": "Steam baseline focus value",
    "--en-c-backdrop-blur": "Steam's blur",
}
GRID_EXCEPTIONS = ["hairlines of 1 or 2px (rims, lips and edges)", "pills (999px)", "speckle dots and their spacing",
                   "ratios (line height, letter spacing, focus growth)", "durations",
                   "the formula and upper limit of a growing size (only its base is checked)"]


def grid_problems(css):
    """[(property, value)] for each size in `css` that breaks the grid unit rule."""
    css = re.sub(r'url\("[^"]*"\)', "", strip_comments(css))
    css = re.sub(r"@media[^{]*", "", css)
    out = []
    for prop, value in declarations(css):
        if prop == "font-size" or any(prop.startswith(n) for n in GRID_NAMES):
            continue
        bare = re.sub(r"var\([^)]*\)", "", value)
        # A growing size is written clamp(base, formula in vw, most): only its base counts.
        bare = re.sub(r"clamp\(([^,]*),[^,]*vw[^,]*,[^)]*\)", r"\1", bare)
        for number, unit in re.findall(r"(?<![\w.-])(\d*\.?\d+)(px|rem)\b", bare):
            n = float(number)
            if unit == "px" and (n in (1, 2, 999) or n % 4 == 0):
                continue
            if unit == "rem" and (n / 0.25).is_integer():
                continue
            out.append((prop, value))
    return out


def check_grid():
    paths = [en.CSS, COMPONENTS, SITE_CSS]
    for path in paths:
        for prop, value in grid_problems(read(path)):
            fail(f"{os.path.relpath(path, en.ROOT)}: {prop}: {value} breaks the grid unit rule")
    print(f"Grid unit rule: every size in {len(paths)} stylesheets is a multiple of 4 in its own unit; exceptions allowed: "
          + "; ".join(GRID_EXCEPTIONS + [f"{n}* ({why})" for n, why in GRID_NAMES.items()]))


# Patterns live on the page ground and in progress fills only.
PATTERN_SELECTORS = {".en-progress__fill", ".en-speckle", ".en-speckle::before"}


def pattern_problems(css):
    """[selector] for each rule that puts a pattern on anything else."""
    return [sel for _, sel, decls in css_rules(re.sub(r'url\("[^"]*"\)', "url()", css))
            for _, value in decls
            if ("--en-speckle" in value or "url(" in value or "repeating-" in value) and sel not in PATTERN_SELECTORS]


def check_patterns():
    for sel in pattern_problems(read(COMPONENTS)):
        fail(f"components: {sel} has a pattern; patterns live on the page ground and in progress fills only")
    print(f"Patterns: only on {', '.join(sorted(PATTERN_SELECTORS))}; nothing you can select is patterned")


def check_no_screens():
    paths = screen_files()
    for path in paths:
        for line, kind, what in screen_mentions(read(path)):
            fail(f"{os.path.relpath(path, en.ROOT)} line {line}: names a {kind} ({what!r}); no layout is tied to "
                 "a device, a screen size or an aspect ratio, and no file names one")
    print(f"Devices and screens: no device name, aspect ratio or screen size in {len(paths)} files "
          "(tokens, components, the style guide pages and styles, DESIGN.md, README.md)")


def check_old_names():
    count, found = old_names.scan()
    for where in found:
        fail(f"{where}: uses an old name from before the rename to Enamel; MIGRATION.md has the new one")
    if not found:
        print(f"Old names: none in {count} files (old dated history entries, MIGRATION.md and its script, "
              "and Kettle Video's folder name are allowed)")


def check_release():
    found, count = release_check.problems()
    for where in found:
        fail(f"release check: {where}")
    if not found:
        print(f"Release check: nothing taken from Steam's files and nothing personal in the {count} files that would be "
              "published (no reference folder, foreign images, Steam names or versions, debug connections, local "
              "Claude Code files, personal paths, emails, Steam IDs or secrets)")


def motion_tokens():
    """(durations, curves): the Group D tokens whose values are times, and those that are curves."""
    group = next(g for g in en.load() if g["title"] == "Motion")
    durations = tuple(t["name"] for t in group["tokens"] if TIME_RE.fullmatch(t["value"].strip()))
    curves = tuple(t["name"] for t in group["tokens"] if CURVE_RE.match(t["value"].strip()))
    return durations, curves
TIMING_PROPS = ("transition", "transition-duration", "transition-delay", "transition-timing-function",
                "animation", "animation-duration", "animation-delay", "animation-timing-function")
TIME_RE = re.compile(r"(?<![\w-])-?\d*\.?\d+m?s\b")
CURVE_RE = re.compile(r"\b(?:ease|ease-in|ease-out|ease-in-out|linear|step-start|step-end)\b|"
                      r"\b(?:cubic-bezier|steps|linear)\(")
REDUCED_DEVICE = ':root:not([data-en-motion="full"])'
REDUCED_ATTR = '[data-en-motion="reduced"]'
COLOUR_FADES = {"background-color", "color", "outline-color", "opacity"}


def css_rules(css):
    """[(at-rule or None, selector, [(property, value)])] for a flat stylesheet
    with one level of @media and @keyframes."""
    out = []
    css = strip_comments(css)
    for m in re.finditer(r"(@media[^{]*|@keyframes[^{]*)\{((?:[^{}]*\{[^{}]*\})*)\s*\}|([^{}@]+)\{([^{}]*)\}", css):
        if m.group(1):
            for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", m.group(2)):
                out.append((" ".join(m.group(1).split()), " ".join(sel.split()), list(declarations(body))))
        else:
            out.append((None, " ".join(m.group(3).split()), list(declarations(m.group(4)))))
    return out


def check_motion_static():
    before = len(failures)
    css = read(COMPONENTS)
    groups = en.load()
    table = {t["name"]: t["value"] for t in en.all_tokens(groups)}
    rules = css_rules(css)
    MOTION_DURATIONS, MOTION_CURVES = motion_tokens()
    count = 0
    # 1. every duration and curve is a motion token
    for at, sel, decls in rules:
        for prop, value in decls:
            if prop not in TIMING_PROPS:
                continue
            for ref in re.findall(r"var\((--[\w-]+)\)", value):
                if ref not in MOTION_DURATIONS + MOTION_CURVES + ("--en-pulse-count",):
                    fail(f"components: {sel} {prop} uses {ref}, which is not a motion token")
            bare = re.sub(r"var\([^)]*\)", "", value)
            for m in TIME_RE.finditer(bare):
                fail(f"components: {sel} {prop} has the duration {m.group(0)}; use a motion token")
            for m in CURVE_RE.finditer(bare):
                fail(f"components: {sel} {prop} has the curve {m.group(0)!r}; use a motion token")
            count += 1
    # 2. the pulse ends after four to six seconds
    pulses = [(sel, item) for at, sel, d in rules for p, v in d if p == "animation"
              for item in re.split(r",(?![^()]*\))", v) if "en-focus-pulse" in item]
    if not pulses:
        fail("components: no rule runs the en-focus-pulse animation")
    for sel, value in pulses:
        refs = re.findall(r"var\((--[\w-]+)\)", value)
        times = [r for r in refs if r in MOTION_DURATIONS]
        counts = [r for r in refs if r == "--en-pulse-count"]
        if len(times) != 2 or len(counts) != 1:
            fail(f"components: {sel}: the pulse needs a duration, a delay and --en-pulse-count, all tokens")
            continue
        ms = lambda n: (lambda v: float(v[:-2]) if v.endswith("ms") else float(v[:-1]) * 1000)(table[n].strip())
        total = ms(times[1]) + ms(times[0]) * float(table["--en-pulse-count"])  # delay + breaths
        if not 4000 <= total <= 6000:
            fail(f"components: the focus pulse ends after {total / 1000:g} s, not between 4 and 6 s")
    # 2b. focus motion works on keyboard focus and on data-focused alike: every
    # rule that names one of them names both, in the same :is()
    for at, sel, decls in rules:
        for part in re.split(r",(?![^()]*\))", sel):
            if ("data-focused" in part or ":focus-visible" in part) and not part.startswith(".en-tab"):
                if ':is(:focus-visible, [data-focused="true"])' not in part:
                    fail(f"components: {part.strip()} should apply on :focus-visible and data-focused alike")
    # 3. the reduced blocks are identical and cancel every animation, transform and movement
    device = [(sel[len(REDUCED_DEVICE):].strip(), d) for at, sel, d in rules
              if at and "prefers-reduced-motion" in at and sel.startswith(REDUCED_DEVICE)]
    attr = [(sel[len(REDUCED_ATTR):].strip(), d) for at, sel, d in rules if not at and sel.startswith(REDUCED_ATTR)]
    if not device or device != attr:
        fail("components: the two reduced-motion blocks are missing or not identical")
    reduced = {}
    for target, decls in attr:
        reduced.setdefault(target, {}).update(decls)
    base = lambda sel: re.sub(r":is\([^)]*\)|:not\([^)]*\)|\[[^\]]*\]|(?<!:):(?!:)[\w-]+(?:\([^)]*\))?", "", sel)
    covered = 0
    for at, sel, decls in rules:
        if at or sel.startswith(REDUCED_ATTR):
            continue
        for part in re.split(r",(?![^()]*\))", sel):
            target = base(part.strip())
            r = reduced.get(target, {})
            for prop, value in decls:
                if prop in ("animation", "animation-name") and value != "none":
                    covered += 1
                    if r.get("animation") != "none":
                        fail(f"reduced motion keeps the animation on {part.strip()}")
                if prop in ("transform", "scale", "translate", "rotate") and value != "none":
                    covered += 1
                    if r.get(prop) != "none":
                        fail(f"reduced motion keeps the {prop} on {part.strip()}")
                if prop == "transition" and value != "none":
                    moving = [x.split()[0] for x in value.split(",") if x.split()[0] not in COLOUR_FADES]
                    if moving:
                        covered += 1
                        kept = r.get("transition-property")
                        # fine if the transition is gone, keeps only colour fades, or what it
                        # moves is itself set to none in reduced motion
                        ok = r.get("transition") == "none" or (
                            kept and all(k.strip() in COLOUR_FADES for k in kept.split(","))) or all(
                            r.get(m) == "none" for m in moving)
                        if not ok:
                            fail(f"reduced motion keeps {moving} moving on {part.strip()}")
    if len(failures) > before:
        print("Motion: problems found (listed at the end)")
        return
    print(f"Motion: {count} timing declarations in components/ all use motion tokens; "
          f"the focus pulse ends after {total / 1000:g} s; both reduced-motion blocks match and cancel "
          f"all {covered} animations, transforms and movements")


# Which style guide pages a change touches, for --quick. A change is every
# file that differs from where this branch left main (committed or not, plus
# new files). Each rule maps files to the pages that show them; "frames"
# means the frame checks (components in frames, the smallest box, the
# Resize page) run too.
BUILDERS = {"tools/build_styleguide.py": ["index.html"], "tools/components_page.py": ["components.html"],
            "tools/motion_page.py": ["motion.html"], "tools/resize_page.py": ["resize.html"]}


def changed_files():
    def git(*a):
        return subprocess.run(["git", *a], cwd=en.ROOT, capture_output=True, text=True).stdout.split()
    base = (git("merge-base", "HEAD", "origin/main") or git("merge-base", "HEAD", "main") or ["HEAD"])[0]
    return sorted(set(git("diff", "--name-only", base)) | set(git("ls-files", "--others", "--exclude-standard")))


def touched_pages(files):
    """Return (pages, frames) for the changed files."""
    pages, frames = set(), False
    for f in files:
        if f.startswith("docs/") and os.path.basename(f) in PAGES:
            pages.add(os.path.basename(f))
            frames = frames or f == "docs/resize.html"
        elif f in BUILDERS:
            pages.update(BUILDERS[f])
            frames = frames or f == "tools/resize_page.py"
        elif f.startswith(("tokens/", "components/")) or f in ("docs/site.css", "docs/site.js"):
            # every component and both behaviours are on these two pages
            pages.update(["components.html", "motion.html"])
            frames = True
        elif f in ("tools/browser_check.py", "tools/check_guide.py", "tools/browser_session.py"):
            # the check itself changed: every page, and the frame checks
            pages.update(PAGES)
            frames = True
    return [p for p in PAGES if p in pages], frames


def check_browser(shots, quick=False):
    import browser_check

    class Quiet(Handler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=en.ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        if quick:
            pages, frames = touched_pages(changed_files())
            if not pages and not frames:
                print("\nIn Firefox: skipped, the change touches no style guide page (the full check runs before a release)")
                return
            errs, lines = browser_check.check(f"http://127.0.0.1:{server.server_port}/", pages, shots,
                                              quick=True, frames=frames)
        else:
            errs, lines = browser_check.check(f"http://127.0.0.1:{server.server_port}/", PAGES, shots)
    except Exception as ex:
        fail(f"browser check could not run: {ex}")
        return
    finally:
        server.shutdown()
    for f in errs:
        fail(f)
    if quick:
        print(f"\nIn Firefox (quick: the pages this change touches, full and reduced motion by attribute"
              f"{', with the frame checks' if frames else ''}):")
    else:
        print("\nIn Firefox, full and reduced motion (by attribute and by device setting):")
    for line in lines:
        print(line)


def main():
    args = sys.argv[1:]
    shots = args[args.index("--screenshots") + 1] if "--screenshots" in args else None
    check_fetch()
    check_generated()
    check_braces()
    check_menu()
    check_colours()
    check_sizes()
    check_states()
    check_resize()
    check_tokens()
    check_contrast()
    check_accents()
    check_motion_static()
    check_grid()
    check_patterns()
    check_no_screens()
    check_old_names()
    check_release()
    if "--no-browser" not in args:
        check_browser(shots, quick="--quick" in args)
    if notes:
        print("\nNotes:")
        for n in notes:
            print("  " + n)
    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
