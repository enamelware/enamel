# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #16: the five small components for onboarding, measured on the
Components page in the device's Firefox (headless, its own temporary profile;
Steam is never touched):

  - badge: its row or tab is exactly the same size, and so is the badge,
    focused or not and selected or not; only its colours change (to the page
    colour on a focused row or a selected tab, and since #18 on a picker row's
    cream focus fill); its text is part of its row's or tab's name;
  - message in a row: it has role="status" and aria-live="polite"; while
    empty it takes no space and the row is the same as one without it; when
    it shows, the row is taller and never wider, nothing in it is cut off,
    and its icon is the red disc; it fades in, and not in reduced motion;
  - group band: it can't take focus; the two kinds differ by fill and icon,
    not colour alone; the name and count never overlap, in a narrow box too;
  - step label: inside a heading, on a line of its own above the title, in
    the muted text colour;
  - numbered steps: two to five, each number in a round mark as big as a
    button glyph, every line of a step's text starting at the same place
    after its number, in a narrow box too;
  - all of the above again in the Resize page's frames, set to the smallest
    supported box's width, the whole column and very wide;
  - the step label is said once, inside one heading with its title;
  - the badge's and the message's text pass 4.5:1 against what is really
    behind them, on rows, tabs, and rows inside a picker (including the
    focused row's white fill).

    scripts/test.sh check onboarding_parts_check
"""
import functools
import http.server
import os
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import browser_check  # noqa: E402
from serve import Handler  # noqa: E402

MEASURE = r"""
async (args) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const errors = [], seen = {};
  // Where to look (the Components page's main, or the Resize page's frames),
  // and on the Resize page the width every resizable frame is set to first.
  const R = (args && args.root) || 'main';
  if (args && args.width) {
    document.querySelectorAll('.site-resize').forEach(el => { el.style.width = args.width; });
    await wait(50);
  }
  const fail = m => errors.push(m);
  const cs = (el, pseudo) => getComputedStyle(el, pseudo || null);
  const rect = el => { const r = el.getBoundingClientRect(); return [r.left, r.top, r.width, r.height].map(v => Math.round(v * 100) / 100); };
  const same = (a, b) => a.every((v, i) => Math.abs(v - b[i]) < 0.02);
  const probe = (prop, value) => { const p = document.createElement('div'); p.style[prop] = value;
    document.body.append(p); const c = getComputedStyle(p)[prop]; p.remove(); return c; };
  const colour = name => probe('color', `var(${name})`);
  const settle = () => { document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} }); return wait(30); };
  const name = el => el.textContent.replace(/\s+/g, ' ').trim();

  // Badge
  const badges = [...document.querySelectorAll(`${R} .en-badge`)];
  seen.badges = badges.length;
  for (const b of badges) {
    const host = b.closest('.en-row, .en-tab, .en-picker__row');
    if (!host) { fail(`a badge "${name(b)}" is in neither a row nor a tab`); continue; }
    if (b.closest('[aria-hidden="true"]')) fail(`the badge "${name(b)}" is hidden from screen readers`);
    if (!name(host).includes(name(b))) fail(`the badge "${name(b)}" is not part of its ${host.className}'s name`);
    // A focused picker row rises (#18): compare its size, not where it sits.
    const risen = host.classList.contains('en-picker__row');
    const sameBox = (a, c) => risen ? same(a.slice(2), c.slice(2)) : same(a, c);
    const states = host.matches('.en-row, .en-picker__row')
      ? [['data-focused', null], ['data-focused', 'true']]
      : [['aria-selected', 'false'], ['aria-selected', 'true'], ['data-demo', 'focus-visible']];
    // A badge that doesn't fit beside the title moves under it: it never
    // overlaps the title, and the title's words are never broken up.
    const title = [...host.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
    if (title) {
      const rg = document.createRange(); rg.selectNodeContents(title);
      const br = b.getBoundingClientRect();
      for (const tr of rg.getClientRects())
        if (tr.width && Math.min(tr.right, br.right) - Math.max(tr.left, br.left) > 0.5 &&
            Math.min(tr.bottom, br.bottom) - Math.max(tr.top, br.top) > 0.5) fail(`the badge "${name(b)}" overlaps its title`);
      const words = title.textContent.trim().split(/\s+/).length;
      if (rg.getClientRects().length > words) fail(`the title beside the badge "${name(b)}" is broken inside its words`);
    }
    const keep = states.map(([k]) => [k, host.getAttribute(k)]);
    const sizes = [];
    for (const [k, v] of states) {
      if (v === null) host.removeAttribute(k); else host.setAttribute(k, v);
      await settle();
      sizes.push([rect(host), rect(b), cs(b).backgroundColor, cs(b).color, cs(host).backgroundColor]);
    }
    for (const [k, v] of keep) { if (v === null) host.removeAttribute(k); else host.setAttribute(k, v); }
    await settle();
    for (const s of sizes.slice(1)) {
      if (!sameBox(s[0], sizes[0][0])) fail(`the ${host.className.split(' ')[0]} with the badge "${name(b)}" changes size (${sizes[0][0]} to ${s[0]})`);
      if (!sameBox(s[1], sizes[0][1])) fail(`the badge "${name(b)}" changes size (${sizes[0][1]} to ${s[1]})`);
    }
    for (const s of sizes) {
      if (s[3] !== colour('--en-text-soft')) fail(`the badge "${name(b)}" text is ${s[3]}, not --en-text-soft`);
      // On the control grey, or on the cream focus fill (#18), it turns to the page colour.
      const onGrey = s[4] === colour('--en-surface-control') || s[4] === colour('--en-focus-fill');
      const want = onGrey ? colour('--en-surface-page') : colour('--en-surface-control');
      if (s[2] !== want) fail(`the badge "${name(b)}" is ${s[2]} on a ${s[4]} ${host.className.split(' ')[0]}`);
    }
  }

  // Message in a row
  // A message in a destructive row (#21) has its own colours, checked by destructive_row_check.
  const DESTRUCTIVE = '.en-row--destructive, .en-picker__row--destructive';
  const messages = [...document.querySelectorAll(`${R} .en-row__message`)].filter(m => !m.closest(DESTRUCTIVE));
  seen.messages = messages.length;
  seen.showing = 0;
  for (const m of messages) {
    const row = m.closest('.en-row');
    if (m.getAttribute('role') !== 'status' || m.getAttribute('aria-live') !== 'polite')
      fail('a message in a row is not a polite status');
    if (!row || m.parentElement !== row) { fail('a message is not directly inside a row'); continue; }
    const saved = m.innerHTML;
    m.innerHTML = ''; await settle();
    const empty = rect(row);
    if (cs(m).display !== 'none') fail('an empty message takes space');
    const bare = row.cloneNode(true); bare.querySelector('.en-row__message').remove();
    row.after(bare); await settle();
    if (!same(rect(bare).slice(2), empty.slice(2))) fail(`an empty message changes its row (${empty} against ${rect(bare)})`);
    bare.remove();
    m.innerHTML = saved; await settle();
    if (!saved) continue;
    seen.showing++;
    const shown = rect(row);
    if (!(shown[3] > empty[3] + 1)) fail(`a message did not make its row taller (${empty[3]} to ${shown[3]})`);
    if (Math.abs(shown[2] - empty[2]) > 0.02) fail(`a message made its row wider (${empty[2]} to ${shown[2]})`);
    if (row.scrollWidth > row.clientWidth + 0.5 || m.scrollWidth > m.clientWidth + 0.5) fail('a message is cut off');
    const mr = m.getBoundingClientRect(), rr = row.getBoundingClientRect();
    if (mr.left < rr.left - 0.5 || mr.right > rr.right + 0.5 || mr.bottom > rr.bottom + 0.5) fail('a message spills out of its row');
    const icon = m.querySelector('.en-icon');
    if (!icon || icon.getAttribute('aria-hidden') !== 'true') fail('a message has no hidden icon');
    else if (cs(icon).color !== colour('--en-danger')) fail(`a message icon is ${cs(icon).color}, not the error red`);
    if (cs(m).color !== colour('--en-text-strong')) fail(`a message's text is ${cs(m).color}`);
    if (cs(m).animationName !== 'en-fade-in') fail(`a message appears with ${cs(m).animationName}, not a fade`);
    document.documentElement.setAttribute('data-en-motion', 'reduced');
    if (cs(m).animationName !== 'none') fail('a message still fades in reduced motion');
    document.documentElement.removeAttribute('data-en-motion');
  }

  // Group band
  const bands = [...document.querySelectorAll(`${R} .en-band`)];
  seen.bands = bands.length;
  for (const band of bands) {
    if (band.tabIndex >= 0 || band.matches('a, button, input, select, textarea, [tabindex]')) fail('a group band can take focus');
    if (!/^H[1-6]$/.test(band.tagName)) fail(`a group band is a ${band.tagName}, not a heading`);
    const n = band.querySelector('.en-band__name'), c = band.querySelector('.en-band__count'), i = band.querySelector('.en-icon');
    if (!n || !c || !i) { fail('a group band is missing its icon, name or count'); continue; }
    const a = n.getBoundingClientRect(), b = c.getBoundingClientRect();
    if (Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5)
      fail(`in the band "${name(band)}" the name and count overlap`);
    const inner = band.getBoundingClientRect().right - parseFloat(cs(band).paddingRight);
    if (Math.abs(b.right - inner) > 1) fail(`in the band "${name(band)}" the count is not on the right`);
    if (band.scrollWidth > band.clientWidth + 0.5) fail(`the band "${name(band)}" is cut off`);
    if (cs(n).textTransform !== 'uppercase') fail('a band name is not in capitals');
  }
  const filled = bands.find(b => !b.classList.contains('en-band--outline'));
  const outlined = bands.find(b => b.classList.contains('en-band--outline'));
  if (!filled || !outlined) fail('the page does not show both kinds of band');
  else {
    if (cs(filled).backgroundColor !== colour('--en-surface-control')) fail('the filled band is not filled');
    if (cs(outlined).backgroundColor !== 'rgba(0, 0, 0, 0)') fail('the outlined band has a fill');
    if (!cs(outlined).boxShadow.includes(colour('--en-text-muted'))) fail('the outlined band has no outline');
    if (filled.querySelector('.en-icon').innerHTML === outlined.querySelector('.en-icon').innerHTML)
      fail('the two kinds of band have the same icon');
  }

  // Step label
  const labels = [...document.querySelectorAll(`${R} .en-steplabel`)];
  seen.labels = labels.length;
  for (const l of labels) {
    const h = l.parentElement;
    if (!/^H[1-6]$/.test(h.tagName)) { fail('a step label is not inside a heading'); continue; }
    if (h.firstElementChild !== l) fail('a step label is not before its title');
    if (cs(l).display !== 'block') fail('a step label is not on a line of its own');
    if (cs(l).color !== colour('--en-text-muted')) fail('a step label is not muted');
    if (!(parseFloat(cs(l).fontSize) < parseFloat(cs(h).fontSize))) fail('a step label is not smaller than its title');
    // One heading, read once: the heading's name is its own text (no label
    // of its own that would replace it or repeat the step), the step label is
    // not hidden, and the step is said exactly once, followed by the title.
    for (const a of ['aria-label', 'aria-labelledby', 'aria-describedby'])
      if (h.hasAttribute(a) || l.hasAttribute(a)) fail(`a step label's heading has ${a}, so the step may be read twice or not at all`);
    if (l.closest('[aria-hidden="true"]') || cs(l).display === 'none' || cs(l).visibility === 'hidden')
      fail('a step label is hidden from screen readers');
    if (name(h).split(name(l)).length !== 2) fail(`the step "${name(l)}" is not said exactly once in its heading`);
    if (!(name(h).length > name(l).length)) fail(`the step label "${name(l)}" has no title after it`);
  }

  // Numbered steps
  const lists = [...document.querySelectorAll(`${R} .en-steps`)];
  seen.steps = lists.length;
  const glyph = parseFloat(probe('width', 'var(--en-c-glyph-size)'));
  for (const ol of lists) {
    if (ol.tagName !== 'OL') fail('numbered steps are not an ordered list');
    const items = [...ol.children];
    if (items.length < 2 || items.length > 5) fail(`a list has ${items.length} steps, not two to five`);
    items.forEach((li, k) => {
      const mark = cs(li, '::before');
      if (!mark.content.includes('counter(en-step)')) fail(`step ${k + 1} has no number (${mark.content})`);
      if (Math.abs(parseFloat(mark.width) - glyph) > 0.5 || Math.abs(parseFloat(mark.height) - glyph) > 0.5)
        fail(`step ${k + 1}'s number is ${mark.width} by ${mark.height}, not a glyph's ${glyph}px`);
      const text = [...li.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
      const range = document.createRange(); range.selectNodeContents(text);
      const lines = [...range.getClientRects()].filter(r => r.width > 0);
      const lefts = new Set(lines.map(r => Math.round(r.left)));
      if (lefts.size !== 1) fail(`step ${k + 1}'s lines start at ${[...lefts]}`);
      const start = li.getBoundingClientRect().left + glyph;
      if (lines.length && lines[0].left < start) fail(`step ${k + 1}'s text runs under its number`);
      if (lines.length > 1) seen.wrapped = (seen.wrapped || 0) + 1;
      if (li.scrollWidth > li.clientWidth + 0.5) fail(`step ${k + 1} is cut off`);
    });
  }
  return JSON.stringify({ errors, seen });
}
"""

# The badge's and the message's text, measured against what is really behind
# it: on every row and tab on the Components page, and on rows inside a picker
# (raised, current choice, and focused, which fills white), as the issue asks
# ("a focused row lifts to the control grey, and fills white inside a picker;
# the badge and the error message must stay readable on both").
CONTRAST = r"""
async (args) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const errors = [], seen = { pairs: 0 };
  const cs = el => getComputedStyle(el);
  const rgb = c => c.match(/[\d.]+/g).map(Number);
  const lum = c => { const [r, g, b] = rgb(c).slice(0, 3).map(v => { v /= 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const opaque = c => { const v = rgb(c); return v.length < 4 || v[3] > 0; };
  const behind = el => { for (let e = el; e; e = e.parentElement) { const c = cs(e).backgroundColor; if (opaque(c)) return c; }
    return cs(document.body).backgroundColor; };
  const name = el => el.textContent.replace(/\s+/g, ' ').trim();
  const mark = '<svg class="en-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">' +
    '<circle cx="12" cy="12" r="10" fill="currentColor" stroke="none"/><path d="M12 7v6"/></svg>';
  const picker = document.createElement('div');
  picker.className = 'en-picker';
  picker.innerHTML = '<div class="en-picker__rows">' + [['', 'raised'], [' aria-current="true"', 'current choice'],
    [' data-focused="true"', 'focused']].map(([a, what]) =>
    `<button class="en-picker__row"${a} data-what="${what}"><span>SD card › Films</span><span class="en-badge">Movies</span>` +
    `<span class="en-row__message" role="status" aria-live="polite">${mark}Already your movies folder.</span></button>`).join('') + '</div>';
  document.querySelector('main').append(picker);
  document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
  await wait(50);
  const check = (el, where) => {
    const fg = cs(el).color, bg = behind(el), r = ratio(fg, bg);
    seen.pairs++;
    if (r < 4.5) errors.push(`${where}: the ${el.className.split(' ')[0]} "${name(el)}" is ${fg} on ${bg}, ${r.toFixed(2)}:1, below 4.5:1`);
  };
  // A message in a destructive row (#21) is checked by destructive_row_check.
  for (const el of [...document.querySelectorAll('main .en-badge, main .en-row__message:not(:empty)')]
      .filter(e => !e.closest('.en-row--destructive, .en-picker__row--destructive'))) {
    const host = el.closest('.en-row, .en-tab, .en-picker__row');
    const where = host.classList.contains('en-picker__row') ? `inside a picker, on a ${host.dataset.what} row`
      : `on a ${host.className.split(' ')[0]}${host.matches('[data-focused="true"], [aria-selected="true"]') ? ', focused or selected' : ''}`;
    check(el, where);
  }
  picker.remove();
  return JSON.stringify({ errors, seen });
}
"""


class OnboardingParts(unittest.TestCase):
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

    def test_readable_on_every_row_including_inside_a_picker(self):
        """#16 Watch for: the badge and the message stay readable on a row, a focused row, and a
        focused (white) row inside a picker; every text pair at least 4.5:1."""
        self.ff.load(self.base + "components.html")
        out = self.ff.run(CONTRAST, {}, "the onboarding parts contrast check")
        self.assertEqual(out["errors"], [], "\n".join(out["errors"]))
        self.assertGreaterEqual(out["seen"]["pairs"], 15)

    def test_on_the_resize_page_from_the_smallest_box_to_very_wide(self):
        """#16 Done when: no overflow, band name and count never overlap, a badge row or tab keeps
        its size, a message only makes its row taller, steps line up, from the smallest supported
        box (browser_check.SMALLEST) up to very wide, on the Resize page's frames."""
        smallest = f"{browser_check.SMALLEST[0]:g}rem"
        widest = f"{browser_check.FRAMES[-1][0]:g}rem"
        for width in (smallest, "100%", widest):
            with self.subTest(width=width):
                self.ff.load(self.base + "resize.html")
                out = self.ff.run(MEASURE, {"root": ":is(.site-resize, .site-fixed)", "width": width},
                                  f"the onboarding parts check on the Resize page at {width}")
                errors, seen = out["errors"], out["seen"]
                if self.ff.errors():
                    errors.append(f"script errors: {self.ff.errors()}")
                self.assertEqual(errors, [], "\n".join(errors))
                for what in ("badges", "messages", "showing", "bands", "labels", "steps"):
                    self.assertGreaterEqual(seen[what], 1, f"no {what} on the Resize page")
                if width == smallest:
                    self.assertGreaterEqual(seen.get("wrapped", 0), 1, "no step wraps in the smallest box")

    def test_on_the_components_page(self):
        ff = self.ff
        ff.load(self.base + "components.html")
        out = ff.run(MEASURE, {}, "the onboarding parts check")
        errors, seen = out["errors"], out["seen"]
        if ff.errors():
            errors.append(f"script errors: {ff.errors()}")
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertGreaterEqual(seen["badges"], 6)
        self.assertGreaterEqual(seen["messages"], 4)
        self.assertGreaterEqual(seen["showing"], 3)
        self.assertGreaterEqual(seen["bands"], 5)
        self.assertGreaterEqual(seen["labels"], 2)
        self.assertGreaterEqual(seen["steps"], 3)
        self.assertGreaterEqual(seen.get("wrapped", 0), 1, "no step wraps, so lining up after the number is untested")
        print(f"Onboarding parts: {seen['badges']} badges keep their size, {seen['messages']} messages "
              f"({seen['showing']} showing), {seen['bands']} bands, {seen['labels']} step labels and "
              f"{seen['steps']} step lists ({seen.get('wrapped', 0)} wrapped steps) all as specified")


if __name__ == "__main__":
    unittest.main()
