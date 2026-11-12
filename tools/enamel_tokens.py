"""Read tokens/enamel.css into a list of groups and tokens.

Shared by build_design_md.py, build_styleguide.py and check_guide.py.
Standard library only. Also checks that the file parses: one :root block,
then only the accent selection rules; balanced braces; every declaration well
formed; no duplicate names; every var() reference defined; and that the
accent rules are complete and match the :root values (see check_accents).
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "tokens", "enamel.css")

# Source labels per group; Group C lines whose comment starts "steam baseline:"
# become "Steam baseline". Group D (motion) has no default: each line's comment
# starts with "steam baseline:" or "enamel:", which gives its label.
BASELINE = "Steam baseline"
GROUP_LABELS = {"A": BASELINE, "B": "Enamel", "C": "Enamel", "D": None}
LABEL_RE = re.compile(r"(steam baseline|enamel):", re.I)
GROUPS = list(GROUP_LABELS)

GROUP_RE = re.compile(r"/\*\s*Group ([A-Z]):\s*(.*?)\s*\*/")
DECL_RE = re.compile(r"^(--en-[a-z0-9-]+)\s*:\s*([^;]+?)\s*;\s*(?:/\*\s*(.*?)\s*\*/)?\s*$")
VAR_RE = re.compile(r"var\((--en-[a-z0-9-]+)\)")
ACCENT_SEL_RE = re.compile(r'\[data-en-accent(?:="([a-z][a-z0-9]*)")?\]')
NAMED_ACCENT_RE = re.compile(r"--en-accent-([a-z][a-z0-9]*)")
ACTIVE = ("--en-accent", "--en-accent-ink")


class TokenError(Exception):
    pass


def check_css(text):
    """Raise TokenError unless the stylesheet is structurally sound. Return
    [(selector, {name: value})] for every block, :root first."""
    bare = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    if bare.count("{") != bare.count("}"):
        raise TokenError("unbalanced braces")
    blocks = re.findall(r"([^{}]*)\{([^{}]*)\}", bare)
    if re.sub(r"[^{}]*\{[^{}]*\}", "", bare).strip():
        raise TokenError("text outside a { } block")
    if not blocks or blocks[0][0].strip() != ":root":
        raise TokenError("expected the :root block first")
    out = []
    for i, (sel, body) in enumerate(blocks):
        sel = sel.strip()
        if i and not ACCENT_SEL_RE.fullmatch(sel):
            raise TokenError(f"after :root only accent selection rules are allowed, found {sel!r}")
        decls = {}
        for decl in filter(None, (d.strip() for d in body.split(";"))):
            m = re.fullmatch(r"(--en-[a-z0-9-]+)\s*:\s*(\S.*)", decl, flags=re.S)
            if not m:
                raise TokenError(f"malformed declaration: {decl!r}")
            if m.group(1) in decls:
                raise TokenError(f"{sel}: {m.group(1)} declared twice")
            decls[m.group(1)] = m.group(2).strip()
        out.append((sel, decls))
    return out


def load(path=CSS):
    """Return [{"key", "title", "tokens": [{"name", "value", "label", "note"}]}]."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = check_css(text)
    root_text = text[:text.index("}")]  # the :root block, with its comments
    groups, seen = [], set()
    for line in root_text.splitlines():
        line = line.strip()
        m = GROUP_RE.fullmatch(line)
        if m:
            groups.append({"key": m.group(1), "title": m.group(2), "tokens": []})
            continue
        if not line.startswith("--"):
            continue
        m = DECL_RE.match(line)
        if not m:
            raise TokenError(f"put one declaration per line: {line!r}")
        if not groups:
            raise TokenError(f"token before any group comment: {m.group(1)}")
        name, value, note = m.groups()
        if name in seen:
            raise TokenError(f"duplicate token {name}")
        seen.add(name)
        g = groups[-1]
        label = GROUP_LABELS[g["key"]]
        m = LABEL_RE.match(note or "")
        if g["key"] == "C" and m and m.group(1).lower() == "steam baseline":
            label = BASELINE
        if label is None:
            if not m:
                raise TokenError(f"{name}: Group {g['key']} lines need a comment starting 'steam baseline:' or 'enamel:'")
            label = BASELINE if m.group(1).lower() == "steam baseline" else "Enamel"
        g["tokens"].append({"name": name, "value": value, "label": label, "note": note})
    if [g["key"] for g in groups] != GROUPS:
        raise TokenError(f"expected groups {', '.join(GROUPS)} in that order")
    for t in all_tokens(groups):
        for ref in VAR_RE.findall(t["value"]):
            if ref not in seen:
                raise TokenError(f"{t['name']} refers to undefined {ref}")
    check_accents(groups, blocks[1:])
    return groups


def accents(groups):
    """The named accents, in file order: [{"name", "token", "value", "ink",
    "ink_value", "default"}]. A named accent is a pair of tokens,
    --en-accent-<name> and --en-accent-<name>-ink. The default is the one
    --en-accent points at on :root."""
    table = {t["name"]: t["value"] for t in all_tokens(groups)}
    m = VAR_RE.fullmatch(table.get("--en-accent", ""))
    default = m.group(1) if m else None
    out = []
    for name in table:
        m = NAMED_ACCENT_RE.fullmatch(name)
        if not m or m.group(1) in ("ink", "glow"):
            continue
        ink = f"{name}-ink"
        if ink not in table:
            raise TokenError(f"named accent {name} has no {ink}")
        out.append({"name": m.group(1), "token": name, "value": table[name], "ink": ink,
                    "ink_value": table[ink], "default": name == default})
    return out


