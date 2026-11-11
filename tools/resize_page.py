"""The Resize page, docs/resize.html, written by build_styleguide.py.

Two sections. Resize by hand: every component in its own frame, which the
reader resizes by dragging its corner (the browser's own resizable box,
CSS resize), so each component responds to its frame as it would inside an
app. Fixed widths: a row of frames from the smallest supported box to very
wide, each labelled by its width only, in rem with the pixel width at the
browser's normal font size. The widths are the ones the browser check puts
the components in (FRAMES in browser_check.py), so the page shows what is
checked. The live picker and toast are run by components/enamel-components.js
and docs/site.js, as on the Motion page. Standard library only.
"""
import html
import components_page as cp
from browser_check import FRAMES

MENU_SECTIONS = [("by-hand", "Resize by hand"), ("fixed", "Fixed widths")]
NORMAL_PX = 16  # the browser's normal font size, for the pixel widths in the labels
WIDTHS = [w for w, _ in FRAMES]


def e(s):
    return html.escape(str(s), quote=True)


def label(width):
    """A fixed frame's label: its width only."""
    return f"{width:g}rem wide ({width * NORMAL_PX:g}px)"


HINTS_FIVE = ('<footer class="en-hintbar">\n'
              '  <span class="en-hint"><span class="en-glyph en-glyph--shoulder">L1</span>Movies</span>\n'
              '  <span class="en-hint"><span class="en-glyph en-glyph--shoulder">R1</span>TV shows</span>\n'
              '  <span class="en-hint"><span class="en-glyph">A</span>Resume</span>\n'
              '  <span class="en-hint"><span class="en-glyph">X</span>Remove</span>\n'
              '  <span class="en-hint"><span class="en-glyph">B</span>Back</span>\n'
              '</footer>')

# Two hints, as in the smallest supported box (DESIGN.md Part 2): they fit on
# one line in its 20rem.
HINTS = ('<div class="en-hintbar">\n  <span class="en-hint"><span class="en-glyph">A</span>Select</span>\n'
         '  <span class="en-hint"><span class="en-glyph">B</span>Back</span>\n</div>')

# Two hints that wrap onto two lines in the smallest supported box's 20rem:
# the picker and the toast then stop above the taller bar.
HINTS_TWO_LINES = ('<div class="en-hintbar">\n  <span class="en-hint"><span class="en-glyph">A</span>Select</span>\n'
                   '  <span class="en-hint"><span class="en-glyph">B</span>Cancel</span>\n</div>')

TABS = ('<div class="en-tabs" role="tablist" aria-label="Library">\n'
        f'  {cp.TAB_MOVIES.format(sel="true", extra="")}\n'
        f'  {cp.TAB_TV}\n'
        '  <button class="en-tab" role="tab" aria-selected="false">Home videos <span class="en-tab__count">12</span></button>\n'
        f'  {cp.badged_tab("Library", "Beta")}\n'
        '</div>')

FLOW = (cp.steplabel("Step 3 of 3", "No videos found yet") + "\n" + cp.steps(*cp.STEPS_THREE))

GROUPS = (cp.band("SD card", "2 folders", outline=True) + '\n<ul class="en-rows">\n'
          f'  <li>{cp.badged_row("SD card › Films", "Movies")}</li>\n'
          f'  <li>{cp.message_row("SD card › Films › Old", "4 videos", "This folder is inside your movies folder, so pick a different one.", focused=True)}</li>\n'
          '</ul>\n' + cp.band("Internal storage", "1 folder") + '\n<ul class="en-rows">\n'
          f'  <li>{cp.message_row("Videos", "8 videos")}</li>\n'
          '</ul>')

RESULT = (cp.stat_pair(cp.STATS_MOVIES, cp.STATS_SHOWS) + "\n" + cp.stat_pair(cp.stat_panel(None, "Movies"), cp.STATS_SHOWS)
          + "\n" + cp.NOTES_TWO)

ROWS = ('<ul class="en-rows">\n'
        '  <li><button class="en-row" data-focused="true">Copper Tide Rising <span class="en-row__meta">1995</span></button></li>\n'
        '  <li><div class="en-row">Keep screen awake while a video is paused'
        '<button class="en-toggle" aria-pressed="true" aria-label="Keep screen awake"></button></div></li>\n'
        '  <li><button class="en-row">Driftwood <span class="en-row__meta">Episode 5</span></button></li>\n'
        '</ul>')

