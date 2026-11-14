# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issues #21 and #22: the destructive row, measured in the device's Firefox
(headless, its own temporary profile; Steam is never touched):

  - every destructive list row and picker row on the Components page that is
    neither focused nor pressed looks like a plain row: the raised face, the
    row's text colour, a muted, regular meta or description, an icon in the
    text colour, and a message in the usual error style (#22);
  - focused or pressed, it has the error red face and white text, meta,
    description and icon, as the page really shows it;
  - then its meta or description is bold, and the row's own text keeps its
    row's size, so the one text pair below 4.5:1 stays large or bold;
  - white on its real face passes APCA Lc 60 and is at least 4.4:1;
  - it is the same height and padding as an ordinary row of its kind;
  - focused, it rises by --en-lift onto the accent underside; not focused it
    has neither; pressed it drops back; in reduced motion (the page's switch
    and the device's setting) focus keeps the underside without the rise;
  - an icon sits before the text, and in a picker row the description lines
    up under the title;
  - alone in frames of every width the browser check uses, from the smallest
    supported box to very wide, nothing spills out, is cut off or makes the
    page scroll sideways, even with long text.

    scripts/test.sh check destructive_row_check
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

ROWS = ".en-row--destructive, .en-picker__row--destructive"

MEASURE = r"""
async (args) => {
  const errors = [], seen = { rows: 0, plain: 0, focused: 0, pressed: 0, icons: 0, described: 0 };
  const fail = m => errors.push(m);
  const cs = el => getComputedStyle(el);
  const probe = (prop, value) => { const p = document.createElement('div'); p.style[prop] = value;
    document.body.append(p); const c = getComputedStyle(p)[prop]; p.remove(); return c; };
  const name = el => el.textContent.replace(/\s+/g, ' ').trim().slice(0, 40);
  const rgb = c => c.match(/[\d.]+/g).slice(0, 3).map(Number);
  const lum = c => { const [r, g, b] = rgb(c).map(v => { v /= 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const apca = (t, b) => { const y = c => { const [r, g, bl] = rgb(c).map(v => v / 255);
      const v = 0.2126729 * r ** 2.4 + 0.7151522 * g ** 2.4 + 0.0721750 * bl ** 2.4;
      return v > 0.022 ? v : v + (0.022 - v) ** 1.414; };
    const [yt, yb] = [y(t), y(b)];
    const s = yb > yt ? (yb ** 0.56 - yt ** 0.57) * 1.14 : (yb ** 0.65 - yt ** 0.62) * 1.14;
    return Math.abs(s) < 0.1 ? 0 : (Math.abs(s) - 0.027) * 100; };
  const rise = el => { const t = cs(el).transform; return t === 'none' ? 0 : -new DOMMatrix(t).m42; };
  const red = probe('backgroundColor', 'var(--en-danger)');
  const white = probe('color', 'var(--en-text-strong)');
  const raised = probe('backgroundColor', 'var(--en-surface-raised)');
  const text = probe('color', 'var(--en-text)');
  const muted = probe('color', 'var(--en-text-muted)');
  const ink = probe('color', 'var(--en-focus-fill-ink)');
  const redInk = probe('color', 'var(--en-danger)');
  const accent = probe('color', 'var(--en-focus-ring)');
  const lift = parseFloat(probe('width', 'var(--en-lift)'));
  const reduced = document.documentElement.getAttribute('data-en-motion') === 'reduced'
    || matchMedia('(prefers-reduced-motion: reduce)').matches;
  // An ordinary row of each kind, for the size the destructive one must keep.
  // A picker row with a description is taller, so it is compared with one that has one too.
  const plain = { 'en-row': document.querySelector('main .en-row:not(.en-row--destructive):not(:has(> *))'),
                  'en-picker__row': document.querySelector('main .en-picker__row:not(.en-picker__row--destructive):not(:has(.en-picker__desc))'),
                  'en-picker__row desc': document.querySelector('main .en-picker__row:not(.en-picker__row--destructive):has(.en-picker__desc)') };

  for (const row of document.querySelectorAll(args.rows)) {
    seen.rows++;
    const kind = row.classList.contains('en-row') ? 'en-row' : 'en-picker__row';
    const what = `the destructive ${kind === 'en-row' ? 'list' : 'picker'} row "${name(row)}"`;
    const focused = row.getAttribute('data-focused') === 'true', pressed = row.getAttribute('data-pressed') === 'true';
    const lit = focused || pressed;
    if (focused) seen.focused++;
    if (pressed) seen.pressed++;
    if (!lit) seen.plain++;
    const s = cs(row), face = s.backgroundColor;
    if (lit) {
      if (face !== red) fail(`${what} has a ${face} face, not the error red`);
      if (s.color !== white) fail(`${what} has ${s.color} text, not white`);
      const lc = apca(s.color, face), r = ratio(s.color, face);
      if (lc < 60) fail(`${what}: white on its face is APCA Lc ${lc.toFixed(1)}, below 60`);
      if (r < 4.4) fail(`${what}: white on its face is ${r.toFixed(2)}:1`);
    } else {
      if (face !== raised) fail(`${what} is not focused but has a ${face} face, not a plain row's`);
      if (s.color !== text) fail(`${what} is not focused but has ${s.color} text, not a plain row's`);
    }
    const size = kind === 'en-row' ? 'var(--en-text-body)' : 'var(--en-text-heading)';
    if (s.fontSize !== probe('fontSize', size)) fail(`${what} is ${s.fontSize}, not its row's text size`);
    for (const small of row.querySelectorAll('.en-row__meta, .en-picker__desc')) {
      seen.described++;
      const want = lit ? white : muted, weight = parseFloat(cs(small).fontWeight);
      if (cs(small).color !== want) fail(`the meta or description in ${what} is ${cs(small).color}, not ${want}`);
      if (lit && weight < 700) fail(`the meta or description in ${what} is not bold`);
      if (!lit && weight >= 700) fail(`the meta or description in ${what} is bold while the row is not focused`);
    }
    const message = row.querySelector('.en-row__message');
    if (message && message.textContent.trim()) {
      seen.messages = (seen.messages || 0) + 1;
      if (!lit) seen.plainMessages = (seen.plainMessages || 0) + 1;
      const disc = message.querySelector('.en-icon');
      const [discColour, mark] = lit ? [white, red] : [redInk, ink];
      if (cs(message).color !== white) fail(`the message in ${what} is ${cs(message).color}, not white`);
      if (cs(disc).color !== discColour || cs(disc).stroke !== mark)
        fail(`the message disc in ${what} is ${cs(disc).color} with a ${cs(disc).stroke} mark, not ${discColour} with a ${mark} one`);
    }
    const icon = row.querySelector(':scope > .en-icon');
    if (icon) {
      seen.icons++;
      if (icon.getAttribute('aria-hidden') !== 'true') fail(`the icon in ${what} is not hidden from screen readers`);
      if (cs(icon).stroke !== s.color) fail(`the icon in ${what} is drawn in ${cs(icon).stroke}, not its text colour ${s.color}`);
      if (lit && cs(icon).stroke !== white) fail(`the icon in ${what} is drawn in ${cs(icon).stroke}, not white`);
      const text = [...row.childNodes].find(n => n !== icon && n.textContent.trim());
      const range = document.createRange(); range.selectNodeContents(text);
      if (range.getBoundingClientRect().left < icon.getBoundingClientRect().right - 0.5) fail(`the text of ${what} runs under its icon`);
      const desc = row.querySelector('.en-picker__desc');
      if (desc && Math.abs(desc.getBoundingClientRect().left - range.getBoundingClientRect().left) > 0.5)
        fail(`the description in ${what} does not line up under its title`);
    }
    const base = plain[kind === 'en-picker__row' && row.querySelector('.en-picker__desc') ? 'en-picker__row desc' : kind];
    if (base) {
      for (const p of ['minHeight', 'paddingLeft', 'paddingRight', 'borderTopLeftRadius'])
        if (s[p] !== cs(base)[p]) fail(`${what}: ${p} is ${s[p]}, an ordinary row's is ${cs(base)[p]}`);
    }
    const under = s.boxShadow.includes(accent);
    const up = rise(row);
    if (focused && !pressed) {
      if (!under) fail(`${what} is focused but shows no accent underside`);
      const want = reduced ? 0 : lift;
      if (Math.abs(up - want) > 0.5) fail(`${what} is focused and has risen ${up}px, not ${want}px`);
    } else if (pressed) {
      if (Math.abs(up) > 0.5) fail(`${what} is pressed but still raised ${up}px`);
    } else {
      if (under) fail(`${what} is not focused but shows the accent underside`);
      if (Math.abs(up) > 0.5) fail(`${what} is not focused but raised ${up}px`);
    }
    if (row.scrollWidth > row.clientWidth + 0.5) fail(`${what} is cut off`);
  }
  return JSON.stringify({ errors, seen });
}
"""

LONG = "Averylongfoldernamewithnospacesatall" * 3
FRAME_DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;font-family:var(--en-font);line-height:var(--en-line-height);background:var(--en-surface-page);color:var(--en-text)">
<main style="padding:var(--en-space-gutter)">
<div class="en-rows">
{cp.destructive_row("Remove this folder and everything Kettle remembers about it", "1,204 videos", icon=cp.REMOVE_ICON, focused=True)}
{cp.destructive_row("Remove " + LONG, icon=cp.REMOVE_ICON)}
</div>
{cp.destructive_picker(focus=2)}
<div class="en-picker__rows">{cp.picker_row("Remove " + LONG, "Only the list changes " + LONG, destructive=True, icon=cp.REMOVE_ICON, focused=True)}</div>
</main>
</body></html>"""

IN_FRAMES = r"""
async (args) => {
""" + browser_check.FRAME_HELPERS + r"""
  const out = { errors: [], frames: 0, rootPx };
  for (const [Wr, Hr] of JSON.parse(args.frames)) {
    const W = Math.round(Wr * rootPx), H = Math.round(Hr * rootPx);
    const f = await open(args.doc, W, H), d = f.contentDocument;
    const fail = m => out.errors.push(`${Wr}rem: ${m}`);
    const rect = el => el.getBoundingClientRect();
    const name = el => el.textContent.replace(/\s+/g, ' ').trim().slice(0, 40);
    const page = d.documentElement.clientWidth;
    if (d.scrollingElement.scrollWidth > page + 0.5) fail(`the page scrolls sideways (${d.scrollingElement.scrollWidth}px in ${page}px)`);
    const rows = d.querySelectorAll(args.rows);
    if (rows.length !== 4) fail(`${rows.length} destructive rows in the frame, not 4`);
    for (const el of rows) {
      const r = rect(el);
      if (r.left < -0.5 || r.right > page + 0.5) fail(`"${name(el)}" reaches outside the frame`);
      if (el.scrollWidth > el.clientWidth + 0.5) fail(`"${name(el)}" is cut off`);
      const t = d.createRange(); t.selectNodeContents(el);
      for (const b of t.getClientRects()) if (b.right > r.right + 0.5 || b.left < r.left - 0.5) fail(`the text of "${name(el)}" spills out of it`);
    }
    out.frames++;
    f.remove();
  }
  return JSON.stringify(out);
}
"""


class DestructiveRow(unittest.TestCase):
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

    def measure(self, motion=None, ff=None):
        ff = ff or self.ff
        ff.load(self.base + "components.html")
        if motion:
            ff.run("async (a) => { document.documentElement.setAttribute('data-en-motion', a.m);"
                   " await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));"
                   " return '{}'; }", {"m": motion}, "switching motion")
        out = ff.run(MEASURE, {"rows": ROWS}, "the destructive row check")
        errors, seen = out["errors"], out["seen"]
        if ff.errors():
            errors.append(f"script errors: {ff.errors()}")
        self.assertEqual(errors, [], "\n".join(errors))
        return seen

    def test_on_the_components_page(self):
        seen = self.measure("full")
        self.assertGreaterEqual(seen["rows"], 13)
        self.assertGreaterEqual(seen["plain"], 5)
        self.assertGreaterEqual(seen["focused"], 6)
        self.assertGreaterEqual(seen["pressed"], 2)
        self.assertGreaterEqual(seen["icons"], 9)
        self.assertGreaterEqual(seen["described"], 7)
        self.assertGreaterEqual(seen.get("messages", 0), 2)
        self.assertGreaterEqual(seen.get("plainMessages", 0), 1)
        print(f"Destructive rows: {seen['rows']} rows, {seen['plain']} plain while unfocused, "
              f"{seen['focused']} focused and {seen['pressed']} pressed red with white text, "
              "rising onto the underside on focus")

    def test_in_reduced_motion_focus_keeps_the_underside_without_the_rise(self):
        seen = self.measure("reduced")
        self.assertGreaterEqual(seen["focused"], 6)

    def test_with_the_devices_reduced_motion(self):
        ff = browser_check.Firefox(True)
        try:
            seen = self.measure(ff=ff)
        finally:
            ff.close()
            ff.s.close()
        self.assertGreaterEqual(seen["focused"], 6)

    def test_alone_in_frames_from_the_smallest_box_to_very_wide(self):
        self.ff.load(self.base + "components.html")
        out = self.ff.run(IN_FRAMES, {"frames": json.dumps(browser_check.FRAMES), "doc": FRAME_DOC, "rows": ROWS},
                          "the destructive row frame check")
        self.assertEqual(out["errors"], [], "\n".join(out["errors"]))
        self.assertEqual(out["frames"], len(browser_check.FRAMES))


if __name__ == "__main__":
    unittest.main()
