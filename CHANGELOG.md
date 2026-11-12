# Changelog

Each version of Enamel, newest first. Apps copy a version and re-sync after a new one; check the entry before updating. A version is released only once its entry is written and its git tag (for example `v0.6.0`) is pushed; each entry says which apps should adopt it and when. "Visual" means things look or move differently; no existing name changed unless the entry says so.

## 0.12.0, 2026-11-12 (visual)

A destructive row (#21), found by Kettle Video for the Quit row in its Home menu (enamelware/media-player#98, listed in Enamel's "Gaps found by the apps", #7). Everything that was there before looks the same.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed. No token or component variable was added: the new row uses the error red and the white that were there.

**Who should adopt it, and when:** Kettle Video, through its own "Bring in Enamel 0.12.0" issue, before it builds its Home polish (its #98 waits for this). Apps that don't need it can adopt it whenever they next re-sync; nothing they use changes.

**What each app must do to pick it up:**
- Re-sync the three main files.
- Add the destructive class to the row of an action that closes, removes or deletes, such as Quit: `.en-picker__row--destructive` on a picker row, `.en-row--destructive` on a list row. Use it for nothing else.
- For an icon, put it in front of the row's text, hidden from screen readers, drawn as on the Components page.
- `data-pressed="true"` works on a destructive list row too, as on buttons and picker rows.

Added (classes, new):
- `.en-row--destructive` and `.en-picker__row--destructive`, new: a list row or picker row with a red face and white text and icon in every state. Focus raises it onto the accent underside instead of turning it grey or cream, and a press drops it. Its meta or description is drawn bold. A message inside it keeps showing: its error disc turns white with a red mark.

Rules (DESIGN.md, Part 2):
- Red is a status colour like error, never a second accent, and besides errors is used only for actions that close, remove or delete.
- Text needs 4.5:1, with one exception: white on the error red in a destructive row is 4.44:1, allowed because it reaches APCA Lc 75 and its text is large or bold. The guide's contrast check holds this one pair to APCA instead.

## 0.11.1, 2026-11-11

Ready to go public (#19). Only wording, comments and the repo's own tools changed: nothing looks or moves differently, and every token keeps its value.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed.

**Who should adopt it, and when:** Kettle Video, straight away. The repo's history was replaced by one first commit to go public, so the older tags, v0.11.0 included, no longer exist and a check against them can't run.

**What each app must do to pick it up:** re-sync and record v0.11.1 as the adopted release. The copied files only differ in comments and in DESIGN.md's and NOTICE.md's wording; nothing else needs to change.

Changed:
- Where values come from now reads "Steam baseline", matched to Steam's Gaming Mode, or "Enamel", Enamel's own choice. The two older source labels are gone from the tokens' comments, DESIGN.md and the style guide.
- NOTICE.md says the neutral palette, spacing and motion are designed to match Steam's Gaming Mode, that Enamel includes no Valve code, class names, icons, logos or fonts, and that the MIT licence grants no rights to the Enamel or Kettle names or the Kettle wordmark.
- The style guide's examples use made-up film and show titles.
- The Overview page's before-and-after story is no longer part of the style guide. Its guidelines stay, under Rules.

Removed from the repo (not used by apps): the reference folder and the tools that read the Steam client.

History: the repo's history starts again at 0.11.1, with one first commit, and v0.11.1 is the only tag. The entries below stay as the record of each version; their tags were removed with the old history.

Added: a release check, run with the quick checks, that fails if anything that would be published holds material taken from Steam's files or anything personal.

## 0.11.0, 2026-11-06 (visual)

Enamel's own look (#18). Enamel keeps Steam's greys, layout, type and hint bar, and adds a material of its own taken from enamel kitchenware: satin surfaces, cream focus on a coral underside, a little speckle, and faces that lift and press. Nothing changes in how anything behaves.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed. The script only changes in one place: it measures the hint bar correctly at any interface size, so the toast and the picker's layer still stop at the bar's top when `--en-root-size` is not 100%. Some tokens keep their names and change their values, listed below.

**Who should adopt it, and when:** Kettle Video, through its own "Bring in Enamel" issue, when it is ready for the new look. Its onboarding work doesn't wait for this. Other apps can adopt it whenever they next re-sync.

**What each app must do to pick it up:**
- Re-sync the three main files. The new look arrives by itself; the speckle is built into the tokens, so no new file is needed.
- Set `data-pressed="true"` on a button or picker row while A is held on a controller. A stylesheet can't see a controller's press; without it, things still work and only that movement is missing.
- Choose where the page speckle goes, if anywhere: `.en-speckle` on an empty area of the page ground, never behind list text.
- Check anything of its own that assumes white focus, or that sets `--en-root-size`. That token now scales everything through zoom, pixels included, and the root font size is no longer set, so a page that read it for its own sizes gets the user's own text size.
- Check its own layouts around a focused button: a button now rises 4px and sits on a 4px underside, so whatever holds it must not clip it. Corners are bigger too.
- If it stutters on a small device, turn on the lighter fallback: `data-en-lighter="true"` on `<html>`.

Changed (visual):
- Every raised surface is satin: rows, buttons, tiles, selected tabs, filled group bands, numbered steps' marks, stat panels, the picker and toasts.
- Corners: 8px on rows, buttons, tiles and badges; 12px on panels, pickers and toasts.
- Focus: buttons, picker rows and (when one exists) fields are cream with dark text drawn as heavy as semibold (never wider, so nothing around it moves) on a 4px accent underside. Tiles have one accent ring with a soft glow. Rows lift as before. The off toggle's knob and the hint glyphs are cream.
- A primary button is now the accent colour at rest. It looked the same as any other until focused, and focused it now looks like every other button, so this is what still marks it.
- Motion: a focused button or picker row rises, drops when pressed and springs back. Reduced motion: no movement; focus switches at once and a press only darkens.
- Progress bars are a sunken dark track with a hairline edge and a speckled accent fill: 12px on their own and in a toast, 8px under tiles. A toast can now hold a progress bar.
- Picker rows are 4px apart and rounded, inside a satin panel.

Changed (token values, same names):
- `--en-focus-ring-width`: 3px to 4px.
- `--en-focus-fill`: white to cream.
- `--en-root-size`: same value and same job, but it now drives zoom instead of the root font size.

Changed (component variables, same names, now in px because they should not grow with text): `--en-c-button-padding`, `--en-c-tab-padding`, `--en-c-picker-inset`, `--en-c-menu-bar`, `--en-c-glyph-shoulder-radius`, `--en-c-progress-height` (now 12px), `--en-c-progress-thin` (now 8px).

Added (tokens, new): `--en-cream`, `--en-cream-pressed`, `--en-radius-face`, `--en-radius-panel`, `--en-satin-light`, `--en-satin-edge`, `--en-satin-shadow`, `--en-lift-shadow`, `--en-press-shadow`, `--en-sunken`, `--en-focus-underside`, `--en-lift`, `--en-speckle-fill`, `--en-speckle-page`, `--en-speckle-page-accent`.

Added (class and states, new): `.en-speckle`, the page speckle; `data-pressed="true"`, a press from a controller; `data-en-lighter="true"`, the lighter fallback.

Added (component variables, new): `--en-c-tile-glow`, `--en-c-focus-stroke`, `--en-c-speckle-accent`, `--en-c-rise`, `--en-c-satin-shadow`, `--en-c-lift-shadow`, `--en-c-press-shadow`.

Added (rules): the grid unit rule, satin never gloss, where patterns live, one border per element, one focus style per kind of element, cream as a neutral, only things you press move physically, and rem or px by one question. See DESIGN.md Part 2 and "Scaling". The style guide check enforces the grid rule and the pattern rule.

## 0.10.0, 2026-11-05 (visual)

A stat panel, a stat pair and a note (#17), found by Kettle Video for its onboarding result screen (enamelware/media-player#90, listed in Enamel's "Gaps found by the apps", #7). Everything that was there before looks the same.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed. No token was added; two component variables were, for sizes no token gives.

**Who should adopt it, and when:** Kettle Video, through its own "Bring in Enamel 0.10.0" issue, before it builds its onboarding part 2 result screen (its #90 waits for these parts). Apps that don't need them can adopt it whenever they next re-sync; nothing they use changes.

**What each app must do to pick it up:**
- Re-sync the three main files.
- Use the new classes as DESIGN.md Part 3 describes, with the markup on the Components page. Draw the note's info icon as the Components page does.
- For a stat panel, write the panel's whole text in its label ("124 movies, SD card › Films"), so screen readers read it as one item.
- For a "Not set" panel, say on its second line which kind it is, so two of them can be told apart.

Added (classes, new):
- `.en-statpanel`, `.en-statpanel__counts`, `.en-statpanel__count`, `.en-statpanel__number`, `.en-statpanel__path`, `.en-statpanel__notset`, new: a raised panel with one or two counts and the folder they refer to, or "Not set". It never takes focus.
- `.en-statpair`, new: two stat panels side by side, stacking when they cannot both fit at their minimum width.
- `.en-note`, new: one plain line of neutral information under other content, with an optional icon. Notes that follow each other stack 8px apart.

Added (component variables, new): `--en-c-statpanel-min`, the narrowest a stat panel sits beside another; `--en-c-note-gap`, between stacked notes.

Changed (visual): nothing apps see. On the style guide only, the site's paragraph style no longer reaches a note, so it shows exactly as in an app.

## 0.9.0, 2026-10-30 (visual)

Five small components for onboarding (#16), found by Kettle Video while drafting its first-launch screens (enamelware/media-player#83 and #84, listed in Enamel's "Gaps found by the apps", #7): a step label, a group band, a badge, a message inside a row, and numbered steps. Everything that was there before looks the same.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed. No token was added; the new parts use the tokens and component variables that were there.

**Who should adopt it, and when:** Kettle Video, through its own "Bring in Enamel 0.9.0" issue, before it builds its onboarding screens (its #83 and #84 wait for these parts). Apps that don't need them can adopt it whenever they next re-sync; nothing they use changes.

**What each app must do to pick it up:**
- Re-sync the three main files.
- Use the new classes as DESIGN.md Part 3 describes, with the markup on the Components page. Draw the band icons and the error mark as the Components page does.
- For a message inside a row, keep the message element in the row, empty, and put the icon and text in it when it should show, so screen readers read it.

Added (classes, new):
- `.en-steplabel`, new: a small, muted line above a page title ("Step 1 of 3"), inside the title's heading, so the two are read as one heading.
- `.en-band`, `.en-band--outline`, `.en-band__name`, `.en-band__count`, new: a group band, the header of a group of list rows, with an icon, a name in capitals and a count. Two kinds that differ by fill and icon, not by colour alone.
- `.en-badge`, new: a small, muted tag on a row ("Movies") or after a tab's label ("Beta"). Its row or tab never changes size when focus moves.
- `.en-row__message`, new: a message inside a list row in the error style, with an icon, announced politely by screen readers when it appears. It makes the row taller, never wider.
- `.en-steps`, new: numbered steps, an ordered list of two to five short steps whose text lines up after each number when it wraps.

Changed (visual): nothing apps see. On the style guide only, the site's heading style no longer reaches headings that are components (the picker's question and the group band), so they show exactly as in an app.

## 0.8.0, 2026-10-29 (visual)

Steam baseline sizes, scaled from one root size (#15). Enamel's sizes are raised to Steam's Gaming Mode, as Kettle Video's sizing report measured them (both passes, its #76 and #77): rows, buttons and text get bigger, so the whole interface looks as big as Gaming Mode. Every size except text is a multiple of 4px at the browser's normal font size, and every size follows one root size that an app can turn up or down with one token. Nothing reads the screen's size.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed. Token names are unchanged; their sizes are bigger.

**Who should adopt it, and when:** Kettle Video, through its own "Bring in Enamel" issue, after it has switched to the en names (0.7.0). Its whole interface gets bigger.

**What each app must do to pick it up:**
- Re-sync the three main files.
- Check that its own layouts still fit: rows, buttons, text and the side menu are bigger, so fewer items fit on a screen, and hints in the hint bar wrap onto a second line sooner. App code that uses the tokens through `var()` follows by itself; code that copied the old numbers needs to change.
- Size its own layout in rem or with the tokens, never in fixed pixels (a new rule in DESIGN.md), so it follows the root size with the components.
- If a device needs everything bigger or smaller, set `--en-root-size` on `<html>` (for example `112.5%`) instead of changing sizes one by one.
- The components stylesheet now sets the page's root font size (`:root { font-size: var(--en-root-size) }`). At its 100% that is the browser's own font size, exactly as before; an app that set its own root font size should set `--en-root-size` instead.

Added:
- `--en-root-size` (`100%`), new: the one root size every rem size follows. See "Scaling" in DESIGN.md.
- `--en-size-button` (`3.75rem`, 60px), new: a button's height, a minimum, never below the touch target.
- `--en-size-row-control` (`6rem`, 96px), new: a list row with a toggle or a button at its end.
- `--en-space-gutter-grid` (`clamp(3rem, 2rem + 1vw, 3.6rem)`, from 48px), new: the side gutter of grids and shelves; lists keep `--en-space-gutter`.
- `--en-size-tile-portrait` (`12.5rem`, 200px), new: a portrait cover's width, its height one and a half times it. There is no portrait tile component yet.
- `--en-space-icon` (`1rem`, 16px), new: between an icon or a button glyph and its text.
- `--en-c-menu-width` (`22.5rem`, 360px), new: the side menu's width.
- `--en-c-shelf-gap` (`1.25rem`, 20px), new: between tiles on a shelf.

Changed (visual), tokens, old and new (pixels at the normal font size):
- `--en-text-title` was `clamp(1.875rem, 1.25rem + 0.625vw, 2.25rem)` (30px), now `clamp(2.0625rem, 1.375rem + 0.6875vw, 2.475rem)` (33px).
- `--en-text-body` was `clamp(1.25rem, 0.83333rem + 0.41667vw, 1.5rem)` (20px), now `clamp(1.5rem, 1rem + 0.5vw, 1.8rem)` (24px).
- `--en-text-small` was `clamp(0.9375rem, 0.625rem + 0.3125vw, 1.125rem)` (15px), now `clamp(1.16667rem, 0.77778rem + 0.38889vw, 1.4rem)` (about 18.7px).
- `--en-text-caps` was `clamp(0.8125rem, 0.54167rem + 0.27083vw, 0.975rem)` (13px), now `clamp(1.0625rem, 0.70833rem + 0.35417vw, 1.275rem)` (17px).
- `--en-space-inset` was `clamp(1.125rem, 0.75rem + 0.375vw, 1.35rem)` (18px), now `clamp(1.25rem, 0.83333rem + 0.41667vw, 1.5rem)` (20px).
- `--en-size-row` was `3.5rem` (56px), now `4rem` (64px).
- Unchanged, already Steam's size: `--en-text-heading` (24px), `--en-space-gutter` (36px, lists), `--en-space-gap` (12px), `--en-size-bar` (60px), `--en-size-target` (44px), and every line in px.

Changed (visual), component variables, old and new:
- `--en-c-glyph-size` was `1.875rem`, now `2rem`.
- `--en-c-glyph-shoulder-radius` was `4px`, now `0.25rem` (the same at the normal font size, now following the root size).
- `--en-c-tab-padding` was `1.5rem`, now `1.75rem`.
- `--en-c-dot-size` was `0.625rem`, now `0.75rem`.
- `--en-c-tile-large-max` was `28rem`, now `28.25rem`.
- `--en-c-toggle-width` was `3.625rem`, now `3.75rem`; `--en-c-toggle-height` was `2.125rem`, now `2.25rem`; `--en-c-toggle-padding` was `3px`, now `0.25rem`.
- `--en-c-progress-height` was `8px`, now `0.5rem`; `--en-c-progress-thin` was `4px`, now `0.25rem` (the same at the normal font size).
- `--en-c-menu-item-height` was `3.875rem`, now `4.5rem`.
- `--en-c-menu-bar` was `4px`, now `0.5rem`.
- `--en-c-picker-inset` was `1.3125rem`, now `1.5rem`.
- `--en-c-text-detail` was `calc(var(--en-text-small) * 17 / 15)`, now `var(--en-text-small)`.
- Unchanged, already Steam's size: `--en-c-picker-row` (72px), `--en-c-button-padding` (36px), `--en-c-hint-gap` (28px).

Changed (visual), components:
- List rows: a row with a toggle or a button at its end is at least `--en-size-row-control` tall; rows in `.en-rows` are `--en-space-gap` apart (was `--en-space-tight`).
- Buttons: at least `--en-size-button` tall, never below the touch target (`min-height` was `var(--en-size-target)`, now `max(var(--en-size-target), var(--en-size-button))`); an icon button is square at that size. The gap between a button's icon and its label is `--en-space-icon`.
- Hint bar and toast: the gap between a glyph or icon and its text is `--en-space-icon` (was `--en-space-gap`).
- Shelf: tiles are `--en-c-shelf-gap` apart (was `--en-space-gap`).
- Side menu: `.en-menu` is `--en-c-menu-width` wide, or its space if that is narrower.
- Hint bar: its side padding was `var(--en-space-gutter)`, now `min(var(--en-space-gutter), 5%)`: the gutter wherever there is room, less in a narrow space, so two hints still share a line in the smallest supported box.
- Tabs: a single tab wider than its space wraps its label (`white-space: nowrap` replaced by `overflow-wrap: anywhere`); wherever tabs fit they look as before.
- Action bar: its minimum height was `var(--en-size-bar)`, now a button's height plus `--en-space-tight` above and below (68px at the normal font size), so a bar on one line is exactly as tall as its buttons need.
- The style guide's token reference shows each size's pixels at the normal font size, and has the new tokens.

Each value is matched to Steam's Gaming Mode; why, in DECISIONS.md.

## 0.7.0, 2026-10-27 (breaking)

The design system is now called Enamel (#12 and #13). Enamel is a design system for controller-first apps that feel at home in Steam's Gaming Mode: Steam's own baseline with one accent colour on top, like a thin coat of enamel over steel. Nothing looks or moves differently, and every value is the same as in 0.6.0: only names changed.

**Renamed (breaking):** every public name takes the `en` prefix in place of the old one: all tokens and component variables (`--en-…`), all component classes (`en-…`), the two state attributes (`data-en-accent`, `data-en-motion`), the animation names, and the behaviour script's global (`window.EnamelUI`) and events (`en-select`, `en-cancel`). The three main files are now `tokens/enamel.css`, `components/enamel-components.css` and `components/enamel-components.js`. [`MIGRATION.md`](MIGRATION.md) lists every old name next to its new one, file names included. Nothing was removed and nothing was added.

**Who should adopt it, and when:** Kettle Video, through its own switch issue (its #67), when that issue is picked up. Until then it stays on 0.6.0 with the old names, which keep working there.

**What each app must do to pick it up:**
- Rename every name in its stylesheets, markup and scripts as MIGRATION.md lists: tokens, classes, the accent and motion attributes, and the script's global and events.
- Copy the three main files by their new names: the sync script must look for them under the new names.
- Find this repo's folder as "enamel" first, then the old folder name, and compare its copy with the files at tag `v0.7.0`.
- This repo's GitHub address is now `enamelware/enamel`; GitHub forwards the old address.

Also in this version:
- README, DESIGN.md, NOTICE.md, the style guide's titles and text, and the build scripts call it Enamel. NOTICE.md says the MIT licence grants no rights to the Enamel or Kettle names or the Kettle wordmark.
- The style guide launcher on the Desktop is now "Enamel style guide".
- The structure check (`tools/check_guide.py`, run on every change) fails on any old name left outside old dated history entries, MIGRATION.md and its script.

## 0.6.0, 2026-10-21 (visual)

The responsive series (#3, #4, #5, #9 and #6): components size themselves from the space they are given, never from a screen size, a device or an aspect ratio. At the browser's normal font size, on pages up to 100rem (1600px) wide, everything looks as it did in 0.5.1 wherever there is room.

**Renamed or removed: none.** No token, component class, state attribute, component variable, or script function or event was renamed or removed. Three component variables were added (`--kt-c-tile-large-max`, `--kt-c-shelf-room`, `--kt-c-hintbar-height`); no token was added.

**Who should adopt it, and when:** Kettle Video, now. It replaces 0.5.1.

**What each app must do to pick it up:**
- Re-sync, including `components/kettle-components.js` (since #9 the script keeps the picker and the toast clear of the hint bar).
- Keep each `.kt-hintbar` and its `.kt-dialog` in the same parent element, one hint bar per parent (see #9 below).
- Give a width to any `.kt-shelf` placed where its width would come from its content (see #4 below).
- Check its own layout code that relied on the old fixed sizes. Every token whose value or unit changed is listed below, old and new. They are now rem (and some grow on very wide pages), so they equal the old pixels only at the browser's normal 16px font size and on pages up to 100rem wide. App code that does sums assuming, for example, that `--kt-size-bar` is exactly 60px, or that a tile is always 256px wide, or that sets one of the changed component variables itself, needs to change: use the tokens in `calc()` instead of copying their old numbers, and treat heights such as the row, the hint bar and the side menu item as minimums. Code that only uses the tokens through `var()` needs no change.
- Its own checks that open the browser at fixed screen sizes still work, but they now test only two of many sizes; components follow their own space, so checks at a row of widths, and with a larger browser font, catch more.

Changed (visual), from #3:
- Picker dialog: `--kt-c-picker-min` was `25vw`, now `25cqi`; `--kt-c-picker-max` was `66.667vw`, now `66.667cqi`. The picker stays as wide as its longest row, but its limits are now a quarter and two thirds of the space its dialog gives it, not of the whole screen. `.kt-dialog` is now a size container (`container-type: inline-size`) so this works. Longer text still wraps.
- Toast: `--kt-c-toast-width` was `35vw` (a fixed width), now `28rem` (448px at the browser's normal font size), and it is now the widest the toast grows: the toast is as wide as its text (`width` was `var(--kt-c-toast-width)`, now `fit-content`), and never wider than its space less a gutter (`max-width` was `100%`, now `min(var(--kt-c-toast-width), 100% - var(--kt-space-gutter))`). Longer text wraps (`overflow-wrap: anywhere` added, so even a single long word breaks). It still sits at the bottom right above the hint bar, slides in from the right, fades out in place, and in reduced motion simply appears and disappears.
- Action bar: when its buttons don't fit on one line they wrap onto another and the bar gets taller (`flex-wrap: wrap` added), so a label is never cut short; a single button wider than the bar wraps its own label (`overflow-wrap: anywhere` added). Its padding was `0 var(--kt-space-gutter)`, now `var(--kt-space-tight) var(--kt-space-gutter)`, so wrapped lines don't touch its edges; at one line it looks exactly as before.
- A toast without an icon no longer keeps an empty space where the icon would be (`.kt-toast__icon[hidden]` is now hidden), so it hugs its text.
- The picker and toast measurements no longer name where they were measured in the stylesheet's comments.

Changed (visual), from #4: text and spacing in rem, every other component sized from its content and space, and the smallest supported box. At the browser's normal font size (16px), on pages up to 100rem (1600px) wide, every size below is exactly what it was wherever there is room; only in a smaller space do tiles get narrower and rows of hints or tabs wrap. A larger browser font now makes text, spacing and components larger. On wider pages, text, the gutter and the inset grow evenly by at most a fifth, reached at 160rem.
- Tokens, old and new:
  - `--kt-text-title` was `30px`, now `clamp(1.875rem, 1.25rem + 0.625vw, 2.25rem)`.
  - `--kt-text-heading` was `24px`, now `clamp(1.5rem, 1rem + 0.5vw, 1.8rem)`.
  - `--kt-text-body` was `20px`, now `clamp(1.25rem, 0.83333rem + 0.41667vw, 1.5rem)`.
  - `--kt-text-small` was `15px`, now `clamp(0.9375rem, 0.625rem + 0.3125vw, 1.125rem)`.
  - `--kt-text-caps` was `13px`, now `clamp(0.8125rem, 0.54167rem + 0.27083vw, 0.975rem)`.
  - `--kt-space-gutter` was `36px`, now `clamp(2.25rem, 1.5rem + 0.75vw, 2.7rem)`.
  - `--kt-space-inset` was `18px`, now `clamp(1.125rem, 0.75rem + 0.375vw, 1.35rem)`.
  - `--kt-space-gap` was `12px`, now `0.75rem` (does not grow).
  - `--kt-space-tight` was `4px`, now `0.25rem` (does not grow).
  - `--kt-size-row` was `56px`, now `3.5rem`, used as a minimum height.
  - `--kt-size-bar` was `60px`, now `3.75rem`, used as a minimum height.
  - Unchanged on purpose: `--kt-size-target` (44px, the smallest touch target), `--kt-radius`, `--kt-radius-pill`, `--kt-focus-ring-width`, `--kt-focus-ring-offset`, `--kt-focus-ring-start`, `--kt-focus-affordance` and the shadows.
- Component variables, old and new: `--kt-c-hint-gap` was `28px`, now `1.75rem`; `--kt-c-glyph-size` was `30px`, now `1.875rem`; `--kt-c-glyph-text` was `16px`, now `1rem`; `--kt-c-glyph-shoulder-width` was `48px`, now `3rem`; `--kt-c-glyph-shoulder-height` was `36px`, now `2.25rem`; `--kt-c-tab-padding` was `24px`, now `1.5rem`; `--kt-c-dot-size` was `10px`, now `0.625rem`; `--kt-c-tile-width` was `256px`, now `clamp(10rem, 40cqi, 16rem)`; `--kt-c-tile-width-large` was `448px`, now `clamp(12rem, 75cqi, var(--kt-c-tile-large-max))`; `--kt-c-button-padding` was `36px`, now `2.25rem`; `--kt-c-toggle-width` was `58px`, now `3.625rem`; `--kt-c-toggle-height` was `34px`, now `2.125rem`; `--kt-c-toggle-thumb` was `28px`, now `1.75rem`; `--kt-c-menu-item-height` was `62px`, now `3.875rem`, used as a minimum; `--kt-c-icon-size` was `24px`, now `1.5rem`; `--kt-c-picker-row` was `72px`, now `4.5rem`; `--kt-c-picker-row-tall` was `96px`, now `6rem`; `--kt-c-picker-inset` was `21px`, now `1.3125rem`; `--kt-c-text-detail` was `17px`, now `calc(var(--kt-text-small) * 17 / 15)`, so it grows with the small text. Unchanged: `--kt-c-glyph-shoulder-radius`, `--kt-c-toggle-padding`, the progress heights, `--kt-c-menu-bar`, `--kt-c-icon-stroke` and the backdrop.
- Added component variables: `--kt-c-tile-large-max` (`28rem`, the widest a large tile grows) and `--kt-c-shelf-room` (the shelf's padding, now also its scroll padding).
- Tiles take their width from their shelf: `.kt-shelf` is now a size container (`container-type: inline-size`), a tile is two fifths of it between 10rem and 16rem, and a large tile three quarters between 12rem and 28rem. The shelf's padding is worked out from the widest large tile, and the same scroll padding keeps a focused tile's ring and growth inside the shelf when it scrolls into view. A shelf placed where its width comes from its content (for example inside an inline-block or a shrinking flex item) must now be given a width, because a size container does not take its width from its tiles.
- Hint bar: `height` was `var(--kt-size-bar)`, now `min-height`; hints that don't fit wrap onto another line (`flex-wrap: wrap`, row gap `--kt-space-tight`) and the bar gets taller; padding was `0 var(--kt-space-gutter)`, now `var(--kt-space-tight) var(--kt-space-gutter)`.
- Tabs: a set of tabs that doesn't fit wraps onto another line; a tab's `height` is now a `min-height`.
- List row, side menu item and tile title: long text wraps (`overflow-wrap: anywhere`). The side menu item's `height` is now a `min-height`, with `--kt-space-tight` above and below its label.
- Icon button: `width` and `height` are now `min-width` and `min-height` (still the 44px touch target), with `--kt-space-tight` padding, so a larger icon makes it bigger, never smaller.
- Progress head line: its two parts wrap onto two lines when they don't fit side by side.
- DESIGN.md has a new rule: the smallest supported box, 20rem wide by 15rem tall, where a list row with its title and the hint bar with two hints on one line fit without overlapping and every focus ring stays visible; below it the page scrolls.
- The tokens' source comments no longer name a device; they say the value is matched to Steam's Gaming Mode. DESIGN.md's source label says the same.
- Style guide: its layout widths are in rem, and the menu moves above the page when the menu and the narrowest readable page cannot sit side by side (56.25rem) instead of below 900px. The Overview page's measurement labels show the new values.

Added to the style guide, from #5 (apps see no change from this):
- A Resize page (`docs/resize.html`), in the left menu of every page: every component in a frame you resize by dragging its corner, and a row of fixed frames from the smallest supported box (20rem) to very wide, each labelled by its width only. The live picker and toast use the same behaviour script as the Motion page.

Changed (visual), from #9: the picker and the toast always clear the hint bar, however tall it is. No token, component class, state attribute, component variable, or script function or event was renamed or removed, and no token was added.
- Until now the picker's layer and the toast stopped one fixed hint bar height (`--kt-size-bar`) above the bottom, so a hint bar that wrapped onto two lines (for example Select and Cancel in the smallest supported box) had them about 12px over its top line. Now the picker's layer meets the top of the hint bar and the toast sits just above it, at any height, in full and reduced motion and with a larger browser font.
- Added component variable: `--kt-c-hintbar-height`, where the picker's layer and the toast stop above the bottom. By default it is `var(--kt-size-bar)`, so without the behaviour script both stop where they did before. `.kt-dialog`'s `inset` was `0 0 var(--kt-size-bar) 0`, now `0 0 var(--kt-c-hintbar-height) 0`; `.kt-toast`'s `bottom` was `var(--kt-size-bar)`, now `var(--kt-c-hintbar-height)`.
- The behaviour script (`components/kettle-components.js`) now keeps `--kt-c-hintbar-height` on each hint bar's parent element at the bar's real height, and follows it whenever the bar changes height (hints wrapping, a larger font, a hint added or removed). It finds hint bars on the page when it loads and any added later.
- A hint bar that is hidden (not drawn at all) or removed changes nothing: the picker's layer and the toast keep the one-bar gap (`--kt-size-bar`) above the bottom, as before. Apps that hide their hint bar, for example during playback, see no change.
- What apps must check: a picker dialog or toast follows the hint bar that has the same parent element, or one of its ancestors. Keep the `.kt-hintbar` and the `.kt-dialog` in the same parent (or the dialog inside the bar's parent), with one hint bar per parent; the toast the script makes goes at the end of `<body>`, so it follows a hint bar whose parent is `<body>`. Kettle Video's hint bar and remove picker are both directly in `<body>`, so its markup needs no change. Its own rule that sets the remove picker's `bottom` to its shell bar height still wins over this; it can keep it, or drop it to have the picker follow the hint bar's real height.
- Style guide: the narrowest fixed frame on the Resize page also shows the picker and the toast over a hint bar whose hints, Select and Cancel, wrap onto two lines.

Added to the checks, from #6 (apps see no change from this):
- A new structure check (in `tools/check_guide.py`, run on every change) fails if a device name, an aspect ratio or a screen size appears in the tokens, the components, the style guide pages and their styles, `DESIGN.md` or `README.md`. The history and workflow files are not checked. The trademark line and the tile frame's 16:9 picture shape are allowed. Contrast ratios such as 4.5:1, font weights, times and fractions are not mistaken for one.
- What it found was cleaned up: DESIGN.md's smallest supported box rule gave its pixels as "320 by 240", which reads as a screen size; it now says "320px wide and 240px tall at the browser's normal font size". Same rule, same box. Everything else had already been cleaned up by #3 and #4.

## 0.5.1, 2026-10-19 (visual)

**Who should adopt it, and when:** Kettle Video skips it: it goes from 0.5.0 straight to 0.6.0, which includes it.

No token, component class, state attribute, or script function or event was renamed or removed. Apps only need to re-sync.

Changed (visual):
- The toast now fades out where it is when it leaves, as Steam's own toast does, instead of sliding back out to the right. It still slides in from the right, and in reduced motion it still simply appears and disappears. The fade takes the same time as before (`--kt-motion-slow`), so the behaviour script removes the toast at the same moment.
- The Overview page's focus rule now also says that inside a picker the focused row fills white with dark text, while rows on a page lift to the control grey.

## 0.5.0, 2026-10-14 (visual)

**Who should adopt it, and when:** Kettle Video, adopted on 2026-10-19 (from 0.3.1, so it took 0.4.0 and 0.4.1 with it).

No existing token, component class or state attribute was renamed or removed.

Added:
- Three components: the action bar (`.kt-actionbar`, with `.kt-icon` for drawn icons), the picker dialog (`.kt-dialog`, `.kt-picker` and its rows, for action lists, choice lists and confirms) and the toast (`.kt-toast`).
- `components/kettle-components.js`, a small behaviour script for the picker dialog and the toast, with plain functions on `window.KettleUI` and the events `kt-select` and `kt-cancel`. The CSS works without it.
- The token `--kt-motion-dialog` (500ms, matched to Steam's dialogs in Gaming Mode).
- A new state attribute, `data-closing="true"`, set by the script while a picker or toast leaves.
- The focus rule now says that inside a picker the focused row fills white; rows on a page still lift to the control grey.
- The three components on the Components and Motion pages, with live demos that use the same script, and behaviour checks in `tools/check_guide.py`.

## 0.4.1, 2026-10-10 (visual)

**Who should adopt it, and when:** Kettle Video skipped it: it went from 0.3.1 straight to 0.5.0, which includes it.

No existing token, component class or state attribute was renamed or removed.

Added:
- Tokens `--kt-ease-pulse` (ease-in-out, Steam's breathing curve), `--kt-focus-ring-start` (12px) and `--kt-motion-ring` (400ms), all matched to Steam's Gaming Mode.
- A second look at Steam's colours, matching the two Settings greys to Steam's Gaming Mode. No token changed.
- The overview's rules list has a rule on movement.

Changed (visual):
- `--kt-motion-slow` is now 300ms (was 360ms), matched to Steam's Gaming Mode. A focused tile grows over it; the progress fill glides over it, a little faster than before.
- A focused tile's ring now appears 12px thick and narrows to its width over 400ms, instead of fading in. Its breathing is smoother and starts after that, ending 5.2 seconds after focus arrives. In reduced motion it simply appears.
- The tile returns over `--kt-motion-fast` when focus leaves, as before, but now grows more slowly when focus arrives.
- The shelf's padding grows from about 15px to about 22px, so the thick ring isn't cut off at the shelf's edge.

## 0.4.0, 2026-10-10 (visual)

**Who should adopt it, and when:** Kettle Video skipped it: it went from 0.3.1 straight to 0.5.0, which includes it.

No existing token, component class or state attribute was renamed or removed. Apps that re-sync get motion without changing their markup.

Added:
- A Motion group of tokens (Group D) in `tokens/kettle.css`: `--kt-motion-fast`, `--kt-motion-medium`, `--kt-motion-slow`, `--kt-ease-standard`, `--kt-ease-enter`, `--kt-focus-scale`, `--kt-pulse-duration`, `--kt-pulse-count` and `--kt-pulse-min`. Each is labelled as matched to Steam's Gaming Mode, or as Enamel's own choice (then called Kettle).
- Motion on the components: the tile grows and its ring fades in, breathes four times and rests; rows, tabs, toggles, progress fills, the side menu and the new dot fade, slide or grow; the hint bar and the button do not move.
- Reduced motion: from the device's setting, or `data-kt-motion="reduced"` on `<html>` (or any element). `data-kt-motion="full"` on `<html>` forces full motion.
- Style guide: a Motion page (`docs/motion.html`) with live demos, a Full or Reduced switch at the bottom of the menu, the Motion group on the token reference, and a line per component on the Components page saying what moves.
- `CHANGELOG.md`, this file.

Changed (visual):
- The shelf's padding grows from 10px to about 15px, to leave room for a focused large tile's growth.
- The toggle thumb is now positioned by its left margin instead of flex alignment, so it can slide. It looks the same at rest.
- The side menu's focus bar and current-item glow are drawn by `::before` and `::after` instead of a box shadow and a background, so they can grow and fade. They look the same at rest. Apps that put their own `::before` or `::after` on `.kt-menu__item` will clash with them.

## 0.3.1, 2026-10-09

**Who should adopt it, and when:** Kettle Video, adopted on 2026-10-09 as its first copy of Kettle UI.

MIT licence, NOTICE and SPDX headers.

## 0.3.0, 2026-10-09

**Who should adopt it, and when:** Kettle Video skipped it: its first copy was 0.3.1, which includes it.

The accent became a slot, with named accents and a style guide switcher.
