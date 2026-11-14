# Decisions

A dated log of design decisions for the Enamel design system. Newest first.

## 2026-11-14, the destructive row is plain until focused (#22)

**Red only with the focus.** The owner tried the 0.12.0 row on Kettle Video's Quit and wanted it to look like the rows around it, turning red only when it has the focus (enamelware/media-player#98). Unfocused, a destructive row is now a plain row of its kind, message and icon included; focused or pressed it takes the red face, white text, bold meta or description and the rise onto the coral underside it had before. The classes keep their names.

**The red replaces the usual focus look.** A focused destructive row turns red instead of taking a list row's grey lift or a picker row's cream fill, and it still rises onto the underside, so focus reads the same way in a list and in a picker. The face changes colour at once, as a picker row's cream does, while the rise keeps its motion.

## 2026-11-12, the destructive row (#21)

**A red face with white text, not red text.** Red text fails on every Enamel grey, and a red light enough to pass on the dark rows turns into a salmon next to the coral accent. The owner chose the error red as the row's face with Enamel's white for the text and icon, so there is still one red and one accent.

**One text pair is judged by APCA.** White on the error red is 4.44:1, just under the 4.5:1 every other text pair needs. Under APCA it is Lc 75, and its text is large (the row's own size) or bold (its meta or description), so the contrast check holds this pair, and only this pair, to APCA's Lc 60 for large or bold text. The owner chose to keep today's red rather than add a slightly darker one.

**Focus is a rise onto the underside.** A face that stays red can't show focus by turning grey or cream, so a focused destructive row rises onto the coral underside and drops when pressed, as a picker row does, in a plain list too. Reduced motion keeps the underside without the movement. There is no darker red for a press: the drop is the press.

**It is a modifier, one per kind of row.** `.en-row--destructive` and `.en-picker__row--destructive`, like `.en-button--primary`: a kind of row, not a state. In a picker an icon sits in front of the title and its description.

## 2026-11-11, Enamel goes public with only its own work

**Sources are "Steam baseline" or "Enamel".** Values chosen to sit naturally beside Steam's Gaming Mode are labelled Steam baseline and recorded under Enamel's own names only; everything else is Enamel's choice. Nothing taken from the Steam client's files is kept, so the reference folder and the tools that read the Steam client are gone, and a release check keeps it that way (#19).

**The browser check keeps its own connection.** It starts a private headless Firefox and drives it over a small websocket client, now called `tools/browser_session.py`. Only the part that pointed at the Steam client was removed. The release check looks for a connection to the Steam client, not to that Firefox.

**The before-and-after story is case-study material.** It now lives outside the repo; the eight guidelines it ended with are the system's rules, so they stay on the Overview page under Rules.

**The history starts again at 0.11.1.** To publish nothing from before, the history was replaced by one first commit and every older branch and tag was removed, v0.11.0 included. This is the one exception to "a pushed tag is never moved or deleted", agreed by the owner on #19 ("yes, rewrite"); from 0.11.1 on that rule holds again. The first commit is tagged v0.11.1, so apps always have a release to compare against.

**Examples use made-up titles.** Film and show names in examples, tests and docs are invented, never taken from anyone's library.

## 2026-11-06, Enamel's own look: where it comes from

Enamel looked like Steam with one accent on top, which made it familiar and also anonymous. The new material comes from enamel kitchenware: speckled camp plates, cream-rimmed pans, rimmed pie dishes. Hard, soft-shining, a little imperfect, with a lip you can feel. Every new value is Enamel's own; nothing is copied from Valve. Boards A5 and A6 on the owner's canvas were the reference (#18).

## 2026-11-06, the grid unit rule

Every size is a multiple of 4 in its own unit, 0.25rem if it grows with text and 4px if it does not, because one rule that a check can enforce keeps sizes consistent without anyone having to remember. The shadows, focus value and blur matched to Steam's Gaming Mode are exceptions rather than being rounded, since rounding them would make them no longer match. The check lists every exception it allows.

## 2026-11-06, two corner sizes, and new tokens rather than a changed one

8px on rows, buttons and tiles, 12px on panels, pickers and toasts, because the new surfaces need a softer edge and a panel holds faces, so its corner must be larger than theirs. `--en-radius` stays at Steam's 2px under its name, since it records a Steam baseline value and apps may use it; the components use the two new tokens.

## 2026-11-06, satin surfaces

A very faint light, a soft rim, a dark lip and a short soft shadow on every raised surface, so it reads as satin enamel and not car paint. The strongest light is a tenth of white, and a test holds it there.

## 2026-11-06, cream focus on a coral underside

Cream is Enamel's white, used through the existing `--en-focus-fill`, so anything using that token follows. The underside gives focus a physical reading that a fill alone doesn't. Tiles keep a ring because a picture can't be filled, and rows keep their lift because a list of cream rows would shout. The hint glyphs go cream too, since they use the same token and cream is the neutral.

## 2026-11-10, focused text looks semibold without getting wider

The issue asks for semibold text on cream focus. Switching the font weight makes the text wider, so a focused button pushed its neighbours along and a picker row with a badge grew 26px wider and 50px taller, breaking the badge rule that a row never changes size. Focused text is instead drawn with a 1px outline in its own colour (`--en-c-focus-stroke`), which reads as semibold and takes no extra room. A check holds buttons and picker rows to the same size focused and unfocused.

## 2026-11-10, the hint bar is measured in the page's own units

With the interface size now working through zoom, the script measured the hint bar after zoom and wrote that height back into the zoomed page, enlarging it twice: at 125% the toast stopped about 19px short of the bar. It now divides by the zoom in effect, and the hint bar check runs once at 125% too.

## 2026-11-06, a primary button is the accent colour at rest

It used to look like any other button until focused, when it turned accent. Focused, every button is now cream, as the issue asks, so without this nothing would mark a primary button at all. Board A5 draws it this way, and the Overview already showed it this way.

## 2026-11-06, progress bars

A sunken track with a speckled fill, because a bar is the one place where the material can show a texture without getting in the way. 8px under tiles and 12px in toasts as asked; the scanning bar also takes 12px, since it is the same bar on its own. All in px, since a bar holds no text. A toast gains a bar simply by holding a `.en-progress`, with no new class.

## 2026-11-06, the speckle is built into the tokens

Three SVG images written into `tokens/enamel.css` by `tools/build_speckle.py`, from fixed seeds, so running it again changes nothing. Apps sync three main files, and separate images would have meant changing each app's sync script. The price is three long token values, which the token reference shows in a small scrolling box. SVG keeps the flecks sharp at any interface size.

## 2026-11-06, the page speckle is a class an app chooses, and its coloured flecks follow the accent

A stylesheet can't know which areas are empty, so `.en-speckle` goes on an empty area, by choice, and never behind list text. Text that stands beside it still passes the contrast check against its strongest fleck, which is why the flecks are no stronger than a tenth. The coloured flecks are a mask filled with the active accent, not coral drawn into the image, because components never name a specific accent and another app may use another one.

## 2026-11-06, lift and press

Buttons and picker rows rise and drop, and nothing else moves physically: a list of rows bobbing would be tiring, and a tile already has its growth. A press from a keyboard, mouse or touch needs nothing from an app; a controller's press can't be seen by a stylesheet, so `data-pressed="true"` is a new state an app sets while A is held. Without it, things still work.

## 2026-11-06, picker rows are 4px apart, inside a panel with 4px of padding

A row that rises 4px and sits on a 4px underside would otherwise cover its neighbours and be cut off. The panel's 12px corner minus its 4px padding gives the rows' 8px corner, so the two line up. Rows stay in the panel's colour at rest, so only the focused one stands out.

## 2026-11-06, the toast's right corners stay square

The toast sits flush with the right edge, as Steam's does. Rounded corners there would show a notch of the page behind them, so only its left corners take the 12px.

## 2026-11-06, the lighter fallback

`data-en-lighter="true"` drops the soft shadows and the lift and press movement, because those are what a small device may struggle with, and keeps everything else. It works by emptying four component variables rather than by a second set of rules, so nothing can drift out of step. The blur behind a dialog stays, as the issue keeps everything else; if that also proves costly it can be added.

## 2026-11-06, the root size token drives zoom

Enamel no longer sets the root font size, so 1rem stays the user's own text size. `--en-root-size` keeps its name and its job, scaling the whole interface, but through zoom, so it scales pixels too. At 100% it does nothing. The owner's option A in #15 is kept in spirit: one setting still scales everything. It also means sizes in px are no longer a floor at other interface sizes: at 50% the 44px target is 22px, as with browser zoom.

## 2026-11-06, rem or px by one question

Should this grow when the user makes text bigger? The side padding of buttons, tabs and picker rows moved to px, since growing it would squeeze the text it holds. The gutter and inset tokens stay in rem, because they are Steam's measured values, also serve as vertical space, and hold up at 200% text; moving them would change every app's layout for little gain.

## 2026-11-06, the Overview page was edited by hand, with the owner's permission

For this issue only (#18, question 2): a new section, the guideline wording, and the few words the new look made untrue ("white fill", "3px wide"). Nothing was regenerated and nothing already there was restyled. Other old figures on that page are left alone, as they were before.

## 2026-11-05, stat panel, stat pair and note

**A stat panel is one item for screen readers through `role="img"` and a label** (#17). The spec asks for each panel to be read as one item, "124 movies, SD card › Films". This role treats everything inside as one item and carries that exact text, comma included. The cost is that some screen readers add "image" or "graphic" after it, and the app has to write the label.

**A "Not set" panel's second line says which kind it is.** Two panels that both say only "Not set" can't be told apart, by eye or by screen reader, so the line under it names the kind ("Movies"), and its label says "Movies, not set".

**A pair stacks below two panels at 18rem each.** The minimum is `--en-c-statpanel-min`, 18rem, which holds a usual path such as "Internal storage › Videos" on one line. It is a wrapping container with no query, so it follows its own space.

**The number uses the title size.** Enamel's heading and body sizes are the same, so only the title size makes the number read as large.

**The note uses soft text only.** The spec allows soft or muted. One colour keeps every note alike, and soft reads better at the small size. No variant was added.

**The › is part of the text.** Enamel has no separator token or class, and every existing example writes it as text.

**Two component variables, no tokens.** `--en-c-statpanel-min` and `--en-c-note-gap` hold the two sizes no token gives. The new classes follow `.en-steplabel` in joining their words.

**The satin surface waits.** The spec gives a stat panel the satin surface once Enamel's own look lands. That look isn't in the repo yet, so the panel uses the plain raised surface like every other raised surface today.

**Style guide paragraphs leave notes alone.** The site's paragraph style no longer reaches a note, so it shows exactly as in an app. Apps see no change.

## 2026-10-30, five small components for onboarding

**The error style is white text after a red disc** (#16). Enamel's red is too faint as text on the greys (about 3.4:1 on a row and 2.2:1 on a focused row, where text needs 4.5:1), so a message inside a row is white, bold small text, and the red is carried by its icon: a filled red disc with a dark exclamation mark (about 4.2:1, where a graphic needs 3:1). It reads the same on a focused row and on a row that isn't.

**A message is a live region that waits in the row.** Screen readers announce a polite live region reliably only when text arrives in one that is already there, so the message element stays in the row, empty, and takes no space until the app puts the icon and text in it. Showing and hiding it, and moving focus, is the app's job.

**The two group bands differ by fill and by icon.** The filled band, with a drive, is for storage on the device itself; the outlined band, with a card, for storage you can take out. The outline is drawn as thick as the icon's line (`--en-c-icon-stroke`) in the muted grey, so it passes 3:1 against the page. Both icons are Enamel's own drawings.

**The badge only changes colour.** Muted soft text in capitals on the control grey; on a focused row or a selected tab, which are that grey themselves, it turns to the page colour. Its size never changes, so neither does its row or tab. A badge that doesn't fit beside a row's title or a tab's label moves under it, so the title keeps whole words.

**Numbered steps reuse the glyph's size.** Each number sits in a round mark as big as a button glyph (`--en-c-glyph-size`), on the control grey rather than the glyph's white, so it can't be taken for a controller button.

**Nothing new in the tokens.** All five use existing tokens and component variables, so no token or variable was added. The new classes are `.en-steplabel`, `.en-band` (with `.en-band--outline`, `.en-band__name`, `.en-band__count`), `.en-badge`, `.en-row__message` and `.en-steps`, named like the existing ones.

**Style guide headings leave components alone.** The style guide's own heading style no longer reaches headings that are components (the group band and the picker's question), so they show exactly as in an app. Apps see no change.

## 2026-10-29, the interface scales from one root size

**Every size follows one root size, and nothing reads the screen** (#15, the owner's option A). Kettle Video's sizing report found that Firefox draws one to one on both the Deck and the Nova, and that Steam itself doesn't scale by the screen's height (on the taller Nova it is about 4% bigger, where height would have made it 20% bigger). So Enamel keeps every size in rem, and the root size is the page's root font size. The components stylesheet sets it from a new token, `--en-root-size`, at 100%: the browser's own font size, exactly as before. An app that needs the whole interface bigger or smaller sets that one token on `<html>`. A percentage of the browser's font size, rather than a multiplier inside every token, keeps every token's value readable and keeps a larger browser font working the same way.

**Lines don't scale.** Hairlines, the focus ring, corners, the icon stroke, the backdrop blur, shadows and the 44px touch target stay in px. Everything else that was in px (the toggle's padding, the progress tracks, the L1 and R1 glyph's corners, the side menu's focus bar) now follows the root size in rem.

**Every size except text is a multiple of 4px at 16px per rem.** Sizes the report didn't measure were moved to the nearest multiple of 4: the glyph 32, the "new" dot 12, the toggle 60 by 36 with a 4 padding (its 28 thumb unchanged).

**No device preview in the style guide.** The issue asked for a preview switch at another device's screen size, but CLAUDE.md doesn't let the style guide name a device or a screen size, and with nothing reading the screen that preview would show the same sizes. The token reference shows each size's pixels at the normal font size instead, and the Resize page's frames cover narrower, shorter and wider spaces.

## 2026-10-29, Gaming Mode measured larger than Enamel's old sizes

**Enamel's sizes are raised to Steam's Gaming Mode** (#15). Kettle Video's sizing report (its #76 and #77) measured Steam next to Kettle Video on the same screens: Enamel's rows were about 12% shorter, its text about 17% smaller and its buttons about a quarter shorter, and none of that came from scaling. Every measured size is now the report's baseline: rows 64, rows with a control 96, buttons 60, body text about 24, caps 17, small text about 18.7, the page title about 33, the list inset 20, the picker inset 24, tab padding 28, the side menu item 72 with an 8 focus bar and a 360 width, the large tile up to 452, tiles 20 apart, list rows 12 apart, and an icon 16 from its text. The hint bar, the picker row, the button padding, the list gutter, the section heading and the gap between hints already matched.

**New tokens, as the owner asked:** `--en-size-button`, `--en-size-row-control` (used by a row with a toggle or a button at its end), `--en-space-gutter-grid` (grids and shelves; lists keep `--en-space-gutter`), `--en-size-tile-portrait` (Enamel has no portrait tile component yet; this is the width one would use), `--en-space-icon` (between an icon or a button glyph and its text) and `--en-root-size`. Two component variables were added: `--en-c-menu-width` and `--en-c-shelf-gap`. Nothing was renamed or removed.

**Rounding follows the report.** The report rounds each Steam size up to a multiple of 4. Where Steam was within a pixel of Enamel, that alone moves Enamel's size: the list inset (18 to 20), the picker inset (21 to 24) and the tab padding (24 to 28). They follow the report as the owner asked.

**The hint bar's labels stay at the small text size.** The report's "caps labels" came from the hint bar, whose labels use `--en-text-small`, not `--en-text-caps`. At the new small size they measure close to Steam's (about 18.7 against Steam's about 17 to 19.5, depending on the reading); `--en-text-caps` is still raised to the report's 17 for the other caps labels.

## 2026-10-28, checks scale with the issue's size

**Why.** A retro of the first 13 issues: test-checker never failed anything (its value was the tests it wrote), the reviewer's failures on medium issues were tidy-ups that cost a whole round, and the full check found nothing in four runs. Kettle Video's retro agreed, and added that re-running the agents after a pause never found anything. So the builder writes the tests, S and M go to the reviewer alone, and only L gets test-checker and the full check. The rules are in CLAUDE.md ("Sizes", "Checks by size") and `.claude/commands/next.md` ("Size and path").

**What "screen", "launch" and "data" mean here.** The sizes were written for the apps. In this repo a screen is a component or a style guide page; launch is the style guide launcher and `tools/serve.py`; there is no data folder or settings file, and tokens take their place in the list that turns an S into an M.

**An item that can't be split stays one L.** /draft still splits an item into one issue per feature or screen, but a change across the design system that isn't useful in pieces is one `size:L` issue rather than several pieces that only make sense together.

**The reviewer may commit, in a narrow lane.** To fix tidy-ups itself, the reviewer can now edit tests, tools, scripts, the workflow's commands and agents and the hand-written docs, and make one `WIP issue-N:` commit on an issue branch; the guard refuses a commit on `main` and any edit to tokens, components or the style guide pages, whose tidy-ups come back to the builder instead.

**A bundle still lands as one commit per issue.** Each bundled issue's work ends with a marker commit on the shared branch, and the merge rebuilds `main` one issue at a time from those markers, so every issue keeps its own `Refs #N:` commit.

**A series' follow-up goes straight to Ready for dev.** It only fixes what the owner already approved, and in Drafted it would hold the whole series in Building until the owner moved it.

**/tidy keeps both agents.** Its improvements are tests written by test-writer, which is exactly where test-checker earns its place.

## 2026-10-28, a faster focus check; the quick check aims for under 2 minutes

**The focus and motion probe settles motion instead of waiting it out.** After recording each example's motion, the probe used to wait nearly half a second, so a page of about 58 examples took about 30 seconds in each motion mode. It now finishes every running motion at that point: this example's focus and the previous one's leaving, both already recorded. Run both ways on every page, in full and reduced motion, every result was identical (each look, every motion recorded, every pulse end, every reduced-motion finding); only the pulse-restart times varied by the browser's usual fraction of a millisecond, far inside their 100 ms limit. A page now takes about 5 seconds per mode. The slowest quick check (a change to the checker itself, so every page) fell from about 5 minutes to about 1 minute 30 seconds. A component change's quick check, which took about 2 minutes 40 seconds, checks fewer pages than that, so every quick check now fits in 2 minutes. The complete check gains the same per page.

## 2026-10-27, renamed to Enamel for the public launch (0.7.0, #13)

**The design system is called Enamel.** A thin coat of colour over a solid base, as the one accent sits over Steam's own baseline. The prefix changed now (#12), while one app uses it and the version is below 1.0, so the cost of the break is one switch issue in Kettle Video. Both parts ship together as 0.7.0, marked breaking, with MIGRATION.md listing every old name.

**"Kettle" alone stays.** The shared Kettle board, Kettle Video and the Kettle wordmark keep their names. The token source label "Kettle" (this system's own choice) is now "Enamel", and the sample sentence in the picker demo ("Only Kettle's list changes") stays, since it is Kettle Video's own wording.

**What keeps the old name, and why.** The local folder stays where it is, and Kettle Video keeps its copy in a folder with the old name until its switch issue; the check allows exactly that folder spelling. The progress-comment marker the workflow uses (`kettle-progress`) stays, because the progress comments already on GitHub are found by it. Old dated history entries keep the names they were written with.

**The repo moved to `enamelware/enamel`.** GitHub forwards the old address. The board settings name the new repo, because the board script picks this repo's cards by it.

## 2026-10-27, the names move to the en prefix (part 1 of the rename to Enamel, #12)

**Every public name takes the `en` prefix, and the main files take the new name.** Tokens and component variables (`--en-…`), component classes (`en-…`), the two state attributes (`data-en-accent`, `data-en-motion`), and the behaviour script's global (`EnamelUI`) and events (`en-select`, `en-cancel`). The animation names and the two properties the script keeps on elements follow, so nothing in the system is left with the old prefix. The files are `tokens/enamel.css`, `components/enamel-components.css` and `components/enamel-components.js`, and the tokens module in tools/ is `enamel_tokens.py`. No value changed. This breaks apps on purpose, while Kettle Video is the only one and the version is below 1.0; it ships together with part 2 (#13) as one breaking version.

**MIGRATION.md is written from the rename itself.** `tools/build_migration.py` holds the rename's rules and writes MIGRATION.md from the names the system has now, each with the old name the rules give back, so no renamed name can be missed and rebuilding changes nothing. That script, MIGRATION.md and the history entries dated before this one are the only places the old names stay; `tests/test_old_prefix.py` keeps it that way.

**Source notes follow too.** Wherever this system's own tokens are named next to the Steam values they match, the token names are now the new ones, so a reader can find them.

**Brand words wait for part 2.** "Kettle" in titles, headers, page markers, the style guide launcher and the repo name are renamed by #13, not here.

## 2026-10-21, a release is a written changelog entry and a pushed tag (#10)

**Released means tagged.** Kettle Video's check compared its copy with `main`, so it failed whenever a version was being built over several issues, even though Kettle Video was on the version it had been told to use. From now on a version counts as released only when its changelog entry is written and its annotated tag (`v` plus the version) is pushed, and an app compares its copy with the files at the tag for the version it records. The issue that finishes a release tags its `Refs #N:` commit on `main` (next.md step 9). Tags are pushed one at a time with a plain push and never moved or deleted, because apps rely on them; a mistake is fixed by releasing the next version.

**Each changelog entry says who should adopt it and when.** The older entries now say what Kettle Video did with them: it started at 0.3.1, went from there to 0.5.0, and goes from 0.5.0 to 0.6.0.

**Past versions are tagged from v0.3.0, and v0.6.0 is on the commit that released it.** The owner chose this on #10. v0.3.0 to v0.5.1 are on the one commit that set each version, the rule Kettle Video's check used until tags existed, so it gets the same files. v0.6.0 is on the commit that finished 0.6.0, not the earlier one where VERSION first said 0.6.0 part-way through the series: an app that adopts 0.6.0 gets the finished files. 0.1.0, 0.2.0 and 0.2.1 have no changelog entry and no app ever used them, so they have no tags.

## 2026-10-21, a check for devices and screen sizes; 0.6.0 ships (#6)

**A structure check keeps the responsive rule.** `tools/check_guide.py` now fails if a device name, an aspect ratio or a screen size appears in `tokens/`, `components/`, the style guide pages and their styles in `docs/` (the Overview page included), `DESIGN.md` or `README.md`, exactly the files agreed on #2. It needs no browser, so it runs on every issue. The history, the workflow files and `NOTICE.md` are not read. The trademark line and the tile frame's 16:9 picture shape (in the tile frame's own rule, or on a line about the tile frame) are allowed.

**It looks for screens, not numbers.** A ratio counts only when it is a known screen shape (16:10, 4:3, 16:9, 21:9 and the like, either way round, or the same as a decimal in `aspect-ratio`), so a contrast ratio such as 4.5:1, a time such as 19:15 and a fraction in `calc()` pass. A screen size is two pixel sizes joined by "by", "x" or "×", a resolution name (1080p, 4K), a size in inches, a pixel size followed by "screen" or "display", "at 1280" with a common screen width, or a media query on the device or the orientation, or in px at a common screen width or height. A font weight of 800 or a width given in rem with its pixels ("20rem wide (320px)") passes. A time that happens to read 16:10 would be a false alarm; none is in the checked files.

**DESIGN.md's smallest box gives its pixels one at a time.** The rule said "(320 by 240 at the browser's normal font size)", which reads as a screen size. It now says "(320px wide and 240px tall ...)", like the Resize page's labels. The rule and the box are unchanged. Nothing else was found: #3 and #4 had already removed every device and capture size, and the Overview page needed no change beyond the sentences agreed on #2.

**0.6.0 ships.** Its changelog entry now says what every app must do, that nothing was renamed or removed, and that Kettle Video should adopt it now. Its git tag comes with #10.

## 2026-10-21, the picker and toast clear the hint bar however tall it is (0.6.0, #9)

**A small piece of the behaviour script measures the hint bar; CSS alone could not do it robustly.** Since #4 the hint bar only has a minimum height and wraps, but the picker's layer and the toast are fixed in place and stopped one minimum bar height above the bottom. CSS has no way to give a fixed element another element's height. Anchor positioning could place them against the bar, but it is too new to rely on in every Firefox the apps may run on, and with several hint bars on a page (the style guide has dozens) each picker would need its own anchor name. Making the bar's height fixed again would bring back cut-off hints. So the stylesheet places both against a new component variable, `--kt-c-hintbar-height`, which defaults to `--kt-size-bar` (exactly the old placement, so the styles still work without the script), and the behaviour script keeps it in step with the real bar using a ResizeObserver, which reports a new height before the next paint, so nothing is ever drawn over the bar. A MutationObserver picks up hint bars added later. The script still sets no colour or timing; this one measurement is written in its header and in DESIGN.md.

**The variable goes on the hint bar's parent element.** The picker dialog and the toast inherit it from there, so a page with several screens (the style guide's frames, a split view) gets the right height in each, and an app whose hint bar is directly in `<body>` (as Kettle Video's is) covers its pickers and the toast the script makes in `<body>`. One hint bar per parent. No token was added and no name changed.

**A hidden hint bar keeps the old one-bar gap.** When an app hides its hint bar (not drawn at all, for example during playback) or removes it, the script takes the variable off the bar's parent, so the picker's layer and the toast stop `--kt-size-bar` above the bottom, exactly as before #9. Only a hint bar that is showing moves them, to its real height. The owner chose this on #9 ("1 is fine") so that apps that hide their hint bar see nothing new; measuring a hidden bar as 0 tall would have dropped the layer to the bottom of the screen and put the toast in the corner.

**The browser check covers one-line and two-line bars.** In every frame from the smallest supported box to very wide, the picker's layer must meet the top of the hint bar and the toast sit just above it, with Select and Back on one line and again with Select and Cancel and, in wider frames, more hints until it wraps onto two lines; the toast must follow the bar when it changes height while showing, and with the bar hidden the layer and the toast must keep the one-bar gap. This runs in full and reduced motion and with a larger browser font. The same rule applies to every frame on the Resize page.

## 2026-10-20, the Resize page (0.6.0, #5)

**A style guide page for seeing every component at any size.** `docs/resize.html`, generated from `tools/resize_page.py` like the Components and Motion pages, is in the left menu of every page. Each component sits in a frame resized by dragging its corner (the browser's own resizable box), and a row of fixed frames shows them at set widths. Plain HTML and CSS; the live picker and toast use the same behaviour script as the Motion page. A live picker is modal, so it covers the whole window, as it covers the whole screen in an app; the picker drawn in its frame shows how it fits a smaller space.

**Fixed frames are labelled by width only, in rem with the pixels at the browser's normal font size** ("20rem wide (320px)"), never by a device or a ratio. Their widths are the ones the browser check already puts the components in, from the smallest supported box (20rem) to 150rem, so the page shows what is checked.

**A frame's edge is drawn as an outline, so the components get the whole labelled width.** The page sets its text size on the body only, so 1rem on it is the browser's own font size and a frame labelled 20rem really is 20rem.

**The frames use two hints, Select and Back, as the smallest supported box does.** At exactly 20rem, a bar with Select and Cancel wraps onto two lines, and the picker and the toast, which then sat one bar height above the bottom, ran 12px over it; the same happened when a frame was dragged narrower than 20rem. That was a gap in the components, not fixed here: #9 fixed it (see its entry above), before #6 ships 0.6.0. The frames keep Select and Back, and since #9 the narrowest fixed frame also shows Select and Cancel on two lines. The browser check now fails if an open picker or a toast runs over a hint bar in any frame on the page.

## 2026-10-20, text and spacing in rem, every other component, the smallest supported box (0.6.0, #4)

**Text and spacing follow the browser's font size and grow a little on very wide pages, exactly as agreed on #2.** Each growing token is one `clamp()`: its base size in rem, then a straight line that reaches a fifth more at a page 160rem wide, starting at 100rem. The line is written as rem plus vw (for example `1.25rem + 0.625vw` for the title), which is the only way a token can follow the page's width; the numbers are worked out so the growth starts and stops at those widths in rem whatever the browser's font size. Gap and tight are plain rem; row and hint bar are plain rem used as minimums. The picker and toast detail text is 17/15 of the small text, so it grows with it without a screen unit in the components file. No token was added, renamed or removed.

**Tiles take their width from their shelf.** The shelf is a size container; a tile is two fifths of it and a large tile three quarters, each between a narrowest size (10rem, 12rem) and today's size (16rem, 28rem), so at the normal font size a roomy shelf looks as before and a narrow one shows smaller tiles instead of cutting them. The shelf's padding is worked out from the widest large tile (a new `--kt-c-tile-large-max`), and the same amount is its scroll padding (a new `--kt-c-shelf-room`), so a focused tile scrolled into view keeps its thick ring and growth inside the shelf at any size. Both new names are component variables, which may be added.

**Wrapping instead of cutting.** The hint bar and tabs wrap onto another line, and heights that held text (hint bar, tab, side menu item, icon button) became minimums, so a larger font makes them taller rather than spilling. Hairlines, the focus ring, the progress tracks and the 44px touch target stay in px, as the audit said.

**The smallest supported box is 20rem by 15rem, as agreed.** Measured in Firefox, a list row with its title and a focused toggle above a hint bar with two hints needs about 18.8rem by 11.75rem (the same in rem with a 24px browser font), so the agreed box fits it with room to spare; the height especially is generous. The box stays 20rem by 15rem, as agreed, and is written into DESIGN.md as a content rule. The browser check confirms it at both font sizes, and that a smaller box scrolls instead of overlapping.

**Matched values name no device.** The tokens say they are matched to Steam's Gaming Mode; DESIGN.md's source label and the token reference say the same, without naming a device.

**The style guide's menu breakpoint is named by what it does.** The menu moves above the page when the menu (17.5rem) and the narrowest readable page (38.75rem) cannot sit side by side, written as 56.25rem, the same 900px at the normal font size. Its layout widths are in rem.

## 2026-10-19, picker, toast and action bar adapt to their space (0.6.0, #3)

**The picker's limits come from its dialog, not the screen.** `.kt-dialog` is a size container, and the picker's narrowest and widest sizes are a quarter and two thirds of the dialog's inner width (`25cqi` and `66.667cqi`). The values were measured as a quarter and two thirds of a whole screen; inside a full-window dialog that is nearly the same, and inside a smaller frame (a style guide example, a split view) the picker now follows the frame. A picker used outside a dialog falls back to the browser's viewport, as before.

**The toast hugs its text, up to 28rem.** The toast width matched to Steam's Gaming Mode (448px) becomes its limit, written as 28rem so it is 448px at the browser's normal font size and grows with a larger font. It also never grows wider than its space less one gutter, so it leaves a margin on a narrow window. No token was added: the limit stays in the existing `--kt-c-toast-width`, whose meaning changes from "the width" to "the widest".

**The action bar wraps.** As agreed on #2, its buttons move onto a new line and the bar gets taller; a button alone wider than the bar wraps its own label. No label is ever cut short, so its full name is always both on screen and given to screen readers.

**The stylesheet names no capture.** The picker and toast values are matched to Steam's Gaming Mode, and the stylesheet names no device or capture size. The tokens' comments follow in #4.

## 2026-10-19, the responsive rule

**No layout is tied to a screen size, a device or an aspect ratio.** This replaces the rule "Layouts must work at 16:10 and 4:3." Layouts adapt to the space they are given (relative units, min(), max() and clamp(), intrinsic sizing, wrapping, and container queries, so a component responds to its own box rather than to the whole screen). Breakpoints, where needed, come from the content and are named by what they do, never by a device. Devices are for testing, never targets. No file names a capture size or a device as the source of a value. The rule is in CLAUDE.md (Hard rules) and DESIGN.md Part 2, and the style guide copies it. The owner said yes to the whole proposal on issue #2; the answers, which the rest of the responsive series (#3 to #6) builds on:

- **Text and spacing are written in rem, with capped growth.** At the browser's normal font size every size stays where it is today; a larger browser font makes them larger. Above a page width of 100rem they grow by at most a fifth, reaching the limit at 160rem: title 1.875rem to 2.25rem, heading 1.5rem to 1.8rem, body 1.25rem to 1.5rem, small 0.9375rem to 1.125rem, caps 0.8125rem to 0.975rem, picker and toast detail text 1.0625rem to 1.275rem, gutter 2.25rem to 2.7rem, inset 1.125rem to 1.35rem. Gap 0.75rem and tight 0.25rem do not grow. Row and hint bar become minimums of 3.5rem and 3.75rem. No new tokens. The values change in #3 and #4, not here.
- **When the action bar runs out of room, it gets taller.** Buttons wrap onto a second line and every label stays readable. Cutting labels short was turned down: on a controller there is no pointer to reveal the rest of a cut-off label.
- **The smallest supported box is 20rem wide by 15rem tall**: a list row with its title and the hint bar fit without overlapping, every focus ring stays fully visible, and the hint bar shows at least two hints on one line (more wrap). Below that the page scrolls. #4 writes this into DESIGN.md and measures it in Firefox.
- **Sources name no device**, from #3 and #4: the device and capture-size comments in the tokens and components files go, and each value is simply labelled as matched to Steam's Gaming Mode.
- **The new check (#6) covers** `tokens/`, `components/`, every style guide page and its styles in `docs/` (the Overview page included), `DESIGN.md` and `README.md`. It leaves alone `CHANGELOG.md` and `DECISIONS.md` (history), `CLAUDE.md`, `.claude/` and `scripts/` (they name the test devices) and `NOTICE.md`. The trademark line and the tile frame's 16:9 picture shape are always allowed.
- **The Overview page's sentences follow the rule.** Its rule now reads "Layouts adapt to the space they are given, never to a screen size, a device or an aspect ratio.", and "A small set of measurements, matched to Steam Deck screens." no longer names the device. Its measurement labels change with the values in #3 and #4. Its drawn home screen stays as it is: a fixed picture of an example screen, not a component.

No token, class, state attribute or script function changed, and apps see nothing yet, so there is no version bump.

## 2026-10-19, the toast fades out in place (0.5.1)

**The toast now leaves by fading out where it is, instead of sliding back out to the right.** This replaces the 0.5.0 choice ("slides out, as briefed"). Steam's own toast fades out in place: in Gaming Mode it fades over 300ms with the same curve it slides in with. Following Steam's motion is the rule everywhere else, so the toast follows it too. It still slides in from the right. The fade uses the existing tokens, `--kt-motion-slow` and `--kt-ease-enter`, so no token was added; the leaving state `data-closing="true"` and the script's timing are unchanged. In reduced motion it still simply disappears. The old slide-out keyframes stay in the stylesheet, unused, so nothing an app might use is removed.

## 2026-10-19, app names

**Kettle apps are named Kettle plus their medium, with no verbs.** Kettle Watch is now Kettle Video, and Kettle Listen is now Kettle Audio. Current docs, the style guide and the workflow files use the new names; older entries below keep the names used at the time. Only the names changed: no token, class, state attribute, file or folder was renamed, and Kettle Video's repo is still `~/Development/media-player`.

## 2026-10-14, action bar, picker dialog and toast (0.5.0)

**kettle-ui now ships one small behaviour script, `components/kettle-components.js`.** The picker dialog and the toast need behaviour: focus kept inside, Up and Down stopping at the ends, select, cancel, focus returned, and the toast's timer and one-at-a-time rule. Without a shared script every app would write it again, slightly differently, and the style guide needed it for its own demos anyway. It is plain JavaScript with no dependencies and no build step, knows nothing about controllers, and only sets state attributes. The CSS still works without it: a picker or toast written by hand in HTML looks right even if the script is never loaded. Its functions and attributes are part of the system, so renaming one is a breaking change.

**Inside a picker dialog the focused row fills white; rows on a page lift.** Steam fills white in dialogs and lifts on pages. A white bar moving down a long list would be too strong, so list rows keep lifting to the control grey; in a short picker over a darkened page, the white fill makes the choice unmistakable. On white, the title and description both use the dark focus ink, because muted or soft text on white would fail contrast.

**Where Steam's Gaming Mode and the existing values disagree, Steam's value wins, as a component variable.** Picker rows are 72px or 96px (the row token is 56px), text starts 21px in (the inset token is 18px), descriptions and toast text are 17px (no type token), and the toast is 35% of the screen wide. Colours within one step of a token use the token: rows #23262F are `--kt-surface-raised`, the current choice #3D434F is `--kt-surface-control`, the toast #0D141C is `--kt-surface-page`. The gap before Cancel uses `--kt-space-tight` (4px) for the measured 3px. The action bar keeps the system's button (`--kt-surface-control`) rather than Steam's #46494E, so there is one button style.

**Dialog and toast motion follow Steam's.** The darkened, blurred layer (Steam's own 85% black and 3px blur) appears at once; the panel fades in over 500ms with the standard curve, as Steam's dialogs and menus do (`--kt-motion-dialog`, added, matched to Steam's Gaming Mode). Steam's dialogs have no closing animation, so closing mirrors opening. The toast slides in from the right over 300ms with `--kt-ease-enter`, as Steam's does, and, as briefed, leaves the same way; Steam's own toast fades out in place instead.

## 2026-10-10, motion tuning (0.4.1)

**The focus ring follows Steam more closely.** It breathes with Steam's own in-and-out curve (`--kt-ease-pulse`, ease-in-out), so it dims and brightens smoothly. On focus it appears 12px thick and narrows to its width over 400ms, as in Gaming Mode (`--kt-focus-ring-start`, `--kt-motion-ring`), instead of fading in; the narrowing uses `--kt-ease-standard`, since Steam's plain "ease" has no token. The breathing starts once the ring has narrowed and still ends about five seconds after focus arrives (5.2 seconds). In reduced motion the ring simply appears.

**A tile grows over Steam's 300ms and returns over `--kt-motion-fast`.** `--kt-motion-slow` is now 300ms, matched to a tile moving towards you on focus in Gaming Mode, replacing Kettle's 360ms. The progress fill also uses it and now glides slightly faster.

**Steam's sheen is left out on purpose.** A focused Gaming Mode tile also has a light sheen sweeping across it once. Kettle leaves it out because motion marks focus or a change of state only, and the ring already marks focus.

**The side menu keeps its bar and glow** instead of Steam's 10% growth of the focused item, which has no token and would push past the menu's edge.

**Rows fade over `--kt-motion-fast`** instead of Steam's 0.5 seconds, so focus stays quick to follow when moving through long lists.

**The two Settings greys match Steam.** In Gaming Mode's settings, the content column is #1A1C21 and the page list column is #2B2D33. Both are one step from the values first matched (#1B1C21 and #2C2D32), so no token was changed.

## 2026-10-10, motion (0.4.0)

**Motion values match Steam where found.** Where Gaming Mode has a clear match, the token matches it, so moving into an Enamel app feels familiar: a focused tile returns over 100ms (`--kt-motion-fast`); the toggle thumb and slider handle move over 200ms (`--kt-motion-medium`); tiles gain and lose focus with `cubic-bezier(0.16, 0.86, 0.43, 0.99)` (`--kt-ease-standard`); toasts slide in with `cubic-bezier(0, 0.73, 0.48, 1)` (`--kt-ease-enter`); a focused landscape tile shows at 1.024 times its size (`--kt-focus-scale`); one breath of the focus ring is 1.2s (`--kt-pulse-duration`) and dims it to 0.4 of its strength (`--kt-pulse-min`). Progress bars have no single duration in Gaming Mode, so `--kt-motion-slow` stays Kettle's 360ms.

**The pulse stops after about five seconds.** Gaming Mode's ring breathes 20 times (24 seconds). Kettle's breathes `--kt-pulse-count` times, 4, so it ends 4.9 seconds after focus arrives and then rests fully visible. This is a Kettle decision, whatever Steam does.

**Where Steam moves differently from the brief, Kettle follows Steam.** A focused toggle shows its ring at once and does not breathe, and a button's focus fill changes at once, as in Gaming Mode. The side menu keeps its own bar and glow motion: Gaming Mode grows the focused item by 10%, which has no token and would push past the menu's edge.

**Reduced motion is honoured from the device and can be forced by an app.** `prefers-reduced-motion: reduce` or `data-kt-motion="reduced"` removes the pulse, the growth and every slide; colour fades stay at `--kt-motion-fast`, and focus is exactly as visible. `data-kt-motion="full"` on `<html>` forces full motion, for apps with their own setting. Gaming Mode itself keeps its focus ring breathing under both its own Reduce Motion setting and the device preference; Kettle does not copy that.

**Performance was deliberately not considered.** Motion animates whatever properties read best (transform, width, margin, outline colour, inset). This is to be checked on the Steam Deck and on the Nova before Kettle Watch adopts this version.

## 2026-10-09, MIT licence (0.3.1)

**Kettle UI is MIT licensed, so the system can be reused freely and included in the GPL apps.** MIT code can be combined into a GPL-3.0-or-later app such as Kettle Watch.

**The Kettle name and wordmark are kept separate from the code licence.** The MIT licence covers the code and documentation only; `NOTICE.md` says so.

## 2026-10-09, independence from apps

**This repo stays independent of any app; apps depend on it, never the other way round.** Kettle Watch (`~/Development/media-player`) keeps an unmodified copy in its `vendor/kettle-ui/` folder and updates it with its own sync script after a new VERSION here. Nothing here reads, writes or refers to an app's files. Gaps an app finds are fixed here first, then the app re-syncs.

## 2026-10-09, the accent becomes a slot (0.3.0)

**Menus, the Components page and tab focus are as recorded in the 0.2.1 entry below.** Each page's menu is written with its own page marked, so it works without scripts. The Components page is generated from one source per example. Tabs get a keyboard-only focus ring.

**The accent is a slot.** Components use only the active accent: `--kt-accent`, `--kt-accent-ink` and `--kt-accent-glow`, whose names do not change. An accent is two values, a colour and its ink, plus a passing accent check: 4.5:1 on the page and on rows, 3:1 on the control surface, its ink 4.5:1 on it, and at least 25 (CIE76 Delta E) away from green, yellow and red. `data-kt-accent="<name>"` on `<html>` or on any element switches it.

**The glow is calculated from the active accent.** `--kt-accent-glow` is the active accent at 42% strength, mixed with `color-mix`, which renders correctly in the Firefox on the Steam Deck. It and the focus ring are declared again on every `[data-kt-accent]` element, so they follow the accent chosen there instead of inheriting the default.

**Coral is the default; Sage is an example alternate, not a shipping decision.** Sage (#B7CC94, dark ink) is there to prove the slot works and passes the check.

**Still open: whether Kettle tools share one accent or each have their own.**

## 2026-10-09, tidy-up (0.2.1)

**Each page's menu is written with its own page marked, so it works without scripts.** The build script writes every style guide page's menu with that page already marked `aria-current="page"` and only its own sections listed. The menus are no longer identical across pages. `docs/site.js` only marks the section in view while scrolling.

**The Components page is generated from one source per example.** Each example's HTML is written once, in `tools/components_page.py`. The build script writes both the live example and the escaped "HTML to copy" from it, so they cannot differ.

**Tabs get a keyboard-only focus ring.** On a controller, tabs are switched with L1 and R1 and still show no focus. For keyboard use, `:focus-visible` (but not `data-focused`) shows the accent ring, as on a tile. This replaces "tabs have no focus style" from the entry below.

## 2026-10-09, first components (0.2.0)

**State comes from standard attributes.** Components read `aria-selected`, `aria-pressed`, `aria-current` and `disabled` instead of extra classes, so the markup that styles a component is also the markup that tells assistive tools its state.

**Focus works on `:focus-visible` and on `data-focused="true"`.** Keyboard focus shows on its own. Apps that move focus themselves (for example with a controller) set `data-focused="true"`, and the style guide uses it to show focus in static examples.

**A primary button only shows the accent when focused, as SteamOS does.** Unfocused, it looks like any other button. This keeps the accent rare and matches Gaming Mode.

**Tabs have no focus style, because L1 and R1 switch them.** Focus never lands on a tab during controller use, so a focus style would never be seen there.

**The style guide menu is built from the system's own side menu.** Its left menu uses `.kt-menu`, so the guide uses the component it documents. The menu is written into every page by `tools/build_styleguide.py`, from one list, so it is the same on every page.

## 2026-10-08, overview page and contrast rules

**The overview is the front door; the token reference is the catalogue.** `docs/overview.html` is the readable introduction: what Kettle looks like and why, written by hand. `docs/index.html`, now titled "Token reference", is the complete catalogue of every token, generated from `tokens/kettle.css`. Each page links to the other.

**No accent-coloured text on the control surface.** Coral on `--kt-surface-control` measures 3.98:1, below the 4.5:1 that text needs. Status text in coral stays on the page or on a row, never on a control or a focused row.

**Muted text steps up on a focused row.** Muted text on `--kt-surface-control` measures 3.12:1, also below 4.5:1. When a row is focused and lifts to the control surface, the muted text inside it switches to `--kt-text-soft`, which measures 5.13:1 there.

## 2026-10-08

**Baseline greys match Steam's Gaming Mode.** The seven greys, the three status colours, the four shadows, the 2px corner, the 12px gap, the 10px focus space and the 1.4 line height are matched to Steam's Gaming Mode, so an app sits naturally beside it.

**The accent replaces Steam's blue, and nothing else changes.** Wherever Gaming Mode uses its blue, Kettle uses its accent. Every other part of the look (greys, status colours, shadows, spacing) stays as Steam has it, so Kettle tools feel at home on the Deck.

**Focus has two styles.** Tiles and toggles get an accent ring (3px wide, 4px from the edge). Buttons and fields get a white fill with dark text. A focused row lifts to the control surface colour. Only one element shows focus at a time.

**The accent is coral, #EE8A72, with dark labels.** It was chosen over brick, sage, mustard and hot pink on contrast. Labels on the accent use the darkest grey (`--kt-accent-ink`), never white.

**System font only, nothing bundled.** Kettle uses the device's own font. No web fonts and no font files are shipped, so letter shapes differ between devices.

**Token names are version 0.** Names may change until Kettle Watch ships. Apps copy a dated version of the tokens, so a rename never breaks them silently.

**DESIGN.md exists so AI coding tools follow the same rules as people.** Its token tables are generated from `tokens/kettle.css` by `tools/build_design_md.py`, so the file and the tokens can't drift apart. The rules underneath are written by hand.

**The pill radius is a Kettle value, not a Steam one.** `--kt-radius-pill: 999px` was briefed as part of the Steam baseline. Steam's Gaming Mode only uses 1px, 2px and 3px corners, so it moved to the brand group and is labelled as Enamel's own choice (then called Kettle).
