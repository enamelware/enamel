# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""The release check (#19): nothing taken from Steam's files and nothing
personal goes public. Standard library only.

It reads every file that would be published (tracked or new, not ignored)
and fails on:
  - a reference folder;
  - a screenshot or other image, as a file or written into a page as a
    picture, unless it is one of the style guide's own assets (ASSETS). The
    speckle is drawn in the tokens as a small SVG, which is allowed;
  - a name starting with Steam's variable prefix or its system or colour
    names;
  - the words for taking values out of Steam's files;
  - a Steam client version;
  - code that opens a debug connection to the Steam client (its debug port,
    its page list, or its debugger's commands). The browser check's own
    headless Firefox is not the Steam client and is allowed;
  - a tracked local settings file or CLAUDE.local.md;
  - a home folder or removable drive path, an email address other than the
    GitHub noreply address, a Steam ID or Steam user folder, a device's own
    login name, and anything that looks like a token, key or password.

Some patterns would match their own text, so they are built from parts.
Used by check_guide.py and tests/test_release_rules.py.

The public-text check (#23) reads the same published files for what the
"Public writing" section of CLAUDE.md rules out: a home folder path written
with a tilde, the project's owner named by role, the old account name, a
commit email address (the GitHub noreply address), a claude.ai link, and a
link to a private repo or to the private planning board. Every published
file counts, CLAUDE.md and .claude/ included; the few lines that need such
a text to work are listed in PUBLIC_TEXT_ALLOWED with the reason. Findings
in the text written before the rule are listed in PUBLIC_TEXT_KNOWN, which
the rewrite (#24) empties: more of a kind in a file than listed there is a
failure. Used by check_guide.py and tests/test_public_text.py.
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The style guide's own image files, as repo paths. There are none: the
# speckle is an SVG written into tokens/enamel.css by tools/build_speckle.py.
ASSETS = set()
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".avif", ".heic", ".tif", ".tiff", ".ico", ".svg")
LOCAL_FILES = (".claude/settings.local.json", "CLAUDE.local.md")
NOREPLY = re.compile(r"\d+\+enamelware@users\.noreply\.github\.com$")

GP = "g" + "p"
EXTRACT = "extract" + "ed"
VALVE_VARS = "Valve" + "['’]s variables"
DEBUG_PORT = "80" + "80"

PATTERNS = [
    ("Steam's variable names", re.compile(rf"(?<![\w-])--{GP}[A-Za-z0-9_-]|\b{GP}(?:System|Color)")),
    ("words for taking values out of Steam's files", re.compile(rf"\b{EXTRACT}\b|{VALVE_VARS}", re.I)),
    ("a Steam client version", re.compile(r"\bsteam\s+client\s+(?:version\s+|build\s+)?\d{4,}|\bclient\s+version\s*[:=]?\s*\d"
                                          r"|\bbuild\s?id\s*[:=]\s*\d{6,}", re.I)),
    ("a debug connection to the Steam client", re.compile(
        rf"(?:127\.0\.0\.1|localhost):{DEBUG_PORT}\b|remote-debugging-" + "address"
        + r"|cef-enable-" + "debugging|steam" + r"webhelper|/json/(?:list|version)\b"
        + r"|[\"'](?:Runtime|Page|CSS|DOM|Target|Network)\.[a-z]\w+[\"']")),
    ("a home folder path", re.compile(r"(?:/home|/var/home|/Users)/[a-z_][\w.-]*|[A-Z]:\\\\?Users\\\\?\w"
                                      r"|/run/media/(?!\*)[\w.-]+")),
    ("a Steam ID or Steam user folder", re.compile(r"\b7656119\d{10}\b|\bSTEAM_[0-5]:[01]:\d+|\[U:1:\d+\]"
                                                   r"|userdata/\d+|\.local/share/" + r"Steam\b|\.steam/" + r"steam\b")),
    ("a device's own login name", re.compile(r"\b\w+@steam" + r"deck\b", re.I)),
    ("something that looks like a secret", re.compile(
        r"\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_\w{20,}|\bAKIA[0-9A-Z]{16}\b|-----BEGIN [A-Z ]*PRIVATE " + "KEY"
        + r"|\bxox[abprs]-[\w-]{10,}|\bsk-[A-Za-z0-9_-]{20,}"
        + r"|\b(?:pass" + r"word|passwd|secret|api[_-]?key|token)\s*[:=]\s*[\"'](?!--|var\()[^\"'\s]{8,}[\"']", re.I)),
    ("an image written into a page", re.compile(r"data:image/(?:png|jpe?g|gif|webp|bmp|avif)", re.I)),
]
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SSH_HOST = re.compile(r"^git@github\.com$")


# The public-text check. The GitHub account and its one public repo; any
# other repo of the account is private.
ACCOUNT = "enamelware"
PUBLIC_REPOS = {"enamel"}
OLD_ACCOUNT = "steamos" + "tools"
HOME_PATH = "a home folder path"
OWNER_WORDING = "the " + "own" + "er"     # in parts, so this file doesn't use the words
BOARD_LINK = "a link to the private planning board"
PRIVATE_REPO = "a link to a private repo"
PUBLIC_TEXT = [
    (HOME_PATH, re.compile(r"(?<![\w/~])~/[\w.-]")),       # /home/... is a release problem already
    (OWNER_WORDING, re.compile(r"\bthe\s+" + "own" + r"er\b", re.I)),
    ("the old account name", re.compile(OLD_ACCOUNT, re.I)),
    ("a commit email address", re.compile(r"\d+\+[\w-]+@users\.noreply\.github\.com", re.I)),
    ("a claude.ai link", re.compile(r"\bclaude\.ai/", re.I)),
    (BOARD_LINK, re.compile(r"github\.com/(?:users|orgs)/[\w-]+/projects\b", re.I)),
]
# owner/name, alone or in a GitHub address; the board's users/<account>/projects is not a repo.
REPO_SLUG = re.compile(rf"(?<![\w.+-])(?<!users/)(?<!orgs/){ACCOUNT}/([\w-]+(?:\.[\w-]+)*)", re.I)

# (file, kind): why that file needs it. Few, and each one explained.
PUBLIC_TEXT_ALLOWED = {
    (".claude/settings.json", HOME_PATH):
        "the deny rules keep Claude Code out of the secret folders (SSH keys, GitHub login, git credentials) in the "
        "home folder of whoever runs it; they are written from the home folder's short form, with no name in them",
    (".claude/board.json", BOARD_LINK):
        "the workflow's board settings: the board's own address, which the board script and its tests read",
}

# (file, kind): how many findings the text written before the rule still
# has. A file may have at most this many of a kind; one more is a failure.
# The rewrite in the project voice (#24) brings these to zero and empties it.
PUBLIC_TEXT_KNOWN = {
    (".claude/agents/refactor-scout.md", OWNER_WORDING): 1,
    (".claude/agents/reviewer.md", OWNER_WORDING): 5,
    (".claude/agents/test-checker.md", OWNER_WORDING): 3,
    (".claude/agents/test-writer.md", OWNER_WORDING): 2,
    (".claude/commands/draft.md", OWNER_WORDING): 2,
    (".claude/commands/next.md", OWNER_WORDING): 19,
    (".claude/commands/tidy.md", OWNER_WORDING): 4,
    ("CHANGELOG.md", PRIVATE_REPO): 4,
    ("CLAUDE.md", HOME_PATH): 4,
    ("CLAUDE.md", PRIVATE_REPO): 1,
    ("CLAUDE.md", OWNER_WORDING): 4,
    ("DECISIONS.md", HOME_PATH): 2,
    ("DECISIONS.md", PRIVATE_REPO): 1,
    ("DECISIONS.md", OWNER_WORDING): 14,
    ("README.md", HOME_PATH): 1,
    ("README.md", PRIVATE_REPO): 1,
}


def private_repos(line):
    """The account's repo names on one line that are not its public repo."""
    out = []
    for m in REPO_SLUG.finditer(line):
        name = m.group(1).rstrip(".")
        if name.lower().endswith(".git"):
            name = name[:-4]
        if name.lower() not in PUBLIC_REPOS:
            out.append(m.group(0))
    return out


def public_text_findings(rel, text):
    """[(line number, kind, what was found)] for one file's text, exceptions left out."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for what, pattern in PUBLIC_TEXT:
            m = pattern.search(line)
            if m:
                found.append((n, what, m.group(0)))
        repos = private_repos(line)
        if repos:
            found.append((n, PRIVATE_REPO, repos[0]))
    return [f for f in found if (rel, f[1]) not in PUBLIC_TEXT_ALLOWED]


def public_text(root=ROOT, known=None):
    """(new, known_counts, files): findings beyond the known list as 'path line N: kind (found)', the count of
    each (file, kind) found within the known list, and how many files were read."""
    known = PUBLIC_TEXT_KNOWN if known is None else known
    files = published_files(root)
    groups = {}
    for rel in files:
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            continue
        for n, what, match in public_text_findings(rel, text):
            groups.setdefault((rel, what), []).append(f"{rel} line {n}: {what} ({match[:60]!r})")
    new, within = [], {}
    for key, lines in sorted(groups.items()):
        if len(lines) > known.get(key, 0):
            new += lines
        else:
            within[key] = len(lines)
    return new, within, len(files)


def published_files(root=ROOT):
    """Every file that would be published: tracked, or new and not ignored."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root,
                         capture_output=True, text=True, check=True).stdout
    return sorted(f for f in out.splitlines() if os.path.isfile(os.path.join(root, f)))


def tracked(root=ROOT):
    out = subprocess.run(["git", "ls-files", "--cached"], cwd=root, capture_output=True, text=True, check=True).stdout
    return set(out.splitlines())


def text_problems(rel, text):
    """['path line N: what (found)'] for one file's text."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for what, pattern in PATTERNS:
            m = pattern.search(line)
            if m:
                found.append(f"{rel} line {n}: {what} ({m.group(0)[:60]!r})")
        for m in EMAIL.finditer(line):
            if not (NOREPLY.match(m.group(0)) or SSH_HOST.match(m.group(0))):
                found.append(f"{rel} line {n}: an email address other than the GitHub noreply address ({m.group(0)!r})")
    return found


def problems(root=ROOT):
    """Every release problem in the repo at `root`."""
    found = []
    if os.path.isdir(os.path.join(root, "reference")):
        found.append("reference/: the reference folder must not be published")
    files = published_files(root)
    for rel in tracked(root) & set(LOCAL_FILES):
        found.append(f"{rel}: a local Claude Code file is tracked by git")
    for rel in files:
        if rel.lower().endswith(IMAGE_EXT) and rel not in ASSETS:
            found.append(f"{rel}: an image that is not one of the style guide's own assets")
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            found.append(f"{rel}: a binary file the release check cannot read")
            continue
        found += text_problems(rel, text)
    return found, len(files)
