---
description: Close open issues already in Done, resume any interrupted issue, then rework the top More to do issue on the Kettle board, or else build the top Ready for dev one (or a named one, or a bundle of small ones), on its own issue-N branch. Runs the checks its size calls for (reviewer for S and M; test-checker, reviewer and the full check for L), merges into main, pushes, and moves it to Ready for testing (a series waits for its series review). "all" or a number works through several issues in a row; "all" ends with idle work (/tidy) when nothing is left to build.
argument-hint: "[#N | all | N]"
---

Build or rework issues end to end. Argument: $ARGUMENTS

Follow CLAUDE.md throughout, especially the hard rules, "Who uses this", "How we work" and "How to talk to me", and DESIGN.md.

**Modes**, from the argument:
- *(empty)*: **single mode**, one issue picked from the board.
- `#N`: **single mode**, issue N.
- `all`: **batch mode**, no limit.
- `N` (a plain number without `#`): **batch mode**, at most N issues built or reworked. Blocked and skipped issues do not count towards N; resumed issues do.

Single mode runs step 0, then steps 1 to 13 once (a bundle of small issues counts as one). Batch mode is described after step 13.

**Never stop to ask the owner, in either mode, and never use the interactive question prompt.** Questions go in the issue. Every choice is either decided and recorded, or a hard stop that becomes one plain-language question in the issue's comments and the `blocked` label (see "Decide or block" and "Blocked"); the branch is kept. In batch mode the run then goes on with the next issue; single mode builds one issue, so it ends with its report.

## Decide or block

"The design system" means this repo's own tokens and components (CLAUDE.md, "Decide more, stop less").

**Decide** yourself, without asking or stopping, when all of these are true: the choice can be undone with a git revert; you would recommend one option; none of the hard stops below applies. An unclear spec, a spec that conflicts with the code or DESIGN.md, or a choice between ways to build it is decided this way. Then:
- comment on the issue, written to a file and posted with `gh issue comment N --body-file ...`: `Decided: <what>. Why: <one line>. To change it, reply on this issue.` One comment per decision; on a resume, don't post one that is already there;
- add the label if it isn't there: `scripts/board.sh label N add decided`, so the owner can review all of these together on the board;
- record it in `DECISIONS.md` too if it is a real design decision, as usual, and list it under "Decided" in the testing comment (step 11).

