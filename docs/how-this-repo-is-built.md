# How this repo is built

Enamel is built with [Claude Code](https://www.anthropic.com/claude-code), Anthropic's coding agent, working from a designer's specs and decisions. The designer decides what Enamel should be and how it should look and behave, writes that down as ideas and specs, and tests every finished change in the style guide. Claude Code turns the specs into issues, builds them, checks them and records what it decided along the way. This page explains how that work moves, for a curious designer or developer reading the repo.

The instructions Claude Code follows are part of the repo: [`CLAUDE.md`](../CLAUDE.md) holds the rules, and the [`.claude/`](../.claude) folder holds the commands and the helper agents described below.

## The planning board

Every piece of work is a GitHub issue in this repo and a card on a planning board. The board itself is private; the issues are public. A card moves through six columns:

- **Drafted**: an idea written up as an issue, waiting for the designer to read it and leave notes.
- **Ready for dev**: approved by the designer and waiting to be built, top of the column first.
- **Building**: being built on its own branch, with one progress comment on the issue that is kept up to date.
- **More to do**: tested by the designer and sent back with feedback; these are built again before anything new.
- **Ready for testing**: built, checked and merged; waiting for the designer to try it in the style guide.
- **Done**: tested and approved by the designer; the issue is closed on the next run.

Moving a card to Done is the approval. Nothing else closes an issue.

## The commands

Three commands drive the work. Each is a written set of steps in [`.claude/commands/`](../.claude/commands).

- **/draft** turns an idea or spec into one or more issues in Drafted. It splits an idea that holds several features into separate issues (a series), labels each with a size, and builds nothing.
- **/next** builds one issue: it resumes anything interrupted first, then takes the top card from More to do, or else from Ready for dev. It builds on a branch named after the issue, runs the checks the issue's size calls for, merges into `main` only when they pass, and moves the card to Ready for testing with a comment listing what to try. `/next all` works through every waiting issue in a row; `/next 3` stops after three.
- **/tidy** is idle work for when nothing is waiting: it adds missing tests or fixes docs that no longer match the code, and proposes refactors as new Drafted issues for the designer to approve.

While building, Claude Code never stops to ask. A choice that can be undone and has a clear best option is made and written on the issue as "Decided: …, Why: …", with the `decided` label, so the designer can review all of them together. Only a few things stop the work (a new dependency or licence question, anything that can't be undone, a product change nobody asked for, security or privacy): the issue then gets one plain question and the `blocked` label, and the run moves on.

## The helper agents

Each issue is built and checked by separate agents, so the one that wrote a change is never the only one that checked it. Their instructions are in [`.claude/agents/`](../.claude/agents).

- **The builder** (a general helper started by /next) builds the issue and writes the tests it needs.
- **reviewer** checks the change against the issue and the rules, fixes small tidy-ups itself, and says PASS or FAIL with a numbered list of real problems.
- **test-checker** checks, on larger issues, that every point of the issue is covered by a test that would fail if the feature broke, and adds any that are missing.
- **test-writer** adds missing tests and fixes out-of-date docs during idle work.
- **refactor-scout** reads the code during idle work and proposes the most worthwhile refactors as issues. It changes nothing itself.

## Sizes and checks

/draft labels every issue with a size, and the size decides how it is checked.

| Size | What it is | Checks before merging |
|---|---|---|
| S | One small change, about three files or fewer, no new component or style guide page, nothing in the tokens | the reviewer, and the quick checks |
| M | One feature, or one component or style guide page | the reviewer, and the quick checks |
| L | Several components or pages, or a change across the design system | test-checker, then the reviewer, the quick checks and the full checks |

The quick checks run the unit tests, rebuild the generated pages to see nothing was edited by hand, check that every colour and size comes from a token, check contrast, and open the style guide pages the change touches in Firefox, in full and reduced motion. The full checks open every page, in four motion modes and with a larger font, and run every browser check. They also run before any new version is released, since apps only take released versions.

A failed check sends the issue back to the builder; after two rounds of fixes that still fail, the issue is blocked with an explanation. An issue that turns out bigger than its label is moved up a size and takes the bigger path. Small neighbouring issues in the same area are built together on one branch, and the issues of a series get one more review of their combined change once the last one is merged.

## The decision log

[`DECISIONS.md`](../DECISIONS.md) records why things are the way they are: each real design decision, with its date and reason. The "Decided" comments on issues are the day-to-day record; the ones that shape the design system are copied into the log. [`CHANGELOG.md`](../CHANGELOG.md) records what changed in each version, and which apps should adopt it and when.

## Public writing

Everything in this repo is written for a stranger to read: in the project's voice, with nothing private in it and only invented examples. The rule is the "Public writing" section of [`CLAUDE.md`](../CLAUDE.md), and a check in the quick checks catches the patterns it can, such as personal paths and links to private places.
