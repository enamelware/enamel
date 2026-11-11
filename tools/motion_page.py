"""The Motion page, docs/motion.html, written by build_styleguide.py.

Sections: the motion tokens (each with its value, source label and a live
demo with a replay button), focus moving along tiles and rows, controls you
can operate, and the same focus demo forced into reduced motion. The demos
are run by docs/site.js; the components move on their own, from
components/enamel-components.css. Standard library only.
"""
import html, re
import components_page as cp

MENU_SECTIONS = [("tokens", "Motion tokens"), ("focus", "Focus"), ("press", "Lift and press"), ("controls", "Controls"),
                 ("overlays", "Picker, toast, action bar"), ("reduced", "Reduced motion")]

# How each token's demo moves (docs/site.js reads data-motion-demo).
DEMOS = {
    "--en-motion-fast": ("duration", "A dot crosses the track in this time."),
    "--en-motion-medium": ("duration", "A dot crosses the track in this time."),
    "--en-motion-slow": ("duration", "A dot crosses the track in this time."),
    "--en-ease-standard": ("curve", "The dot crosses over --en-motion-slow with this curve, drawn above it."),
    "--en-ease-enter": ("curve", "The dot crosses over --en-motion-slow with this curve, drawn above it."),
    "--en-ease-pulse": ("curve", "The dot crosses over --en-motion-slow with this curve, drawn above it. "
                                 "Each half of a breath uses it, so the ring dims and brightens smoothly."),
    "--en-focus-ring-start": ("ringin", "The ring starts this thick and narrows to --en-focus-ring-width."),
    "--en-motion-ring": ("ringin", "The ring narrows to its width in this time; the breathing starts after it."),
    "--en-motion-dialog": ("duration", "A picker dialog's panel fades in, and out, in this time."),
    "--en-focus-scale": ("scale", "The box grows to this size over --en-motion-slow, as a focused tile does."),
    "--en-pulse-duration": ("pulse", "One breath of the ring takes this long."),
    "--en-pulse-count": ("pulse", "The ring breathes this many times, then rests fully visible."),
    "--en-pulse-min": ("pulse", "The ring dims to this opacity half-way through each breath."),
}


def e(s):
    return html.escape(str(s), quote=True)


# The CSS curve keywords as cubic-bezier control points.
KEYWORDS = {"ease": (0.25, 0.1, 0.25, 1), "ease-in": (0.42, 0, 1, 1), "ease-out": (0, 0, 0.58, 1),
            "ease-in-out": (0.42, 0, 0.58, 1), "linear": (0, 0, 1, 1)}


def curve_path(value):
    """An SVG path for a cubic-bezier() value or a curve keyword, in a 100 by 40 box."""
    m = re.fullmatch(r"cubic-bezier\(([^)]*)\)", value.strip())
    x1, y1, x2, y2 = (float(v) for v in m.group(1).split(",")) if m else KEYWORDS[value.strip()]
    pt = lambda x, y: f"{x * 100:g} {40 - y * 40:g}"
    return f"M0 40 C{pt(x1, y1)} {pt(x2, y2)} 100 0"


def token_card(t):
    kind, what = DEMOS[t["name"]]
    did = "demo" + t["name"][4:]
    if kind in ("duration", "curve"):
        stage = (f'<div class="site-track" id="{did}" data-motion-demo="{kind}" data-token="{e(t["name"])}">'
                 '<span class="site-track__dot"></span></div>')
        if kind == "curve":
            stage = (f'<svg class="site-curve" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">'
                     f'<path d="{curve_path(t["value"])}"/></svg>' + stage)
    elif kind == "ringin":
        stage = f'<div class="site-ring" id="{did}" data-motion-demo="ringin" data-token="{e(t["name"])}"></div>'
    elif kind == "scale":
        stage = f'<div class="site-grow" id="{did}" data-motion-demo="scale" data-token="{e(t["name"])}"></div>'
    else:
        stage = f'<div class="site-ring" id="{did}" data-motion-demo="pulse" data-token="{e(t["name"])}"></div>'
    return (f'<figure class="site-state site-token">'
            f'<div class="site-stage site-stage--center">{stage}</div>'
            f'<figcaption><code class="site-token__name">{e(t["name"])}</code> '
            f'<code>{e(t["value"])}</code> <span class="site-label">{e(t["label"])}</span></figcaption>'
            f'<p class="site-note">{e(what)}</p>'
            f'<div class="site-actions"><button class="en-button" data-replay="{did}">Replay</button></div></figure>')


def tiles(prefix):
    titles = [("Copper Tide Rising", 3), ("Driftwood · Episode 5", 18), ("Orchard Weather · Part 1", 11)]
    out = []
    for i, (title, value) in enumerate(titles):
        f = ' data-focused="true"' if i == 0 else ""
        out.append(f'  <div class="en-tile"{f}>\n'
                   '    <div class="en-tile__frame">Paused frame</div>\n'
                   f'    <div class="en-progress en-progress--thin" style="--value: {value}%"><span class="en-progress__fill"></span></div>\n'
                   f'    <div class="en-tile__title">{e(title)}</div>\n'
                   '  </div>')
    return f'<div class="en-shelf" id="{prefix}-tiles">\n' + "\n".join(out) + "\n</div>"


