"""The Components page, docs/components.html, written by build_styleguide.py.

Each example's HTML is written once, in SECTIONS below. The page shows it
live, and the "HTML to copy" under each section is the same text, escaped,
taken from the examples marked copy=True. So the two cannot differ.
Standard library only.
"""
import html, textwrap

# Stage looks (docs/site.css): "" = page colour, "raised" = row colour,
# "flush" = no padding, "center" / "start" = how the example is aligned.


def ex(caption, markup, stage="", wide=False, copy=False):
    return {"caption": caption, "html": textwrap.dedent(markup).strip(),
            "stage": stage, "wide": wide, "copy": copy}


def tile(title, value, large=False, focused=False):
    cls = "en-tile en-tile--large" if large else "en-tile"
    f = ' data-focused="true"' if focused else ""
    return (f'<a class="{cls}" href="#tile"{f}>\n'
            '  <div class="en-tile__frame">Paused frame</div>\n'
            f'  <div class="en-progress en-progress--thin" style="--value: {value}%"><span class="en-progress__fill"></span></div>\n'
            f'  <div class="en-tile__title">{title}</div>\n'
            '</a>')


def indent(s):
    return textwrap.indent(s, "  ")


TAB_MOVIES = '<button class="en-tab" role="tab" aria-selected="{sel}"{extra}>Movies <span class="en-tab__count">3</span></button>'
TAB_TV = ('<button class="en-tab" role="tab" aria-selected="false">TV shows <span class="en-tab__count">1</span>'
          '<span class="en-dot" role="img" aria-label="New"></span></button>')
TOGGLE = '''
<div class="en-row">
  Keep screen awake
  <button class="en-toggle" aria-pressed="{on}" aria-label="Keep screen awake"{f}></button>
</div>'''
PROGRESS = ('<div class="en-progress" role="progressbar" aria-label="{label}" aria-valuenow="{v}" '
            'style="--value: {v}%"><span class="en-progress__fill"></span></div>')

# Icons are drawn here, as inline SVG that takes its colour from the text.
SEARCH_ICON = ('<svg class="en-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">'
               '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 20 20"/></svg>')
INFO_ICON = ('<svg class="en-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.5v.5"/></svg>')
# Storage on the device itself: a drive with its light. Storage you can take
# out: a card with a cut corner and its contacts. The error mark: a disc,
# filled, with an exclamation mark drawn over it.
STORAGE_ICON = ('<svg class="en-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">'
                '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 13h18"/><path d="M16.5 15.5h1"/></svg>')
CARD_ICON = ('<svg class="en-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">'
             '<path d="M9 3h8a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7z"/><path d="M10 7v3M13 7v3M16 7v3"/></svg>')
ERROR_ICON = ('<svg class="en-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">'
              '<circle cx="12" cy="12" r="10" fill="currentColor" stroke="none"/><path d="M12 7v6"/><path d="M12 16.5v.5"/></svg>')


def steplabel(step, title):
    return f'<h1><span class="en-steplabel">{html.escape(step)}</span> {html.escape(title)}</h1>'


def band(name, count, outline=False):
    cls, icon = ("en-band en-band--outline", CARD_ICON) if outline else ("en-band", STORAGE_ICON)
    return (f'<h2 class="{cls}"><span class="en-band__name">{icon}{html.escape(name)}</span>'
            f'<span class="en-band__count">{html.escape(count)}</span></h2>')


def badged_row(title, badge, focused=False):
    f = ' data-focused="true"' if focused else ""
    return f'<button class="en-row"{f}>{html.escape(title)} <span class="en-badge">{html.escape(badge)}</span></button>'


def badged_tab(label, badge, selected=False, extra=""):
    return (f'<button class="en-tab" role="tab" aria-selected="{"true" if selected else "false"}"{extra}>'
            f'{html.escape(label)} <span class="en-badge">{html.escape(badge)}</span></button>')


def message_row(title, meta, message=None, focused=False):
    f = ' data-focused="true"' if focused else ""
    inner = f"{ERROR_ICON}{html.escape(message)}" if message else ""
    return (f'<button class="en-row"{f}>{html.escape(title)} <span class="en-row__meta">{html.escape(meta)}</span>'
            f'<span class="en-row__message" role="status" aria-live="polite">{inner}</span></button>')


