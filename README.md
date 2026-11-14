# Enamel

Enamel is a design system for controller-first apps that feel at home in Steam's Gaming Mode: Steam's own baseline with one accent colour on top, like a thin coat of enamel over steel.

It holds design tokens (CSS custom properties), the rules for using them, and the first components.

Enamel is built with Claude Code from a designer's specs and decisions. [How this repo is built](docs/how-this-repo-is-built.md) explains how the work moves from an idea to a tested release: the planning board, the commands and helper agents, the issue sizes and their checks, and the decision log.

## The four token groups

All tokens live in [`tokens/enamel.css`](tokens/enamel.css), in one `:root` block, and start with `--en-`.

- **Group A, Steam baseline.** Greys, status colours, shadows, corner radius, gap, focus space and line height, matched to Steam's Gaming Mode so an Enamel app sits naturally beside it. Labelled *Steam baseline*.
- **Group B, Enamel brand.** The named accents (each a colour and its ink; coral is the default), the active accent with its ink and glow, and the pill radius. Labelled *Enamel*. Switch the accent with `data-en-accent`; see the Accents section of `DESIGN.md`.
- **Group C, Semantic.** What apps actually use: surfaces, text, focus, status, font, type sizes, spacing and sizes. These point at Groups A and B. They're labelled *Enamel*, except the type sizes, gutter, inset and sizes, which are matched to Steam's Gaming Mode and labelled *Steam baseline*.
- **Group D, Motion.** Durations, curves, the focused tile's growth and the focus ring's breathing. Each is labelled *Steam baseline* (matched to how Gaming Mode moves) or *Enamel*. The components use them; reduced motion is described in the Motion section of `DESIGN.md`.

## Using it in an app

1. Copy `tokens/enamel.css` and `DESIGN.md` into the app.
2. Note the version you copied (from [`VERSION`](VERSION), currently 0.13.0) next to them, for example in a comment at the top of the copied CSS or in the app's README.
3. Link `enamel.css` before the app's own styles. Use only the Group C tokens, and follow the rules in `DESIGN.md`.
4. To use the components, also copy [`components/enamel-components.css`](components/enamel-components.css) and link it after `enamel.css`.
5. For the picker dialog and the toast, also copy [`components/enamel-components.js`](components/enamel-components.js) and load it after the stylesheets. Apps with their own key handling should read the "Behaviour script" part of `DESIGN.md`.

## Versions and tags, for apps

Every released version has an annotated git tag named `v` plus the version, for example `v0.11.1`. A version counts as released only when its `CHANGELOG.md` entry is written and its tag is pushed; work in progress on `main` is never a release, even when `VERSION` already shows the next number. Each changelog entry says which apps should adopt it and when. Pushed tags are never moved or deleted. The history starts at 0.11.1, the first tag; older versions are listed in `CHANGELOG.md` but have no tags.

- **Files at a given tag:** in a clone, `git fetch --tags origin`, then `git show v0.11.1:DESIGN.md` prints one file as it was at that version, and `git archive v0.11.1 tokens components DESIGN.md VERSION LICENSE NOTICE.md | tar -x -C <folder>` writes those files into a folder.
- **The newest tag:** `git ls-remote --tags --sort=-v:refname origin "v*"` lists the tags on GitHub, newest first (ignore lines ending in `^{}`); in a clone, `git tag --list "v*" --sort=-v:refname` does the same.
- **An app's check** compares its copy with the files at the tag for the version it records. It fails only when the copy differs from that tag. When a newer tag exists it at most warns, so an app is never failed by work in progress here or by a release it hasn't adopted yet.

## Components

`components/enamel-components.css` has eleven components, in plain CSS: hint bar, tabs, list row, tile, button, toggle, progress, side menu, action bar, picker dialog and toast. The picker and the toast get their behaviour from `components/enamel-components.js`. Class names start with `en-`. State comes from standard attributes (`aria-selected`, `aria-pressed`, `aria-current`, `disabled`), and focus shows on keyboard focus or on `data-focused="true"`. DESIGN.md Part 3 lists each one's classes and states.

Components move on their own (focus, state changes) and honour reduced motion; see the Motion section of `DESIGN.md`.