def rows(prefix):
    items = [("Orchard Weather", "2 parts"), ("Copper Tide Rising", "1995"), ("Driftwood", "Episode 5")]
    out = []
    for i, (title, meta) in enumerate(items):
        f = ' data-focused="true"' if i == 0 else ""
        out.append(f'  <li><div class="en-row"{f}>{e(title)} <span class="en-row__meta">{e(meta)}</span></div></li>')
    return f'<ul class="en-rows" id="{prefix}-rows">\n' + "\n".join(out) + "\n</ul>"


def focus_demo(prefix):
    return (f'<figure class="site-state site-state--wide"><div class="site-stage">\n{tiles(prefix)}\n</div>'
            f'<figcaption>Tiles</figcaption>'
            f'<div class="site-actions"><button class="en-button" data-move-focus="{prefix}-tiles">Move focus</button></div></figure>\n'
            f'<figure class="site-state site-state--wide"><div class="site-stage">\n{rows(prefix)}\n</div>'
            f'<figcaption>List rows</figcaption>'
            f'<div class="site-actions"><button class="en-button" data-move-focus="{prefix}-rows">Move focus</button></div></figure>')


CONTROLS = '''<div class="site-states" data-demo-controls>
<figure class="site-state site-state--wide"><div class="site-stage site-stage--raised site-stage--flush">
<div class="en-row">
  Keep screen awake
  <button class="en-toggle" aria-pressed="false" aria-label="Keep screen awake"></button>
</div>
</div><figcaption>Toggle</figcaption>
<p class="site-note">Press it. The thumb slides and the track colour fades over --en-motion-medium.</p></figure>
<figure class="site-state site-state--wide"><div class="site-stage">
<div>
  <div class="en-progress__head"><span id="demo-progress-text">40%</span><span>Scanning</span></div>
  <div class="en-progress" id="demo-progress" role="progressbar" aria-label="Scan my folders" aria-valuenow="40" style="--value: 40%"><span class="en-progress__fill"></span></div>
</div>
</div><figcaption>Progress</figcaption>
<p class="site-note">The fill glides to each new value over --en-motion-slow.</p>
<div class="site-actions"><button class="en-button" data-progress-step="demo-progress">Add 20%</button></div></figure>
<figure class="site-state site-state--wide"><div class="site-stage site-stage--center">
<div class="en-tabs" role="tablist" aria-label="Library">
  <button class="en-tab" role="tab" aria-selected="true">Movies <span class="en-tab__count">3</span></button>
  <button class="en-tab" role="tab" aria-selected="false" id="demo-new-tab">TV shows <span class="en-tab__count">1</span><span class="en-dot" role="img" aria-label="New"></span></button>
  <button class="en-tab" role="tab" aria-selected="false">Music <span class="en-tab__count">0</span></button>
</div>
</div><figcaption>Tabs</figcaption>
<p class="site-note">Press one. The selected pill's background fades over --en-motion-medium. The new dot fades in over --en-motion-medium.</p>
<div class="site-actions"><button class="en-button" data-new-dot="demo-new-tab">Show the new dot again</button></div></figure>
<figure class="site-state site-state--wide"><div class="site-stage site-stage--raised site-stage--flush">
<ul class="en-menu" id="demo-menu">
  <li><div class="en-menu__item" aria-current="page">Movies</div></li>
  <li><div class="en-menu__item" data-focused="true">TV shows</div></li>
  <li><div class="en-menu__item">Scan my folders</div></li>
</ul>
</div><figcaption>Side menu</figcaption>
<p class="site-note">The focus bar grows from the centre and the current item's glow fades, over --en-motion-medium.</p>
<div class="site-actions"><button class="en-button" data-move-focus="demo-menu">Move focus</button>
<button class="en-button" data-make-current="demo-menu">Make the focused item current</button></div></figure>
</div>'''


def rows_list():
    films = ["Orchard Weather", "Copper Tide Rising", "Driftwood", "Lantern Street", "Quiet Harbour", "The Glasshouse Year",
             "North of the Orchard", "Ember"]
    return "\n".join(f'  <li><div class="en-row">{e(f)}</div></li>' for f in films)