def steps(*items):
    return '<ol class="en-steps">\n' + "\n".join(f"  <li>{html.escape(s)}</li>" for s in items) + "\n</ol>"


def stat_panel(counts, path):
    """counts is a list of (number, word), or None for "Not set". The whole panel
    is one item for screen readers, named by aria-label. A "Not set" panel's second
    line says which kind it is, so two of them can be told apart."""
    if counts is None:
        label, top = f"{path}, not set", '<span class="en-statpanel__notset">Not set</span>'
    else:
        label = ", ".join([f"{n} {w}" for n, w in counts] + [path])
        top = ('<span class="en-statpanel__counts">' + "".join(
            f'<span class="en-statpanel__count"><span class="en-statpanel__number">{n}</span> {html.escape(w)}</span>'
            for n, w in counts) + "</span>")
    return (f'<div class="en-statpanel" role="img" aria-label="{html.escape(label, quote=True)}">\n'
            f'  {top}\n  <span class="en-statpanel__path">{html.escape(path)}</span>\n</div>')


def stat_pair(*panels):
    return '<div class="en-statpair">\n' + "\n".join(indent(p) for p in panels) + "\n</div>"


def note(text, icon=False):
    return f'<p class="en-note">{INFO_ICON if icon else ""}{html.escape(text)}</p>'


STATS_MOVIES = stat_panel([(124, "movies")], "SD card › Films")
STATS_SHOWS = stat_panel([(18, "TV shows"), (240, "episodes")], "Internal storage › Videos")
# In their own box: a parent with a gap of its own would add it to the notes' gap.
NOTES_TWO = ("<div>\n  " + note("4 files could not be read as a movie or an episode.")
             + "\n  " + note("12 files in Films look like episodes.") + "\n</div>")

STEPS_THREE = ("Make one folder for movies and one for TV shows, on this device or on a card.",
               "Copy your videos in. Give each TV show its own folder.",
               "If they are on a card, put it in. Then choose Look again.")


def actionbar(focus=None):
    f = lambda which: ' data-focused="true"' if focus == which else ""
    return ('<header class="en-actionbar">\n'
            f'  <button class="en-button"{f("text")}>Menu</button>\n'
            f'  <button class="en-button en-button--icon" aria-label="Search"{f("icon")}>{SEARCH_ICON}</button>\n'
            '</header>')


def picker_row(label, desc=None, focused=False, current=False, cancel=False, first=False, value=None):
    cls = "en-picker__row en-picker__cancel" if cancel else "en-picker__row"
    attrs = (f' value="{value}"' if value else "") + (' aria-current="true"' if current else "") \
        + (" autofocus" if first else "") + (' data-focused="true"' if focused else "")
    inner = f'<span>{html.escape(label)}</span>'
    if desc:
        inner += f'<span class="en-picker__desc">{html.escape(desc)}</span>'
    return f'<button class="{cls}"{attrs}>{inner}</button>'


# The three uses of the picker. focus is the index of the focused row in a
# static example (None for none); live=True marks the row to focus first.
PICKERS = {
    "actions": (None, [("Play from the start", "Starts again from 0:00", "restart"),
                       ("Mark as watched", None, "watched"),
                       ("Remove from Continue watching", "The film stays in your library", "forget")]),
    "choices": (None, [("Title", None, "title"), ("Date added", "Newest first", "added"), ("Year", None, "year")]),
    "confirm": ("Remove 2 missing items?", [("Yes, remove", "Only Kettle's list changes. Your files are never touched.", "remove")]),
}


def picker(kind, focus=None, live=False):
    title, rows = PICKERS[kind]
    lines = ['<div class="en-picker">']
    if title:
        lines.append(f'  <h2 class="en-picker__title">{html.escape(title)}</h2>')
    lines.append('  <div class="en-picker__rows">')
    for i, (label, desc, value) in enumerate(rows):
        lines.append('    ' + picker_row(label, desc, focused=(focus == i), current=(kind == "choices" and i == 0),
                                         value=value))
    lines.append('  </div>')
    lines.append('  ' + picker_row("Cancel", cancel=True, focused=(focus == len(rows)),
                                   first=(live and kind == "confirm")))
    lines.append('</div>')
    return "\n".join(lines)