**Hard stops**, the only reasons to stop:
- a new dependency or licence question (anything copied from Valve's CSS, class names, icons, logos or fonts, or doing more to the Steam client than read it, counts);
- anything that could change, move or delete the owner's media or other files outside the repo;
- anything a git revert can't undo;
- a product change nobody asked for that doesn't come from the issue or the design system. Renaming or removing a token, component class, state attribute, or function or event of `components/enamel-components.js` that the issue doesn't ask for counts (apps use these names), and so does adding a token or rule the issue doesn't ask for;
- security or privacy;
- the issue and CLAUDE.md contradicting each other.

For a hard stop: handle the issue as **Blocked** (see "Blocked") with one plain-language question, and move on.

**Not stops:**
- *Design system changes are expected.* When the issue changes sizes, spacing, colours or components, everything in this repo that uses them (components, style guide pages, docs, tests) follows, and that is in scope. Never hardcode a size the design system provides: read its token or measure the element, in code and in tests. Only treat it as a problem if something stops working (can't be reached, read or used), not because it looks different, and even then fix it here if you can.
- *Kettle Video would need to change:* never edit it from here; note what it needs in the testing comment and the report.
- *The workflow's own steps* (merging, pushing, tagging the release the issue ships) are not choices to stop on.

**Time limit:** if one problem takes more than about 30 minutes without progress, write what you found and what you tried in the issue, and handle it as **Blocked**.

## Size and path

Sizes are defined in CLAUDE.md ("Sizes"). Read the issue's size label at step 3; an issue with no size label gets one there by those definitions (one line on the issue, as for an upgrade). The size decides the path:

| Size | Builder | Checks (step 8) | Test runs |
|---|---|---|---|
| S, M | builds it and writes the tests it needs | `reviewer` only (it also checks the tests) | quick |
| L | builds it and writes the tests it needs | `test-checker`, then `reviewer` | quick, and `scripts/test.sh full` before merging |

Every size keeps its own branch, merging only when the checks pass, the progress comment, the testing comment and the board moves. The full check also runs before any `VERSION` bump, whatever the size (step 6).

**Upgrades, automatic.** While building (steps 5 to 7, and again before step 8), compare the change with the size. An S becomes M if it touches more than about 3 files (not counting files the build scripts regenerate, `VERSION` and `CHANGELOG.md`), or touches tokens (`tokens/enamel.css`), the style guide launcher or `tools/serve.py`, privacy or licences (`LICENSE`, `NOTICE.md`, anything copied). An M becomes L if it grows past one screen or feature (more than one component or style guide page, or across the design system). Then: `scripts/board.sh label N remove size:S` and `scripts/board.sh label N add size:M` (or M to L), one comment on the issue `Size: S → M. Why: <one line>.` (once; not again on a resume), update the progress comment's `Size:` line, and follow the new size's path from here. Sizes only go up during a build. Note every upgrade for the report.

**Tidy-ups.** The reviewer fixes tidy-ups itself in one commit, `WIP issue-N: reviewer tidy-ups`, and lists them; they never fail a review. Tidy-ups it couldn't make (in `tokens/`, `components/` or `docs/`) come back under "Tidy-ups left": make them before merging (step 9), re-run the build scripts if they apply and the quick suite, with no new review round. If one of them would change anything apps or the style guide show, it isn't a tidy-up: skip it and note it in the testing comment.

### Bundles of small issues

At step 2, when the issue taken from **Ready for dev** is `size:S`, look at the cards right below it in Ready for dev, in board order. Each one that is also `size:S`, not `blocked`, not waiting on an unbuilt dependency outside the bundle, the same kind (`refactor` with `refactor` only), and **touches the same area** (the same component, style guide page or tools, judged from the bodies and topic labels) joins the bundle; stop at the first card that doesn't. A bundle of one is just a normal issue. Issues from More to do are never bundled.

- **Branch:** one branch, named after the first issue: `issue-N`. Every bundled issue's card moves to Building, and each gets its own progress comment with `Branch: issue-N (bundle: #N, #M, …)`; the plan for all of them lives in the first issue's progress comment.
- **One issue at a time on the branch**, in board order. Each ends with a commit `WIP issue-N: #M done` (`--allow-empty` if nothing is left to commit), which marks where its work ends; WIP commits in between are named `WIP issue-N: #M <checkpoint>`.
- **Upgrades:** if a bundled issue becomes M, it stays in the bundle (S and M take the same path); if one becomes L, the whole bundle takes the L path.
- **One review** (step 8) over the whole branch, prompted with every issue: `Issues #N, #M. Check the change on branch issue-N against main. Round R.`
- **One commit per issue on `main`** (step 9, "Bundles"). Fixes made after the review go into the last issue's commit; its message says which issue each fix is for.
- **Each issue** still gets its own card move, its own testing comment, and its own line in the report.

### Series

Issues that /draft split from one feature share a label `series: <name>` and link to each other. Each one is built on its own size's path as usual. What changes is the end:

- **Not the last one:** after the merge (step 9), the card **stays in Building**. Post the testing comment as usual (step 11) with the line `Series: waits in Building for the "<name>" series review, after #X and #Y are built.` and set the progress comment's `Next: series review, after #X and #Y`. It counts as built for dependencies.
- **The last one** (every other issue in the series is merged, or closed): after its own merge, run the **series review** before step 10.
  - Base: the parent of the series' first `Refs #` commit on `main` (`git log origin/main --reverse --format=%H --grep="^Refs #A:"` for each issue in the series; take the earliest, then `git rev-parse <commit>^`).
  - Run the `reviewer` agent with: `Series review: "<name>", issues #A, #B, #C. Check the combined change on main against <base>.`
  - **PASS:** move every card in the series to Ready for testing, post on each issue one comment `Series review passed: <the verdict word for word>`, and update each progress comment (`Next: owner testing`).
  - **FAIL:** file one small follow-up issue in the same series: title `<name>: fixes from the series review`, body with What / Watch for / Done when (the numbered problems, plus any "Tidy-ups left"), labels `size:S` (or bigger, by CLAUDE.md's sizes) and the series label, a line linking the series, then `scripts/board.sh add F` and `scripts/board.sh status F "Ready for dev"` (it goes straight there: it only fixes what the owner already asked for). Comment on every series issue `Series review found problems; fixes in #F. The cards move to Ready for testing once it passes.` Building #F is the next issue to take; when it merges it is the last of the series, so the series review runs again over everything from the same base.
  - **Still FAIL after two follow-ups:** handle the last follow-up as **Blocked** with the verdict word for word; the series' cards stay in Building.
  - Tidy-ups left from a passing series review go in the report, not into a new issue.
- Note each series review and its result for the report.

## Safe to interrupt

A run can stop at any moment: usage limit, the session closed, the Deck turned off. Everything below is built so that the next /next can pick up where it stopped:

- **One branch per issue** (or per bundle of small issues), named `issue-N`, started from the latest `main`. Work in progress is committed and pushed to that branch at each checkpoint. `main` only ever receives finished work: merged once the checking agents of its size say PASS and all automated tests pass on the final code. Kettle Video copies its Enamel files from this folder with its own sync script, so nothing half-done may reach `main`, and every run ends with the folder back on `main`.
- **One progress comment per issue**, edited in place at each checkpoint (see "Progress comment").
- **Every step is safe to repeat.** Before moving a card, pushing, merging, commenting or labelling, check whether it already happened. A resume never duplicates a comment, a commit or a board move.
- **Never start a new issue while there are uncommitted changes from another one.**

Work-in-progress commits are named `WIP issue-N: <checkpoint>` (no `#`, so they don't clutter the issue's timeline). The single commit that lands on `main` is named `Refs #N: <summary>`, as before. WIP commits may hold unfinished code and failing tests; the merge into `main` may not.

## Progress comment

Each issue has exactly one progress comment from /next, recognised by its first line `<!-- kettle-progress -->`. It is reused for every round on the issue (a new build, a rework, a resume), and edited in place, never posted twice.

- **Read it:** `scripts/board.sh progress N` (says so if there is none yet).
- **Create or update it:** write the whole body to a file in the scratchpad, then `scripts/board.sh progress N <file>`. It edits the existing comment in place, or creates it if there is none.

Body, in plain language:

```
<!-- kettle-progress -->
**Progress** (kept up to date by /next)
Branch: issue-N <(bundle: #N, #M) | > · From: <More to do | Ready for dev> · Round started: <YYYY-MM-DD HH:MM>
Size: <S | M | L> · Path: <reviewer | test-checker, reviewer, full> <· Series: <name> | >
Checks passed on: <short commit, and which agents; or "not yet">
Done: <checkpoints so far, e.g. plan, code, checks round 1>
Next: <what comes next, e.g. fixes from round 1, then checks round 2>
Plan:
- <the 3–5 bullet plan for this round>
Last update: <YYYY-MM-DD HH:MM>
```

`Checks passed on:` is written as soon as every agent of the path has said PASS, with the commit the branch was on after the reviewer's tidy-ups. A resume uses it to decide whether the agents need to run again.

When the issue is finished, `Done:` ends with `merged into main as <short commit>, moved to Ready for testing, testing comment posted` and `Next:` says `owner testing`. When it is blocked, `Next:` says `blocked: <one line>`.

**Checkpoints** (commit to `issue-N` if anything changed, push, then update the progress comment):
1. **plan**: branch created and pushed, card in Building, plan written in the progress comment. Commit `WIP issue-N: plan` with `--allow-empty` (the plan itself lives in the comment).
2. **code**: the main code change is written and the suite has run.
3. **fixes round R**: after fixing what the checking agents reported in round R, including tests test-checker added and the reviewer's tidy-up commit.
4. **merged**, **card moved**, **testing comment posted**: after each of those in steps 9 to 11.

## 0. Housekeeping, then resume

**Board housekeeping**, first, every run: `scripts/board.sh close-done`. It closes every open issue whose card is in Done, with the one-line comment "Closed by /next: its card is in Done but the issue was still open." Note the issues it closed for the report.

Then, before taking anything new, look for unfinished work. Read step 1 first, then:

- `git fetch origin --prune`
- `git status --porcelain` and `git branch --show-current`: uncommitted changes, and which branch they are on.
- `git branch --list "issue-*"` and `git branch -r --list "origin/issue-*"`: issue branches, local or on GitHub.
- For the current branch, `main` and every local `issue-*` branch: `git rev-list --count origin/<branch>..<branch>` (unpushed commits; a local branch with no copy on GitHub counts as unpushed).
- The board (step 2's list): cards in **Building**.

Each finding belongs to an issue N: `issue-N` branches by name, Building cards by number. A Building card whose progress comment names a bundle branch (`Branch: issue-N (bundle: …)`) belongs to that bundle, which is resumed as one. A Building card whose progress comment says `Next: series review` is **waiting**, not unfinished: leave it, unless every issue in its series is merged or closed, in which case the series review was interrupted: run it now (see "Series"). An issue with the `blocked` label is **parked**, not unfinished: leave its branch alone; it is picked up as normal once the owner removes the label (step 4 then continues from its branch). An issue labelled `tests` is idle work: /next leaves it to `.claude/commands/tidy.md` ("Resume"), which /next all runs at the end and /tidy runs on its own; in single mode, just mention it in the report.

Handle what you find in this order:

1. **Uncommitted changes on `issue-N`**: commit them as `WIP issue-N: saved after interruption` and push. Then treat N as unfinished.
2. **Uncommitted changes on `main` or any other branch**, or **unpushed commits on `main`** that are not explained below: the state is unclear, and no issue can be built safely on top of it. Touch nothing, start nothing new, and end the whole run with a plain-language report of what you found (which files or commits, on which branch) and one question for the owner. This is the one case where batch mode ends early: it isn't waiting on an issue, and nothing else can run until the folder is clean.
3. **Unpushed commits on `main` that are exactly one `Refs #N:` commit**, or the `Refs #` commits of some or all the issues of one bundle, where `git diff --quiet main issue-N` shows it holds the same files as `issue-N` (for a bundle cut short, the same files as the last merged issue's `#M done` commit): the merge happened but the push didn't, or it stopped part way. Treat N as unfinished; it continues at step 8, checked against `origin/main` from `main`, and step 9 then only pushes and cleans up.
4. **Every other unfinished issue** (a Building card, or an `issue-N` branch that is not blocked): treat N as unfinished.

For each unfinished issue N, in issue-number order:
- Read the issue, its comments and its progress comment (step 3). The progress comment says where it stopped, which column it came from, and the plan.
- **Unclear or broken state**: no progress comment and no branch but a Building card is fine (it stopped right at the start: begin it again from step 4). Anything that doesn't add up, such as a branch that won't switch, history that doesn't match the progress comment, or a merge conflict with `main`, counts as unclear. Then: keep the branch exactly as it is (never reset, delete or rewrite it), comment once in plain language what you found, headed "Blocked", add the `blocked` label, move the card back to the column it came from (if known), switch back to `main`, and move on.
- **Otherwise continue from the last checkpoint**, going through the remaining steps as normal. Whatever the checkpoint, **run the quick suite again before merging** (`scripts/test.sh`; on the exact code it already passed, it says so, and that counts). **Re-run the checking agents only if the code changed since they last passed**: when the progress comment's `Checks passed on:` names a commit and `git diff --quiet <that commit>` shows nothing changed since (no new commits other than merging `main`, nothing uncommitted), their PASS stands and step 8 is skipped. Note each resumed issue for the report.

**Single mode:** if anything was resumed, finish it, report (step 12, saying it was resumed from an earlier interruption) and stop: the next /next takes the next issue. With `#N`, resume first, then go on with #N. If nothing was unfinished, go on to step 1.

## Steps

1. **Board and tests.** Board changes only through `scripts/board.sh` (it reads the IDs in `.claude/board.json` itself); tests only through `scripts/test.sh`. Run one simple command at a time: no `&&`, `;` or pipes, no `cd`, no `export`. Run git from this repo's folder without `git -C`; read Kettle Video only with `scripts/peek.sh`. Every helper agent follows the same rules, and any general-purpose helper you start (the builder, or any other) gets them in its prompt.

2. **Pick the issue.**
   - List the board: `scripts/board.sh list` (number, status, labels, title).
   - If an issue number was given, use it. **Its Status must be More to do or Ready for dev** (or Building, when step 0 is resuming it). If it is anything else, say which status it has and stop. If it has the `blocked` label, say so, point to the open question in its comments, and stop: the owner unblocks it by removing the label.
   - Otherwise, **first** take the first item (board order) whose Status is More to do. **Only if** none is in More to do, take the first item whose Status is Ready for dev **and that is not labelled `refactor`**. **Only if** none of those is left, take the first Ready for dev item labelled `refactor`: refactors always come after every other Ready for dev issue (see "Refactor issues"). In every case skip items with the `blocked` label, and items that depend on a blocked or unbuilt issue (see "Dependencies" below).
   - If nothing is left to take, say "Nothing in More to do or Ready for dev" (mentioning any blocked or skipped issues) and stop.
   - Note its issue number N, and whether it came from **More to do** (a rework) or **Ready for dev** (a new build).
   - **Bundle:** if it came from Ready for dev and is `size:S`, check the cards right below it for a bundle (see "Bundles of small issues"). Steps 3 to 11 then run once for the bundle, each issue read, built, committed and reported in turn.

3. **Read it fully**: `gh issue view N --json body,comments,labels` (`--comments` alone prints nothing here), the body, labels and ALL comments. Note its size and any `series:` label (see "Size and path"). The owner's review notes and failure reports are in the comments; they override the original body where they differ.
   - **For a rework (More to do):** these are issues the owner tested and sent back. Find when it last left Building (your last "Ready for testing" comment) and focus on the owner's feedback since then. List each point of feedback separately; every one must be addressed.
   - **For a previously blocked issue** (it has a "Blocked" comment from you, and the owner has since removed the label): the owner's answer is in the comments after it. Follow that answer.

4. **Branch and plan** (checkpoint "plan"). Check `git status --porcelain` is empty first; if not, go back to step 0.
   - `git switch main` and `git pull --ff-only`.
   - If `issue-N` exists locally, `git switch issue-N`; if it only exists on GitHub, `git switch issue-N` (it follows `origin/issue-N`). If it exists, bring it up to date with `git merge main` (a conflict counts as unclear state, see step 0). If it doesn't exist, `git switch -c issue-N` from the fresh `main`.
   - `git push -u origin issue-N`.
   - Move the card to **Building** if it isn't there already: `scripts/board.sh status N Building`
   - Write the plan (3–5 bullets) and create or update the progress comment. A new round (a fresh build, a rework, or a blocked issue picked up again) gets a new "Round started" time; a resume keeps the old one.
   - Commit `WIP issue-N: plan` (`--allow-empty`) unless the branch already has it for this round, and push.

5. **Build.** Build without asking for plan approval, and never ask during the build. **Write the tests the change needs as part of building it**, whatever the size: for each acceptance point that can be checked from the terminal, a test that would fail if the feature broke (`tests/test_*.py`, or a `tests/*_check.py` script for what needs the device's Firefox; standard library only, the MIT SPDX header, a docstring naming the issue). On S and M no one else writes tests: the reviewer only checks them. Keep an eye on the size as the change grows (see "Upgrades"). Each choice is either decided (comment, `decided` label) or a hard stop (Blocked), as "Decide or block" says. A visible change counts as a stop only when it goes beyond the spec and doesn't come from the issue or the design system. Record real decisions in `DECISIONS.md`, as usual.

6. **Test everything you can yourself.** Never ask the owner to run commands or test cases.
   - After any change to tokens, rules or components, run `python3 tools/build_design_md.py`, then `python3 tools/build_styleguide.py`, and run both again to see that the second run changes nothing (CLAUDE.md).
   - Run `scripts/test.sh` (quick: the unit tests, the build and structure checks, and the device's Firefox on the style guide pages the change touches, in full and reduced motion). If anything fails, fix it and run again. Slower checks for the code you touched: `scripts/test.sh check <name>`.
   - Work through every item under "Checked automatically" in "Done when": run the scripts and read their output, look at screenshots of the style guide in the device's Firefox (`tools/check_guide.py --screenshots` can save them), measure timings.
   - **Version and changelog.** If apps would notice the change (any token, component, rule or script change), bump `VERSION` (the next minor version for additions or visual changes, a note "breaking" for renames or removals), add a plain-language `CHANGELOG.md` entry marked "visual" or "breaking" that also says which apps should adopt it and when, and re-run the build scripts so the version is stamped. A rename or removal is only allowed when the issue asks for it, and its entry says exactly what apps need to change. **Before any `VERSION` bump, and before merging a `size:L` issue, run `scripts/test.sh full`** (everything, including the complete style guide check; about 12 minutes) on the final code: apps only sync released versions. Run it in the foreground with the longest command timeout.
   - **Released means tagged.** A version counts as released only when its `CHANGELOG.md` entry is written and its tag is pushed (step 9). Work in progress on `main` never counts, even when `VERSION` already shows the new number: a version built over several issues is released by the issue that finishes it (its entry is complete and the issue says it ships the version), and only that issue tags it.
   - **Never run the same check twice on the same code.** `scripts/test.sh` remembers a pass against the exact code and says "already passed" instead of running again; that counts as a pass. Only `--again` forces a re-run, and only when there is a reason to doubt the earlier result.
   - If you cannot make it pass, or one problem takes more than about 30 minutes without progress, handle it as **Blocked** with a plain explanation of what fails and what you tried.

7. **Checkpoint "code":** stage only the files for this issue (check `git status`), commit `WIP issue-N: code`, push, update the progress comment.

8. **Independent checks** by the project agents in `.claude/agents/` that the size calls for (see "Size and path"), on the change on `issue-N` compared with `main`: the `reviewer` alone for S and M; `test-checker`, then the `reviewer`, for L. Nothing reaches `main` until every agent of the path says PASS. Skip this step on a resume whose checks already passed on the same code (step 0).
   - First make sure the branch holds the latest `main`: `git fetch origin`, and if `origin/main` has moved, `git merge origin/main` into `issue-N` (a conflict counts as unclear state) and run the suite again.
   - **Round 1:** run the agents of the path (Agent tool, `subagent_type` set to each name), one after the other. Prompt each with: `Issue #N. Check the change on branch issue-N against main. Round 1.` (When step 0 found a merge that wasn't pushed, say `against origin/main` instead, from `main`.) On L, run the reviewer even if test-checker failed, so you get every problem at once. Keep every verdict word for word.
   - **All PASS:** push the reviewer's tidy-up commit if it made one, write `Checks passed on:` in the progress comment, and go on to step 9.
   - **Any FAIL:** fix every numbered problem (the system's own files for the system, a test only if test-checker's test is itself wrong), run the quick suite again (step 6; it only re-runs what changed), commit and push checkpoint "fixes round R", then run the path's agents again, as round 2. At most **2 fix rounds** (rounds 2 and 3), and always every agent of the path each round. The reviewer's tidy-ups never count as a FAIL.
   - **Still FAIL after round 3**, or a problem marked "Needs the owner" (that is a hard stop, not something to fix): handle it as **Blocked** (see "Blocked") with one plain-language question or explanation built from the remaining problems. In single mode, then report and stop; in batch mode, move on.

9. **Merge into main** (checkpoint "merged"), only after every agent of the path said PASS in step 8.
   - Make any "Tidy-ups left" from the reviewer (see "Tidy-ups"), then commit anything left on `issue-N` (such as tests test-checker added) as `WIP issue-N: checked`, and push.
   - **Merged but not pushed** (found by step 0): run the quick suite on `main`, `git push origin main`, then the clean-up below.
   - **Already merged?** If `git log origin/main --since="<round started>" --grep="^Refs #N:"` finds a commit and `git diff --quiet origin/main issue-N` shows the same files, skip to the clean-up below.
   - `git switch main`, `git pull --ff-only`. If `main` moved since step 8, go back to step 8.
   - `git merge --squash issue-N`, then run the quick suite on `main` once more: `scripts/test.sh`. If it fails, `git reset --merge` to undo the uncommitted merge, switch back to `issue-N` and fix there (back to step 6).
   - Commit `Refs #N: <summary>` and `git push origin main`. Never force-push.
   - **Bundles** use this instead of the squash merge, so `main` gets one commit per issue. `git rev-list --count issue-N..main` must be 0 (the branch holds all of `main`; otherwise go back to step 8). Then for each bundled issue M in order, skipping any whose `Refs #M:` commit is already on `main`: find where its work ends (`git log issue-N --format=%H --grep="^WIP issue-N: #M done"`; for the last issue, the branch itself), `git restore --source=<that commit> --staged --worktree .`, and commit `Refs #M: <summary>`. If a `main` merge into the branch came after the first issue's `done` commit, the per-issue split can't be made cleanly: use one squash merge instead, committed as `Refs #N, #M: <summary>`, and say so in each testing comment. Then `git diff --quiet issue-N` must show `main` holds exactly the branch's files; run the quick suite (it says "already passed" on this code) and `git push origin main`. If anything here fails, leave `main` unpushed and handle the bundle as **Blocked** (step 0 picks it up from there).
   - **Tag the release**, only when this issue releases a version (step 6, "Released means tagged"). If `git ls-remote --tags origin v<version>` already shows the tag, skip this. Otherwise make an annotated tag on the `Refs #N:` commit just pushed, named `v` plus the version, with the version and its changelog date as its message (`git tag -a v<version> -m "Enamel <version>, <changelog date>"`), then push it with one plain `git push origin v<version>`. One push per tag, never forced; a pushed tag is never moved or deleted (a mistake is fixed by releasing the next version). Say the tag in the testing comment's "Version" line.
   - **Clean-up:** `scripts/branch-done.sh N`. It deletes `issue-N` locally and on GitHub only once `main` on GitHub holds the same files, and skips whatever is already gone. Update the progress comment.

10. **Move to Ready for testing** if it isn't there already (`scripts/board.sh status N "Ready for testing"`). Update the progress comment. **In a series**, only once the series review has passed (see "Series"): until then the card stays in Building. In a bundle, move each issue's card.

11. **Comment on the issue**, unless you already posted a "Ready for testing" comment after this round started. Write it to a file and use `gh issue comment N --body-file ...`, in plain language, with:
   - **For a rework only — Feedback addressed**: each point of the owner's feedback, and what you changed in response (or why nothing needed changing).
   - **Decided**: one line per decision you made on this round (the "Decided" comments), or "nothing".
   - **Verified automatically**: one line per thing you checked and its result.
   - **Not verified automatically**: anything in "Done when" you could not check from the terminal, and why. Write "nothing" if so.
   - **Things to try**: one short list of things to look at or try in the style guide, opened with the Enamel style guide launcher. Never commands. Write "nothing visible to check" when that is true. For a rework, give the updated list if it changed, or say it is unchanged.
   - **Version**: the new version and its changelog line, or "no version change: apps see nothing new".
   - **For Kettle Video**: what Kettle Video must do to pick this up (re-sync, new files for its sync script, markup or key handling to change), or "nothing". Never change Kettle Video from here.
   - **Size and path**: the size (and any upgrade, with its reason), the path it took (reviewer only, or test-checker, reviewer and the full check), whether it was built in a bundle (with which issues) and whether it belongs to a series.
   - **Checks**: the final verdict of each agent of the path from step 8 (test-checker's then reviewer's on L), word for word, how many rounds it took, and any tidy-ups the reviewer made or left.
   - **Series** (only in a series that isn't finished): the line from "Series" saying the card waits in Building for the series review.
   - **Resumed** (only if it was): one line saying it was picked up after an interruption, from which checkpoint.
   Then update the progress comment to its finished form.

12. **Report back** in plain language, no code or jargon, as three short parts:
    - **What changed** in the design system and the style guide (say "nothing visible yet" when that is true), and the new version if there is one. Mention it if the issue was resumed from an earlier interruption.
    - **What to try** in the style guide, or "nothing visible yet".
    - **What Kettle Video needs to do**, or "nothing".
    - **Decided along the way**: each decision made without asking (all labelled `decided` on the board), or "nothing".
    - **Blocked**, if it was: the question waiting in the issue.

13. **Never close the issue here.** It moves on through the pass/fail phrases in CLAUDE.md ("How we work").

## Refactor issues

Issues labelled `refactor` (proposed by refactor-scout through /tidy, approved by the owner moving them to Ready for dev) change how the code is organised, never what the design system does. On top of the steps above:
- **Tests pass before:** right after step 4, run the quick suite on the fresh branch before changing anything. If it fails, handle as Blocked ("the tests already fail before the refactor"); never refactor on a failing suite.
- **Tests first:** if the issue's "How the tests cover it" names behaviour without a test, add those tests first and see them pass on the unchanged code.
- **Behaviour stays the same:** no token value, component look, motion, script behaviour or generated page changes, no token, class, state attribute or script function renamed, no version bump, and no existing test loosened or removed (tests may be added or moved, checking the same things). Anything else is a hard stop: a product change nobody asked for.
- **Tests pass after:** the quick suite on the final code, as always.
- The testing comment's things to try are a short smoke check ("nothing visible should change").

## Dependencies

An issue depends on another when its body or comments say so ("Needs #M first", "Depends on #M"). Issue M counts as **built** once its Status is Ready for testing or Done, or it is closed, or it is in a series and waits in Building for the series review (merged; its progress comment says `Next: series review`). It counts as **blocked** if it has the `blocked` label. Anything else (Drafted, Ready for dev, Building, More to do) is **unbuilt**.

Skip an issue whose dependency is blocked or unbuilt. Leave it in its column without a label, and comment once (not again on later runs if your last comment already says the same): "Skipped by /next: needs #M first, which is <blocked / not built yet>." Check this when the issue comes up, not at the start of a batch: a dependency built earlier in the same batch counts as built.

## Blocked

When an issue is blocked (a hard stop, tests that still fail, a problem past the 30-minute time limit, step 8 still failing after round 3, or unclear state found on resume; in either mode): nothing goes to `main`. Keep the work on its branch instead of throwing it away:
- if the state is clear, commit what is there as `WIP issue-N: blocked` and push `issue-N`; if it was unclear, leave the branch exactly as it is;
- `git switch main`, so the next issue starts clean;
- comment on the issue, headed "Blocked", unless your latest comment already says the same. Give ONE plain-language question (at most 3 options, your recommendation and one sentence why) or, for failing tests or checks, a plain explanation of what fails and what you tried. When step 8 caused it, include the last verdict of each agent of the path word for word;
- add the label if it isn't there: `scripts/board.sh label N add blocked`;
- move it back to the column it came from (More to do or Ready for dev) if it isn't there already;
- update the progress comment (`Next: blocked: <one line>`).

The branch stays parked. When the owner removes the label, the next /next continues from it (step 4).

## Batch mode (`/next all`, `/next N`)

Start with step 0 (housekeeping, then its checks). Resumed issues come first, then every issue in More to do (board order, top to bottom), then every issue in Ready for dev (top to bottom, small neighbours bundled as in "Bundles of small issues"), with `refactor` issues after all the others. A series follow-up issue filed during the run is taken next. Before each issue, list the board again (step 2), since statuses change as you go, and check `git status --porcelain` is empty and you are on `main`.

**Keep the main session small.** It only holds the queue, the checking agents' verdicts and the final summary. Each issue (or bundle) is built in its own fresh helper agent:

1. **Start a builder**: Agent tool, `subagent_type` `general-purpose`, prompt:
   `You are the builder for Enamel issue #N in a /next batch run. Read CLAUDE.md and .claude/commands/next.md, especially "Decide or block". Never ask the owner and never use the interactive question prompt: decide what a git revert can undo and you would recommend (comment "Decided: ...", add the decided label), and handle a hard stop, tests that still fail, or one problem stuck for about 30 minutes as Blocked. Changes that come from the issue or the design system are in scope; never hardcode a size a token provides. Write the tests the change needs as part of building it, and upgrade the size label yourself if the change grows past its size (next.md "Size and path"). <"It is size S|M|L." | "It is a bundle of #N, #M: one issue at a time, as next.md "Bundles of small issues" says."> Run one plain command at a time (never chain with &&, ; or |), run git from this repo's folder without git -C, and read Kettle Video only with scripts/peek.sh. <"This is a new build from <column>." | "This is a resume: continue from the progress comment, then re-run the quick suite.">  Do steps 3 to 7 (or the remaining ones), then stop: you cannot run the checking agents yourself. Reply in at most 5 lines, starting with READY FOR CHECKS or BLOCKED, plus the issue title, its size now (and any upgrade) and any decisions made.`
2. **Run the checks** yourself (step 8, the agents of the issue's size, in order), with the same prompts as single mode. Use the size from the builder's reply: an upgrade changes the path. On a resume whose checks already passed on the same code, skip them (step 0).
3. **Any FAIL**: send the builder every verdict word for word with SendMessage, asking it to fix them, commit and push checkpoint "fixes round R", and reply READY FOR CHECKS. Then run the path's agents again. The same limit applies: at most 2 fix rounds.
4. **All PASS**: send the builder the final verdicts (with any "Tidy-ups left") and the number of rounds, asking it to do steps 9 to 11 and reply in one line: `DONE: #N title — what to try in the style guide` (or "nothing visible yet"), or `WAITING: #N title — merged, waits for the series review` for a series issue that isn't the last.
5. **Last of a series**: after its DONE, run the series review yourself (see "Series"), then move the cards and comment, or file the follow-up issue.
6. **Still FAIL after round 3**, or a "Needs the owner" problem: ask the builder to handle it as Blocked with those verdicts and reply in one line with what the owner needs to answer.

If helper agents aren't available, do the same steps in the main session. If a builder stops without replying, run step 0's checks for that issue and carry on from its progress comment.

For each issue, the steps are the same as in single mode, with these differences:

- **Skip** issues with the `blocked` label, and issues whose dependencies are blocked or unbuilt (see "Dependencies").
- **A hard stop** (step 5), **tests that still fail** or **the time limit** (step 6): handle the issue as **Blocked** and move on to the next issue.
- Skip step 12 per issue; report once at the end instead.

**Never stop to ask.** Every choice is decided or, for a hard stop, becomes Blocked; every failing test or check becomes Blocked; and the run moves on. The only early end is step 0's unclear state on `main`.

**Stop** when no issue is left to take in More to do or Ready for dev (apart from blocked and skipped ones), or when N issues have reached Ready for testing.

**Release check** (`/next all` only, once, if anything was merged into `main` during the run): on a clean, up-to-date `main`, run `scripts/test.sh full`, in the foreground with the longest command timeout. If it passes, say so in the final report. If it fails, find from the commits merged during this run which issue caused it: read the failure, then `git log` and `git show` the run's `Refs #N:` commits. Move that issue to More to do with one plain-language comment headed "Full check failed" (what fails and why that issue), and note in the final report that no `VERSION` may be bumped until full passes again. Never revert or fix it here: the next /next reworks it. If the cause can't be pinned to one issue, comment on each candidate and say so in the report.

**Idle work** (`/next all` only, not `/next N`): once nothing is left to take, after the release check, follow `.claude/commands/tidy.md` from its step 0 (it resumes unfinished idle work first): up to 2 tests or docs improvements by test-writer, each fully checked and merged, reported on one `tests` issue in Ready for testing; then up to 3 refactor proposals by refactor-scout, filed in Drafted. Its report goes into the final report.

**Final report**, in plain language, no code or jargon:
- **Housekeeping**: the issues closed because their cards were already in Done, or "nothing".
- **Size and path**: one line per issue built or reworked: `#N title — size, path` (reviewer only, or test-checker, reviewer and full), adding "upgraded from S: <why>", "bundled with #M" or "series <name>" where they apply. Then one line per series review: `Series "<name>" (#A, #B, #C): passed` or `found problems, fixes in #F`.
- **Resumed**: one line per issue picked up from an earlier interruption: `#N title`, which checkpoint it continued from, and where it ended (Ready for testing or blocked). Write "nothing" if none.
- **Ready for testing**: one line per issue (a series' issues only once its review passed; the others are listed as waiting in Building): `#N title`, the new version if any, what to look at in the style guide (or "nothing visible yet"), and what Kettle Video needs to do (or "nothing").
- **Decided**: one line per decision made without asking: `#N title` and what was decided. Then: "All labelled decided on the board; reply on the issue to change one." Write "nothing" if none.
- **Blocked**: one line per issue: `#N title`, and what it needs from the owner. Then: "Answer in the issue comments and remove the blocked label; the next /next picks it up."
- **Skipped**: one line per issue: `#N title`, and which issue it is waiting for.
- **Left over** (only when the N limit was reached): how many issues are still waiting in More to do and Ready for dev.
- **Release check** (`/next all` only): the full check passed, or which issue it sent back to More to do and why; or "nothing merged, not run".
- **Idle work** (`/next all` only): tidy.md's report: tests and docs (with the smoke check), refactor proposals filed, and anything found along the way.

The `blocked` label is the owner's switch: once they remove it, the issue is picked up again by any /next as normal.
