# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #18, Enamel's own look, in the device's Firefox (headless, its own
temporary profile; Steam is never touched):

  - each focus style: a button or picker row in cream with dark text drawn as
    heavy as semibold, never changing its size, on
    its 4px accent underside with no outline; a tile with one ring and a soft glow,
    its frame's rim gone; a row lifted to the control grey, its meta text stepping
    up; the off toggle's knob in cream;
  - lift and press timings in full motion: rising over the medium time, settling
    over the fast one, dropping over the fast one, springing back over the medium
    one, all with the standard curve;
  - reduced motion: no rising or dropping and no moving transition; focus switches
    at once and a press only darkens;
  - the lighter fallback: soft shadows and movement gone; colours, cream, underside
    and speckle kept;
  - nothing cut off by a lift: a risen button stays inside its bar, a risen picker
    row covers no neighbour and stays inside its panel;
  - progress: a sunken dark track, speckled fill, 8px under a tile, 12px in a toast;
  - nothing you can select is patterned, on the real Components page.

    scripts/test.sh check own_look_check
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

DOC = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0;font-family:var(--en-font)">
<header class="en-actionbar" id="bar"><button class="en-button" id="barbutton">Menu</button></header>
<button class="en-button" id="b">Rescan</button>
<button class="en-button en-button--primary" id="primary">Scan</button>
<div class="en-picker" id="panel"><div class="en-picker__rows">
  <button class="en-picker__row" id="p0"><span>Title</span></button>
  <button class="en-picker__row" id="p1"><span>Date added</span><span class="en-picker__desc">Newest first</span></button>
  <button class="en-picker__row" id="p2"><span>Year</span></button>
