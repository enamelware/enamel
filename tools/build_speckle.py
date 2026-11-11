# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Generate Enamel's speckle images and write them into tokens/enamel.css.

Three static images, drawn at random from fixed seeds, so running this again
changes nothing. They are built into the tokens as SVG, because apps sync three
main files and a separate image would need a change to each app's sync script.

  --en-speckle-fill          cream flecks for a progress fill; the accent shows
                             through, so it follows whichever accent is active
  --en-speckle-page          very faint cream flecks for the page ground
  --en-speckle-page-accent   the occasional fleck in the accent: a mask, which
                             the components fill with the active accent

Flecks that cross an image's edge are drawn again on the opposite edge, so the
images tile without a seam, and they are placed at random, not on a grid. The
two page images differ in size, so together they repeat far apart.

    python3 tools/build_speckle.py
"""
import os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enamel_tokens as en

CREAM = "#F2EBDA"
# The strongest a page fleck gets. tools/check_guide.py uses it to check text
# that stands beside the speckle, so it is written once, here.
PAGE_STRONGEST = 0.1
ACCENT_STRONGEST = 0.1  # the accent flecks: --en-c-speckle-accent in the components

# name: (seed, width, height, colour, [(fleck width, how many, opacity)])
IMAGES = {
    "--en-speckle-fill": (18, 256, 32, CREAM, [(1, 44, 0.9), (1.5, 26, 0.9), (2, 8, 0.9)]),
    "--en-speckle-page": (180, 640, 640, CREAM, [(1, 70, 0.06), (1.5, 44, 0.08), (2.5, 14, PAGE_STRONGEST)]),
    "--en-speckle-page-accent": (1800, 704, 704, "#000000", [(1.5, 14, 1), (2.5, 6, 1)]),
}


def flecks(rng, width, height, size, count):
    """The path data for `count` flecks at random places. A fleck near an edge
    is drawn on the opposite edge too, so the image tiles without a seam."""
    out = []
    for _ in range(count):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        xs = [x] + [x - width] * (x > width - size) + [x + width] * (x < size)
        ys = [y] + [y - height] * (y > height - size) + [y + height] * (y < size)
        out += [f"M{a:.1f} {b:.1f}h0" for a in xs for b in ys]
    return "".join(out)


def svg(name):
    seed, width, height, colour, groups = IMAGES[name]
    rng = random.Random(seed)
    paths = "".join(f"<path stroke-width='{size:g}' stroke-opacity='{opacity:g}' d='{flecks(rng, width, height, size, count)}'/>"
                    for size, count, opacity in groups)
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>"
            f"<g fill='none' stroke='{colour}' stroke-linecap='round'>{paths}</g></svg>")


def value(name):
    encoded = svg(name).replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")
    return f'url("data:image/svg+xml,{encoded}")'


def main():
    with open(en.CSS, encoding="utf-8") as f:
        text = f.read()
    new = text
    for name in IMAGES:
        new, n = re.subn(rf"^(  {re.escape(name)}: )[^;]*;", lambda m: f"{m.group(1)}{value(name)};", new, flags=re.M)
        if n != 1:
            sys.exit(f"tokens/enamel.css must declare {name} once")
    if new != text:
        with open(en.CSS, "w", encoding="utf-8") as f:
            f.write(new)
        print("tokens/enamel.css: speckle images updated")
    else:
        print("tokens/enamel.css: speckle images already up to date")


if __name__ == "__main__":
    main()
