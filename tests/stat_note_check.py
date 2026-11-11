# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #17: the stat panel, stat pair and note, measured in the device's
Firefox (headless, its own temporary profile; Steam is never touched):

  - neither part can take focus (the browser refuses it), and nothing about
    them or their parts changes on focus, or under a real mouse pointer;
  - each panel is one item for screen readers, whose name is exactly its counts
    and its path, and it has no focusable or labelled parts of its own;
  - nothing is cut off or spills out, on the Components page, in the Resize
    page's frames at the smallest supported box's width and the whole column,
    and alone in frames of every width the browser check uses, from the smallest
    box to very wide, even with long text that has no spaces to wrap at;
  - two "Not set" panels side by side differ on screen and in their names;
  - at the normal text size every size except text (padding, gaps, minimum
    width, icon) is a multiple of 4; corners and lines are Enamel's own px values;
  - a pair sits side by side when both panels fit at their minimum width, and
    stacks when they don't, at the exact width worked out from the minimum and
    the gap (read from the page, never hardcoded), and its panels never overlap;
  - both panels of a pair side by side are the same height, and a panel outside
    a pair is only as tall as its content;
  - stacked notes are --en-c-note-gap apart, and no note sits inside a row;
  - the number, path, "Not set" and note have the text size and colour asked
    for, as they really show, and the note's icon takes the note's colour;
  - a panel's and a note's text passes 4.5:1 against what is really behind it.

    scripts/test.sh check stat_note_check
"""
import functools
import http.server
import json
import os
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import browser_check  # noqa: E402
import components_page as cp  # noqa: E402
from serve import Handler  # noqa: E402

# Everything the browser works out for an element and all its parts, so any
# change at all shows.
LOOK = r"""
  const look = el => [el, ...el.querySelectorAll('*')].map(e => { const s = getComputedStyle(e);
    return [...s].map(p => `${p}: ${s.getPropertyValue(p)}`).join('; '); }).join(' | ');
"""

# True if the browser will not give focus to the element or any of its parts.
UNFOCUSABLE = r"""
  const takesFocus = el => [el, ...el.querySelectorAll('*')].some(e => { e.focus(); return document.activeElement === e; });
