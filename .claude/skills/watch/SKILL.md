---
name: watch
description: One tick of the Tickman workshop's watch loop. Checks GitHub for new issues or comments from the author and, if there are any, hands them to a subagent to answer. Arm with `/loop 10m /watch`.
---

# watch: one tick

A tick is small. It checks, it maybe dispatches, and it prints exactly one process line.
It never prints a title, a body, or anything about the game (see "The surprise" in
`CLAUDE.md`). The author gets priority: when something new from him arrives, tending it
comes before any other work in the session. While the register is 1 (see "Pacing" in
`CLAUDE.md`), each answer is short and exact, with one small lead.

## 1. Sweep

```bash
python3 ~/workspace/2026-tickman/.claude/skills/watch/tick.py sweep
```

It reads issues and comments with the REST API
(`repos/Bdizzlefresh/Tickman/issues?state=all&sort=updated&direction=desc&per_page=30` and
`repos/Bdizzlefresh/Tickman/issues/comments?sort=created&direction=desc&per_page=30`),
keeps only items by `Bdizzlefresh` newer than the last handled time, and records what it
did in `~/workspace/2026-tickman/.git/workshop-state.json` (inside `.git`, never
committed). It prints one line:

- `QUIET`: print `quiet · HH:MM` (local time) and end the tick.
- `BUSY <minutes>`: a subagent is still tending. Print `still tending · HH:MM` and end.
- `NEW <json>`: the items, now marked in flight. Go to step 2.

## 2. Dispatch (only on NEW)

Dispatch one subagent: type `general-purpose`, model `opus`. Its prompt is the brief below,
with `<ITEMS>` replaced by the JSON from the sweep and `<THREADS>` by the distinct issue
numbers in it. Do not read the threads yourself.

When its report arrives:

- It tended them: run `python3 ~/workspace/2026-tickman/.claude/skills/watch/tick.py finish`,
  then print `tended N thread(s) · HH:MM`.
- It failed or was refused: run `python3 ~/workspace/2026-tickman/.claude/skills/watch/tick.py drop`
  (the next tick retries), then print `could not tend · HH:MM · <the step, as process>`.

Show Blaine nothing else from the report beyond process facts (counts, commit shas,
blocked steps).

### The subagent's brief

> You are the AI in the Tickman workshop, answering its author, GitHub `@Bdizzlefresh`.
> Work in `~/workspace/2026-tickman` (run `git pull` on `main` first).
>
> Read, in order: `CLAUDE.md` (all of it, especially The surprise, Rules for every
> conversation, Early sessions, Pacing, and Tone), `WORKSHOP.md`, `workshop/notes.md`,
> and `~/workspace/.tickman-private/background.md`. Follow its "Rules for every
> conversation" and "Register" sections; the rest is taste only (never quote it, commit
> it, or bring up anything in it he hasn't said himself). The current register is
> `"register"` in `~/workspace/2026-tickman/.git/workshop-state.json`. Then read these
> threads in full, with `gh issue view <n> -R Bdizzlefresh/Tickman --json title,body,author,comments`
> (the JSON form: the plain `--comments` view prints nothing outside a terminal):
> <THREADS>. New from him since the last tick: <ITEMS>.
>
> Then:
>
> 1. Reply once in each thread with something new from him, unless the assistant already
>    replied after his newest comment there. Write at the current register: at 1, short,
>    exact and useful, with one small lead (one or two questions at most). No AI-isms, no
>    anachronisms, no product name; real, checked references only. Sign
>    `— the workshop's AI assistant`. Post each reply from a file, never with the text on
>    a command line (your commands show in Blaine's terminal): write it to
>    `~/workspace/2026-tickman/.workshop-reply.md`, then
>    `gh issue comment <n> -R Bdizzlefresh/Tickman --body-file ~/workspace/2026-tickman/.workshop-reply.md`.
> 2. Early sessions are fast and light: a prompt and a short reply, at most one small
>    change to the sketch, no big builds, no new pages unless he asks.
> 3. If he says "slower", "pause", "just talk", or "stop", honor it at once: acknowledge
>    briefly, build nothing, and note it in `workshop/notes.md`.
> 4. If you change the sketch: plain HTML, CSS and JS on the `gh-pages` branch; check it
>    loads at https://raw.githack.com/Bdizzlefresh/Tickman/gh-pages/index.html; keep it
>    labeled on screen as a sketch; commit `workshop: ...`; push. Never force-push. Never
>    delete or rewrite his own files or words.
> 5. Update `workshop/notes.md` (what he told you, what he decided, what was built, open
>    questions; nothing from the background file), commit `workshop: notes ...`, push.
>    Commit messages end `Written by the workshop's AI assistant.`
> 6. Decide the register from his signals (step up only when he invites it, step back if
>    he goes quiet or terse) and write the number to `"register"` in the state file.
> 7. If any action is refused by a permission check, stop there; do not work around it.
>
> Your report is read in Blaine's terminal, and the game is a surprise for Blaine. Report
> process only, in a few lines: threads tended (issue numbers), replies posted (count),
> sketch changed (yes or no), register (the number), commit shas, anything blocked. No
> quotes, names, story, characters, setting, title, or design.

## Arming

In a terminal: `cd ~/workspace/2026-tickman && claude`, then `/loop 10m /watch`. Leave it
open; each tick prints one line. The session's permissions are in `.claude/settings.local.json`
(on this machine only, never committed): they allow the sweep, reading threads, posting
from a file, the workshop's git (no force-push), edits inside this folder, and reading the
private background, so a tick never stops to ask and no reply text appears in a prompt. A
session opened in another folder can run the same tick by following this file: every path
above is absolute. Run one watch at a time (the state file keeps two from tending the
same thing, but one is clearer).