def accent_dependents(groups):
    """Tokens other than the active pair whose value depends on it."""
    table = {t["name"]: t["value"] for t in all_tokens(groups)}
    def depends(name, depth=0):
        refs = VAR_RE.findall(table[name])
        return depth < 10 and any(r in ACTIVE or depends(r, depth + 1) for r in refs)
    return [n for n in table if n not in ACTIVE and depends(n)]


def check_accents(groups, rules):
    """The active pair must point at a named accent on :root; each named
    accent needs one [data-en-accent="<name>"] rule pointing the active pair
    at it; one [data-en-accent] rule must redeclare every token calculated
    from the accent, with its :root value."""
    table = {t["name"]: t["value"] for t in all_tokens(groups)}
    named = accents(groups)
    defaults = [a for a in named if a["default"]]
    if len(defaults) != 1 or table["--en-accent-ink"] != f"var({defaults[0]['ink']})":
        raise TokenError("--en-accent and --en-accent-ink must point at one named accent pair")
    by_sel = {}
    for sel, decls in rules:
        if sel in by_sel:
            raise TokenError(f"{sel} appears twice")
        by_sel[sel] = decls
    for a in named:
        sel = f'[data-en-accent="{a["name"]}"]'
        want = {"--en-accent": f"var({a['token']})", "--en-accent-ink": f"var({a['ink']})"}
        if by_sel.pop(sel, None) != want:
            raise TokenError(f"{sel} must set exactly --en-accent and --en-accent-ink to the {a['name']} pair")
    want = {n: table[n] for n in accent_dependents(groups)}
    if by_sel.pop("[data-en-accent]", None) != want:
        raise TokenError(f"[data-en-accent] must redeclare exactly {sorted(want)} with their :root values")
    if by_sel:
        raise TokenError(f"accent rules for unknown accents: {sorted(by_sel)}")


def all_tokens(groups):
    return [t for g in groups for t in g["tokens"]]


def resolve(groups, value):
    """Follow var() references until a plain value is left."""
    table = {t["name"]: t["value"] for t in all_tokens(groups)}
    for _ in range(10):
        m = VAR_RE.fullmatch(value.strip())
        if not m:
            return value
        value = table[m.group(1)]
    raise TokenError(f"var() chain too deep at {value}")


def hex_rgb(value):
    h = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise TokenError(f"not a 6-digit hex colour: {value}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c / 255) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG 2.x contrast ratio between two hex colours."""
    la, lb = sorted((luminance(hex_rgb(a)), luminance(hex_rgb(b))), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def apca(text, background):
    """APCA lightness contrast (Lc, APCA-W3 0.0.98G) of text on a background,
    both hex colours, as a positive number. Used only for the one text pair
    allowed below 4.5:1 (DESIGN.md, Part 2)."""
    def y(rgb):
        r, g, b = (c / 255 for c in rgb)
        v = 0.2126729 * r ** 2.4 + 0.7151522 * g ** 2.4 + 0.0721750 * b ** 2.4
        return v if v > 0.022 else v + (0.022 - v) ** 1.414
    t, b = y(hex_rgb(text)), y(hex_rgb(background))
    if abs(b - t) < 0.0005:
        return 0.0
    s = (b ** 0.56 - t ** 0.57) * 1.14 if b > t else (b ** 0.65 - t ** 0.62) * 1.14
    return 0.0 if abs(s) < 0.1 else (abs(s) - 0.027) * 100


def read_rules(design_md):
    """Return the bullet list under '## Part 2: Rules' in DESIGN.md."""
    with open(design_md, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^## Part 2: Rules\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if not m:
        raise TokenError("DESIGN.md has no '## Part 2: Rules' section")
    return [l[2:].strip() for l in m.group(1).splitlines() if l.startswith("- ")]


# The accent check. Every named accent must pass all of these.
ACCENT_MIN_DISTANCE = 25  # CIE76 colour difference (Delta E) from each status colour
STATUS = ["--en-green", "--en-yellow", "--en-red"]


def lab(value):
    """CIE L*a*b* (D65) of a hex colour."""
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
               for c in (v / 255 for v in hex_rgb(value)))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def distance(a, b):
    """CIE76 colour difference (Delta E) between two hex colours."""
    return sum((p - q) ** 2 for p, q in zip(lab(a), lab(b))) ** 0.5


def accent_checks(groups, accent):
    """[(what, value, need, passed)] for one named accent; value is a contrast
    ratio, or a Delta E for the status colour rows."""
    colour = lambda n: resolve(groups, f"var({n})")
    a, ink = colour(accent["token"]), colour(accent["ink"])
    out = []
    for bg, need in [("--en-surface-page", 4.5), ("--en-surface-raised", 4.5), ("--en-surface-control", 3.0)]:
        r = contrast(a, colour(bg))
        out.append((f"on {bg}", r, need, r >= need))
    r = contrast(ink, a)
    out.append((f"{accent['ink']} on the accent", r, 4.5, r >= 4.5))
    for s in STATUS:
        d = distance(a, colour(s))
        out.append((f"distance from {s}", d, ACCENT_MIN_DISTANCE, d >= ACCENT_MIN_DISTANCE))
    return out