def page(menu_block, groups):
    motion = next(g for g in groups if g["title"] == "Motion")
    cards = "\n".join(token_card(t) for t in motion["tokens"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enamel motion</title>
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
<!-- Generated by tools/build_styleguide.py from tools/motion_page.py. Do not edit by hand. -->
{menu_block}
<main class="site-main">
<h1>Motion</h1>
<p>Motion marks focus or a change of state, nothing else. Its durations and curves are matched to Steam's
Gaming Mode where a clear match was found (<b>Steam baseline</b>), so moving into an Enamel app feels familiar, and are
Enamel's choice otherwise (<b>Enamel</b>).</p>
<p class="site-note">Use the Motion switch at the bottom of the menu to see the whole guide in reduced motion. Without
a choice there, the guide follows the device's setting. The demos are shown side by side, so several look focused
at once. In an app, only one element shows focus at a time.</p>

<section id="tokens">
<h2>Motion tokens</h2>
<p>Every token in the Motion group, with a demo. Press Replay to run it again.</p>
<div class="site-states">
{cards}
</div>
</section>

<section id="focus">
<h2>Focus</h2>
<p>Move focus along a shelf of tiles and a list. A focused tile grows to <code>--en-focus-scale</code> over
<code>--en-motion-slow</code> without moving its neighbours. Its ring appears <code>--en-focus-ring-start</code> thick and
narrows over <code>--en-motion-ring</code>, then breathes <code>--en-pulse-count</code> times and rests fully visible,
about five seconds after focus arrived. Each time focus arrives it all starts again. When focus leaves, the tile and
ring return over <code>--en-motion-fast</code>. A row's colours fade over <code>--en-motion-fast</code>.</p>
<div class="site-states">
{focus_demo("focus")}
</div>
</section>

<section id="press">
<h2>Lift and press</h2>
<p>Only things you press move physically: buttons and picker rows. When focus arrives the face rises
<code>--en-lift</code> over <code>--en-motion-medium</code> as its underside appears, and settles back over
<code>--en-motion-fast</code> when focus leaves. Hold a press: it drops onto its underside over
<code>--en-motion-fast</code> and darkens, and release springs it back over <code>--en-motion-medium</code>.</p>
<div class="site-states">
<figure class="site-state site-state--wide"><div class="site-stage site-stage--raised site-stage--start">
<div class="site-actions" id="demo-press">
  <button class="en-button" data-focused="true">Rescan library</button>
  <button class="en-button">Scan my folders</button>
  <button class="en-button">Remove</button>
</div>
</div><figcaption>Buttons</figcaption>
<div class="site-actions"><button class="en-button" data-move-focus="demo-press">Move focus</button></div></figure>
</div>
</section>

<section id="controls">
<h2>Controls</h2>
<p>These controls work. Press them to see each change of state.</p>
{CONTROLS}
</section>

<section id="overlays">
<h2>Picker, toast and action bar</h2>
<p>Open each picker and close it with its Cancel row, Escape, or by choosing a row. The darkened, blurred page
appears at once and the panel fades in over <code>--en-motion-dialog</code>; it leaves the same way. The focused row
rises and presses as a button does. A toast slides in from the right over <code>--en-motion-slow</code> with
<code>--en-ease-enter</code>; three seconds after its last update it fades out where it is, over the same time with
the same curve, as Steam's own toast does. All of this is run by
<code>components/enamel-components.js</code>, the same file apps use.</p>
<div class="site-states">
<figure class="site-state site-state--wide"><figcaption>Picker dialog</figcaption>
{cp.open_buttons("motion")}
{cp.live_pickers("motion")}
</figure>
<figure class="site-state site-state--wide"><figcaption>Toast</figcaption>
{cp.TOAST_BUTTONS}
</figure>
<figure class="site-state site-state--wide"><div class="site-stage site-stage--flush">
<div class="site-scroller" id="demo-actionbar">
{cp.actionbar()}
<ul class="en-rows">
{rows_list()}
</ul>
</div>
</div><figcaption>Action bar</figcaption>
<p class="site-note">Scroll the list: the bar stays docked and opaque. It has no motion of its own; its buttons behave
like every other button.</p>
<div class="site-actions"><button class="en-button" data-move-focus="demo-actionbar">Move focus along its buttons</button></div>
</figure>
</div>
</section>

<section id="reduced" data-en-motion="reduced">
<h2>Reduced motion</h2>
<p>The same focus demo, forced into reduced motion with <code>data-en-motion="reduced"</code> on this section. There
is no breathing, no growing, no narrowing, no rising and no sliding: the ring simply appears, a focused button turns
cream at once, a press only darkens, the colours still fade over <code>--en-motion-fast</code>, and focus ends up
exactly as visible as in full motion.</p>
<div class="site-states">
{focus_demo("reduced")}
<figure class="site-state site-state--wide"><figcaption>Picker and toast</figcaption>
<p class="site-note">In reduced motion they simply appear and disappear.</p>
<div class="site-actions"><button class="en-button" data-open-picker="reduced-confirm">Open the confirm</button>
<button class="en-button" data-toast="show" data-toast-element="reduced-toast">Show a toast</button></div>
{cp.dialog(cp.picker("confirm", live=True), "reduced-confirm")}
<div class="en-toast" id="reduced-toast" role="status" aria-live="polite" hidden><span class="en-toast__text"></span></div>
</figure>
</div>
</section>
</main>
<footer class="site-footer">Enamel is not affiliated with Valve. Steam and Steam Deck are trademarks of Valve Corporation.</footer>
</body>
</html>
"""
