"""Check motion in the device's own browser. Used by check_guide.py.

Starts the Firefox on this device (the flatpak) headless, with a fresh
profile in a temporary folder and no network services, and drives it over
WebDriver BiDi with the small websocket client in browser_session.py. It is started
twice: once as a device with no motion preference, and once as a device
that asks for reduced motion. Every style guide page is loaded in four modes:

  full              device normal, no attribute
  reduced           device normal, data-en-motion="reduced" on <html>
  device-reduced    device asks for reduced motion, no attribute
  forced-full       device asks for reduced motion, data-en-motion="full"

and these are checked:
  - the page loads without script errors;
  - every component example that can take focus shows it, and once focus
    has arrived it looks exactly the same in every mode (colours, ring,
    fill, bar); only the tile's growth differs;
  - in the reduced modes no component runs an animation, no component or
    pseudo-element has a transform, and the only transitions are colour
    fades;
  - in the full modes a focused tile's ring breathes and stops between four
    and six seconds after focus arrives, and starts again when focus returns.
Focus is given with data-focused="true". A headless window on this device
never receives keyboard focus, so :focus-visible cannot be produced here;
check_guide.py checks instead that every focus rule lists both.

It also runs the picker and toast behaviour of components/enamel-components.js
on the Motion page, in full, reduced and device-reduced motion: focus stays
inside the picker, Up and Down stop at the ends, keys never reach the app
while it is open and do again after, Escape, the Cancel row and cancel()
return focus to the opener, Enter and a tap select, a confirm focuses Cancel
first and a choice list the current choice; one toast at a time, never
focused, never blocking, polite, its timer restarting on update, leaving by
fading out in place; in reduced motion both simply appear and disappear.

Then, once in each browser (full motion, and a device asking for reduced
motion), and once more in a browser whose font size is made larger
(LARGE_FONT_PX instead of the normal 16), it puts the components in frames
of several sizes (FRAMES, in rem, from the smallest supported box to very
wide) and checks that: the picker stays between a quarter and two thirds of its
dialog's space, as narrow as it can be with short rows and as wide as it can
be with a long row, which wraps; the toast hugs a short text, grows to its
limit with a long one and wraps it, sits at the bottom right just above the
hint bar, and fades out in place (or disappears at once in reduced motion);
all of this with a hint bar on one line and again on two lines (Select and
Cancel, with more hints in wider frames until it wraps), where the picker's
layer meets the top of the hint bar, neither the layer nor the panel nor the
toast runs over it, and the toast follows the bar when it changes height;
with the hint bar hidden, the picker's layer and the toast keep the old
one-bar gap (--en-size-bar) above the bottom;
the action bar is full width, never overflows, wraps its buttons onto more
lines and gets taller instead of cutting a label, and every button keeps its
full name; focused rows and buttons stay inside the frame, and nothing
scrolls sideways;
every other component (hint bar, tabs, rows, toggle, shelf and tiles,
buttons, progress, side menu) stays inside the frame without sideways
scrolling, nothing overlaps, no label is cut off, the hint bar wraps and
gets taller instead of cutting off a hint, tiles take their width from the
shelf, and every focus ring (a tile's at its thickest and largest, scrolled
into view in its shelf) is fully visible, never clipped by the shelf;
the smallest supported box (20rem by 15rem): a list row with its title and
a focused toggle, and the hint bar with two hints on one line, fit without
overlapping or scrolling, every focus ring visible; the smallest box the
content actually needs is measured and reported; below it the page scrolls;
on the Resize page (docs/resize.html), each fixed frame is as wide as its
label, which names a width only, and no frame there, fixed or resizable
(resizable by hand, and checked again at the smallest box's width and at
the whole column), scrolls sideways, has anything overlapping or cut off,
a picker or toast over the hint bar, or a focus ring cut off, and the
narrowest frame also shows the picker and the toast above a hint bar with
Select and Cancel on two lines;
with the larger font, text is larger and all of the above still holds.
These frames are inside the page, so the check does not depend on the
browser window's own size.

Every wait on Firefox has a limit (LOAD_LIMIT, RUN_LIMIT): a page that never
loads or a script that never finishes fails the check, naming which one,
instead of leaving it waiting forever.

Screenshots of every page in full and in reduced motion are saved if a
folder is given. Standard library only.
"""
import base64, json, os, shutil, socket, subprocess, tempfile, time

from browser_session import Session

FIREFOX = ["flatpak", "run", "--command=firefox", "org.mozilla.firefox"]
PREFS = """
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("app.normandy.enabled", false);
user_pref("app.update.disabledForTesting", true);
user_pref("messaging-system.rsexperimentloader.enabled", false);
user_pref("services.settings.server", "http://127.0.0.1:1/");
user_pref("network.connectivity-service.enabled", false);
user_pref("network.captive-portal-service.enabled", false);
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("browser.safebrowsing.downloads.enabled", false);
user_pref("extensions.update.enabled", false);
user_pref("browser.region.network.url", "");
user_pref("network.dns.disablePrefetch", true);
user_pref("network.prefetch-next", false);
"""
COLOUR_PROPS = {"background-color", "color", "outline-color", "opacity", "border-color",
                "border-top-color", "border-right-color", "border-bottom-color", "border-left-color"}

# Run in the page: focus every focusable component example in turn and report
# what is moving and how focus looks once it has arrived.
PROBE = r"""
async (args) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const en = el => [...el.classList].some(c => c.startsWith('en-'));
  const pseudos = [null, '::before', '::after'];
  const look = el => pseudos.map(p => { const s = getComputedStyle(el, p);
    return [s.backgroundColor, s.color, s.outlineStyle, s.outlineWidth, s.outlineColor, s.outlineOffset,
            s.boxShadow, s.opacity, s.top, s.bottom, s.marginLeft].join(' ; '); }).join(' | ');
  const motionNow = () => {
    const anims = [], trans = [], transforms = [];
    for (const a of document.getAnimations()) {
      const t = a.effect && a.effect.target;
      if (!t || !en(t) || a.playState === 'finished') continue;
      const where = t.className + (a.effect.pseudoElement || '');
      if (a instanceof CSSAnimation) anims.push(where + ' ' + a.animationName);
      else if (a instanceof CSSTransition) trans.push([where, a.transitionProperty]);
      else anims.push(where + ' (script animation)');
    }
    for (const el of document.querySelectorAll('*')) {
      if (!en(el)) continue;
      for (const p of pseudos) {
        const s = getComputedStyle(el, p);
        for (const k of ['transform', 'scale', 'translate', 'rotate'])
          if (s[k] && s[k] !== 'none') transforms.push(el.className + (p || '') + ' ' + k + ': ' + s[k]);
      }
    }
    return { anims, trans, transforms };
  };
  if (args.attr) document.documentElement.setAttribute('data-en-motion', args.attr);
  else document.documentElement.removeAttribute('data-en-motion');
  await frame();
  const out = { reducedMatch: matchMedia('(prefers-reduced-motion: reduce)').matches, items: [], during: [],
                pulse: [], restart: [] };
  // An example held pressed is left out: pressed rightly wins over focus.
  const sel = '.en-tile, .en-row, .en-toggle, .en-button:not(:disabled, [data-pressed="true"]), .en-menu__item';
  const all = [...document.querySelectorAll(sel)].filter(el => !el.closest('[data-en-motion]:not(html)'));
  const was = all.map(el => el.getAttribute('data-focused'));
  all.forEach(el => el.removeAttribute('data-focused'));
  await wait(500);
  document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
  await frame();
  for (const [i, el] of all.entries()) {
    const before = look(el);
    el.setAttribute('data-focused', 'true');
    await frame();
    const m = motionNow();
    out.during.push(m);
    if (el.classList.contains('en-tile')) {
      const p = el.getAnimations({ subtree: true }).find(a => a.animationName === 'en-focus-pulse');
      out.pulse.push(p ? p.effect.getComputedTiming().endTime : null);
      if (p) {
        await wait(300);
        el.removeAttribute('data-focused'); await frame();
        el.setAttribute('data-focused', 'true'); await frame();
        const q = el.getAnimations({ subtree: true }).find(a => a.animationName === 'en-focus-pulse');
        out.restart.push(q ? q.currentTime : null);
      }
    }
    // Settle every motion at once instead of waiting it out: this example's
    // focus and the previous one's leaving, which the snapshot above caught.
    document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
    await frame();
    out.items.push({ what: el.className, before, after: look(el),
                     transform: getComputedStyle(el).transform });
    el.removeAttribute('data-focused');
  }
  all.forEach((el, i) => { if (was[i] !== null) el.setAttribute('data-focused', was[i]); });
  return JSON.stringify(out);
}
"""