Token names are version 0 and may change until Kettle Video ships, so check `CHANGELOG.md` and `DECISIONS.md` when you update. [`MIGRATION.md`](MIGRATION.md) lists every name from before the move to the `en` prefix next to its new name, file names included.

## Who uses this

- Kettle Video (on this device at `~/Development/kettle-video`; its GitHub repo is still `enamelware/media-player`) uses this system through an unmodified copy in its `vendor/enamel/` folder.
- Apps update by re-running their own sync script after a new VERSION here. Nothing in this repo reaches into an app.
- Never edit an app's files from this repo.
- Renaming or removing a token, a component class or a state attribute breaks apps. Before doing so, stop and report what would break.
- Gaps found while building an app are fixed here, then the app re-syncs. Apps never style around a missing part: they add the gap to the standing issue "Gaps found by the apps" (#7, label `gaps`).

## Style guide

Open the style guide with the Enamel style guide launcher, never by double-clicking the html files.

The launcher is "Enamel style guide" on the Desktop. It runs `tools/serve.py`, which serves this repo on this device only (127.0.0.1) and opens the page in the browser. Firefox here is sandboxed and can't load `tokens/enamel.css` from a page opened as a file, so a double-clicked page shows up unstyled. Close the launcher's terminal window to stop the server.

It has five pages, with the same left menu on each:

- [`docs/overview.html`](docs/overview.html), the overview (written by hand).
- [`docs/index.html`](docs/index.html), the token reference: every token with its value, a sample and where it came from, plus contrast results and the rules.
- [`docs/components.html`](docs/components.html), the Components page: every component in every state, with the HTML to copy.
- [`docs/motion.html`](docs/motion.html), the Motion page: every motion token with a demo, focus moving along tiles and rows, controls you can operate, and the same focus demo in reduced motion.
- [`docs/resize.html`](docs/resize.html), the Resize page: every component in a frame you resize by dragging its corner, and a row of fixed frames from the smallest supported box to very wide, each labelled by its width.

Each page's menu is written with that page already marked, so it works without scripts. The menu's layout is in `docs/site.css`; `docs/site.js` marks the section in view while scrolling, runs the accent and motion switches at the bottom of the menu, and runs the Motion page demos.

## Other files

- `DESIGN.md`: tokens and rules for people and AI coding tools.
- `DECISIONS.md`: why things are the way they are.
- `docs/how-this-repo-is-built.md`: how the work is planned, built and checked.
- `CHANGELOG.md`: what changed in each version.
- `LICENSE` and `NOTICE.md`: the licence and the notice that goes with it.
- `tools/`: scripts (system Python, standard library only).
  - `build_design_md.py` regenerates the token tables in `DESIGN.md`.
  - `build_styleguide.py` regenerates `docs/index.html`, `docs/components.html` (whose examples live in `components_page.py`), `docs/motion.html` (from `motion_page.py`) and `docs/resize.html` (from `resize_page.py`), writes the left menu into `docs/overview.html` between its menu markers, and writes the version from `VERSION` into the header comments of the two stylesheets.
  - `check_guide.py` checks the style guide and components: pages, menu, colours, sizes, contrast and motion, and that nothing in the tokens, components, style guide, `DESIGN.md` or this README names a device, an aspect ratio or a screen size. With `browser_check.py` it also loads every page in the device's Firefox, in full and in reduced motion.
  - `release_check.py`, run by `check_guide.py`, fails if anything that would be published holds Steam's own names or anything personal (personal paths, email addresses other than the GitHub noreply address, Steam IDs, secrets). Its public-text check also fails on what the "Public writing" rule in `CLAUDE.md` rules out and a pattern can find: home folder paths, "owner" wording, the old account name, commit email addresses, claude.ai links, and links to private repos or the private planning board.
  - `serve.py` serves the repo locally and opens the style guide (used by the launcher).

## Licence

MIT. See [`LICENSE`](LICENSE). [`NOTICE.md`](NOTICE.md) covers the values matched to Steam's Gaming Mode, trademarks, and the Enamel and Kettle names and the Kettle wordmark, which the licence does not cover.

Enamel is not affiliated with Valve. Steam and Steam Deck are trademarks of Valve Corporation.
