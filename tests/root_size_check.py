# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issues #15 and #18: --en-root-size scales everything, pixels included, through
zoom, and Enamel never sets the root font size. In the device's Firefox (headless,
its own temporary profile; Steam is never touched), a frame narrower than 100rem
links the tokens and the components, once as they are and once with
--en-root-size set to 125% on <html>, and measures every size token and
component variable:

  - the root font size is the browser's own (16px) both times;
  - every size, written in rem or in px (through var() too), comes out exactly
    1.25 times bigger.

Sizes that depend on their container (cqi), mix px and rem, or are not a
length (percentages, ratios, shadows, times) are left out; the unit tests
check those are the only ones.

    scripts/test.sh check root_size_check
"""
import functools
import http.server
import json
import os
import re
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import browser_check  # noqa: E402
from serve import Handler  # noqa: E402

SCALE = 1.25


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def variables():
    """{name: value} for every token and component variable on :root."""
    out = {}
    for path in (("tokens", "enamel.css"), ("components", "enamel-components.css")):
        css = re.sub(r"/\*.*?\*/", "", read(*path), flags=re.S)
        block = re.search(r":root\s*\{([^}]*)\}", css).group(1)
        for name, value in re.findall(r"(--en-[a-z0-9-]+)\s*:\s*([^;]+);", block):
            out[name] = " ".join(value.split())
    return out


def resolved(table, value):
    for _ in range(10):
        value = re.sub(r"var\((--en-[a-z0-9-]+)\)", lambda m: f"({table[m.group(1)]})", value)
    return value


def kinds():
    """(names that must scale, names that must stay fixed)."""
    table = variables()
    scales, fixed = [], []
    for name, value in table.items():
        full = resolved(table, value)
        # Shadows (Steam's, and Enamel's satin, lift, press and sunken ones) are not a length.
        if name.startswith("--en-shadow") or re.search(r"cqi|%|ms\b|\ds\b|#|[a-z]+-[a-z]|rgba?\(|inset",
                                                       full.replace("var(", "")):
            continue
        rem, px = bool(re.search(r"\drem\b", full)), bool(re.search(r"\dpx\b", full))
        if rem and not px:
            scales.append(name)
        elif px and not rem:
            fixed.append(name)
    return scales, fixed


DOC = """<!doctype html><html lang="en" style="{root}"><head><meta charset="utf-8">
<link rel="stylesheet" href="../tokens/enamel.css"><link rel="stylesheet" href="../components/enamel-components.css">
</head><body style="margin:0"><div id="probe" style="display:block;height:1px"></div></body></html>"""

MEASURE = r"""
async (args) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const names = JSON.parse(args.names), out = {};
  for (const [key, doc] of [['plain', args.plain], ['scaled', args.scaled]]) {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:0;top:0;width:640px;height:480px;border:0';
    f.srcdoc = doc;
    document.body.append(f);
    for (let i = 0; i < 100 && !(f.contentDocument && f.contentDocument.getElementById('probe')
         && f.contentDocument.styleSheets.length >= 2); i++) await wait(50);
    await wait(100);
    const d = f.contentDocument, w = f.contentWindow, probe = d.getElementById('probe');
    const sizes = { root: parseFloat(w.getComputedStyle(d.documentElement).fontSize) };
    for (const n of names) {
      probe.style.width = `var(${n})`;
      sizes[n] = probe.getBoundingClientRect().width;
    }
    out[key] = sizes;
    f.remove();
  }
  return JSON.stringify(out);
}
"""


class RootSize(unittest.TestCase):
    def test_every_rem_size_scales_and_every_px_size_stays(self):
        scales, fixed = kinds()
        self.assertGreater(len(scales), 30, f"too few sizes found to scale: {scales}")
        self.assertIn("--en-size-target", fixed)
        self.assertIn("--en-focus-ring-width", fixed)
        self.assertIn("--en-lift", fixed)

        class Quiet(Handler):
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        ff = None
        try:
            ff = browser_check.Firefox(False)
            ff.load(f"http://127.0.0.1:{server.server_port}/docs/index.html")
            out = ff.run(MEASURE, {"names": json.dumps(scales + fixed), "plain": DOC.format(root=""),
                                   "scaled": DOC.format(root=f"--en-root-size: {SCALE * 100:g}%")},
                         "the root size check")
            plain, scaled = out["plain"], out["scaled"]
            errors = [f"script errors: {ff.errors()}"] if ff.errors() else []
            if abs(plain["root"] - 16) > 0.01:
                errors.append(f"the root font size is {plain['root']}px as shipped, not the browser's 16px")
            if abs(scaled["root"] - 16) > 0.01:
                errors.append(f"with --en-root-size at {SCALE * 100:g}% the root font size is {scaled['root']}px, so it was set")
            for n in scales + fixed:
                if plain[n] <= 0 or abs(scaled[n] - plain[n] * SCALE) > 0.05:
                    errors.append(f"{n} is {plain[n]}px, then {scaled[n]}px: it does not scale with the interface size")
            self.assertEqual(errors, [], "\n".join(errors))
            print(f"Interface size: at {SCALE * 100:g}% the root font size stays {scaled['root']:g}px; {len(scales)} rem "
                  f"sizes and {len(fixed)} px sizes all scale by {SCALE:g}")
        finally:
            if ff:
                ff.close()
                ff.s.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