def dialog(inner, did=None, opened=False):
    ident = f' id="{did}"' if did else ""
    label = ' aria-label="Choose"' if "en-picker__title" not in inner else ""
    return (f'<dialog class="en-dialog"{ident}{label}{" open" if opened else ""}>\n'
            + textwrap.indent(inner, "  ") + "\n</dialog>")


def toast(text, icon=True, progress=None):
    i = f'<span class="en-toast__icon" aria-hidden="true">{INFO_ICON}</span>' if icon else ""
    bar = "" if progress is None else PROGRESS.format(label=html.escape(text), v=progress)
    return f'<div class="en-toast" role="status" aria-live="polite">{i}<span class="en-toast__text">{html.escape(text)}</span>{bar}</div>'


HINTS = ('<div class="en-hintbar">\n  <span class="en-hint"><span class="en-glyph">A</span>Select</span>\n'
         '  <span class="en-hint"><span class="en-glyph">B</span>Cancel</span>\n</div>')


def live_pickers(prefix):
    """Closed picker dialogs for the demos, opened by enamel-components.js."""
    return "\n".join(dialog(picker(kind, live=True), f"{prefix}-{kind}") for kind in PICKERS)


def open_buttons(prefix):
    return ('<div class="site-actions">'
            f'<button class="en-button" data-open-picker="{prefix}-actions">Open the action list</button>'
            f'<button class="en-button" data-open-picker="{prefix}-choices">Open the choice list</button>'
            f'<button class="en-button" data-open-picker="{prefix}-confirm">Open the confirm</button></div>')


TOAST_BUTTONS = (f'<template id="site-info-icon">{INFO_ICON}</template>'
                 '<div class="site-actions">'
                 '<button class="en-button" data-toast="show">Show a toast</button>'
                 '<button class="en-button" data-toast="update">Update it</button>'
                 '<button class="en-button" data-toast="hide">Hide it</button></div>')


# What moves in each component, one line each, shown under its purpose.
MOTION = {
    'hintbar': 'Motion: none. The hint bar never moves.',
    'tabs': "Motion: the selected pill's background and text colour fade over --en-motion-medium; a new dot fades in over --en-motion-medium.",
    'row': 'Motion: on focus the background and text colours fade over --en-motion-fast, and back again when focus leaves.',
    'tile': 'Motion: on focus the tile grows to --en-focus-scale over --en-motion-slow, without moving its neighbours, and the ring appears thick and narrows over --en-motion-ring; the ring then breathes --en-pulse-count times and rests. Losing focus reverses over --en-motion-fast.',
    'button': "Motion: when focus arrives the face rises --en-lift over --en-motion-medium with --en-ease-standard as its underside appears, and settles back over --en-motion-fast when focus leaves. Pressed, it drops onto its underside over --en-motion-fast and darkens; release springs it back over --en-motion-medium. In reduced motion focus switches at once and a press only darkens.",
    'toggle': 'Motion: the thumb slides and the track colour fades over --en-motion-medium when it is switched. As in Gaming Mode, focus appears at once, without breathing.',
    'progress': 'Motion: the fill glides to each new value over --en-motion-slow.',
    'actionbar': 'Motion: none of its own. Its buttons behave like every other button.',
    'picker': "Motion: when it opens, the darkened, blurred page appears at once and the panel fades in over --en-motion-dialog; it leaves the same way. The focused row rises and presses as a button does.",
    'toast': 'Motion: it slides in from the right edge over --en-motion-slow with --en-ease-enter, and fades out where it is over the same time with the same curve. In reduced motion it simply appears and disappears.',
    'menu': "Motion: on focus the focus bar grows from the centre and the colours fade over --en-motion-medium; the current item's glow fades in and out over --en-motion-medium.",
    'steplabel': 'Motion: none.',
    'band': 'Motion: none. A band never takes focus.',
    'badge': 'Motion: none of its own. On a row it changes colour with the row, over --en-motion-fast.',
    'message': 'Motion: it fades in over --en-motion-fast when it appears. In reduced motion it simply appears.',
    'steps': 'Motion: none.',
    'stat': 'Motion: none. A stat panel never takes focus.',
    'note': 'Motion: none. A note never takes focus.',
    'speckle': 'Motion: none. Nothing animates.',
    'lighter': 'Motion: faces no longer rise or drop. Everything else moves as usual.',
}