</div></div>
<div class="en-shelf"><a class="en-tile" id="t" href="#t"><div class="en-tile__frame" id="tf">A</div><div class="en-progress en-progress--thin" id="thin" style="--value: 40%"><span class="en-progress__fill" id="thinfill"></span></div></a></div>
<div class="en-rows"><button class="en-row" id="r">Driftwood <span class="en-row__meta" id="m">1995</span></button></div>
<div class="en-row"><button class="en-toggle" id="off" aria-pressed="false" aria-label="A"></button></div>
<div class="en-toast" id="toast" style="position:static"><span class="en-toast__text">Scanning</span><div class="en-progress" id="tp" style="--value: 40%"><span class="en-progress__fill" id="tpfill"></span></div></div>
<div class="en-speckle" id="speckle" style="height:100px"></div>
</body></html>"""

MEASURE = r"""
async (args) => {
  const f = document.createElement('iframe');
  f.style.cssText = 'position:absolute;left:0;top:0;width:900px;height:1400px;border:0';
  const loaded = new Promise(r => f.addEventListener('load', r, { once: true }));
  f.srcdoc = args.doc;
  document.body.append(f);
  await loaded;
  const d = f.contentDocument, w = f.contentWindow, root = d.documentElement;
  const frame = () => new Promise(r => w.requestAnimationFrame(() => w.requestAnimationFrame(r)));
  const cs = (el, p) => w.getComputedStyle(el, p);
  const $ = id => d.getElementById(id);
  const settle = async () => { d.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} }); await frame(); };
  const token = (prop, value) => { const p = d.createElement('div'); p.style[prop] = value; d.body.append(p); const v = cs(p)[prop]; p.remove(); return v; };
  await frame();
  const CREAM = token('backgroundColor', 'var(--en-cream)'), PRESSED = token('backgroundColor', 'var(--en-cream-pressed)');
  const INK = token('color', 'var(--en-focus-fill-ink)'), ACCENT = token('backgroundColor', 'var(--en-accent)');
  const CONTROL = token('backgroundColor', 'var(--en-surface-control)'), SOFT = token('color', 'var(--en-text-soft)');
  const BAR = token('backgroundColor', 'var(--en-surface-bar)');
  const MEDIUM = cs(root).getPropertyValue('--en-motion-medium').trim(), FAST = cs(root).getPropertyValue('--en-motion-fast').trim();
  const out = { errors: [], notes: [] };
  const fail = m => out.errors.push(m);
  const ms = v => v.endsWith('ms') ? parseFloat(v) : parseFloat(v) * 1000;
  const rise = el => new w.DOMMatrix(cs(el).transform === 'none' ? '' : cs(el).transform).m42;
  const trans = (el, prop) => el.getAnimations().find(a => a.transitionProperty === prop);

  const cream = (el, name) => {
    if (cs(el).backgroundColor !== CREAM) fail(`${name}: focused fill is ${cs(el).backgroundColor}, not cream`);
    if (cs(el).color !== INK) fail(`${name}: focused text is ${cs(el).color}`);
    if (!(parseFloat(cs(el).webkitTextStrokeWidth) > 0)) fail(`${name}: focused text is not drawn heavier (semibold in look)`);
    if (cs(el).outlineStyle !== 'none') fail(`${name}: focused has an outline as well`);
    if (cs(el).backgroundImage !== 'none') fail(`${name}: focused still has the satin light`);
    if (!cs(el).boxShadow.includes(`${ACCENT} 0px 4px 0px`)) fail(`${name}: no 4px accent underside: ${cs(el).boxShadow}`);
  };

  // Full motion.
  root.setAttribute('data-en-motion', 'full');
  for (const [id, name] of [['b', 'button'], ['primary', 'primary button'], ['p1', 'picker row']]) {
    const el = $(id);
    if (id === 'primary' && cs(el).backgroundColor !== ACCENT) fail('a primary button at rest is not the accent colour');
    const restSize = [el.offsetWidth, el.offsetHeight];
    el.setAttribute('data-focused', 'true'); await frame();
    const focusSize = [el.offsetWidth, el.offsetHeight];
    if (focusSize.join() !== restSize.join()) fail(`${name}: focus changes its size from ${restSize.join('x')} to ${focusSize.join('x')}`);
    const up = trans(el, 'transform');
    if (!up || ms(up.effect.getComputedTiming().duration + 'ms') !== ms(MEDIUM)) fail(`${name}: rising takes ${up && up.effect.getComputedTiming().duration}, not ${MEDIUM}`);
    if (up && up.effect.getTiming().easing === 'linear' && !cs(el).transitionTimingFunction.startsWith('cubic-bezier(0.16')) fail(`${name}: rising does not use the standard curve`);
    await settle();
    cream(el, name);
    if (Math.abs(rise(el) + 4) > 0.01) fail(`${name}: rises ${rise(el)}px, not 4px`);
    el.setAttribute('data-pressed', 'true'); await frame();
    const drop = trans(el, 'transform');
    if (!drop || drop.effect.getComputedTiming().duration !== ms(FAST)) fail(`${name}: dropping takes ${drop && drop.effect.getComputedTiming().duration}, not ${FAST}`);
    await settle();
    if (Math.abs(rise(el)) > 0.01) fail(`${name}: pressed, it is still ${rise(el)}px up`);
    if (cs(el).backgroundColor !== PRESSED) fail(`${name}: pressed fill is ${cs(el).backgroundColor}`);
    el.removeAttribute('data-pressed'); await frame();
    const back = trans(el, 'transform');
    if (!back || back.effect.getComputedTiming().duration !== ms(MEDIUM)) fail(`${name}: springing back takes ${back && back.effect.getComputedTiming().duration}, not ${MEDIUM}`);
    await settle();
    el.removeAttribute('data-focused'); await frame();
    const leave = trans(el, 'transform');
    if (!leave || leave.effect.getComputedTiming().duration !== ms(FAST)) fail(`${name}: settling takes ${leave && leave.effect.getComputedTiming().duration}, not ${FAST}`);
    await settle();
  }

  // Tile, row and toggle.
  const restRim = cs($('tf')).boxShadow;
  if (!restRim.includes('inset')) fail('a tile frame has no satin rim at rest');
  $('t').setAttribute('data-focused', 'true'); await frame(); await settle();
  const ring = cs($('t'), '::after');
  if (ring.outlineWidth !== '4px' || ring.outlineStyle !== 'solid') fail(`a tile's ring is ${ring.outlineWidth} ${ring.outlineStyle}`);
  if (ring.outlineColor !== ACCENT) fail(`a tile's ring is ${ring.outlineColor}`);
  if (ring.boxShadow === 'none') fail('a focused tile has no soft glow');
  if (cs($('tf')).boxShadow !== 'none') fail('a focused tile keeps its rim inside its ring');
  $('t').removeAttribute('data-focused');
  $('r').setAttribute('data-focused', 'true'); await frame(); await settle();
  if (cs($('r')).backgroundColor !== CONTROL) fail('a focused row does not lift to the control grey');
  if (cs($('m')).color !== SOFT) fail('a focused row\'s muted text does not step up');
  if (rise($('r')) !== 0) fail('a focused row moves physically');
  $('r').removeAttribute('data-focused');
  if (cs($('off'), '::before').backgroundColor !== CREAM) fail('the off toggle\'s knob is not cream');

  // Nothing cut off by a lift.
  const bb = $('barbutton'); bb.setAttribute('data-focused', 'true'); await frame(); await settle();
  const bar = $('bar').getBoundingClientRect(), br = bb.getBoundingClientRect();
  if (br.top < bar.top - 0.5) fail(`a risen button sticks out of its bar by ${bar.top - br.top}px`);
  if (br.bottom + 4 > bar.bottom + 0.5) fail('a risen button\'s underside runs past its bar');
  bb.removeAttribute('data-focused');
  for (const id of ['p0', 'p1', 'p2']) {
    $(id).setAttribute('data-focused', 'true'); await frame(); await settle();
    const rows = ['p0', 'p1', 'p2'].map($), i = rows.indexOf($(id)), me = rows[i].getBoundingClientRect();
    const panel = $('panel').getBoundingClientRect();
    if (me.top < panel.top - 0.5) fail(`picker row ${id}: rises out of its panel`);
    if (me.bottom + 4 > panel.bottom + 0.5) fail(`picker row ${id}: its underside runs out of its panel`);
    if (i && me.top < rows[i - 1].getBoundingClientRect().bottom - 0.5) fail(`picker row ${id}: covers the row above`);
    if (i < 2 && me.bottom + 4 > rows[i + 1].getBoundingClientRect().top + 0.5) fail(`picker row ${id}: its underside covers the row below`);
    $(id).removeAttribute('data-focused');
  }
  await settle();

  // Progress.
  if (Math.abs($('thin').getBoundingClientRect().height - 8) > 0.01) fail(`a bar under a tile is ${$('thin').getBoundingClientRect().height}px tall`);
  if (Math.abs($('tp').getBoundingClientRect().height - 12) > 0.01) fail(`a bar in a toast is ${$('tp').getBoundingClientRect().height}px tall`);
  if (cs($('tp')).backgroundColor !== BAR) fail('a track is not dark');
  if (!cs($('tp')).boxShadow.includes('inset')) fail('a track is not sunken');
  if (cs($('tpfill')).backgroundColor !== ACCENT) fail('a fill is not the accent');
  if (!cs($('tpfill')).backgroundImage.startsWith('url(')) fail('a fill is not speckled');
  if (!cs($('speckle')).backgroundImage.startsWith('url(')) fail('the page speckle does not show');
  if (cs($('speckle'), '::before').maskImage === 'none') fail('the page speckle has no accent flecks');
  const tpr = $('tp').getBoundingClientRect(), tr = $('toast').getBoundingClientRect();
  if (tpr.left < tr.left || tpr.right > tr.right) fail('a toast\'s bar runs out of the toast');

  // Reduced motion.
  root.setAttribute('data-en-motion', 'reduced'); await frame();
  for (const [id, name] of [['b', 'button'], ['p1', 'picker row']]) {
    const el = $(id);
    el.setAttribute('data-focused', 'true'); await frame();
    if (el.getAnimations().length) fail(`${name}: in reduced motion, focus still animates`);
    if (cs(el).transform !== 'none') fail(`${name}: in reduced motion it rises (${cs(el).transform})`);
    cream(el, `${name}, reduced`);
    el.setAttribute('data-pressed', 'true'); await frame();
    if (el.getAnimations().length) fail(`${name}: in reduced motion, a press animates`);
    if (cs(el).transform !== 'none') fail(`${name}: in reduced motion it drops (${cs(el).transform})`);
    if (cs(el).backgroundColor !== PRESSED) fail(`${name}: in reduced motion a press does not darken`);
    el.removeAttribute('data-pressed'); el.removeAttribute('data-focused'); await frame();
  }
  root.setAttribute('data-en-motion', 'full'); await frame(); await settle();

  // The lighter fallback.
  const fullFocus = {};
  $('b').setAttribute('data-focused', 'true'); await frame(); await settle();
  fullFocus.shadow = cs($('b')).boxShadow;
  $('b').removeAttribute('data-focused'); await frame(); await settle();
  const restShadow = cs($('r')).boxShadow;
  root.setAttribute('data-en-lighter', 'true'); await frame(); await settle();
  const soft = s => s.split(/,(?![^()]*\))/).filter(x => !x.includes('inset') && !/ 0px 0px( 0px)?$/.test(x.trim()) && !/transparent|rgba\(0, 0, 0, 0\)/.test(x)
    && /(\d+)px (\d+)px (\d+)px (\d+)px/.test(x) && parseInt(x.match(/(\d+)px (\d+)px (\d+)px (\d+)px/)[3]) > 0);
  if (soft(restShadow).length === 0) fail('the check could not find the soft shadow it expects without the fallback');
  if (soft(cs($('r')).boxShadow).length) fail(`the lighter fallback keeps a soft shadow on a row: ${cs($('r')).boxShadow}`);
  $('b').setAttribute('data-focused', 'true'); await frame(); await settle();
  if (Math.abs(rise($('b'))) > 0.01) fail('the lighter fallback still lifts a button');
  cream($('b'), 'button, lighter');
  if (soft(cs($('b')).boxShadow).length) fail('the lighter fallback keeps a focused button\'s soft shadow');
  $('b').setAttribute('data-pressed', 'true'); await frame(); await settle();
  if (cs($('b')).backgroundColor !== PRESSED) fail('the lighter fallback loses the press colour');
  if (Math.abs(rise($('b'))) > 0.01) fail('the lighter fallback still moves a press');
  $('b').removeAttribute('data-pressed'); $('b').removeAttribute('data-focused');
  if (!cs($('tpfill')).backgroundImage.startsWith('url(')) fail('the lighter fallback loses the progress speckle');
  if (!cs($('speckle')).backgroundImage.startsWith('url(')) fail('the lighter fallback loses the page speckle');
  if (!cs($('r')).boxShadow.includes('inset')) fail('the lighter fallback loses the satin rim');
  root.removeAttribute('data-en-lighter');
  f.remove();
  return JSON.stringify(out);
}
"""

# On the real Components page: nothing you can select carries a pattern.
PATTERNS = r"""
async () => {
  const sel = '.en-button, .en-row, .en-tile, .en-tile__frame, .en-tab, .en-toggle, .en-menu__item, .en-picker__row, .en-badge, .en-statpanel, .en-band';
  const bad = [];
  for (const el of document.querySelectorAll(sel)) {
    const image = getComputedStyle(el).backgroundImage;
    if (image.includes('url(')) bad.push(el.className);
  }
  return JSON.stringify({ count: document.querySelectorAll(sel).length, bad: [...new Set(bad)] });
}
"""

# On the real Components page: the two Lighter fallback examples differ only in
# the rise, and the menu's Look switch turns the fallback on for the whole guide.
LOOK = r"""
async () => {
  const root = document.documentElement, errors = [];
  const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const settle = async () => { document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} }); await frame(); };
  const rise = el => { const t = getComputedStyle(el).transform; return t === 'none' ? 0 : new DOMMatrix(t).m42; };
  root.setAttribute('data-en-motion', 'full'); await frame(); await settle();
  const section = document.getElementById('lighter');
  const [full, light] = section ? section.querySelectorAll('.en-button[data-focused="true"]') : [];
  if (!full || !light) return JSON.stringify({ errors: ['the Lighter fallback section does not show its two examples'] });
  if (Math.abs(rise(full) + 4) > 0.01) errors.push(`the Full example rises ${rise(full)}px, not 4px`);
  if (Math.abs(rise(light)) > 0.01) errors.push(`the Lighter example still rises ${rise(light)}px`);
  if (getComputedStyle(light).backgroundColor !== getComputedStyle(full).backgroundColor) errors.push('the Lighter example loses the cream fill');
  const look = document.querySelector('.site-look');
  if (!look || look.hidden) errors.push('the Look switch is not shown in the menu');
  else {
    look.querySelector('[data-look="true"]').click(); await frame(); await settle();
    if (root.getAttribute('data-en-lighter') !== 'true') errors.push('choosing Lighter does not turn the fallback on');
    if (Math.abs(rise(full)) > 0.01) errors.push('with the Look switch on Lighter, a focused button still rises');
    if (look.querySelector('[data-look="true"]').getAttribute('aria-selected') !== 'true') errors.push('the Lighter tab is not marked chosen');
    look.querySelector('[data-look="false"]').click(); await frame(); await settle();
    if (root.getAttribute('data-en-lighter') !== 'false') errors.push('choosing Full does not turn the fallback off');
    if (Math.abs(rise(full) + 4) > 0.01) errors.push('back on Full, a focused button does not rise again');
  }
  return JSON.stringify({ errors });
}
"""


class OwnLook(unittest.TestCase):
    def test_focus_motion_fallback_and_lifts(self):
        class Quiet(Handler):
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        ff = None
        try:
            ff = browser_check.Firefox(False)
            ff.load(f"http://127.0.0.1:{server.server_port}/docs/index.html")
            out = ff.run(MEASURE, {"doc": DOC}, "the own look check")
            errors = out["errors"] + ([f"script errors: {ff.errors()}"] if ff.errors() else [])
            ff.load(f"http://127.0.0.1:{server.server_port}/docs/components.html")
            patterns = ff.run(PATTERNS, {}, "the pattern check")
            self.assertGreater(patterns["count"], 50)
            if patterns["bad"]:
                errors.append(f"patterned, though you can select them: {patterns['bad']}")
            errors += ff.run(LOOK, {}, "the lighter fallback switch check")["errors"]
            self.assertEqual(errors, [], "\n".join(errors))
            print(f"Own look: focus styles, lift and press timings, reduced motion, the lighter fallback, lifts and "
                  f"progress all hold; {patterns['count']} selectable examples have no pattern")
        finally:
            if ff:
                ff.close()
                ff.s.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
