---
description: Idle work for the Kettle board, on its own or at the end of /next all. Has test-writer add up to 2 missing tests or doc fixes (each on its own branch, checked by test-checker and reviewer, merged into main), reported on one "tests" issue in Ready for testing; then has refactor-scout propose up to 3 refactors as Drafted "refactor" issues.
argument-hint: ""
---

Idle work: small tests and docs improvements, then refactor proposals. Never changes what the design system does.

Follow CLAUDE.md throughout, especially "How we work" and "How to talk to me", and the shared rules in `.claude/commands/next.md` ("Safe to interrupt", "Progress comment", "Blocked", step 8 and step 9), which apply here as written unless this file says otherwise. Board changes only through `scripts/board.sh`; tests only through `scripts/test.sh`. One simple command at a time: no `&&`, `;` or pipes, no `cd`, no `export`.

**Never stop to ask the owner,** whether run on its own or from /next all. A question or a check that still fails becomes a "Blocked" comment and label (next.md, "Blocked"); then go on with the next part.

## 0. Before starting

- `git fetch origin --prune`, then `git status --porcelain` must be empty and `git branch --show-current` must be `main`; then `git pull --ff-only`. If the folder isn't clean or isn't on `main`: when run on its own, touch nothing, do nothing and report what you found; from /next all, this can't happen (its step 0 already checked).
- **Resume first.** List open issues labelled `tests` (`gh issue list --state open --label tests --json number,title,labels`). One without the `blocked` label that has an `issue-T` branch (local or on GitHub) is unfinished idle work: continue it (see "Resume") before anything new. A `blocked` one is parked: leave its branch alone.

## A. Tests and docs (at most 2 improvements)

1. **Propose.** Run the `test-writer` agent (Agent tool, `subagent_type` `test-writer`) with: `Propose mode: at most 2 improvements.` Keep its proposals word for word. If it says NOTHING WORTH DOING, note that for the report and go to part B.

2. **The run's issue.** Create one issue for this run (`gh issue create --title "Tests and docs tidy-up, <YYYY-MM-DD>" --body-file <file> --label tests --label size:S`; create the `tests` label first with `gh label create` if it is missing). Body, in plain language:
   - **What**: idle work while nothing was waiting to be built: missing tests and out-of-date docs, no change to what the design system does, and no version change. Then the proposals, numbered, each with its "What".
   - **Watch for**: only `tests/`, `README.md` and the hand-written parts of `DESIGN.md` may change.
   - **Done when**: **Checked automatically by Claude Code:** each proposal's "Done when", the quick suite passes, and nothing outside `tests/`, `README.md` and `DESIGN.md` changed. **Checked by eye:** a quick smoke check of the style guide.
   Then `scripts/board.sh add T` and `scripts/board.sh status T "Ready for testing"` (it goes straight there: there is nothing for the owner to approve first). Create the progress comment (`From: idle work`).

3. **For each proposal k, in order:**
   - Start from a clean, up-to-date `main` (`git switch main`, `git pull --ff-only`), then `git switch -c issue-T`, `git commit --allow-empty -m "WIP issue-T: improvement k plan"`, `git push -u origin issue-T`. One improvement at a time: the branch is deleted after each merge and started again from `main` for the next.
   - Send `Make k. You are on branch issue-T.` to the same test-writer (SendMessage; a fresh `test-writer` agent with the proposals pasted in if it has gone).
   - `git status --porcelain`: only files in `tests/`, `README.md` and `DESIGN.md` may have changed. Anything else counts as unclear: handle as Blocked and end part A.
   - `scripts/test.sh`, then stage those files, commit `WIP issue-T: improvement k code`, push, update the progress comment.
   - **Checks** (next.md step 8, at most 2 fix rounds): `test-checker` then `reviewer`, each prompted with `Issue #T. Check the change on branch issue-T against main. Round R. Only improvement k in the issue body is on this branch (tests and docs only; nothing the design system does may change); earlier improvements are already on main.` On a FAIL, send both verdicts word for word to test-writer as `Fix.`, run the suite, commit and push `WIP issue-T: fixes round R`, and check again.
   - **Both PASS:** merge as in next.md step 9, committing `Refs #T: Tests and docs k/<total>: <title>`, push `main`, `scripts/branch-done.sh T`, update the progress comment.
   - **Still FAIL after round 3, or "Needs the owner":** handle as Blocked (next.md, "Blocked"; the card stays in Ready for testing) and end part A, skipping any later proposal.
   - Note any bug or out-of-date CLAUDE.md that test-writer reported. Never fix them here.

4. **Results comment** on T, once, when part A ends (skip it if you already posted one this run). Plain language:
   - **Made**: one line per improvement merged, with its commit; one line per improvement blocked or not made, and why.
   - **Verified automatically**: one line per thing checked and its result (suite count, the files changed, nothing outside tests and docs).
   - **Not verified automatically**: "nothing" unless something couldn't be checked.
   - **Things to try**: open the style guide with the Enamel style guide launcher and see every page as before.
   - **Checks**: for each improvement, both final verdicts word for word and how many rounds.
   - **Found along the way**: bugs found by a test that failed, and anything in CLAUDE.md that is out of date, each as one line for the owner to decide on. "nothing" if none.
   If nothing was merged and nothing is blocked, say so and that moving it to Done closes it.
   Then update the progress comment to its finished form.

## B. Refactor proposals (at most 3)

1. Run the `refactor-scout` agent (`subagent_type` `refactor-scout`) with: `At most 3 proposals.` If it says NOTHING WORTH PROPOSING, note that for the report and finish.
2. For each proposal, check it again yourself before filing it: `gh issue list --state all --label refactor --json number,title,state` and `gh issue list --state open --json number,title,labels`. Drop it if it repeats an existing refactor issue or plainly overlaps an open or blocked issue, and note why for the report.
3. File each one left: write its body to a file in the scratchpad (the scout's sections as given, then a last line `Proposed by refactor-scout during idle work, <YYYY-MM-DD>. Refactors keep what the design system does the same; /next builds them only after every other Ready for dev issue.`), then `gh issue create --title "<title>" --body-file <file> --label refactor --label <size>` (create the `refactor` label first if it is missing), `scripts/board.sh add N`, `scripts/board.sh status N Drafted`.

## Report

When run on its own, end with this; from /next all, it goes into the final report. Plain language, no code or jargon:
- **Tests and docs**: `#T title`: what was added or fixed, and "quick smoke check of the style guide"; or blocked and what it needs; or "nothing worth doing".
- **Refactor proposals**: one line per issue filed, `#N title (size)`; then "They are in Drafted: move the ones you want into Ready for dev; /next builds them after all other Ready for dev issues." Or "nothing worth proposing". Mention any dropped as duplicates or overlaps.
- **Found along the way**: bugs and out-of-date CLAUDE.md lines from part A, or "nothing".
- **Resumed**: one line if unfinished idle work was picked up, from which checkpoint.

## Resume

For an unfinished `tests` issue T: read the issue and its progress comment (it says which improvement and checkpoint). Continue that improvement from its checkpoint on `issue-T` with a fresh test-writer (paste in the proposals from the issue body, then `Make k. You are on branch issue-T; part of it may already be there: finish it.`), then **re-run the quick suite before merging**, and both checks only if the code changed since they last passed, as next.md step 0 says. Then carry on with any later proposal in the issue body, post the results comment, and go on to part B. Unclear or broken state: as next.md step 0 says (leave the branch, comment "Blocked", add the label).