# (id, menu title, purpose, note, examples)
SECTIONS = [
    ("hintbar", "Hint bar",
     "The black bar along the bottom of the screen that shows which controller button does what.", "", [
        ex("Default", '''
            <div class="en-hintbar">
              <span class="en-hint"><span class="en-glyph">A</span>Resume</span>
              <span class="en-hint"><span class="en-glyph">X</span>Remove</span>
              <span class="en-hint"><span class="en-glyph">B</span>Quit</span>
            </div>''', "flush", wide=True, copy=True),
        ex("Shoulder glyphs", '''
            <div class="en-hintbar">
              <span class="en-hint"><span class="en-glyph en-glyph--shoulder">L1</span>Movies</span>
              <span class="en-hint"><span class="en-glyph en-glyph--shoulder">R1</span>TV shows</span>
            </div>''', "flush", wide=True, copy=True),
     ]),
    ("tabs", "Tabs",
     "Pill tabs that switch between the main lists of a screen, such as Movies and TV shows.",
     "On a controller, tabs are switched with L1 and R1 and never show focus. "
     "For keyboard use only, a tab shows the accent ring.", [
        ex("Selected", f'<div class="en-tabs" role="tablist">{TAB_MOVIES.format(sel="true", extra="")}</div>', "center"),
        ex("Not selected", f'<div class="en-tabs" role="tablist">{TAB_MOVIES.format(sel="false", extra="")}</div>', "center"),
        ex("Not selected, something new", f'<div class="en-tabs" role="tablist">{TAB_TV}</div>', "center"),
        # data-demo draws the :focus-visible ring on a static example (docs/site.css).
        ex("Keyboard focus", f'<div class="en-tabs" role="tablist">'
           f'{TAB_MOVIES.format(sel="true", extra=" data-demo=\"focus-visible\"")}</div>', "center"),
        ex("Row of tabs", f'''
            <div class="en-tabs" role="tablist">
              {TAB_MOVIES.format(sel="true", extra="")}
              {TAB_TV}
            </div>''', "center", wide=True, copy=True),
     ]),
    ("row", "List row",
     "One item in a vertical list, such as a film or a setting, with optional details after the title.", "", [
        ex("Default", '<div class="en-rows"><button class="en-row">Copper Tide Rising <span class="en-row__meta">1995</span></button></div>'),
        ex("Focused", '<div class="en-rows"><button class="en-row" data-focused="true">Copper Tide Rising <span class="en-row__meta">1995</span></button></div>'),
        ex("Stacked rows", '''
            <ul class="en-rows">
              <li><button class="en-row">Orchard Weather <span class="en-row__meta">2 parts</span></button></li>
              <li><button class="en-row" data-focused="true">Copper Tide Rising <span class="en-row__meta">1995</span></button></li>
              <li><button class="en-row">Driftwood <span class="en-row__meta">Episode 5</span></button></li>
            </ul>''', wide=True, copy=True),
     ]),
    ("tile", "Tile",
     "A video on a shelf: a paused frame, how far you have watched, and its title.", "", [
        ex("Default", tile("Copper Tide Rising", 3), "center", wide=True),
        ex("Focused", tile("Copper Tide Rising", 3, focused=True), "center", wide=True),
        ex("Shelf, large tile focused", '<div class="en-shelf">\n'
           + indent(tile("Lighthouse Keepers of the Long Winter", 34, large=True, focused=True)) + "\n"
           + indent(tile("Driftwood · Episode 5", 18)) + "\n"
           + indent(tile("Orchard Weather · Part 1", 11)) + "\n</div>", wide=True, copy=True),
     ]),
    ("button", "Button",
     "Something you press to do an action. The primary button is the main action on a screen.",
     "Buttons sit on a row. The primary button is the accent colour until it is focused; focused, every button is "
     "cream on its accent underside. On a controller, set data-pressed=\"true\" while A is held, since a stylesheet "
     "can't see a controller's press; without it, only that movement is missing.", [
        ex("Default", '<button class="en-button">Rescan library</button>', "raised start", copy=True),
        ex("Focused", '<button class="en-button" data-focused="true">Rescan library</button>', "raised start"),
        ex("Primary", '<button class="en-button en-button--primary">Scan my folders</button>', "raised start", copy=True),
        ex("Primary, focused", '<button class="en-button en-button--primary" data-focused="true">Scan my folders</button>', "raised start"),
        ex("Icon", '<button class="en-button en-button--icon" aria-label="More">&#8943;</button>', "raised start", copy=True),
        ex("Icon, focused", '<button class="en-button en-button--icon" aria-label="More" data-focused="true">&#8943;</button>', "raised start"),
        ex("Pressed", '<button class="en-button" data-focused="true" data-pressed="true">Rescan library</button>', "raised start"),
        ex("Disabled", '<button class="en-button" disabled>Remove</button>', "raised start", copy=True),
     ]),
    ("toggle", "Toggle",
     "An on or off switch for a setting. It is a button that says whether it is pressed.", "", [
        ex("Off", TOGGLE.format(on="false", f=""), "raised flush"),
        ex("Off, focused", TOGGLE.format(on="false", f=' data-focused="true"'), "raised flush"),
        ex("On", TOGGLE.format(on="true", f=""), "raised flush", copy=True),
        ex("On, focused", TOGGLE.format(on="true", f=' data-focused="true"'), "raised flush"),
     ]),
    ("progress", "Progress",
     "How far something has got, such as a library scan. Set --value to a percentage.", "", [
        ex("Default", PROGRESS.format(label="Scan my folders", v=40)),
        ex("With head line", '<div>\n  <div class="en-progress__head"><span>40%</span><span>Scanning</span></div>\n  '
           + PROGRESS.format(label="Scan my folders", v=40) + "\n</div>", copy=True),
        ex("Thin, under tiles", PROGRESS.format(label="Watched", v=34).replace('en-progress"', 'en-progress en-progress--thin"')),
     ]),
    ("menu", "Side menu",
     "The list of places down the left of a screen. The place you are in is marked as current.",
     "This style guide's own left menu is built from this component.", [
        ex("Default", '<div class="en-menu"><a class="en-menu__item" href="#menu">TV shows</a></div>', "raised flush"),
        ex("Current", '<div class="en-menu"><a class="en-menu__item" href="#menu" aria-current="page">Movies</a></div>', "raised flush"),
        ex("Focused", '<div class="en-menu"><a class="en-menu__item" href="#menu" data-focused="true">TV shows</a></div>', "raised flush"),
        ex("Whole menu", '''
            <ul class="en-menu">
              <li><a class="en-menu__item" href="#menu" aria-current="page">Movies</a></li>
              <li><a class="en-menu__item" href="#menu" data-focused="true">TV shows</a></li>
              <li><a class="en-menu__item" href="#menu">Scan my folders</a></li>
            </ul>''', "raised flush", copy=True),
     ]),
    ("actionbar", "Action bar",
     "A bar across the top of a screen with its buttons on the right. It stays docked and opaque while the content "
     "scrolls underneath. When its buttons don't fit on one line, they wrap onto another and the bar gets taller.",
     "It uses the system's buttons. An icon button always has an accessible name (aria-label). Icons are drawn "
     "as inline SVG with stroke=\"currentColor\", so they turn dark on the cream focus fill.", [
        ex("Default", actionbar(), "flush", wide=True, copy=True),
        ex("Text button focused", actionbar("text"), "flush", wide=True),
        ex("Icon button focused", actionbar("icon"), "flush", wide=True),
     ]),
    ("picker", "Picker dialog",
     "A list of choices over a darkened, blurred screen: actions to take, a setting to choose, or a question to "
     "confirm. It is as wide as its longest row, between a quarter and two thirds of the space it is given; longer "
     "text wraps.",
     "Inside a picker the focused row behaves like a button: cream with dark text, on its accent underside; rows on "
     "a page lift to the control grey instead. enamel-components.js opens it, keeps focus inside, moves with Up and Down (stopping at "
     "the ends), selects with Enter or a tap, and cancels with Escape or the Cancel row.", [
        ex("Row", '<div class="en-picker__rows">' + picker_row("Date added", "Newest first") + '</div>', "start"),
        ex("Row, focused", '<div class="en-picker__rows">' + picker_row("Date added", "Newest first", focused=True)
           + '</div>', "start"),
        ex("Row, pressed", '<div class="en-picker__rows">'
           + picker_row("Date added", "Newest first", focused=True).replace("<button ", '<button data-pressed="true" ')
           + '</div>', "start"),
        ex("Row, current choice", '<div class="en-picker__rows">' + picker_row("Date added", "Newest first", current=True)
           + '</div>', "start"),
        ex("Action list", picker("actions", focus=0), "center", wide=True),
        ex("Choice list, current choice marked", picker("choices", focus=1), "center", wide=True),
        ex("Confirm, Cancel focused first", picker("confirm", focus=1), "center", wide=True),
        ex("Over a screen", dialog(picker("confirm", focus=1), opened=True) + "\n" + HINTS, "screen flush",
           wide=True, copy=True),
     ]),
    ("toast", "Toast",
     "A short message at the bottom right, just above the hint bar. It is as wide as its text, up to a limit. It "
     "stays three seconds after its last update, then leaves. A new one replaces the old.",
     "It never takes focus and never blocks what is under it. role=\"status\" makes screen readers read it "
     "politely. enamel-components.js shows, updates and hides it.", [
        ex("With an icon", toast("Library updated: 3 new films") + "\n" + HINTS, "screen flush", wide=True, copy=True),
        ex("Text only", toast("Rescanning your folders", icon=False) + "\n" + HINTS, "screen flush", wide=True),
        ex("With a progress bar", toast("Rescanning your folders", icon=False, progress=40) + "\n" + HINTS,
           "screen flush", wide=True, copy=True),
     ]),
    ("steplabel", "Step label",
     "A small, muted line above a page title that says where you are in a short flow, such as Step 1 of 3.",
     "Put it inside the title's heading element, so screen readers read the step and the title together as one "
     "heading.", [
        ex("Above a title", steplabel("Step 1 of 3", "Which folder has your movies?"), "start", wide=True, copy=True),
        ex("Long title, narrow box", steplabel("Step 2 of 3", "Which folder has your TV shows and your home videos?"),
           "start"),
     ]),
    ("band", "Group band",
     "The header of a group of list rows: an icon, the group's name in capitals and how many it holds.",
     "It never takes focus. Use a heading element. The two kinds differ by fill and by icon, never by colour alone, "
     "so two bands next to each other are easy to tell apart: the filled band with the drive for storage on the "
     "device itself, the outlined band with the card for storage you can take out. The icons are Enamel's own.", [
        ex("Filled", band("Internal storage", "3 folders"), wide=True),
        ex("Outlined", band("SD card", "2 folders", outline=True), wide=True),
        ex("Two groups of rows", band("SD card", "2 folders", outline=True) + '\n<ul class="en-rows">\n'
           '  <li><button class="en-row">SD card › Films <span class="en-row__meta">62 videos</span></button></li>\n'
           '  <li><button class="en-row" data-focused="true">SD card › Series <span class="en-row__meta">31 videos in 4 folders</span></button></li>\n'
           '</ul>\n' + band("Internal storage", "1 folder") + '\n<ul class="en-rows">\n'
           '  <li><button class="en-row">Videos <span class="en-row__meta">8 videos</span></button></li>\n'
           '</ul>', wide=True, copy=True),
        ex("Long name, narrow box", band("Internal storage on this device", "12 folders")),
        ex("Outlined, narrow box", band("SD card in the slot", "2 folders", outline=True)),
     ]),
    ("badge", "Badge",
     "A small, muted tag: a label on a row, such as the folder you already chose, or after a tab's label.",
     "Only its colours change when its row is focused or its tab is selected, so nothing changes size. Its text "
     "is part of the row's or tab's accessible name.", [
        ex("On a row", '<div class="en-rows">' + badged_row("SD card › Films", "Movies") + '</div>', copy=True),
        ex("On a focused row", '<div class="en-rows">' + badged_row("SD card › Films", "Movies", focused=True) + '</div>'),
        ex("On a focused picker row", '<div class="en-picker__rows">' + picker_row("SD card › Films", focused=True)
           .replace("</button>", ' <span class="en-badge">Movies</span></button>') + '</div>', "start"),
        ex("After a tab", f'<div class="en-tabs" role="tablist">{badged_tab("Library", "Beta")}</div>', "center",
           copy=True),
        ex("After a selected tab", f'<div class="en-tabs" role="tablist">{badged_tab("Library", "Beta", True)}</div>',
           "center"),
        ex("After a tab, keyboard focus", '<div class="en-tabs" role="tablist">'
           + badged_tab("Library", "Beta", True, ' data-demo="focus-visible"') + '</div>', "center"),
        ex("Long text, narrow box", '<div class="en-rows">'
           + badged_row("Internal storage › Videos › Films from the family", "Movies and home videos", focused=True)
           + '</div>'),
     ]),
    ("message", "Message in a row",
     "A line inside a list row, in the error style, that says why this row can't be chosen.",
     "Keep the message element in the row, empty, and put the icon and text in it when it should show: "
     "role=\"status\" makes screen readers read it politely when it appears. While it is empty it takes no space. "
     "It may make its row taller, never wider. The text is white and the icon a red disc with a dark mark, since "
     "red text is too faint on the greys.", [
        ex("Empty, waiting", '<div class="en-rows">' + message_row("SD card › Films", "62 videos") + '</div>'),
        ex("Showing", '<div class="en-rows">' + message_row(
            "SD card › Films", "62 videos", "Already your movies folder. Pick a different one.") + '</div>', copy=True),
        ex("Showing, row focused", '<div class="en-rows">' + message_row(
            "SD card › Films", "62 videos", "Already your movies folder. Pick a different one.", focused=True)
           + '</div>'),
        ex("Long text, narrow box", '<div class="en-rows">' + message_row(
            "SD card › Films › Old", "4 videos",
            "This folder is inside your movies folder, so pick a different one.", focused=True) + '</div>'),
     ]),
    ("steps", "Numbered steps",
     "A short list of two to five steps, each with its number in a round mark.",
     "Use an ordered list. When a step wraps, its text lines up after its number.", [
        ex("Three steps", steps(*STEPS_THREE), "start", wide=True, copy=True),
        ex("Two steps", steps("Put the card in.", "Choose Look again."), "start"),
        ex("Long steps, narrow box", steps(*STEPS_THREE), "start"),
     ]),
    ("stat", "Stat panel",
     "A raised panel with one or two counts, each a large number with its word, and under them the folder they "
     "refer to. A stat pair puts two panels side by side.",
     "It never takes focus and has no hover or focus state. role=\"img\" and an aria-label make it one item for "
     "screen readers, so write its whole text in the label. A pair stacks when its panels cannot both fit at their "
     "minimum width. A \"Not set\" panel's second line says which kind it is, so two of them can be told apart.", [
        ex("One count", STATS_MOVIES, copy=True),
        ex("Two counts", STATS_SHOWS, copy=True),
        ex("Zero", stat_panel([(0, "movies")], "SD card › Films")),
        ex("Not set", stat_panel(None, "Movies"), copy=True),
        ex("A pair", stat_pair(STATS_MOVIES, STATS_SHOWS), wide=True, copy=True),
        ex("A pair, one not set", stat_pair(stat_panel(None, "Movies"), STATS_SHOWS), wide=True),
        ex("A pair, narrow box, stacked", stat_pair(STATS_MOVIES, STATS_SHOWS)),
     ]),
    ("note", "Note",
     "One plain line of neutral information under other content. Several can stack.",
     "It never blocks anything, never takes focus and never goes inside a row; a message in a row is for that, in "
     "the error style. The icon is optional and Enamel's own.", [
        ex("Plain", note("12 files in Films look like episodes."), copy=True),
        ex("With an icon", note("12 files in Films look like episodes.", icon=True), copy=True),
        ex("Stacked", NOTES_TWO, wide=True, copy=True),
        ex("Long text, narrow box", note("3 loose files in the TV Shows folder look like films, so they were "
                                         "left out of your shows.", icon=True)),
     ]),
    ("speckle", "Page speckle",
     "Very faint flecks on the page ground, with the occasional one in the accent colour. Put it on an empty area "
     "of the page.",
     "Never put it behind list text, and nothing you can select is ever patterned. Text next to it still passes its "
     "contrast check.", [
        ex("An empty area", '<div class="en-speckle" style="min-height: 15rem"></div>', "flush", wide=True, copy=True),
     ]),
    ("lighter", "Lighter fallback",
     "One switch for devices that stutter: data-en-lighter=\"true\" on the page's root drops the soft shadows and the "
     "lift and press movement. Colours, cream focus, the accent underside and the speckle all stay.",
     "Compare the two below, or use the Look switch at the bottom of the menu to see the whole guide this way.", [
        ex("Full", '<button class="en-button" data-focused="true">Rescan library</button>', "raised start"),
        ex("Lighter", '<div data-en-lighter="true"><button class="en-button" data-focused="true">Rescan library</button></div>', "raised start"),
     ]),
]