SHELF = ('<div class="en-shelf">\n'
         + cp.indent(cp.tile("Lighthouse Keepers of the Long Winter", 34, large=True, focused=True)) + "\n"
         + cp.indent(cp.tile("Driftwood · Episode 5", 18)) + "\n"
         + cp.indent(cp.tile("Orchard Weather · Part 1", 11)) + "\n</div>")

BUTTONS = ('<div class="site-actions" data-set="buttons">\n'
           '  <button class="en-button en-button--primary">Scan my folders</button>\n'
           '  <button class="en-button" data-focused="true">Rescan library</button>\n'
           f'  <button class="en-button en-button--icon" aria-label="Search">{cp.SEARCH_ICON}</button>\n'
           '  <button class="en-button" disabled>Remove</button>\n'
           '</div>')

PROGRESS = ('<div>\n  <div class="en-progress__head"><span>40%</span><span>Scanning your folders</span></div>\n  '
            + cp.PROGRESS.format(label="Scan my folders", v=40) + "\n</div>")

MENU = ('<ul class="en-menu">\n'
        '  <li><a class="en-menu__item" href="#by-hand" aria-current="page">Movies</a></li>\n'
        '  <li><a class="en-menu__item" href="#by-hand" data-focused="true">TV shows</a></li>\n'
        '  <li><a class="en-menu__item" href="#by-hand">Scan my folders</a></li>\n'
        '</ul>')

ACTIONBAR = cp.actionbar("text") + '\n<ul class="en-rows">\n' + "\n".join(
    f'  <li><div class="en-row">{e(t)}</div></li>' for t in ("Orchard Weather", "Copper Tide Rising", "Driftwood")) + "\n</ul>"

PICKER = cp.dialog(cp.picker("choices", focus=1), opened=True) + "\n" + HINTS

TOAST = ('<div class="en-toast" id="resize-toast" role="status" aria-live="polite">'
         f'<span class="en-toast__icon" aria-hidden="true">{cp.INFO_ICON}</span>'
         '<span class="en-toast__text">Library updated: 3 new films</span></div>\n' + HINTS)

TOAST_BUTTONS = ('<div class="site-actions">'
                 '<button class="en-button" data-toast="show" data-toast-element="resize-toast">Show the toast</button>'
                 '<button class="en-button" data-toast="update">Update it</button>'
                 '<button class="en-button" data-toast="hide">Hide it</button></div>')

# (caption, markup, frame look, note, live demo below it). Frame looks
# (docs/site.css): "" = padded, "flush" = no padding, "screen" = a whole
# screen, whose fixed-position components (picker, toast) stay inside it.
BY_HAND = [
    ("Hint bar", HINTS_FIVE, "flush", "Hints that don't fit on one line wrap onto another and the bar gets taller.", ""),
    ("Tabs", TABS, "", "Tabs that don't fit wrap onto another line, each with its badge.", ""),
    ("List rows and toggle", ROWS, "", "Long titles wrap; a title never runs under its toggle.", ""),
    ("Tiles on a shelf", SHELF, "flush", "Tiles take their width from the shelf. When they don't all fit, the shelf "
                                         "scrolls sideways.", ""),
    ("Buttons", BUTTONS, "", "", ""),
    ("Progress", PROGRESS, "", "The two parts of the head line move onto two lines when they don't fit side by side.", ""),
    ("Side menu", MENU, "flush", "", ""),
    ("Step label and numbered steps", FLOW, "", "The title and its step label wrap; each step's text stays lined up "
                                                "after its number.", ""),
    ("Group bands, badges and a message", GROUPS, "", "A band's count moves onto its own line when it doesn't fit; "
                                                      "a message makes its row taller, never wider.", ""),
    ("Stat panels and notes", RESULT, "", "The two panels sit side by side, and stack when they can't both fit at "
                                          "their minimum width. A long note wraps.", ""),
    ("Page speckle", '<div class="en-speckle" style="min-height: 15rem"></div>', "flush",
     "The flecks stay the same size; a bigger area shows more of them, with no visible repeat.", ""),
    ("Action bar", ACTIONBAR, "flush", "When its buttons don't fit on one line they wrap and the bar gets taller.", ""),
    ("Picker dialog", PICKER, "screen", "The picker is as wide as its longest row, between a quarter and two thirds "
                                        "of the space its frame gives it.",
     '<p class="site-note">Try it: a live picker is modal, so it covers the whole window, as it covers the whole '
     'screen in an app.</p>' + cp.open_buttons("resize") + "\n" + cp.live_pickers("resize")),
    ("Toast", TOAST, "screen", "The toast is as wide as its text, up to its limit and never wider than its frame less "
                               "a gutter. It sits at the bottom right, just above the hint bar.",
     '<p class="site-note">Try it: the toast shows in its frame.</p>' + TOAST_BUTTONS),
]


