# Copyright (c) 2026 Mario Carabotta
# SPDX-License-Identifier: MIT
"""Issue #32: the board script finds a just-added card, reads the whole shared board,
and leaves out draft cards and the other repo's cards.

Nothing here reaches GitHub. scripts/board.sh is copied into a temporary folder
with made-up board IDs, and a stand-in for the GitHub command line comes first
on PATH: it answers from planted files and writes down every change it is asked
to make, so the tests can see which card was moved or which issue was closed.

    scripts/test.sh unit tests.test_board_script
"""
import json, os, shutil, subprocess, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "example/enamel"
OTHER_REPO = "example/other-app"
BOARD = {
    "owner": "example", "repo": REPO, "projectNumber": 7, "projectId": "PROJECT",
    "statusFieldId": "STATUS",
    "statusOptions": {"Ready for dev": "opt-ready", "Building": "opt-building", "Done": "opt-done"},
}

# The stand-in for gh. The card list honours --limit, as the real one does.
FAKE_GH = r'''#!/usr/bin/env python3
import json, os, sys
here = os.environ["FAKE_GH_DIR"]
args = sys.argv[1:]
def log(line):
    with open(os.path.join(here, "calls.log"), "a") as f:
        f.write(line + "\n")
def planted(name):
    path = os.path.join(here, name)
    return open(path).read() if os.path.exists(path) else None
if args[:2] == ["project", "item-list"]:
    items = json.loads(planted("items.json"))
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 30
    print(json.dumps({"items": items[:limit]}))
elif args[:2] == ["api", "graphql"]:
    reply = planted("graphql.json")
    if reply is None:
        sys.exit(1)  # as when offline
    print(reply)
elif args[:2] == ["project", "item-edit"]:
    log("edit " + args[args.index("--id") + 1] + " " + args[args.index("--single-select-option-id") + 1])
elif args[:2] == ["project", "item-add"]:
    log("add " + args[args.index("--url") + 1])
elif args[:2] == ["issue", "view"]:
    print("OPEN")
elif args[:2] == ["issue", "close"]:
    log("close " + args[2])
else:
    sys.stderr.write("fake gh: unexpected call " + " ".join(args) + "\n")
    sys.exit(3)
'''


def card(number, repo=REPO, status="Ready for dev"):
    return {"id": f"card-{repo.split('/')[1]}-{number}", "status": status, "labels": [],
            "title": f"Issue {number}", "content": {"number": number, "repository": repo}}


def draft(n, status="Done"):
    """A draft card: no issue, so no number and no repository."""
    return {"id": f"draft-{n}", "status": status, "title": f"Draft idea {n}",
            "content": {"title": f"Draft idea {n}", "type": "DraftIssue"}}


def empty_card(status="Done"):
    """A card whose content comes back empty (null), as for a draft or a card the token can't read."""
    return {"id": "empty-card", "status": status, "title": "Unreadable card", "content": None}


def issue_cards(*cards):
    """The issue's own list of cards, as the GraphQL reply gives it."""
    nodes = [{"id": cid, "project": {"number": number, "owner": {"login": login}}}
             for cid, number, login in cards]
    return {"data": {"repository": {"issue": {"projectItems": {"nodes": nodes}}}}}