"""

MEASURE = r"""
async (args) => {
""" + LOOK + UNFOCUSABLE + r"""
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const errors = [], seen = {};
  const R = (args && args.root) || 'main';
  if (args && args.width) {
    document.querySelectorAll('.site-resize').forEach(el => { el.style.width = args.width; });
    await wait(50);
  }
  const fail = m => errors.push(m);
  const cs = el => getComputedStyle(el);
  const probe = (prop, value) => { const p = document.createElement('div'); p.style[prop] = value;
    document.body.append(p); const c = getComputedStyle(p)[prop]; p.remove(); return c; };
  const name = el => el.textContent.replace(/\s+/g, ' ').trim();
  const overlap = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 &&
    Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5;
  const lum = c => { const [r, g, b] = c.match(/[\d.]+/g).slice(0, 3).map(Number).map(v => { v /= 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

  const panels = [...document.querySelectorAll(`${R} .en-statpanel`)];
  seen.panels = panels.length;
  seen.notset = 0;
  for (const p of panels) {
    const text = name(p);
    if (p.getAttribute('role') !== 'img') fail(`the panel "${text}" is not one item for screen readers`);
    const label = p.getAttribute('aria-label') || '';
    const path = p.querySelector('.en-statpanel__path');
    if (!path) { fail(`the panel "${text}" has no second line`); continue; }
    const unset = p.querySelector('.en-statpanel__notset');
    const counts = [...p.querySelectorAll('.en-statpanel__count')].map(name);
    const want = unset ? `${name(path)}, not set` : [...counts, name(path)].join(', ');
    if (label !== want) fail(`the panel's name is "${label}", not "${want}"`);
    if (!unset && !counts.length) fail(`the panel "${text}" has neither counts nor Not set`);
    if (p.querySelector('[role], [aria-label], [aria-labelledby]')) fail(`the panel "${text}" has a labelled part inside it, so it is not one item`);
    if (unset) {
      seen.notset++;
      if (cs(unset).color !== probe('color', 'var(--en-text-muted)')) fail('Not set is not in the muted colour');
    }
    const number = p.querySelector('.en-statpanel__number');
    if (number) {
      if (cs(number).fontSize !== probe('fontSize', 'var(--en-text-title)')) fail(`the number in "${text}" is not the title size`);
      if (cs(number).color !== probe('color', 'var(--en-text-strong)')) fail(`the number in "${text}" is not the strong text colour`);
    }
    if (cs(path).fontSize !== probe('fontSize', 'var(--en-text-small)')) fail(`the path in "${text}" is not the small size`);
    if (cs(path).color !== probe('color', 'var(--en-text-soft)')) fail(`the path in "${text}" is not the soft text colour`);
    if (p.querySelector('a, button, input, select, textarea, [tabindex]') || p.tabIndex >= 0 || p.hasAttribute('tabindex'))
      fail(`the panel "${text}" can take focus`);
    if (takesFocus(p)) fail(`the browser gives focus to the panel "${text}"`);
    const rest = look(p);
    p.tabIndex = -1; p.focus();
    const bg = cs(p).backgroundColor, outline = cs(p).outlineStyle, focused = look(p);
    p.blur(); p.removeAttribute('tabindex');
    if (focused !== rest) fail(`the panel "${text}" changes on focus`);
    if (bg !== probe('backgroundColor', 'var(--en-surface-raised)')) fail(`the panel "${text}" is ${bg}, not raised`);
    if (outline !== 'none') fail(`the panel "${text}" shows focus`);
    if (!p.parentElement.classList.contains('en-statpair')) {
      seen.lone = (seen.lone || 0) + 1;
      const spare = p.getBoundingClientRect().bottom - p.lastElementChild.getBoundingClientRect().bottom - parseFloat(cs(p).paddingBottom);
      if (Math.abs(spare) > 1) fail(`the lone panel "${text}" has ${spare}px of empty height`);
    }
    if (p.scrollWidth > p.clientWidth + 0.5) fail(`the panel "${text}" is cut off`);
    if (p.getBoundingClientRect().right > p.parentElement.getBoundingClientRect().right + 0.5) fail(`the panel "${text}" spills out`);
    for (const el of p.querySelectorAll('.en-statpanel__number, .en-statpanel__count, .en-statpanel__path, .en-statpanel__notset')) {
      const r = ratio(cs(el).color, bg);
      if (r < 4.5) fail(`${el.className} "${name(el)}" is ${r.toFixed(2)}:1 on its panel, below 4.5:1`);
    }
  }

  const pairs = [...document.querySelectorAll(`${R} .en-statpair`)];
  seen.pairs = pairs.length;
  seen.side = seen.stacked = 0;
  const min = parseFloat(probe('width', 'var(--en-c-statpanel-min)'));
  const gap = parseFloat(probe('width', 'var(--en-space-gap)'));
  for (const pair of pairs) {
    const [a, b] = [...pair.children];
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    if (pair.children.length !== 2) fail(`a pair holds ${pair.children.length} panels`);
    if (overlap(ra, rb)) fail(`two panels in "${name(pair)}" overlap`);
    const room = pair.clientWidth >= 2 * min + gap - 0.5;
    const side = Math.abs(ra.top - rb.top) < 0.5;
    if (room !== side) fail(`a pair ${pair.clientWidth}px wide is ${side ? 'side by side' : 'stacked'} (minimum ${min}px, gap ${gap}px)`);
    if (side) {
      seen.side++;
      if (Math.abs(ra.height - rb.height) > 0.5) fail(`a pair's panels are ${ra.height}px and ${rb.height}px tall`);
      if (Math.abs(ra.width - rb.width) > 0.5) fail(`a pair's panels are ${ra.width}px and ${rb.width}px wide`);
    } else {
      seen.stacked++;
      if (Math.abs(ra.width - pair.clientWidth) > 0.5) fail('a stacked panel does not take the width of its space');
    }
  }

  const notes = [...document.querySelectorAll(`${R} .en-note`)];
  seen.notes = notes.length;
  seen.stackedNotes = 0;
  const noteGap = parseFloat(probe('width', 'var(--en-c-note-gap)'));
  const behind = el => { for (let a = el.parentElement; a; a = a.parentElement) {
    const c = cs(a).backgroundColor; if (!/, 0\)$|transparent/.test(c)) return c; } return 'rgb(0, 0, 0)'; };
  seen.iconNotes = 0;
  for (const n of notes) {
    if (n.closest('.en-row, .en-picker__row')) fail(`the note "${name(n)}" is inside a row`);
    if (n.tabIndex >= 0 || n.hasAttribute('tabindex') || n.querySelector('a, button, [tabindex]')) fail(`the note "${name(n)}" can take focus`);
    if (takesFocus(n)) fail(`the browser gives focus to the note "${name(n)}"`);
    const rest = look(n);
    n.tabIndex = -1; n.focus();
    const focused = look(n);
    n.blur(); n.removeAttribute('tabindex');
    if (focused !== rest) fail(`the note "${name(n)}" changes on focus`);
    if (n.scrollWidth > n.clientWidth + 0.5) fail(`the note "${name(n)}" is cut off`);
    if (cs(n).position !== 'static' || cs(n).zIndex !== 'auto') fail(`the note "${name(n)}" is lifted out of the page, so it could block something`);
    if (cs(n).fontSize !== probe('fontSize', 'var(--en-text-small)')) fail(`the note "${name(n)}" is not the small size`);
    if (cs(n).color !== probe('color', 'var(--en-text-soft)')) fail(`the note "${name(n)}" is not the soft text colour`);
    const nr = ratio(cs(n).color, behind(n));
    if (nr < 4.5) fail(`the note "${name(n)}" is ${nr.toFixed(2)}:1 on what is behind it, below 4.5:1`);
    const before = n.previousElementSibling;
    if (before && before.classList.contains('en-note')) {
      seen.stackedNotes++;
      const d = n.getBoundingClientRect().top - before.getBoundingClientRect().bottom;
      if (Math.abs(d - noteGap) > 0.5) fail(`stacked notes are ${d}px apart, not ${noteGap}px`);
    }
    const icon = n.querySelector('.en-icon');
    if (icon) {
      seen.iconNotes++;
      if (icon.getAttribute('aria-hidden') !== 'true') fail('a note icon is not hidden from screen readers');
      if (cs(icon).stroke !== cs(n).color) fail(`a note's icon is drawn in ${cs(icon).stroke}, not the note's colour`);
    }
  }
  return JSON.stringify({ errors, seen });
}
"""

# Plain frames holding only the real stylesheets and these parts, as an app would
# use them. Nothing here sets a size but the page's own gutter.
LONG = "Averylongfoldernamewithnospacesatall" * 3
FRAME_DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;font-family:var(--en-font);line-height:var(--en-line-height);background:var(--en-surface-page);color:var(--en-text)">
<main style="padding:var(--en-space-gutter)">
<div id="lone">{cp.STATS_MOVIES}</div>
{cp.stat_pair(cp.STATS_MOVIES, cp.STATS_SHOWS)}
<div id="unset">{cp.stat_pair(cp.stat_panel(None, "Movies"), cp.stat_panel(None, "TV shows"))}</div>
{cp.stat_pair(cp.stat_panel([(1234567, "movies"), (1234567, "episodes")], "SD card › " + LONG), cp.STATS_SHOWS)}
<div id="notes">{cp.note("12 files in Films look like episodes.")}{cp.note("With an icon.", icon=True)}{cp.note(LONG, icon=True)}</div>
</main>
</body></html>"""

IN_FRAMES = r"""
async (args) => {
""" + browser_check.FRAME_HELPERS + r"""
  const out = { errors: [], frames: [], rootPx };
  for (const [Wr, Hr] of JSON.parse(args.frames)) {
    const W = Math.round(Wr * rootPx), H = Math.round(Hr * rootPx);
    const f = await open(args.doc, W, H), w = f.contentWindow, d = f.contentDocument;
    const fail = m => out.errors.push(`${Wr}rem: ${m}`);
    const cs = el => w.getComputedStyle(el), rect = el => el.getBoundingClientRect();
    const name = el => el.textContent.replace(/\s+/g, ' ').trim().slice(0, 40);
    const px = v => { const p = d.createElement('div'); p.style.width = v; d.body.append(p);
      const got = p.getBoundingClientRect().width; p.remove(); return got; };
    const textBoxes = el => { const r = d.createRange(); r.selectNodeContents(el); return [...r.getClientRects()]; };
    const page = d.documentElement.clientWidth;

    if (d.scrollingElement.scrollWidth > page + 0.5) fail(`the page scrolls sideways (${d.scrollingElement.scrollWidth}px in ${page}px)`);
    for (const el of d.querySelectorAll('[class*="en-"]')) {
      const r = rect(el);
      if (r.left < -0.5 || r.right > page + 0.5) fail(`${el.getAttribute('class')} "${name(el)}" reaches outside the frame`);
    }
    for (const el of d.querySelectorAll('.en-statpanel, .en-note')) {
      if (el.scrollWidth > el.clientWidth + 0.5) fail(`"${name(el)}" is cut off`);
      const r = rect(el);
      for (const t of textBoxes(el)) if (t.right > r.right + 0.5 || t.left < r.left - 0.5) fail(`the text of "${name(el)}" spills out of it`);
    }

    // The lone panel takes the width of its space.
    const lone = d.querySelector('#lone');
    if (Math.abs(rect(lone.firstElementChild).width - lone.clientWidth) > 0.5) fail('a lone panel does not take the width of its space');

    // Each pair: side by side exactly when both panels fit at their minimum.
    const need = 2 * px('var(--en-c-statpanel-min)') + px('var(--en-space-gap)');
    const shape = { at: Wr, side: 0, stacked: 0 };
    for (const pair of d.querySelectorAll('.en-statpair')) {
      const [a, b] = pair.children, side = Math.abs(rect(a).top - rect(b).top) < 0.5, room = pair.clientWidth >= need - 0.5;
      shape[side ? 'side' : 'stacked']++;
      if (side !== room) fail(`a pair ${pair.clientWidth}px wide is ${side ? 'side by side' : 'stacked'}, and needs ${need}px to sit side by side`);
      if (overlap(rect(a), rect(b))) fail('two panels in a pair overlap');
    }
    out.frames.push(shape);

    // Two Not set panels: both say so, and differ on screen and by name.
    const [m, t] = d.querySelectorAll('#unset .en-statpanel');
    for (const p of [m, t]) if (name(p.querySelector('.en-statpanel__notset')) !== 'Not set') fail('a Not set panel does not say Not set');
    if (m.getAttribute('aria-label') === t.getAttribute('aria-label')) fail('two Not set panels have the same name');
    if (name(m) === name(t)) fail('two Not set panels look the same');

    // Notes: stacked by the variable, the icon keeps its size however long the text, and sits before it.
    const notes = [...d.querySelectorAll('#notes .en-note')], gap = px('var(--en-c-note-gap)');
    for (let i = 1; i < notes.length; i++) {
      const between = rect(notes[i]).top - rect(notes[i - 1]).bottom;
      if (Math.abs(between - gap) > 0.5) fail(`stacked notes are ${between}px apart, not ${gap}px`);
    }
    const iconSize = px('var(--en-c-icon-size)');
    for (const n of notes) {
      const icon = n.querySelector('.en-icon');
      if (!icon) continue;
      const ir = rect(icon);
      if (Math.abs(ir.width - iconSize) > 0.5 || Math.abs(ir.height - iconSize) > 0.5) fail(`a note's icon is ${ir.width}px by ${ir.height}px, not ${iconSize}px`);
      const words = d.createRange(); words.selectNode(n.lastChild);
      if (words.getBoundingClientRect().left < ir.right - 0.5) fail('a note\'s text runs under its icon');
    }

    // Every size except text, a multiple of 4 at the normal text size. Sizes that
    // follow a wide page only grow past 100rem, so they are measured below it.
    if (rootPx === 16 && Wr <= 100) {
      const panel = d.querySelector('.en-statpanel'), counts = d.querySelector('.en-statpanel__counts');
      const pair = d.querySelector('.en-statpair'), iconOf = d.querySelector('.en-note .en-icon');
      const sizes = {
        'panel padding, top': cs(panel).paddingTop, 'panel padding, right': cs(panel).paddingRight,
        'panel padding, bottom': cs(panel).paddingBottom, 'panel padding, left': cs(panel).paddingLeft,
        'gap inside a panel': cs(panel).rowGap, 'gap between counts': cs(counts).columnGap,
        'gap in a pair, across': cs(pair).columnGap, 'gap in a pair, down': cs(pair).rowGap,
        'minimum width in a pair': `${px('var(--en-c-statpanel-min)')}px`,
        'gap between notes': cs(notes[1]).marginTop, 'gap after a note icon': cs(notes[1]).columnGap,
        'note icon': `${rect(iconOf).width}px`,
      };
      for (const [what, v] of Object.entries(sizes)) {
        const n = parseFloat(v) / 4;
        if (!(Math.abs(n - Math.round(n)) < 0.01) || !(n > 0)) fail(`${what} is ${v}, not a multiple of 4`);
      }
    }
    f.remove();
  }
  return JSON.stringify(out);
}
"""

# Hover needs a real pointer, moved by the browser, not a script.
HOVER_PLACE = r"""
async (args) => {
""" + LOOK + r"""
  const el = document.querySelector(args.sel);
  el.scrollIntoView({ block: 'center', inline: 'center' });
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const r = el.getBoundingClientRect();
  return JSON.stringify({ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2), look: look(el) });
}
"""

HOVER_READ = r"""
async (args) => {
""" + LOOK + r"""
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const el = document.querySelector(args.sel);
  return JSON.stringify({ hovered: el.matches(':hover'), look: look(el), anims: el.getAnimations({ subtree: true }).length });
}
"""


class StatNote(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Quiet(Handler):
            def log_message(self, *args):
                pass
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/docs/"
        cls.ff = None
        try:
            cls.ff = browser_check.Firefox(False)
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        if cls.ff:
            cls.ff.close()
            cls.ff.s.close()
            cls.ff = None
        cls.server.shutdown()
        cls.server.server_close()

    def test_on_the_components_page(self):
        self.ff.load(self.base + "components.html")
        out = self.ff.run(MEASURE, {}, "the stat panel and note check")
        errors, seen = out["errors"], out["seen"]
        if self.ff.errors():
            errors.append(f"script errors: {self.ff.errors()}")
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertGreaterEqual(seen["panels"], 10)
        self.assertGreaterEqual(seen["notset"], 2)
        self.assertGreaterEqual(seen.get("lone", 0), 4)
        self.assertGreaterEqual(seen["pairs"], 3)
        self.assertGreaterEqual(seen["notes"], 5)
        self.assertGreaterEqual(seen["stackedNotes"], 1)
        self.assertGreaterEqual(seen["iconNotes"], 1)
        print(f"Stat panels and notes: {seen['panels']} panels, {seen['pairs']} pairs "
              f"({seen['side']} side by side, {seen['stacked']} stacked), {seen['notes']} notes as specified")

    def test_alone_in_frames_from_the_smallest_box_to_very_wide(self):
        self.ff.load(self.base + "components.html")
        out = self.ff.run(IN_FRAMES, {"frames": json.dumps(browser_check.FRAMES), "doc": FRAME_DOC},
                          "the stat panel and note frame check")
        self.assertEqual(out["errors"], [], "\n".join(out["errors"]))
        self.assertEqual(out["rootPx"], 16, "the multiples of 4 are only measured at the normal text size")
        shapes = out["frames"]
        self.assertEqual(len(shapes), len(browser_check.FRAMES))
        self.assertEqual(shapes[0]["side"], 0, "a pair sits side by side in the smallest supported box")
        self.assertEqual(shapes[-1]["stacked"], 0, "a pair is stacked in a very wide frame")

    def test_a_real_pointer_changes_nothing(self):
        def point(x, y):
            self.ff.s.call("input.performActions", _limit=browser_check.LOAD_LIMIT, context=self.ff.ctx, actions=[
                {"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
                 "actions": [{"type": "pointerMove", "x": x, "y": y, "origin": "viewport", "duration": 0}]}])

        self.ff.load(self.base + "components.html")
        for sel in (".en-statpanel", ".en-statpanel:has(.en-statpanel__notset)", ".en-statpair", ".en-note",
                    ".en-note:has(.en-icon)"):
            with self.subTest(sel=sel):
                place = self.ff.run(HOVER_PLACE, {"sel": sel}, f"placing {sel} for the hover check")
                point(0, 0)
                rest = self.ff.run(HOVER_READ, {"sel": sel}, f"reading {sel} at rest")
                self.assertFalse(rest["hovered"], "the pointer did not leave the part")
                point(place["x"], place["y"])
                over = self.ff.run(HOVER_READ, {"sel": sel}, f"reading {sel} under the pointer")
                self.assertTrue(over["hovered"], "the pointer did not reach the part, so this proves nothing")
                self.assertEqual(over["look"], rest["look"], "it changes under the pointer")
                self.assertEqual(over["anims"], 0, "it moves under the pointer")
        point(0, 0)

    def test_on_the_resize_page_from_the_smallest_box_to_very_wide(self):
        # A Resize frame is never wider than its column, however wide it is set; the
        # really wide frames are in test_alone_in_frames_from_the_smallest_box_to_very_wide.
        smallest = f"{browser_check.SMALLEST[0]:g}rem"
        widest = f"{browser_check.FRAMES[-1][0]:g}rem"
        for width, want in ((smallest, "stacked"), ("100%", None), (widest, "side")):
            with self.subTest(width=width):
                self.ff.load(self.base + "resize.html")
                out = self.ff.run(MEASURE, {"root": ".site-resize", "width": width},
                                  f"the stat panel and note check on the Resize page at {width}")
                errors, seen = out["errors"], out["seen"]
                if self.ff.errors():
                    errors.append(f"script errors: {self.ff.errors()}")
                self.assertEqual(errors, [], "\n".join(errors))
                for what in ("panels", "pairs", "notes", "stackedNotes", "notset"):
                    self.assertGreaterEqual(seen[what], 1, f"no {what} on the Resize page")
                if want:
                    self.assertGreaterEqual(seen[want], 1, f"no pair is {want} at {width}")

    def test_the_pair_stacks_at_exactly_its_minimum_width(self):
        """Dragging a frame across the point where two panels stop fitting: side by side just
        above it, stacked just below it, worked out from the token and the variable."""
        self.ff.load(self.base + "resize.html")
        out = self.ff.run(r"""
        async () => {
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const frame = document.querySelector('.site-resize .en-statpair').closest('.site-resize');
          const pair = frame.querySelector('.en-statpair');
          const px = (name) => { const p = document.createElement('div'); p.style.width = `var(${name})`;
            document.body.append(p); const w = p.getBoundingClientRect().width; p.remove(); return w; };
          const need = 2 * px('--en-c-statpanel-min') + px('--en-space-gap');
          const extra = frame.getBoundingClientRect().width - pair.clientWidth;
          const result = {};
          for (const [what, d] of [['above', 2], ['below', -2]]) {
            frame.style.width = `${need + extra + d}px`;
            await wait(50);
            const [a, b] = pair.children;
            result[what] = Math.abs(a.getBoundingClientRect().top - b.getBoundingClientRect().top) < 0.5;
          }
          return JSON.stringify(result);
        }""", {}, "the stacking point check")
        self.assertTrue(out["above"], "the pair stacked although both panels fit")
        self.assertFalse(out["below"], "the pair stayed side by side although both panels did not fit")


if __name__ == "__main__":
    unittest.main()