BEHAVIOUR = r"""
async (args) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  if (args.attr) document.documentElement.setAttribute('data-en-motion', args.attr);
  const K = window.EnamelUI, out = { errors: [] }, fail = m => out.errors.push(m);
  if (!K) return JSON.stringify({ errors: ['window.EnamelUI is missing'] });
  let appKeys = 0;
  const app = () => { appKeys++; };
  window.addEventListener('keydown', app); document.addEventListener('keydown', app);
  const key = k => document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true }));
  const dlg = document.getElementById('motion-actions');
  const opener = document.querySelector('[data-open-picker="motion-actions"]');
  const rows = [...dlg.querySelectorAll('.en-picker__row')];
  const focused = () => rows.filter(r => r.getAttribute('data-focused') === 'true');
  const once = (type) => new Promise(r => dlg.addEventListener(type, e => r(e), { once: true }));
  const leaveTime = 700;

  opener.focus();
  K.picker.open(dlg, opener);
  if (!K.picker.isOpen()) fail('the picker did not open');
  if (focused().length !== 1 || focused()[0] !== rows[0]) fail('the first row is not focused on open');
  if (!dlg.contains(document.activeElement)) fail('focus is not inside the picker');
  out.fill = getComputedStyle(rows[0]).backgroundColor;
  out.panelAnim = getComputedStyle(dlg.querySelector('.en-picker')).animationName;
  for (let i = 0; i < 10; i++) key('ArrowDown');
  if (focused()[0] !== rows[rows.length - 1]) fail('Down does not stop at the last row');
  for (let i = 0; i < 10; i++) key('ArrowUp');
  if (focused()[0] !== rows[0]) fail('Up does not stop at the first row');
  key('Tab');
  if (!dlg.contains(document.activeElement)) fail('Tab took focus out of the picker');
  opener.focus();
  if (!dlg.contains(document.activeElement)) fail('focus could be moved to the page behind');
  if (focused().length !== 1) fail('more than one row shows focus');
  if (appKeys) fail(appKeys + ' key presses reached the app while the picker was open');
  let ev = once('en-cancel');
  key('Escape');
  if (K.picker.isOpen()) fail('Escape did not close the picker');
  if (document.activeElement !== opener) fail('Escape did not return focus to the opener');
  out.openRightAfterClose = dlg.open;
  out.closingRightAfterClose = dlg.getAttribute('data-closing') === 'true';
  await Promise.race([ev, wait(50)]).then(e => { if (!e) fail('no en-cancel event'); });
  await wait(leaveTime);
  if (dlg.open) fail('the dialog is still open after leaving');

  K.picker.open(dlg, opener); key('ArrowDown');
  ev = once('en-select'); key('Enter');
  await Promise.race([ev, wait(50)]).then(e => { if (!e || e.detail.value !== rows[1].value) fail('Enter did not select the focused row'); });
  if (document.activeElement !== opener) fail('selecting did not return focus to the opener');
  await wait(leaveTime);

  K.picker.open(dlg, opener);
  ev = once('en-select'); rows[2].click();
  await Promise.race([ev, wait(50)]).then(e => { if (!e || e.detail.value !== rows[2].value) fail('a tap did not select the row'); });
  await wait(leaveTime);

  K.picker.open(dlg, opener); K.picker.down(); K.picker.down(); K.picker.down(); K.picker.down();
  ev = once('en-cancel'); K.picker.select();
  await Promise.race([ev, wait(50)]).then(e => { if (!e) fail('choosing the Cancel row did not cancel'); });
  await wait(leaveTime);

  const conf = document.getElementById('motion-confirm');
  K.picker.open(conf, opener);
  if (!document.activeElement.classList.contains('en-picker__cancel')) fail('the confirm does not focus Cancel first');
  K.picker.cancel(); await wait(leaveTime);
  const choice = document.getElementById('motion-choices');
  K.picker.open(choice, opener);
  if (document.activeElement.getAttribute('aria-current') !== 'true') fail('the choice list does not focus the current choice first');
  K.picker.cancel();
  if (document.activeElement !== opener) fail('cancel() did not return focus to the opener');
  await wait(leaveTime);
  appKeys = 0; key('ArrowDown');
  if (!appKeys) fail('keys do not reach the app after the picker closed');

  const before = document.activeElement;
  const live = () => [...document.querySelectorAll('.en-toast')].filter(t => !t.hidden && !t.closest('.site-stage'));
  const t1 = K.toast.show('first', { time: 800 });
  const t2 = K.toast.show('second', { time: 800 });
  if (live().length !== 1 || t2.querySelector('.en-toast__text').textContent !== 'second') fail('a second toast did not replace the first');
  if (document.activeElement !== before) fail('the toast took focus');
  if (getComputedStyle(t2).pointerEvents !== 'none') fail('the toast blocks taps on what is under it');
  if (t2.getAttribute('role') !== 'status' || t2.getAttribute('aria-live') !== 'polite') fail('the toast is not a polite status');
  out.toastAnim = getComputedStyle(t2).animationName;
  await wait(500); K.toast.update('third'); await wait(500);
  if (t2.hidden || t2.getAttribute('data-closing') === 'true') fail('the timer did not restart on update');
  if (t2.querySelector('.en-toast__text').textContent !== 'third') fail('update did not change the text');
  await wait(900);
  if (!t2.hidden) fail('the toast did not leave after its time');
  K.toast.show('again', { time: 800 }); K.toast.hide();
  out.toastHiddenRightAfterHide = t2.hidden;
  out.toastClosingRightAfterHide = t2.getAttribute('data-closing') === 'true';
  out.toastLeaveAnim = getComputedStyle(t2).animationName;
  await wait(150);
  out.toastLeaveMoved = !t2.hidden && new DOMMatrix(getComputedStyle(t2).transform).m41 !== 0;
  await wait(350);
  if (!t2.hidden) fail('hide() did not hide the toast');
  window.removeEventListener('keydown', app); document.removeEventListener('keydown', app);
  return JSON.stringify(out);
}
"""


# Frame sizes for the responsive check, in rem, from the smallest supported box
# (20rem by 15rem) to very wide. Each is a frame inside the page, so the check
# does not depend on the browser window's own size; in px they follow the
# browser's font size (320 by 240 up to 2400 by 1200 at the normal 16px).
FRAMES = [(20, 15), (35, 26.25), (56.25, 40), (87.5, 56.25), (150, 75)]
SMALLEST = (20, 15)    # the smallest supported box, DESIGN.md Part 2
LARGE_FONT_PX = 32     # the larger browser font size for the last run: 200%

# The picker, toast and action bar, alone in a frame of each size. The frame
# loads the real stylesheets and behaviour script; nothing here sets a size.
FRAME_DOC = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;font-family:var(--en-font)">
<header class="en-actionbar">
  <button class="en-button">Sort by date added</button>
  <button class="en-button">Select several videos</button>
  <button class="en-button">Rescan every library folder</button>
  <button class="en-button en-button--icon" aria-label="Search"><svg class="en-icon" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/></svg></button>
</header>
<dialog class="en-dialog" id="short"><div class="en-picker"><div class="en-picker__rows">
  <button class="en-picker__row" value="play"><span>Play</span></button>
  <button class="en-picker__row en-picker__cancel"><span>Cancel</span></button>
</div></div></dialog>
<dialog class="en-dialog" id="long"><div class="en-picker"><div class="en-picker__rows">
  <button class="en-picker__row" value="long"><span>Move this video and every other video in the same folder to a different library folder on another drive, keeping their progress and their place in every list</span><span class="en-picker__desc">Nothing is copied twice, and the old folder is left empty</span></button>
  <button class="en-picker__row en-picker__cancel"><span>Cancel</span></button>
