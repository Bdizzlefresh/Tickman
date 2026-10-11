#!/usr/bin/env python3
"""One watch tick's bookkeeping for the Tickman workshop.

  tick.py sweep    Look for new issues and comments from the author.
                   Prints exactly one line:
                     QUIET
                     BUSY <minutes>          (a subagent is still tending)
                     NEW <json>              (items to tend; marked in flight)
  tick.py finish   The subagent reported: move the in-flight items to handled.
  tick.py drop     The subagent failed: clear in flight, so the next tick retries.

State lives in .git/workshop-state.json (inside .git, never committed):
  last_handled  newest created_at among handled items from the author
  handled       the last 200 handled items: kind, id, issue number, created_at
  in_flight     null, or {"since", "items"} while a subagent tends them
  last_tick     when the last sweep ran

Prints only kinds, ids, issue numbers and times: never a title or a body.
"""
import datetime
import json
import os
import subprocess
import sys

REPO = "Bdizzlefresh/Tickman"
AUTHOR = "Bdizzlefresh"
SIGNATURE = "— Claude (the AI in the workshop)"
ROOT = os.path.expanduser("~/workspace/2026-tickman")
STATE = os.path.join(ROOT, ".git", "workshop-state.json")
STALE_MINUTES = 60


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def api(query):
    return json.loads(subprocess.check_output(["gh", "api", query]))


def load():
    try:
        with open(STATE) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save(state):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE)


def minutes_since(stamp):
    then = datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return (datetime.datetime.now(datetime.timezone.utc) - then).total_seconds() / 60


def sweep():
    issues = api(f"repos/{REPO}/issues?state=all&sort=updated&direction=desc&per_page=30")
    comments = api(f"repos/{REPO}/issues/comments?sort=created&direction=desc&per_page=30")
    state = load()
    if state is None:
        # No state yet: the AI's newest signed post marks where handling stopped.
        mine = [x["created_at"] for x in issues + comments if SIGNATURE in (x.get("body") or "")]
        state = {"last_handled": max(mine) if mine else "1970-01-01T00:00:00Z",
                 "handled": [], "in_flight": None}
    state["last_tick"] = now()

    flight = state.get("in_flight")
    if flight and minutes_since(flight["since"]) < STALE_MINUTES:
        save(state)
        print(f"BUSY {int(minutes_since(flight['since']))}")
        return

    items = [{"kind": "issue", "id": x["id"], "issue": x["number"], "at": x["created_at"]}
             for x in issues if x["user"]["login"] == AUTHOR]
    items += [{"kind": "comment", "id": x["id"], "issue": int(x["issue_url"].rsplit("/", 1)[1]),
               "at": x["created_at"]}
              for x in comments if x["user"]["login"] == AUTHOR]
    seen = {(h["kind"], h["id"]) for h in state["handled"]}
    new = sorted((i for i in items
                  if i["at"] > state["last_handled"] and (i["kind"], i["id"]) not in seen),
                 key=lambda i: i["at"])
    if not new:
        state["in_flight"] = None
        save(state)
        print("QUIET")
        return
    state["in_flight"] = {"since": now(), "items": new}
    save(state)
    print("NEW " + json.dumps(new))


def finish():
    state = load()
    flight = state and state.get("in_flight")
    if not flight:
        print("nothing in flight")
        return
    state["handled"] = (state["handled"] + flight["items"])[-200:]
    state["last_handled"] = max([state["last_handled"]] + [i["at"] for i in flight["items"]])
    state["in_flight"] = None
    save(state)
    threads = sorted({i["issue"] for i in flight["items"]})
    print(f"handled {len(flight['items'])} item(s) in {len(threads)} thread(s)")


def drop():
    state = load()
    if state:
        state["in_flight"] = None
        save(state)
    print("in flight cleared")


if __name__ == "__main__":
    {"sweep": sweep, "finish": finish, "drop": drop}[sys.argv[1] if len(sys.argv) > 1 else "sweep"]()