class BoardScript(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="enamel-board-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        for folder in ("scripts", ".claude", "bin", "gh"):
            os.makedirs(os.path.join(self.dir, folder))
        shutil.copy(os.path.join(ROOT, "scripts", "board.sh"), os.path.join(self.dir, "scripts"))
        self.write(".claude/board.json", json.dumps(BOARD))
        self.write("bin/gh", FAKE_GH)
        os.chmod(os.path.join(self.dir, "bin", "gh"), 0o755)
        self.env = dict(os.environ, FAKE_GH_DIR=os.path.join(self.dir, "gh"),
                        PATH=os.path.join(self.dir, "bin") + os.pathsep + os.environ.get("PATH", ""))

    def write(self, path, text):
        with open(os.path.join(self.dir, path), "w", encoding="utf-8") as f:
            f.write(text)

    def plant(self, items, graphql=None):
        self.write("gh/items.json", json.dumps(items))
        if graphql is not None:
            self.write("gh/graphql.json", json.dumps(graphql))

    def run_board(self, *args):
        result = subprocess.run(["bash", "scripts/board.sh", *args], cwd=self.dir, env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr

    def calls(self):
        path = os.path.join(self.dir, "gh", "calls.log")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return f.read().splitlines()

    # A card found through the issue when the board's list doesn't have it yet.

    def test_lagging_list_finds_the_card_through_the_issue(self):
        self.plant([card(1), card(2)], issue_cards(("card-new-40", 7, "example")))
        code, out, err = self.run_board("status", "40", "Building")
        self.assertEqual(code, 0, err)
        self.assertIn("#40 moved to Building", out)
        self.assertEqual(self.calls(), ["edit card-new-40 opt-building"])

    def test_card_added_and_moved_straight_after_works_in_one_go(self):
        self.plant([card(1)], issue_cards(("card-new-41", 7, "example")))
        code, _, err = self.run_board("add", "41")
        self.assertEqual(code, 0, err)
        code, out, err = self.run_board("status", "41", "Ready for dev")
        self.assertEqual(code, 0, err)
        self.assertIn("#41 moved to Ready for dev", out)
        self.assertEqual(self.calls(), [f"add https://github.com/{REPO}/issues/41",
                                        "edit card-new-41 opt-ready"])

    def test_issue_on_other_boards_only_is_not_on_the_board(self):
        # Another board with the same number under another account, and another board of this account.
        self.plant([card(1)], issue_cards(("card-elsewhere", 7, "someone-else"), ("card-other", 8, "example")))
        code, _, err = self.run_board("status", "42", "Building")
        self.assertNotEqual(code, 0)
        self.assertIn("issue #42 is not on the board", err)
        self.assertEqual(self.calls(), [])

    def test_no_reply_from_the_issue_fails_plainly(self):
        self.plant([card(1)])
        code, _, err = self.run_board("status", "43", "Building")
        self.assertNotEqual(code, 0)
        self.assertIn("issue #43 is not on the board", err)
        self.assertEqual(self.calls(), [])

    def test_the_list_comes_first_when_it_has_the_card(self):
        self.plant([card(44)], issue_cards(("card-from-issue", 7, "example")))
        code, _, err = self.run_board("status", "44", "Building")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls(), ["edit card-enamel-44 opt-building"])

    # A card past the 200th is still found.

    def test_card_past_the_200th_is_found_in_the_list(self):
        items = [card(n, OTHER_REPO) for n in range(1, 251)] + [card(500)]
        self.plant(items)  # no answer through the issue: only the list can find it
        code, out, err = self.run_board("status", "500", "Done")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls(), ["edit card-enamel-500 opt-done"])
        code, out, err = self.run_board("list")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.split("\t")[0], "500")

    # Draft cards and other repos' cards are left out.

    def test_list_leaves_out_drafts_and_other_repos(self):
        self.plant([card(1), draft(1, "Ready for dev"), card(2, OTHER_REPO), card(3, status="Building"),
                    {"id": "no-content", "status": "Drafted", "title": "Bare card"},
                    empty_card("Ready for dev")])
        code, out, err = self.run_board("list")
        self.assertEqual(code, 0, err)
        numbers = [line.split("\t")[0] for line in out.splitlines()]
        self.assertEqual(numbers, ["1", "3"])

    def test_close_done_leaves_out_drafts_and_other_repos(self):
        self.plant([card(5, status="Done"), draft(2, "Done"), card(6, OTHER_REPO, "Done"),
                    empty_card("Done"), card(7, status="Building")])
        code, out, err = self.run_board("close-done")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls(), ["close 5"])
        self.assertIn("close-done: 1 closed", out)

    def test_other_repos_card_with_the_same_number_is_never_moved(self):
        self.plant([card(9, OTHER_REPO)], issue_cards(("card-enamel-9", 7, "example")))
        code, _, err = self.run_board("status", "9", "Building")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls(), ["edit card-enamel-9 opt-building"])


if __name__ == "__main__":
    unittest.main()