</div></div></dialog>
<footer class="en-hintbar" style="position:fixed;left:0;right:0;bottom:0"><span class="en-hint"><span class="en-glyph">A</span>Select</span><span class="en-hint"><span class="en-glyph">B</span>Back</span></footer>
<script src="../components/enamel-components.js"></script>
</body></html>"""

# Shared helpers for the frame checks below (RESPONSIVE, COMPONENTS and
# SMALLEST_BOX), run inside the page: the browser's own rem, opening a frame,
# and measuring boxes and focus.
FRAME_HELPERS = r"""
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const open = async (doc, W, H) => {
    const f = document.createElement('iframe');
    f.style.cssText = `position:absolute;left:0;top:0;width:${W}px;height:${H}px;border:0`;
    const loaded = new Promise(r => f.addEventListener('load', r, { once: true }));
    f.srcdoc = doc;
    document.body.appendChild(f);
    await loaded;
    return f;
  };
  // The browser's own font size: what 1rem is in a page that does not change it.
  const blank = await open('<!doctype html><html><body></body></html>', 10, 10);
  const rootPx = parseFloat(blank.contentWindow.getComputedStyle(blank.contentDocument.documentElement).fontSize);
  blank.remove();
  // Things on one line share a vertical centre (a shoulder glyph is taller).
  const lineCount = els => new Set(els.map(e => { const r = e.getBoundingClientRect(); return Math.round((r.top + r.bottom) / 2); })).size;
  const box = r => ({ left: r.left, top: r.top, right: r.right, bottom: r.bottom });
  const grow = (r, by) => ({ left: r.left - by, top: r.top - by, right: r.right + by, bottom: r.bottom + by });
  const inside = (a, b) => a.left >= b.left - 0.5 && a.top >= b.top - 0.5 && a.right <= b.right + 0.5 && a.bottom <= b.bottom + 0.5;
  const overlap = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 &&
                            Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5;
  const show = r => `${Math.round(r.left)},${Math.round(r.top)} to ${Math.round(r.right)},${Math.round(r.bottom)}`;
  // The part of the page visible through every ancestor of el that clips, up
  // to and including upTo when given (a frame inside a page).
  const clipOf = (w, el, upTo) => {
    let c = { left: -1e9, top: -1e9, right: 1e9, bottom: 1e9 };
    for (let a = el.parentElement; a && a !== a.ownerDocument.documentElement && a !== a.ownerDocument.body; a = a.parentElement) {
      const cs = w.getComputedStyle(a);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') {
        const r = a.getBoundingClientRect();
        const left = r.left + a.clientLeft, top = r.top + a.clientTop;
        c = { left: Math.max(c.left, left), top: Math.max(c.top, top),
              right: Math.min(c.right, left + a.clientWidth), bottom: Math.min(c.bottom, top + a.clientHeight) };
      }
      if (a === upTo) break;
    }
    return c;
  };
  // Where an element's focus shows: its outline (a tile's ring on ::after, at
  // its thickest), or its own box for a fill.
  const focusBox = (w, el) => {
    const tile = el.classList.contains('en-tile');
    const cs = w.getComputedStyle(el, tile ? '::after' : null);
    const r = box(el.getBoundingClientRect());
    if (cs.outlineStyle === 'none' || cs.outlineColor === 'rgba(0, 0, 0, 0)') return r;
    const probe = el.ownerDocument.createElement('div');
    probe.style.width = 'var(--en-focus-ring-start)';
    el.ownerDocument.body.appendChild(probe);
    const start = probe.getBoundingClientRect().width; probe.remove();
    const width = tile ? Math.max(start, parseFloat(cs.outlineWidth)) : parseFloat(cs.outlineWidth);
    const scale = tile ? new w.DOMMatrix(w.getComputedStyle(el).transform).a : 1;
    return grow(r, (parseFloat(cs.outlineOffset) + width) * scale);
  };
  const finish = d => d.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
  // Two animation frames of window w: the behaviour script hears of a hint
  // bar's new height before the next paint, so by then it has passed it on.
  const settle = w => new Promise(r => w.requestAnimationFrame(() => w.requestAnimationFrame(r)));
  // Inside root, a frame (in window w) whose box frameBox() gives: every
  // component stays inside it (tiles may scroll along their shelf); nothing in
  // a bar, list or set overlaps, spills out or is cut off; no row is shorter
  // than its minimum or has its title under its toggle; a hint bar that wraps
  // gets taller instead of cutting off a hint, no open picker (its layer or
  // its panel) or toast runs over it, and the layer and toast that share its
  // parent stop exactly at its top, however tall it is; and every focus ring or fill,
  // focused in turn and scrolled into view, is fully visible, clipped by
  // nothing up to and including root. Each problem goes to fail.
  const fitsFrame = async (w, root, frameBox, fail) => {
    const d = root.ownerDocument, frame = frameBox();
    // Where el sits in the layout: a focused face that has risen (a pure
    // translation) is still in its place, so it doesn't spill out of its set.
    const laidOut = el => {
      const r = el.getBoundingClientRect(), t = w.getComputedStyle(el).transform;
      if (t === 'none') return r;
      const m = new w.DOMMatrix(t);
      return m.m11 === 1 && m.m22 === 1 && !m.m12 && !m.m21 ? new w.DOMRect(r.x - m.m41, r.y - m.m42, r.width, r.height) : r;
    };
    for (const el of root.querySelectorAll('[class*="en-"]')) {
      const shelf = el.closest('.en-shelf');
      if (shelf && el !== shelf) continue;  // tiles scroll along their shelf
      const r = el.getBoundingClientRect();
      if (r.width && !inside(box(r), frame)) fail(`${el.className} reaches outside the frame (${show(r)})`);
    }
    const sets = new Set(root.querySelectorAll('[data-set], .en-tabs, .en-rows, .en-menu, .en-hintbar, .en-actionbar'));
    for (const set of sets) {
      const what = set.dataset.set || set.className.split(' ')[0];
      const items = [...set.children].map(c => c.matches('li') ? c.firstElementChild : c);
      for (let i = 0; i < items.length; i++)
        for (let j = i + 1; j < items.length; j++)
          if (overlap(items[i].getBoundingClientRect(), items[j].getBoundingClientRect()))
            fail(`in the ${what}, "${items[i].textContent.trim()}" and "${items[j].textContent.trim()}" overlap`);
      for (const it of items) {
        if (it.scrollWidth > it.clientWidth + 0.5) fail(`in the ${what}, "${it.textContent.trim()}" is cut off`);
        if (!inside(box(laidOut(it)), box(set.getBoundingClientRect())))
          fail(`in the ${what}, "${it.textContent.trim()}" spills out of its bar or list`);
      }
    }
    for (const row of root.querySelectorAll('.en-row')) {
      if (row.getBoundingClientRect().height < parseFloat(w.getComputedStyle(row).minHeight) - 0.5) fail('a row is shorter than its minimum');
      const t = row.querySelector('.en-toggle');
      if (!t) continue;
      const text = [...row.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
      const rg = d.createRange(); rg.selectNodeContents(text);
      for (const tr of rg.getClientRects())
        if (tr.width && overlap(tr, t.getBoundingClientRect())) fail('a row title runs under its toggle');
    }
    for (const bar of root.querySelectorAll('.en-hintbar')) {
      const top = bar.getBoundingClientRect().top, barLines = lineCount([...bar.children]);
      for (const over of root.querySelectorAll('.en-dialog[open], .en-dialog[open] .en-picker, .en-toast:not([hidden])')) {
        // Only the part of it that shows: a picker taller than its dialog scrolls inside it.
        const r = over.getBoundingClientRect(), c = clipOf(w, over, root);
        const seen = { left: Math.max(r.left, c.left), top: Math.max(r.top, c.top),
                       right: Math.min(r.right, c.right), bottom: Math.min(r.bottom, c.bottom) };
        if (overlap(seen, bar.getBoundingClientRect()))
          fail(`the ${over.className} runs over the hint bar (on ${barLines} line(s))`);
        if (over.matches('.en-dialog, .en-toast') && over.parentElement === bar.parentElement && Math.abs(r.bottom - top) > 1)
          fail(`the ${over.className} stops at ${Math.round(r.bottom)}, not at the top of the hint bar (on ${barLines} line(s)) at ${Math.round(top)}`);
      }
      const lines = lineCount([...bar.children]), minH = parseFloat(w.getComputedStyle(bar).minHeight);
      if (lines > 1 && !(bar.getBoundingClientRect().height > minH + 1)) fail('the hint bar wrapped but did not get taller');
      if (lines === 1 && Math.abs(bar.getBoundingClientRect().height - minH) > 1) fail('the hint bar is taller than its minimum on one line');
      if (bar.scrollWidth > bar.clientWidth) fail('the hint bar overflows sideways');
    }
    const focusable = [...root.querySelectorAll('.en-tile, .en-row, .en-toggle, .en-button:not(:disabled), .en-menu__item, .en-picker__row')];
    for (const el of focusable) {
      const was = el.getAttribute('data-focused');
      el.setAttribute('data-focused', 'true');
      el.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      finish(d); await wait(10);
      const fb = focusBox(w, el), clip = clipOf(w, el, root), fr = frameBox();
      const name = `${el.className.split(' ')[0]} "${(el.getAttribute('aria-label') || el.textContent).trim().slice(0, 30)}"`;
      if (!inside(fb, clip)) fail(`the focus of ${name} is cut off (${show(fb)} in ${show(clip)})`);
      if (!inside(fb, fr)) fail(`the focus of ${name} reaches outside the frame (${show(fb)})`);
      if (was === null) el.removeAttribute('data-focused'); else el.setAttribute('data-focused', was);
      finish(d);
    }
  };
"""

RESPONSIVE = r"""
async (args) => {
""" + FRAME_HELPERS + r"""
  const frames = JSON.parse(args.frames), out = { errors: [], sizes: [] };
  const near = (a, b) => Math.abs(a - b) <= 1;
  const lines = node => {
    const r = document.createRange(); r.selectNodeContents(node);
    return new Set([...r.getClientRects()].map(x => Math.round(x.top))).size;
  };
  // More hints, added one at a time until the hint bar wraps onto two lines.
  const MORE = ['Options', 'Details', 'Remove', 'Rename', 'Search', 'Sort', 'Filter', 'Refresh', 'Play', 'Resume',
                'Info', 'Movies', 'TV shows', 'Settings', 'Library', 'Folders', 'Scan', 'Help', 'Home', 'Queue'];
  for (const twoLines of [false, true])
  for (const [Wr, Hr] of frames) {
    const W = Math.round(Wr * rootPx), H = Math.round(Hr * rootPx);
    const f = await open(args.doc, W, H);
    const w = f.contentWindow, d = f.contentDocument, K = w.EnamelUI;
    const at = `${Wr}x${Hr}rem, hint bar on ${twoLines ? 'two lines' : 'one line'}`;
    const fail = m => out.errors.push(`${at}: ${m}`);
    // The hint bar: Select and Back on one line; or Select and Cancel (two
    // lines in the smallest box), with more hints until it wraps onto two lines.
    const hb = d.querySelector('.en-hintbar');
    const hintsAt = () => lineCount([...hb.children]);
    const addHint = name => { const h = hb.lastElementChild.cloneNode(true); h.lastChild.textContent = name; hb.appendChild(h); };
    const oneLineBar = hb.innerHTML;
    if (twoLines) {
      hb.lastElementChild.lastChild.textContent = 'Cancel';
      for (const name of MORE) { if (hintsAt() >= 2) break; addHint(name); }
      if (hintsAt() !== 2) fail(`the hint bar is on ${hintsAt()} line(s), not two`);
      if (Wr === frames[0][0] && hb.children.length !== 2) fail('Select and Cancel do not wrap onto two lines in the smallest box');
    } else if (hintsAt() !== 1) fail(`the hint bar is on ${hintsAt()} lines, not one`);
    await settle(w);
    const rect = el => el.getBoundingClientRect();
    const finish = () => d.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
    const range = (el, what) => { const r = rect(el);
      if (r.left < -0.5 || r.right > W + 0.5) fail(`${what} reaches outside the frame (${Math.round(r.left)} to ${Math.round(r.right)})`); };
    if (!K) { fail('the behaviour script did not load'); f.remove(); continue; }
    const remPx = parseFloat(w.getComputedStyle(d.documentElement).fontSize);
    const probe = d.createElement('div'); probe.style.width = 'var(--en-space-gutter)'; d.body.appendChild(probe);
    const gutter = probe.getBoundingClientRect().width;
    probe.style.height = 'var(--en-size-bar)'; const oneBar = probe.getBoundingClientRect().height; probe.remove();
    const size = { at: `${Wr}x${Hr}rem`, bar: twoLines ? 2 : 1, hintLines: hintsAt(), hintPx: Math.round(hb.getBoundingClientRect().height) };

    // The page's width: the frame's, less a scrollbar when the content is
    // taller than the frame (an action bar on several lines in the smallest box).
    const Wp = d.documentElement.clientWidth;
    if (W - Wp > 20) fail(`the page is only ${Wp}px wide in a ${W}px frame`);
    // Action bar: full width, never overflowing, labels whole, taller when it wraps.
    const bar = d.querySelector('.en-actionbar'), btns = [...bar.querySelectorAll('.en-button')];
    if (!near(rect(bar).width, Wp)) fail(`the action bar is ${rect(bar).width}px wide, not the page's ${Wp}px`);
    if (bar.scrollWidth > bar.clientWidth) fail('the action bar overflows sideways');
    // Buttons on one line share a vertical centre (an icon button may be taller).
    const tops = new Set(btns.map(b => Math.round((rect(b).top + rect(b).bottom) / 2)));
    size.barLines = tops.size;
    const oneLine = parseFloat(w.getComputedStyle(bar).minHeight);
    if (tops.size > 1 && !(rect(bar).height > oneLine + 1)) fail('the action bar wrapped its buttons but did not get taller');
    if (tops.size === 1 && !near(rect(bar).height, oneLine)) fail(`the action bar is ${rect(bar).height}px tall on one line`);
    for (const b of btns) {
      const name = b.getAttribute('aria-label') || b.textContent.trim();
      const br = rect(b), barr = rect(bar);
      if (br.left < barr.left - 0.5 || br.right > barr.right + 0.5) fail(`the button "${name}" spills out of the action bar`);
      if (b.scrollWidth > b.clientWidth + 0.5) fail(`the label of "${name}" is cut off`);
      const cs = w.getComputedStyle(b);
      if (cs.textOverflow === 'ellipsis' || (cs.overflow !== 'visible' && b.scrollWidth > b.clientWidth)) fail(`the label of "${name}" is truncated`);
      if (!name) fail('an action bar button has no accessible name');
      b.setAttribute('data-focused', 'true'); range(b, `the focused button "${name}"`); b.removeAttribute('data-focused');
    }
    if (Wr >= 87.5 && tops.size !== 1) fail('the action bar wrapped although its buttons fit on one line');

    // Picker: between a quarter and two thirds of the dialog's inner width; long
    // rows wrap; its layer meets the top of the hint bar and neither the layer
    // nor the panel runs over it.
    const hint = rect(hb);
    for (const id of ['short', 'long']) {
      const dlg = d.getElementById(id), p = dlg.querySelector('.en-picker');
      K.picker.open(dlg, bar.querySelector('.en-button'));
      finish(); await wait(20);
      if (!near(rect(dlg).bottom, hint.top)) fail(`the ${id} picker's layer stops at ${rect(dlg).bottom}, not at the top of the hint bar at ${hint.top}`);
      const pr = rect(p), dr = rect(dlg);
      const seenP = { left: pr.left, right: pr.right, top: Math.max(pr.top, dr.top), bottom: Math.min(pr.bottom, dr.bottom) };
      if (overlap(rect(dlg), hint) || overlap(seenP, hint)) fail(`the ${id} picker runs over the hint bar`);
      const cs = w.getComputedStyle(dlg);
      // The dialog's content box, as container units measure it (a scrollbar,
      // when the rows are taller than the frame, is not taken off).
      const inner = rect(dlg).width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      const pw = rect(p).width;
      size[id] = Math.round(pw / inner * 1000) / 10;
      if (pw < inner / 4 - 1) fail(`the ${id} picker is ${pw}px, less than a quarter of its ${inner}px space`);
      if (pw > inner * 2 / 3 + 1) fail(`the ${id} picker is ${pw}px, more than two thirds of its ${inner}px space`);
      if (dlg.scrollWidth > dlg.clientWidth) fail(`the ${id} picker's dialog scrolls sideways`);
      range(p, `the ${id} picker`);
      const row = dlg.querySelector('[data-focused="true"]');
      if (!row) fail(`no focused row in the ${id} picker`); else range(row, `the ${id} picker's focused row`);
      if (id === 'short' && Wr >= 56.25 && !near(pw, inner / 4)) fail(`the short picker is ${pw}px, not its narrowest (${inner / 4}px)`);
      if (id === 'long') {
        if (!near(pw, inner * 2 / 3)) fail(`the long picker is ${pw}px, not its widest (${inner * 2 / 3}px)`);
        const title = dlg.querySelector('.en-picker__row span');
        if (lines(title) < 2) fail('a long picker row does not wrap');
        if (title.scrollWidth > title.clientWidth + 0.5) fail('a long picker row is cut off');
      }
      K.picker.close(); finish(); await wait(20);
      if (dlg.open) { dlg.close(); }
    }

    // Toast: hugs its text up to its limit, bottom right above the hint bar.
    const limit = Math.min(parseFloat(w.getComputedStyle(d.documentElement).getPropertyValue('--en-c-toast-width')) * remPx, Wp - gutter);
    const t = K.toast.show('Saved', { time: 60000 });
    finish(); await wait(20);
    let r = rect(t);
    const text = t.querySelector('.en-toast__text');
    if (!near(r.right, Wp)) fail(`the toast's right edge is at ${r.right}, not the page's edge ${Wp}`);
    if (!near(r.bottom, hint.top)) fail(`the toast's bottom is at ${r.bottom}, not just above the hint bar at ${hint.top}`);
    const pad = parseFloat(w.getComputedStyle(t).paddingLeft) + parseFloat(w.getComputedStyle(t).paddingRight);
    if (!near(r.width, rect(text).width + pad)) fail(`a short toast is ${r.width}px, not as wide as its text`);
    size.shortToast = Math.round(r.width);
    K.toast.update('Library updated: 3 new films were found in your folders, and 2 films that had moved were found again in their new places');
    await wait(20);
    r = rect(t);
    size.longToast = Math.round(r.width);
    if (!near(r.width, limit)) fail(`a long toast is ${r.width}px, not its limit of ${limit}px`);
    if (lines(text) < 2) fail('a long toast does not wrap');
    if (!near(r.right, Wp) || !near(r.bottom, hint.top)) fail('a long toast is not at the bottom right above the hint bar');
    range(t, 'the toast');
    if (d.scrollingElement.scrollWidth > W) fail(`the frame scrolls sideways (${d.scrollingElement.scrollWidth}px)`);
    if (twoLines) {
      // The hint bar changes height while the toast shows: back to one line,
      // then two again; the toast follows it each time.
      for (const markup of [oneLineBar, null]) {
        if (markup) hb.innerHTML = markup;
        else { hb.lastElementChild.lastChild.textContent = 'Cancel'; for (const name of MORE) { if (hintsAt() >= 2) break; addHint(name); } }
        await settle(w);
        if (!near(rect(t).bottom, rect(hb).top))
          fail(`with the hint bar changed to ${hintsAt()} line(s) while the toast shows, the toast's bottom is at ${rect(t).bottom}, not at ${rect(hb).top}`);
      }
      // An app hides its hint bar: the toast and the picker's layer keep the
      // old one-bar gap (--en-size-bar) above the bottom, and the toast goes
      // back above the bar when it shows again.
      hb.style.display = 'none'; await settle(w);
      size.hiddenGap = Math.round(H - rect(t).bottom);
      if (!near(rect(t).bottom, H - oneBar))
        fail(`with the hint bar hidden, the toast's bottom is at ${rect(t).bottom}, not one bar (${oneBar}px) above the bottom at ${H - oneBar}`);
      const hiddenDlg = d.getElementById('short');
      K.picker.open(hiddenDlg, bar.querySelector('.en-button')); finish(); await wait(20);
      if (!near(rect(hiddenDlg).bottom, H - oneBar))
        fail(`with the hint bar hidden, the picker's layer stops at ${rect(hiddenDlg).bottom}, not one bar (${oneBar}px) above the bottom at ${H - oneBar}`);
      K.picker.close(); finish(); await wait(20);
      if (hiddenDlg.open) hiddenDlg.close();
      hb.style.display = ''; await settle(w);
      if (!near(rect(t).bottom, rect(hb).top))
        fail(`with the hint bar shown again, the toast's bottom is at ${rect(t).bottom}, not at its top at ${rect(hb).top}`);
    }
    const before = rect(t);
    K.toast.hide();
    if (args.reduced) {
      if (!t.hidden) fail('in reduced motion the toast does not disappear at once');
    } else {
      const anim = w.getComputedStyle(t).animationName;
      await wait(120);
      const now = rect(t);
      if (anim !== 'en-fade-out') fail(`the toast leaves with ${anim}, not a fade`);
      if (t.hidden || !near(now.left, before.left) || !near(now.top, before.top)) fail('the toast does not fade out in place');
      await wait(400);
      if (!t.hidden) fail('the toast did not leave');
    }
    out.sizes.push(size);
    f.remove();
  }
  return JSON.stringify(out);
}
"""


# Every other component, together in a frame of each size. Nothing here sets a size.
COMPONENT_DOC = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;font-family:var(--en-font);line-height:var(--en-line-height);background:var(--en-surface-page);color:var(--en-text)">
<main style="display:flex;flex-direction:column;gap:var(--en-space-gap);padding:var(--en-space-gutter)">
<div class="en-tabs" role="tablist" data-set="tabs">
  <button class="en-tab" role="tab" aria-selected="true">Movies <span class="en-tab__count">3</span></button>
  <button class="en-tab" role="tab" aria-selected="false">TV shows <span class="en-tab__count">1</span><span class="en-dot" role="img" aria-label="New"></span></button>
  <button class="en-tab" role="tab" aria-selected="false">Home videos <span class="en-tab__count">12</span></button>
  <button class="en-tab" role="tab" aria-selected="false">Recently added</button>
</div>
<ul class="en-rows" data-set="rows">
  <li><button class="en-row">Copper Tide Rising <span class="en-row__meta">1995</span></button></li>
  <li><div class="en-row">Keep screen awake while a video is paused<button class="en-toggle" aria-pressed="true" aria-label="Keep screen awake"></button></div></li>
  <li><button class="en-row">Lighthouse Keepers of the Long Winter, the complete director's cut <span class="en-row__meta">Episode 5</span></button></li>
</ul>
<div class="en-shelf">
  <a class="en-tile en-tile--large" href="#"><div class="en-tile__frame">Paused frame</div><div class="en-progress en-progress--thin" style="--value: 34%"><span class="en-progress__fill"></span></div><div class="en-tile__title">Lighthouse Keepers of the Long Winter</div></a>
  <a class="en-tile" href="#"><div class="en-tile__frame">Paused frame</div><div class="en-progress en-progress--thin" style="--value: 18%"><span class="en-progress__fill"></span></div><div class="en-tile__title">Driftwood · Episode 5</div></a>
  <a class="en-tile" href="#"><div class="en-tile__frame">Paused frame</div><div class="en-progress en-progress--thin" style="--value: 11%"><span class="en-progress__fill"></span></div><div class="en-tile__title">Orchard Weather · Part 1</div></a>
</div>
<div style="display:flex;flex-wrap:wrap;gap:var(--en-space-gap)" data-set="buttons">
  <button class="en-button en-button--primary">Scan my folders</button>
  <button class="en-button">Rescan every library folder</button>
  <button class="en-button en-button--icon" aria-label="Search"><svg class="en-icon" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/></svg></button>
  <button class="en-button" disabled>Remove</button>
</div>
<div><div class="en-progress__head"><span>40%</span><span>Scanning your folders</span></div>
  <div class="en-progress" role="progressbar" aria-label="Scan" aria-valuenow="40" style="--value: 40%"><span class="en-progress__fill"></span></div></div>
<ul class="en-menu" data-set="menu">
  <li><a class="en-menu__item" href="#" aria-current="page">Movies</a></li>
  <li><a class="en-menu__item" href="#">TV shows</a></li>
  <li><a class="en-menu__item" href="#">Scan my folders and every library on another drive</a></li>
</ul>
</main>
<footer class="en-hintbar" data-set="hints">
  <span class="en-hint"><span class="en-glyph en-glyph--shoulder">L1</span>Movies</span>
  <span class="en-hint"><span class="en-glyph en-glyph--shoulder">R1</span>TV shows</span>
  <span class="en-hint"><span class="en-glyph">A</span>Resume</span>
  <span class="en-hint"><span class="en-glyph">X</span>Remove</span>
  <span class="en-hint"><span class="en-glyph">B</span>Back</span>
</footer>
</body></html>"""

# The smallest supported box: a screen with a list row (its title and a
# focused toggle) above the hint bar with two hints.
SMALLEST_DOC = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;min-height:100vh;display:flex;flex-direction:column;font-family:var(--en-font);line-height:var(--en-line-height);background:var(--en-surface-page);color:var(--en-text)">
<main style="flex:1;padding:var(--en-space-gutter)">
<div class="en-rows"><div class="en-row">Keep screen awake<button class="en-toggle" aria-pressed="true" aria-label="Keep screen awake" data-focused="true"></button></div></div>
</main>
<footer class="en-hintbar"><span class="en-hint"><span class="en-glyph">A</span>Select</span><span class="en-hint"><span class="en-glyph">B</span>Back</span></footer>
</body></html>"""


COMPONENTS = r"""
async (args) => {
""" + FRAME_HELPERS + r"""
  const frames = JSON.parse(args.frames), out = { errors: [], sizes: [], rootPx };
  for (const [Wr, Hr] of frames) {
    const W = Math.round(Wr * rootPx), H = Math.round(Hr * rootPx), at = `${Wr}x${Hr}rem`;
    const f = await open(args.doc, W, H), w = f.contentWindow, d = f.contentDocument;
    const fail = m => out.errors.push(`${at}: ${m}`);
    const frame = { left: 0, top: -1e9, right: W, bottom: 1e9 };
    const size = { at };
    if (d.scrollingElement.scrollWidth > W) fail(`the page scrolls sideways (${d.scrollingElement.scrollWidth}px in ${W}px)`);
    size.hintLines = lineCount([...d.querySelector('.en-hintbar').children]);
    // Tiles take their width from the shelf, between their limits.
    const shelf = d.querySelector('.en-shelf'), tiles = [...shelf.querySelectorAll('.en-tile')];
    size.tile = Math.round(tiles[1].getBoundingClientRect().width);
    size.large = Math.round(tiles[0].getBoundingClientRect().width);
    if (Wr >= 87.5 && shelf.scrollWidth > shelf.clientWidth) fail('the shelf scrolls although its tiles fit');
    if (size.tile > 16 * rootPx + 0.5 || size.tile < 10 * rootPx - 0.5) fail(`a tile is ${size.tile}px, outside 10rem to 16rem`);
    if (size.large > 28.25 * rootPx + 0.5 || size.large < 12 * rootPx - 0.5) fail(`a large tile is ${size.large}px, outside 12rem to 28.25rem`);
    // Text size follows the browser's font size.
    size.body = Math.round(parseFloat(w.getComputedStyle(d.querySelector('.en-row')).fontSize) * 10) / 10;
    if (size.body < 1.5 * rootPx - 0.5) fail(`row text is ${size.body}px, smaller than 1.5rem`);
    // Nothing outside the frame, overlapping or cut off; every focus ring visible.
    await fitsFrame(w, d.body, () => frame, fail);
    out.sizes.push(size);
    f.remove();
  }
  return JSON.stringify(out);
}
"""

SMALLEST_BOX = r"""
async (args) => {
""" + FRAME_HELPERS + r"""
  const [Wr, Hr] = JSON.parse(args.box), out = { errors: [], rootPx };
  // What goes wrong on the screen at W by H px, or [] if it all fits.
  const problems = (w, d, W, H) => {
    const p = [], doc = d.scrollingElement;
    if (doc.scrollWidth > W) p.push(`it scrolls sideways (${doc.scrollWidth}px)`);
    if (doc.scrollHeight > H) p.push(`it scrolls (${doc.scrollHeight}px tall)`);
    const bar = d.querySelector('.en-hintbar'), hints = [...bar.children];
    if (lineCount(hints) !== 1) p.push('the two hints are not on one line');
    for (const h of hints) if (!inside(box(h.getBoundingClientRect()), box(bar.getBoundingClientRect()))) p.push('a hint spills out of the bar');
    const row = d.querySelector('.en-row'), toggle = row.querySelector('.en-toggle');
    const rr = box(row.getBoundingClientRect()), br = box(bar.getBoundingClientRect());
    if (overlap(rr, br)) p.push('the row and the hint bar overlap');
    if (row.scrollWidth > row.clientWidth + 0.5) p.push('the row title is cut off');
    const ring = focusBox(w, toggle);
    if (!inside(ring, { left: 0, top: 0, right: W, bottom: H })) p.push(`the toggle's focus ring is not fully visible (${show(ring)})`);
    if (overlap(ring, br)) p.push("the toggle's focus ring runs under the hint bar");
    if (!inside(ring, clipOf(w, toggle))) p.push("the toggle's focus ring is clipped");
    return p;
  };
  const W = Math.round(Wr * rootPx), H = Math.round(Hr * rootPx);
  const f = await open(args.doc, W, H), w = f.contentWindow, d = f.contentDocument;
  finish(d); await wait(20);
  for (const m of problems(w, d, W, H)) out.errors.push(`at ${Wr}rem by ${Hr}rem: ${m}`);
  // Measure the smallest width and height the content needs, 1px at a time.
  let mw = W, mh = H;
  while (mw > 100) { f.style.width = `${mw - 1}px`; await wait(5); if (problems(w, d, mw - 1, H).length) break; mw--; }
  f.style.width = `${W}px`;
  while (mh > 50) { f.style.height = `${mh - 1}px`; await wait(5); if (problems(w, d, W, mh - 1).length) break; mh--; }
  out.needW = Math.round(mw / rootPx * 100) / 100;
  out.needH = Math.round(mh / rootPx * 100) / 100;
  // Below the box the page scrolls instead of overlapping.
  const sw = Math.round(W * 0.7), sh = Math.round(H * 0.6);
  f.style.width = `${sw}px`; f.style.height = `${sh}px`; await wait(20);
  const rr = box(d.querySelector('.en-row').getBoundingClientRect()), br = box(d.querySelector('.en-hintbar').getBoundingClientRect());
  if (overlap(rr, br)) out.errors.push('below the smallest box, the row and the hint bar overlap instead of the page scrolling');
  if (!(d.scrollingElement.scrollHeight > sh)) out.errors.push('below the smallest box, the page does not scroll');
  f.remove();
  return JSON.stringify(out);
}
"""

# The Resize page, docs/resize.html, checked in place. Each fixed frame is as
# wide as its label says, which names a width only; each frame on the page,
# fixed or resizable, never scrolls sideways and passes fitsFrame. Each
# resizable frame can be resized by hand, and is checked again set to the
# smallest supported box's width and to the whole column.
RESIZE_PAGE = r"""
async (args) => {
""" + FRAME_HELPERS + r"""
  const out = { errors: [], fixed: [], resizable: [] };
  const client = el => { const r = el.getBoundingClientRect(), left = r.left + el.clientLeft;
                         return { left, top: -1e9, right: left + el.clientWidth, bottom: 1e9 }; };
  const check = async (el, at) => {
    const fail = m => out.errors.push(`${at}: ${m}`);
    finish(document); await settle(window); await wait(20);
    if (el.scrollWidth > el.clientWidth + 0.5) fail(`it scrolls sideways (${el.scrollWidth}px in ${el.clientWidth}px)`);
    await fitsFrame(window, el, () => client(el), fail);
  };
  for (const fig of document.querySelectorAll('.site-frame')) {
    const label = fig.querySelector('figcaption').textContent.trim();
    const m = label.match(/^(\d+(?:\.\d+)?)rem wide \(\d+px\)$/);
    if (!m) { out.errors.push(`the frame label "${label}" does not name a width only`); continue; }
    const frames = [...fig.querySelectorAll('.site-fixed')];
    if (!frames.length) out.errors.push(`${label}: no frames`);
    for (const [i, el] of frames.entries()) {
      const width = el.getBoundingClientRect().width;
      if (Math.abs(width - parseFloat(m[1]) * rootPx) > 1) out.errors.push(`${label}, frame ${i + 1}: it is ${width}px wide`);
      await check(el, `${label}, frame ${i + 1}`);
    }
    out.fixed.push(m[1]);
    // The narrowest frame also shows the picker and the toast over a hint bar on two lines.
    if (parseFloat(m[1]) === parseFloat(args.smallest)) {
      const two = frames.filter(el => { const b = el.querySelector('.en-hintbar');
        return b && lineCount([...b.children]) === 2 && b.textContent.includes('Cancel'); });
      for (const what of ['.en-dialog[open]', '.en-toast'])
        if (!two.some(el => el.querySelector(what))) out.errors.push(`${label}: no frame shows the ${what} over a hint bar with Select and Cancel on two lines`);
      out.twoLines = two.length;
    }
  }
  const narrowest = `${parseFloat(args.smallest) * rootPx}px`;
  for (const el of document.querySelectorAll('.site-resize')) {
    const name = el.closest('figure').querySelector('figcaption').textContent.trim();
    if (getComputedStyle(el).resize !== 'both') out.errors.push(`the ${name} frame cannot be resized by hand`);
    for (const width of [narrowest, '100%']) {
      el.style.width = width;
      await check(el, `the ${name} frame at ${width === '100%' ? 'the whole column' : args.smallest + 'rem'}`);
    }
    el.style.width = '';
    out.resizable.push(name);
  }
  return JSON.stringify(out);
}
"""


def frame_checks(ff, base, mode, reduced):
    """The frame checks, run in one browser. Returns (failures, report lines)."""
    failures, lines = [], []
    ff.load(base + "docs/motion.html")
    r = ff.run(RESPONSIVE, {"frames": json.dumps(FRAMES), "doc": FRAME_DOC, "reduced": "yes" if reduced else None},
               f"the picker, toast and action bar frame check ({mode})")
    failures += [f"frames ({mode}): {m}" for m in r["errors"]]
    c = ff.run(COMPONENTS, {"frames": json.dumps(FRAMES), "doc": COMPONENT_DOC}, f"the component frame check ({mode})")
    failures += [f"components in frames ({mode}): {m}" for m in c["errors"]]
    b = ff.run(SMALLEST_BOX, {"box": json.dumps(SMALLEST), "doc": SMALLEST_DOC}, f"the smallest box check ({mode})")
    failures += [f"smallest box ({mode}): {m}" for m in b["errors"]]
    if ff.errors():
        failures.append(f"frames ({mode}): script errors: {ff.errors()}")
    ff.load(base + "docs/resize.html")
    p = ff.run(RESIZE_PAGE, {"smallest": f"{SMALLEST[0]:g}"}, f"the Resize page check ({mode})")
    failures += [f"resize.html ({mode}): {m}" for m in p["errors"]]
    if ff.errors():
        failures.append(f"resize.html ({mode}): script errors: {ff.errors()}")
    sizes = r["sizes"]
    lines.append(f"  picker and toast against the hint bar ({mode}): layer and toast stop at its top, nothing over it, "
                 "with the bar at " + ", ".join(f"{s['at']} {s['hintLines']} line(s) {s['hintPx']}px" for s in sizes)
                 + "; the toast follows the bar when it changes height; with the bar hidden, the layer and toast keep the "
                 "one-bar gap (" + ", ".join(f"{s['at']} {s['hiddenGap']}px" for s in sizes if 'hiddenGap' in s) + ")")
    sizes = [s for s in sizes if s["bar"] == 1]
    lines.append(f"  picker, toast and action bar in frames of {', '.join(s['at'] for s in sizes)} ({mode}): "
                 "picker between a quarter and two thirds of its dialog ("
                 + ", ".join(f"{s['short']}-{s['long']}%" for s in sizes) + "), long rows wrap; toast hugs its text ("
                 + ", ".join(f"{s['shortToast']}/{s['longToast']}px" for s in sizes)
                 + ") at the bottom right above the hint bar, "
                 + ("disappearing at once" if reduced else "fading out in place") + "; action bar on "
                 + ", ".join(str(s['barLines']) for s in sizes) + " line(s), never overflowing; nothing scrolls sideways")
    cs = c["sizes"]
    lines.append(f"  every other component in frames of {', '.join(s['at'] for s in cs)} ({mode}, root {c['rootPx']:g}px): "
                 "nothing outside the frame, overlapping or cut off; hint bar on "
                 + ", ".join(str(s['hintLines']) for s in cs) + " line(s); tiles "
                 + ", ".join(f"{s['tile']}/{s['large']}px" for s in cs) + "; row text "
                 + ", ".join(f"{s['body']:g}px" for s in cs) + "; every focus ring fully visible")
    lines.append(f"  smallest supported box {SMALLEST[0]}rem by {SMALLEST[1]}rem ({mode}): row, toggle ring and two hints fit; "
                 f"the content needs {b['needW']:g}rem by {b['needH']:g}rem; below the box the page scrolls")
    lines.append(f"  resize.html ({mode}): fixed frames {', '.join(x + 'rem' for x in p['fixed'])} wide as labelled; "
                 f"{len(p['resizable'])} resizable frames ({', '.join(p['resizable'])}) resizable by hand and checked at "
                 f"{SMALLEST[0]:g}rem and the whole column; no frame scrolls sideways, nothing overlaps, every focus ring visible; "
                 f"{p.get('twoLines', 0)} frames at {SMALLEST[0]:g}rem with Select and Cancel on two lines, picker and toast "
                 "stopping at the bar's top")
    return failures, lines


# The longest any one page load or browser script may take before the check
# gives up and says which one never finished (each normally takes seconds).
LOAD_LIMIT = 60
RUN_LIMIT = 300


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Firefox:
    def __init__(self, reduced_device, font_px=None):
        self.dir = tempfile.mkdtemp(prefix="enamel-ff-")
        with open(os.path.join(self.dir, "user.js"), "w") as f:
            f.write(PREFS + (f'user_pref("ui.prefersReducedMotion", 1);\n' if reduced_device else "")
                    + (f'user_pref("font.size.variable.x-western", {font_px});\n' if font_px else ""))
        self.port = _free_port()
        self.proc = subprocess.Popen(
            FIREFOX[:2] + [f"--filesystem={self.dir}"] + FIREFOX[2:] +
            ["--headless", "--no-remote", "--profile", self.dir, f"--remote-debugging-port={self.port}",
             "--window-size=1500,1000", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 60
        while True:
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=1).close()
                break
            except OSError:
                if time.time() > deadline or self.proc.poll() is not None:
                    raise RuntimeError("Firefox did not start")
                time.sleep(0.5)
        time.sleep(1)
        while True:  # the port can open before Firefox is ready to talk on it
            try:
                self.s = Session(f"ws://127.0.0.1:{self.port}/session", timeout=120)
                break
            except (OSError, ConnectionError):
                if time.time() > deadline or self.proc.poll() is not None:
                    raise RuntimeError("Firefox started but never accepted the check's connection")
                time.sleep(0.5)
        self.s.call("session.new", _limit=LOAD_LIMIT, capabilities={})
        self.s.call("session.subscribe", _limit=LOAD_LIMIT, events=["log.entryAdded"])
        self.ctx = self.s.call("browsingContext.getTree", _limit=LOAD_LIMIT)["contexts"][0]["context"]

    def load(self, url):
        self.s.events.clear()
        try:
            self.s.call("browsingContext.navigate", _limit=LOAD_LIMIT, context=self.ctx, url=url, wait="complete")
        except TimeoutError:
            raise RuntimeError(f"{url} did not finish loading within {LOAD_LIMIT} s") from None
        time.sleep(0.3)

    def errors(self):
        return [e["params"].get("text") for e in self.s.events
                if e.get("method") == "log.entryAdded" and e["params"].get("level") == "error"]

    def run(self, fn, arg, what="a browser script"):
        """Run fn in the page and return its JSON result. Gives up with a
        clear message if it has not finished within RUN_LIMIT seconds."""
        try:
            r = self._run(fn, arg)
        except TimeoutError:
            raise RuntimeError(f"{what} did not finish within {RUN_LIMIT} s; something it waits for never came") from None
        if r.get("type") == "exception":
            raise RuntimeError(f"{what}: {r['exceptionDetails'].get('text')}")
        return json.loads(r["result"]["value"])

    def _run(self, fn, arg):
        return self.s.call("script.callFunction", _limit=RUN_LIMIT, functionDeclaration=fn, awaitPromise=True,
                        target={"context": self.ctx}, arguments=[{"type": "object", "value": [
                            [k, {"type": "string", "value": v} if v else {"type": "null"}] for k, v in arg.items()]}])

    def screenshot(self, path):
        self.s.call("script.evaluate", expression="window.scrollTo(0, 0)", target={"context": self.ctx},
                    awaitPromise=False, _limit=LOAD_LIMIT)
        try:
            r = self.s.call("browsingContext.captureScreenshot", _limit=LOAD_LIMIT, context=self.ctx, origin="document")
        except RuntimeError:  # too tall for one image: take the visible part
            r = self.s.call("browsingContext.captureScreenshot", _limit=LOAD_LIMIT, context=self.ctx, origin="viewport")
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["data"]))

    def close(self):
        try:
            self.s.call("browser.close", _limit=30)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.dir, ignore_errors=True)


MODES = [("full", False, None, False), ("reduced", False, "reduced", True),
         ("device-reduced", True, None, True), ("forced-full", True, "full", False)]


def check(base, pages, shots=None, quick=False, frames=True):
    """Return (failures, report lines).

    quick=True is the per-issue check (scripts/test.sh): one browser only, a
    device with no motion preference, so each page is checked in the "full"
    and "reduced" (attribute) modes; no device-reduced browser and no larger
    font. frames=False leaves out the frame checks. The full check
    (scripts/test.sh full) runs everything."""
    failures, lines, results, behaviour, responsive = [], [], {}, {}, {}
    ran = [m for m, dev, *_ in MODES if not (quick and dev)]
    for reduced_device in ((False,) if quick else (False, True)):
        ff = Firefox(reduced_device)
        try:
            for mode, dev, attr, expect_reduced in MODES:
                if dev != reduced_device:
                    continue
                for page in pages:
                    ff.load(base + "docs/" + page)
                    out = ff.run(PROBE, {"attr": attr}, f"the focus and motion probe on {page} ({mode})")
                    errs = ff.errors()
                    if errs:
                        failures.append(f"{page} ({mode}): script errors: {errs}")
                    if out["reducedMatch"] != dev:
                        failures.append(f"{page} ({mode}): the device motion setting did not take effect")
                    results[(mode, page)] = out
                    if page == "motion.html":
                        ff.load(base + "docs/" + page)
                        b = ff.run(BEHAVIOUR, {"attr": attr}, f"the picker and toast behaviour check ({mode})")
                        failures += [f"behaviour ({mode}): {m}" for m in b["errors"]]
                        if ff.errors():
                            failures.append(f"behaviour ({mode}): script errors: {ff.errors()}")
                        if b.get("fill") != "rgb(242, 235, 218)":
                            failures.append(f"behaviour ({mode}): a focused picker row is {b.get('fill')}, not cream")
                        moving = not expect_reduced
                        if (b.get("panelAnim") != "none") != moving or (b.get("toastAnim") != "none") != moving:
                            failures.append(f"behaviour ({mode}): picker or toast animation is "
                                            f"{b.get('panelAnim')}/{b.get('toastAnim')} in {'full' if moving else 'reduced'} motion")
                        if b.get("openRightAfterClose") != moving or b.get("toastHiddenRightAfterHide") == moving:
                            failures.append(f"behaviour ({mode}): picker or toast does not "
                                            f"{'leave with motion' if moving else 'disappear at once'}")
                        leave_anim = "en-fade-out" if moving else "none"
                        if b.get("toastLeaveAnim") != leave_anim or b.get("toastLeaveMoved"):
                            failures.append(f"behaviour ({mode}): the toast leaves with {b.get('toastLeaveAnim')}"
                                            f"{', moving sideways' if b.get('toastLeaveMoved') else ''}, "
                                            f"not {'a fade in place' if moving else 'at once'}")
                        behaviour[mode] = b
                        ff.load(base + "docs/" + page)
                    if shots and mode in ("full", "reduced"):
                        time.sleep(0.8)  # let focus arrive on the examples again
                        ff.screenshot(os.path.join(shots, f"{page[:-5]}-{mode}.png"))
                    if expect_reduced:
                        for m in out["during"]:
                            for a in m["anims"]:
                                failures.append(f"{page} ({mode}): animation still runs: {a}")
                            for t in m["transforms"]:
                                failures.append(f"{page} ({mode}): transform in reduced motion: {t}")
                            for where, prop in m["trans"]:
                                if prop not in COLOUR_PROPS:
                                    failures.append(f"{page} ({mode}): {where} moves ({prop}) in reduced motion")
                    else:
                        for end in out["pulse"]:
                            if end is None or not 4000 <= end <= 6000:
                                failures.append(f"{page} ({mode}): tile pulse ends at {end} ms, not 4 to 6 s")
                        for t in out["restart"]:
                            if t is None or t > 100:
                                failures.append(f"{page} ({mode}): pulse did not restart when focus returned ({t} ms)")
            if frames:
                mode = "reduced motion" if reduced_device else "full motion"
                errs, more = frame_checks(ff, base, mode, reduced_device)
                failures += errs
                responsive[mode] = more
        finally:
            ff.close()
    if not quick:
        # Once more with a larger browser font size: text grows and everything still fits.
        ff = Firefox(False, LARGE_FONT_PX)
        try:
            mode = f"full motion, browser font size {LARGE_FONT_PX}px"
            ff.load("about:blank")
            root = ff.run("async () => JSON.stringify(parseFloat(getComputedStyle(document.documentElement).fontSize))", {})
            if root != LARGE_FONT_PX:
                failures.append(f"the larger browser font size did not take effect (root is {root}px)")
            errs, more = frame_checks(ff, base, mode, False)
            failures += errs
            responsive[mode] = more
        finally:
            ff.close()
    for page in pages:
        base_items = results[("full", page)]["items"]
        for item in base_items:
            if item["before"] == item["after"]:
                failures.append(f"{page}: focusing {item['what']} changes nothing visible")
        for mode in ran[1:]:
            items = results[(mode, page)]["items"]
            if [i["after"] for i in items] != [i["after"] for i in base_items]:
                diff = [(a["what"], a["after"], b["after"]) for a, b in zip(base_items, items) if a["after"] != b["after"]]
                failures.append(f"{page}: focus in {mode} motion differs from full motion: {diff[:2]}")
        full, red = results[("full", page)], results[("reduced", page)]
        moving = sum(len(m["anims"]) + len(m["trans"]) for m in full["during"])
        lines.append(f"  {page:16} {len(base_items):2} focusable examples; focus identical in all {len(ran)} modes; "
                     f"{moving} motions on focus in full, "
                     f"{sum(len(m['anims']) for m in red['during'])} animations and "
                     f"{sum(len(m['transforms']) for m in red['during'])} transforms in reduced"
                     + (f"; pulse ends at {full['pulse'][0] / 1000:.1f} s" if full["pulse"] else ""))
    lines.append(f"  picker and toast behaviour checked on motion.html in {len(behaviour)} modes "
                 "(focus kept inside, ends stop, keys held back, focus returned, select, tap, cancel row, "
                 "first focus, one toast, timer restart, no focus taken, toast fading out in place; "
                 "leaving with motion in full, at once in reduced)")
    for more in responsive.values():
        lines += more
    return failures, lines
