# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #5: the live demos on the Resize page (docs/resize.html) work, run by
the same behaviour script as the Motion page. In the device's Firefox
(headless, its own temporary profile; Steam is never touched):

  - each "Open the ..." button opens its picker, modal, with focus on a row
    inside it; Escape closes it and focus returns to the button;
  - "Show the toast" shows the toast inside its own resizable frame (not a
    new toast elsewhere on the page), "Update it" changes its text, and
    "Hide it" hides it;
  - the page logs no script errors.

The full style guide check (scripts/test.sh guide) covers the page's look,
frames and focus; this covers the buttons.

    scripts/test.sh check resize_live_check
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

LIVE = r"""
async () => {
  const errors = [], wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 100 && !window.EnamelUI; i++) await wait(50);
  if (!window.EnamelUI) return JSON.stringify({ errors: ['the behaviour script never loaded'], pickers: 0 });
  const slow = 1500;  // longer than any leaving animation
  const openers = [...document.querySelectorAll('[data-open-picker]')];
  if (openers.length < 3) errors.push(`only ${openers.length} picker buttons on the page`);
  for (const b of openers) {
    const id = b.getAttribute('data-open-picker'), dlg = document.getElementById(id);
    if (!dlg) { errors.push(`${b.textContent}: no picker with id ${id}`); continue; }
    b.focus(); b.click(); await wait(100);
    if (!dlg.open || !dlg.matches(':modal')) errors.push(`${b.textContent}: the picker did not open as a modal`);
    if (!EnamelUI.picker.isOpen()) errors.push(`${b.textContent}: the behaviour script does not see a picker open`);
    const act = document.activeElement;
    if (!act || !dlg.contains(act) || !act.matches('.en-picker__row'))
      errors.push(`${b.textContent}: focus is not on a picker row`);
    (act || document.body).dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    await wait(slow);
    if (dlg.open || EnamelUI.picker.isOpen()) errors.push(`${b.textContent}: Escape did not close the picker`);
    if (document.activeElement !== b) errors.push(`${b.textContent}: focus did not return to the button`);
  }
  const toast = document.getElementById('resize-toast');
  const show = document.querySelector('[data-toast="show"]'), update = document.querySelector('[data-toast="update"]'),
        hide = document.querySelector('[data-toast="hide"]');
  if (!toast || !show || !update || !hide) {
    errors.push('the toast demo or its buttons are missing');
    return JSON.stringify({ errors, pickers: openers.length });
  }
  const frame = toast.closest('.site-resize');
  if (!frame) errors.push('the demo toast is not in a resizable frame');
  const before = document.querySelectorAll('.en-toast').length;
  toast.querySelector('.en-toast__text').textContent = '';
  show.click(); await wait(slow);
  if (toast.hidden) errors.push('Show the toast: the toast is hidden');
  if (toast.querySelector('.en-toast__text').textContent !== 'Library updated: 3 new films')
    errors.push(`Show the toast: its text is "${toast.querySelector('.en-toast__text').textContent}"`);
  if (document.querySelectorAll('.en-toast').length !== before) errors.push('Show the toast: a second toast appeared on the page');
  if (frame) {
    const r = toast.getBoundingClientRect(), f = frame.getBoundingClientRect();
    if (!r.width || r.left < f.left - 0.5 || r.right > f.right + 0.5 || r.top < f.top - 0.5 || r.bottom > f.bottom + 0.5)
      errors.push('Show the toast: the toast is not inside its frame');
  }
  update.click(); await wait(100);
  if (toast.querySelector('.en-toast__text').textContent !== 'Library updated: 4 new films')
    errors.push(`Update it: the text is "${toast.querySelector('.en-toast__text').textContent}"`);
  hide.click(); await wait(slow);
  if (!toast.hidden) errors.push('Hide it: the toast is still showing');
  return JSON.stringify({ errors, pickers: openers.length });
}
"""


class ResizePageLiveDemos(unittest.TestCase):
    def test_pickers_and_toast_work(self):
        class Quiet(Handler):
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        ff = None
        try:
            ff = browser_check.Firefox(False)
            ff.load(f"http://127.0.0.1:{server.server_port}/docs/resize.html")
            out = ff.run(LIVE, {}, "the Resize page live demo check")
            errors = list(out["errors"])
            if ff.errors():
                errors.append(f"script errors: {ff.errors()}")
            self.assertEqual(errors, [], "\n".join(errors))
            print(f"Resize page: {out['pickers']} live pickers open, close with Escape and return focus; "
                  "the toast shows in its frame, updates and hides")
        finally:
            if ff:
                ff.close()
                ff.s.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