def by_hand(caption, markup, look, note, live):
    cls = "site-resize" + "".join(f" site-resize--{x}" for x in look.split())
    out = [f'<figure class="site-state site-state--wide"><div class="{cls}">\n{markup}\n</div>',
           f'<figcaption>{e(caption)}</figcaption>']
    if note:
        out.append(f'<p class="site-note">{e(note)}</p>')
    if live:
        out.append(live)
    out.append("</figure>")
    return "\n".join(out)


def screen(width):
    """A whole screen at one width: the action bar, the components, the hint bar."""
    body = "\n".join([TABS, ROWS, SHELF, BUTTONS, PROGRESS, MENU])
    return (f'<div class="site-fixed" style="width: {width:g}rem">\n{cp.actionbar()}\n'
            f'<div class="site-fixed__body">\n{body}\n</div>\n{HINTS}\n</div>')


def over_bar(width, hints):
    """A picker over a screen, and a toast above the hint bar, at one width."""
    toast = cp.toast("Library updated: 3 new films") + "\n" + hints
    return (f'<div class="site-fixed site-fixed--screen" style="width: {width:g}rem">\n'
            f'{cp.dialog(cp.picker("actions", focus=0), opened=True)}\n{hints}\n</div>\n'
            f'<div class="site-fixed site-fixed--toast" style="width: {width:g}rem">\n{toast}\n</div>\n')


def fixed(width):
    # The narrowest frame also shows a hint bar that wraps onto two lines.
    two = over_bar(width, HINTS_TWO_LINES) if width == WIDTHS[0] else ""
    return (f'<figure class="site-state site-frame"><figcaption>{e(label(width))}</figcaption>\n{screen(width)}\n'
            f'{over_bar(width, HINTS)}{two}</figure>')


def page(menu_block):
    hand = "\n".join(by_hand(*x) for x in BY_HAND)
    frames = "\n".join(fixed(w) for w in WIDTHS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enamel resize</title>
<link rel="stylesheet" href="../tokens/enamel.css">
<link rel="stylesheet" href="../components/enamel-components.css">
<link rel="stylesheet" href="site.css">
<script src="../components/enamel-components.js" defer></script>
<style>
html {{ background: var(--en-surface-page); }}
body {{ margin: 0; background: var(--en-surface-page); color: var(--en-text);
  font-family: var(--en-font); font-size: var(--en-text-body); line-height: var(--en-line-height); }}
</style>
</head>
<body>
<!-- Generated by tools/build_styleguide.py from tools/resize_page.py. Do not edit by hand. -->
{menu_block}
<main class="site-main">
<h1>Resize</h1>
<p>Enamel components adapt to the space they are given, never to a screen size, a device or an aspect ratio. Here
each one sits in a frame: it responds to its frame, as it would to its space inside an app.</p>
<p class="site-note">Several examples look focused at once, so each frame shows focus. In an app, only one element
shows focus at a time.</p>

<section id="by-hand">
<h2>Resize by hand</h2>
<p>Drag the bottom right corner of a frame to make it narrower, wider, shorter or taller, and watch the component
adapt.</p>
<div class="site-states">
{hand}
</div>
</section>

<section id="fixed">
<h2>Fixed widths</h2>
<p>The same components in frames from very narrow to very wide. Scroll along the row. Each frame shows a screen with
the action bar, the components and the hint bar; a picker over a screen; and a toast above the hint bar. The narrowest
frame is the smallest supported box's width, {WIDTHS[0]:g}rem; it also shows the picker and the toast over a hint bar
whose hints, Select and Cancel, wrap onto two lines, and both still stop just above it. Widths are in rem, so a larger browser font makes the
frames and everything in them larger; the pixel widths are at the browser's normal font size.</p>
<div class="site-frames">
{frames}
</div>
</section>
</main>
<footer class="site-footer">Enamel is not affiliated with Valve. Steam and Steam Deck are trademarks of Valve Corporation.</footer>
</body>
</html>
"""
