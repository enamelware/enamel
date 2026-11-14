---
description: Turn an idea or spec into one or more Enamel GitHub issues on the Kettle board as Drafted. Does not build anything.
argument-hint: <idea, sentence or spec; several items separated by a line with only ===>
---

Draft work items for the owner to review. The text is:

$ARGUMENTS

Follow CLAUDE.md, especially "How we work" and "How to talk to me". **Do not build anything, create branches or edit project files.** This command only writes issues.

1. **Board.** Board changes only through `scripts/board.sh` (it reads the IDs in `.claude/board.json` itself). Run one simple command at a time: no `&&`, `;` or pipes.

2. **Items.** If the text contains a line with only `===` on it, it holds several items: split the text at those lines, ignore empty items, and handle each item through steps 3 to 5 in the order given. Otherwise the whole text is one item, exactly as before.

3. **Size and split.** Sizes are defined in CLAUDE.md ("Sizes"); use exactly those definitions, so labels are consistent and /next picks the right path. For each item, decide how many issues the text needs. An item that holds more than one feature or screen (in this repo: a component or a style guide page) becomes several issues, each useful on its own and in a sensible build order; a change across the design system that can't usefully be split stays one `size:L` issue. If a chunk depends on another, say so in its body ("Needs #N first").
   - **Series.** When one item is split into several issues, they form a series: create a label `series: <short name>` (a few plain words, for example `series: responsive`) with `gh label create`, add it to every issue of the item, and link them to each other with one line at the top of each body: `Series: #A, #B, #C (this is 2 of 3).` Create the issues first, then add the lines with `gh issue edit --body-file`. When the last one merges, /next reviews the series' combined change once, and its cards wait in Building until that review passes. An item that stays one issue has no series label.
   - **Dependencies between items** in the same paste ("depends on the item above", "needs the colours item first"): link the issues by mentioning each in the other. The dependent issue says "Needs #N first" and the other says "Needed by #M". If an item depends on one that comes later in the paste, or the wording is unclear, create everything first, then add the lines with `gh issue edit --body-file`. If it is unclear which item is meant, say so in the reply instead of guessing.

4. **Write each issue** as a public ticket, following CLAUDE.md "Public writing" (project voice, nothing private, invented examples), in plain language for a designer, no code or jargon, with these headings:
   - **Problem**: what is missing or wrong today, for apps using Enamel and in the style guide.
   - **Why it matters**: who it affects and why it is worth doing.
   - **Proposal**: what changes for apps using Enamel and in the style guide.
   - **Watch for** (part of the proposal): risks, edge cases, and anything that touches a CLAUDE.md hard stop (new dependency; a token, component class, state attribute, or function or event of the behaviour script renamed or removed; anything copied from Valve; a change apps would see beyond the spec that doesn't come from the issue or the design system). If apps (Kettle Video) would notice the change, say that it bumps VERSION, adds a plain-language CHANGELOG entry, and what apps need to change.
   - **Done when**, in two parts:
     - **Checked automatically by Claude Code**: `scripts/test.sh` (quick: tokens, generated pages and DESIGN.md, colours and sizes only from tokens, contrast, every component state, and the style guide pages the change touches in the device's Firefox in full and reduced motion), plus `scripts/test.sh full` if the issue bumps `VERSION`, screenshots, anything doable from a terminal on this device.
     - **Manual checks on the reference devices**: a short list of what to look at or try in the style guide (opened with the Enamel style guide launcher) and its components, on the Steam Deck (SteamOS) and the Retroid Pocket Nova (Armada). Never commands. Write "nothing visible yet" when the change has no visible effect.
   Add exactly one size label (`size:S`, `size:M` or `size:L`, by CLAUDE.md's definitions; when unsure between two, take the bigger one) and a topic label if one fits (for example `tokens`, `components`, `motion`, `style-guide`). Create a missing label with `gh label create`.

5. **Create and place** each issue:
   - `gh issue create --title ... --body ... --label ...` and note its URL and number.
   - Add it to the board: `scripts/board.sh add N`
   - Set Status to Drafted: `scripts/board.sh status N Drafted`

6. **Reply.**
   - One item: one line per issue: `#N (size) — what it does, in one plain sentence.`
   - Several items: one line per issue, in the order given: `#N — title (size)`, adding "needs #M" where a dependency was linked.
   - For each series, one more line: `Series "<name>": #A, #B, #C — reviewed together once the last one is built.`
   Then stop. The owner reviews on the board, leaves notes as issue comments, and moves the ones to build into Ready for dev.