# Live demos after a section's examples, run by components/enamel-components.js.
EXTRA = {
    "picker": '<p class="site-note">Try it:</p>' + open_buttons("try") + "\n" + live_pickers("try"),
    "toast": '<p class="site-note">Try it:</p>' + TOAST_BUTTONS,
}

MENU_SECTIONS = [(sid, name) for sid, name, *_ in SECTIONS]


def state(x):
    cls = "site-state site-state--wide" if x["wide"] else "site-state"
    st = "site-stage" + "".join(f" site-stage--{s}" for s in x["stage"].split())
    return (f'<figure class="{cls}"><div class="{st}">\n{x["html"]}\n</div>'
            f'<figcaption>{html.escape(x["caption"])}</figcaption></figure>')


def section(sid, name, purpose, note, examples):
    out = [f'<section id="{sid}">', f"<h2>{html.escape(name)}</h2>", f"<p>{html.escape(purpose)}</p>",
           f'<p class="site-note site-motion-note">{html.escape(MOTION[sid])}</p>']
    if note:
        out.append(f'<p class="site-note">{html.escape(note)}</p>')
    out.append('<div class="site-states">\n' + "\n".join(state(x) for x in examples) + "\n</div>")
    copy = "\n\n".join(x["html"] for x in examples if x["copy"])
    out.append(f'<pre class="site-code"><code>{html.escape(copy)}</code></pre>')
    if sid in EXTRA:
        out.append(EXTRA[sid])
    out.append("</section>")
    return "\n".join(out)


def page(menu_block):
    body = "\n".join(section(*s) for s in SECTIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enamel components</title>
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
<!-- Generated by tools/build_styleguide.py from tools/components_page.py. Do not edit by hand. -->
{menu_block}
<main class="site-main">
<h1>Components</h1>
<p>The Enamel components, in <code>components/enamel-components.css</code>. Link it after
<code>tokens/enamel.css</code>. The picker dialog and the toast also use <code>components/enamel-components.js</code>
for their behaviour; they look right without it. State comes from standard attributes (<code>aria-selected</code>,
<code>aria-pressed</code>, <code>aria-current</code>, <code>disabled</code>), and focus shows on keyboard focus
or on <code>data-focused="true"</code>. A press from a controller is <code>data-pressed="true"</code>.</p>
<p class="site-note">The examples are shown side by side to compare states, so several look focused at once.
In an app, only one element shows focus at a time. The examples move as they would in an app; the
<a href="motion.html">Motion page</a> has demos you can operate.</p>
{body}
</main>
<footer class="site-footer">Enamel is not affiliated with Valve. Steam and Steam Deck are trademarks of Valve Corporation.</footer>
</body>
</html>
"""
