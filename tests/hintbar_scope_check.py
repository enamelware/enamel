# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #9: the picker's layer and the toast follow the hint bar when an app
removes, adds or moves it, not only when it wraps or is hidden. In the
device's Firefox (headless, its own temporary profile; Steam is never
touched), in a frame the size of the smallest supported box (20rem by
15rem), with Select and Cancel on two lines:

  - with the bar showing, the toast's bottom and the picker's layer meet its
    top (and the bar really is taller than one bar, so this tells the two
    apart);
  - with the bar removed from the page, both go back to the one-bar gap
    (--en-size-bar) above the bottom, as chosen on #9;
  - a new hint bar added later (never seen before) is found, and both stop
    at its top;
  - when that bar is moved into another element, the toast in <body> goes
    back to the one-bar gap, and a picker in the bar's new parent stops at
    its top;
  - #18: with the interface size at 125% (zoom), both still stop at the
    bar's top;
  - the frame logs no script errors.

tools/browser_check.py covers the bar wrapping, changing height and being
hidden; this covers removing, adding and moving it, and another interface size.

    scripts/test.sh check hintbar_scope_check
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

SCOPE = r"""
async (args) => {
  const errors = [], fail = m => errors.push(m), out = { errors };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const blank = document.createElement('iframe');
  const load = (f, doc) => { const p = new Promise(r => f.addEventListener('load', r, { once: true }));
                             f.srcdoc = doc; document.body.appendChild(f); return p; };
  await load(blank, '<!doctype html><html><body></body></html>');
  const rootPx = parseFloat(blank.contentWindow.getComputedStyle(blank.contentDocument.documentElement).fontSize);
  blank.remove();
  const W = Math.round(20 * rootPx), H = Math.round(15 * rootPx);
  const f = document.createElement('iframe');
  f.style.cssText = `position:absolute;left:0;top:0;width:${W}px;height:${H}px;border:0`;
  await load(f, args.doc);
  const w = f.contentWindow, d = f.contentDocument, K = w.EnamelUI;
  if (!K) { fail('the behaviour script did not load'); return JSON.stringify(out); }
  const settle = () => new Promise(r => w.requestAnimationFrame(() => w.requestAnimationFrame(r)));
  const finish = () => d.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
  const rect = el => el.getBoundingClientRect();
  const near = (a, b) => Math.abs(a - b) <= 1;
  const probe = d.createElement('div'); probe.style.height = 'var(--en-size-bar)'; d.body.appendChild(probe);
  const oneBar = rect(probe).height; probe.remove();
  const gap = H - oneBar;
  const lines = bar => new Set([...bar.children].map(e => { const r = rect(e); return Math.round((r.top + r.bottom) / 2); })).size;
  const layerBottom = async dlg => {
    K.picker.open(dlg, d.querySelector('.en-button')); finish(); await wait(20);
    const b = rect(dlg).bottom;
    K.picker.close(); finish(); await wait(20);
    if (dlg.open) dlg.close();
    return b;
  };

  let bar = d.querySelector('.en-hintbar');
  bar.lastElementChild.lastChild.textContent = 'Cancel';
  await settle();
  out.lines = lines(bar); out.barPx = Math.round(rect(bar).height); out.oneBar = Math.round(oneBar);
  if (out.lines !== 2) fail(`Select and Cancel are on ${out.lines} line(s) in the smallest box, not two`);
  if (!(rect(bar).height > oneBar + 1)) fail('the two-line hint bar is no taller than one bar, so the check cannot tell them apart');
  const t = K.toast.show('Saved', { time: 60000 }); finish(); await wait(20);
  const dlg = d.getElementById('short');
  if (!near(rect(t).bottom, rect(bar).top)) fail(`showing: the toast's bottom is at ${rect(t).bottom}, not at the bar's top ${rect(bar).top}`);
  let b = await layerBottom(dlg);
  if (!near(b, rect(bar).top)) fail(`showing: the picker's layer stops at ${b}, not at the bar's top ${rect(bar).top}`);

  // Removed: the one-bar gap, as before #9.
  const spare = bar.cloneNode(true);
  bar.remove(); await settle(); await settle();
  if (!near(rect(t).bottom, gap)) fail(`removed: the toast's bottom is at ${rect(t).bottom}, not one bar above the bottom at ${gap}`);
  b = await layerBottom(dlg);
  if (!near(b, gap)) fail(`removed: the picker's layer stops at ${b}, not one bar above the bottom at ${gap}`);

  // A new hint bar, never seen before, added later.
  bar = spare; d.body.appendChild(bar); await settle(); await settle();
  if (!near(rect(t).bottom, rect(bar).top)) fail(`added: the toast's bottom is at ${rect(t).bottom}, not at the new bar's top ${rect(bar).top}`);
  b = await layerBottom(dlg);
  if (!near(b, rect(bar).top)) fail(`added: the picker's layer stops at ${b}, not at the new bar's top ${rect(bar).top}`);

  // Moved into another element: <body> loses it; the bar's new parent has it.
  const shell = d.createElement('div');
  const inner = dlg.cloneNode(true); inner.id = 'inner';
  shell.appendChild(inner); d.body.insertBefore(shell, t);
  shell.appendChild(bar); await settle(); await settle();
  if (!near(rect(t).bottom, gap)) fail(`moved: the toast in <body> is at ${rect(t).bottom}, not back at the one-bar gap ${gap}`);
  b = await layerBottom(inner);
  if (!near(b, rect(bar).top)) fail(`moved: the picker beside the bar stops at ${b}, not at the bar's top ${rect(bar).top}`);

  // #18: at another interface size (zoom), both still meet the bar's top.
  d.body.appendChild(bar); await settle(); await settle();
  d.documentElement.style.setProperty('--en-root-size', '125%'); await settle(); await settle();
  out.zoom = d.documentElement.currentCSSZoom;
  if (out.zoom !== 1.25) fail(`the interface size of 125% gives a zoom of ${out.zoom}`);
  if (!near(rect(t).bottom, rect(bar).top)) fail(`at 125%: the toast's bottom is at ${rect(t).bottom}, not at the bar's top ${rect(bar).top}`);
  b = await layerBottom(dlg);
  if (!near(b, rect(bar).top)) fail(`at 125%: the picker's layer stops at ${b}, not at the bar's top ${rect(bar).top}`);
  K.toast.hide();
  return JSON.stringify(out);
}
"""


class HintBarScope(unittest.TestCase):
    def test_removed_added_and_moved(self):
        class Quiet(Handler):
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        ff = None
        try:
            ff = browser_check.Firefox(False)
            ff.load(f"http://127.0.0.1:{server.server_port}/docs/motion.html")
            out = ff.run(SCOPE, {"doc": browser_check.FRAME_DOC}, "the hint bar removed, added and moved check")
            errors = list(out["errors"])
            if ff.errors():
                errors.append(f"script errors: {ff.errors()}")
            self.assertEqual(errors, [], "\n".join(errors))
            print(f"Hint bar on {out['lines']} lines ({out['barPx']}px, one bar is {out['oneBar']}px) at 20rem by 15rem: "
                  "the picker's layer and the toast stop at its top; removed, they keep the one-bar gap; "
                  "a bar added later and a bar moved to another parent are followed; at 125% they still meet it")
        finally:
            if ff:
                ff.close()
                ff.s.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
