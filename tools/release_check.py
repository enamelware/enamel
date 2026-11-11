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
