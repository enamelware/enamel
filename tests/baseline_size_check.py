# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #15, changed by #18: the real components come out at the Steam baseline, and
--en-root-size scales them together through zoom, in the device's Firefox (headless, its own temporary
profile; Steam is never touched).

tests/root_size_check.py measures the tokens; this one measures drawn
components. A frame 640px wide (narrower than 100rem, so text is at its base)
links the tokens and the components, with --en-root-size on <html> at 100%,
125% and 50%, and checks at each that:

  - a plain list row is --en-size-row tall (64px at 100%), and a row with a
    toggle, or with a button, is --en-size-row-control tall (96px);
  - rows in a list are --en-space-gap apart (12px);
  - a button is --en-size-button tall (60px) and an icon button is square at
    that size;
  - a one-line action bar is a button and its padding tall (68px);
  - the hint bar is --en-size-bar tall (60px), a glyph is 32px, and a glyph
    sits --en-space-icon (16px) from its label;
  - the toggle is 60 by 36px; tiles on a shelf are 20px apart;
  - the side menu is 360px wide with room, or as wide as a narrower space,
    and an item is 72px tall;
  - row text is 24px and hint text about 18.7px, and the focus ring 4px, in
    the page's own units at every interface size (zoom draws them bigger);
  - the root font size stays the browser's own (16px) at every interface size,
    and everything scales, the 44px touch target and the focus ring included.

    scripts/test.sh check baseline_size_check
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
from serve import Handler  # noqa: E402

TARGET = 44  # the touch target, in px

DOC = """<!doctype html><html lang="en" style="--en-root-size: {root}%"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;font-family:var(--en-font)">
<ul class="en-rows" id="rows">
  <li><button class="en-row" id="row">Driftwood</button></li>
  <li><div class="en-row" id="row-toggle">Keep screen awake <button class="en-toggle" id="toggle" aria-pressed="false" aria-label="Keep screen awake" data-focused="true"></button></div></li>
  <li><div class="en-row" id="row-button">Library <button class="en-button" id="row-btn">Rescan</button></div></li>
</ul>
<button class="en-button" id="button">Rescan</button>
<button class="en-button en-button--icon" id="icon" aria-label="More">&#8943;</button>
<header class="en-actionbar" id="actionbar"><button class="en-button">Menu</button></header>
<div class="en-hintbar" id="hintbar"><span class="en-hint" id="hint"><span class="en-glyph" id="glyph">A</span>Select</span></div>
<div class="en-shelf" id="shelf"><a class="en-tile" href="#a"><div class="en-tile__frame">A</div></a><a class="en-tile" href="#b"><div class="en-tile__frame">B</div></a></div>
<ul class="en-menu" id="menu"><li><a class="en-menu__item" id="menu-item" href="#m">Movies</a></li></ul>
<div style="width:200px"><ul class="en-menu" id="menu-narrow"><li><a class="en-menu__item" href="#m">Movies</a></li></ul></div>
</body></html>"""

MEASURE = r"""
async (args) => {
  const out = {};
  for (const root of JSON.parse(args.roots)) {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:absolute;left:0;top:0;width:640px;height:2000px;border:0';
    const loaded = new Promise(r => f.addEventListener('load', r, { once: true }));
    f.srcdoc = args.doc.replace('{root}', String(root));
    document.body.append(f);
    await loaded;
    await new Promise(r => f.contentWindow.requestAnimationFrame(() => f.contentWindow.requestAnimationFrame(r)));
    const d = f.contentDocument, w = f.contentWindow;
    const r = id => d.getElementById(id).getBoundingClientRect();
    const rows = [...d.querySelectorAll('#rows > li')].map(li => li.getBoundingClientRect());
    const tiles = [...d.querySelectorAll('#shelf .en-tile')].map(t => t.getBoundingClientRect());
    const hint = d.getElementById('hint'), label = hint.lastChild, range = d.createRange();
    range.selectNodeContents(label);
    out[root] = {
      rootPx: parseFloat(w.getComputedStyle(d.documentElement).fontSize),
      row: r('row').height, rowToggle: r('row-toggle').height, rowButton: r('row-button').height,
      rowGap: rows[1].top - rows[0].bottom,
      button: r('button').height, iconW: r('icon').width, iconH: r('icon').height,
      actionbar: r('actionbar').height,
      hintbar: r('hintbar').height, glyph: r('glyph').width, glyphGap: range.getBoundingClientRect().left - r('glyph').right,
      toggleW: r('toggle').width, toggleH: r('toggle').height,
      shelfGap: tiles[1].left - tiles[0].right,
      menu: r('menu').width, menuNarrow: r('menu-narrow').width, menuItem: r('menu-item').height,
      // Computed values are the page's own, before zoom: the text and the ring keep them.
      rowText: parseFloat(w.getComputedStyle(d.getElementById('row')).fontSize),
      hintText: parseFloat(w.getComputedStyle(hint).fontSize),
      ring: parseFloat(w.getComputedStyle(d.getElementById('toggle')).outlineWidth),
      zoom: d.documentElement.currentCSSZoom,
      target: (() => { const p = d.createElement('div'); p.style.cssText = 'width:var(--en-size-target);height:1px'; d.body.append(p); const x = p.getBoundingClientRect().width; p.remove(); return x; })(),
    };
    f.remove();
  }
  return JSON.stringify(out);
}
"""


def expected(scale):
    """What each measurement should be at a root of scale x 16px."""
    s = lambda px: px * scale
    button = s(60)
    return {
        "rootPx": 16, "row": s(64), "rowToggle": s(96), "rowButton": s(96), "rowGap": s(12),
        "button": button, "iconW": button, "iconH": button, "actionbar": button + s(8),
        "hintbar": s(60), "glyph": s(32), "glyphGap": s(16), "toggleW": s(60), "toggleH": s(36),
        "shelfGap": s(20), "menu": s(360), "menuNarrow": min(s(360), s(200)), "menuItem": s(72), "target": s(TARGET),
        # Written in the page's own units, then drawn scale times bigger by zoom.
        "rowText": 24, "hintText": 56 / 3, "ring": 4, "zoom": scale,
    }


class BaselineSizes(unittest.TestCase):
    def test_components_at_the_baseline_and_scaled(self):
        class Quiet(Handler):
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        ff = None
        try:
            ff = browser_check.Firefox(False)
            ff.load(f"http://127.0.0.1:{server.server_port}/docs/index.html")
            roots = [100, 125, 50]
            out = ff.run(MEASURE, {"roots": json.dumps(roots), "doc": DOC}, "the baseline size check")
            errors = [f"script errors: {ff.errors()}"] if ff.errors() else []
            for root in roots:
                got, want = out[str(root)], expected(root / 100)
                for key, value in want.items():
                    if abs(got[key] - value) > (0.001 if key == "zoom" else 0.6):
                        errors.append(f"at a root size of {root}%, {key} is {got[key]:.2f}px, not {value:.2f}px")
            self.assertEqual(errors, [], "\n".join(errors))
            print("Baseline sizes: " + "; ".join(
                f"{root}%: row {out[str(root)]['row']:g}, with a control {out[str(root)]['rowToggle']:g}, "
                f"button {out[str(root)]['button']:g}" for root in roots))
        finally:
            if ff:
                ff.close()
                ff.s.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
