<!-- SPDX-License-Identifier: AGPL-3.0-only -->
---
name: briefing
description: "Assembles a session context briefing from your configured issue tracker, recent git history, and active work signals. Use when: starting a new session, resuming after a break, user says 'catch me up', 'what was I working on', 'where did I leave off', context recovery after compaction, or user asks for project orientation. Complements Claude Code's native /recap (which auto-triggers after extended idle); briefing is invoked explicitly and pulls from cross-tool sources native /recap does not aggregate."
disable-model-invocation: false
metadata:
  author: Backchain
  version: 1.0.0
---

# Briefing

Produce a concise orientation briefing for session start or context recovery. Aggregate signals from multiple sources into a single scannable summary so the user can quickly re-orient.

Read-only. Reads issue-tracker state and git history; never writes, never modifies state.

## Relationship to native `/recap`

Native [Claude Code `/recap`](https://code.claude.com/docs/en/changelog) (v2.1.108+) provides a recap of prior session activity when returning after a 75+ minute absence, or on demand. `briefing` **complements** `/recap` rather than replacing it:

- `/recap` is auto-triggered after idle and operates on Claude Code session history.
- `briefing` is invoked explicitly and aggregates *cross-tool* signals: issue tracker, git, working-memory presence, staging directory staleness.

Use `/recap` when you want the narrative of the last session. Use `briefing` when you want a structured snapshot of where the project stands across tools.

## Data sources

`briefing` reads from sources the user's project has configured. **Detect available sources from project signals; ask the user when ambiguous.**

| Signal | Source detection | What to read |
|--------|-----------------|--------------|
| Issue tracker | `.beads/` directory → Beads. `.linear/` or environment → Linear. `gh` CLI authenticated → GitHub Issues. Explicit declaration in `CLAUDE.md` → use that. None of the above → **ask the user.** | Ready / available work, in-progress items, blocked items, project counts |
| Git activity | Always available in a git repo | Recent commits (last 10), uncommitted changes (`git status --short`) |
| Working memory | A `.memory/` directory in the working tree → see the `working` skill | Active in-progress checkpoint state |
| Staging dir | A configured staging directory (often `outputs/`) | Files older than 7 days as a staleness signal |

If a source is unavailable, skip it gracefully and note the gap in the output. Do not fail the whole briefing if one source is missing.

If the user has not declared a primary issue tracker and none can be detected, ask once: *"Which issue tracker should I read for ready / in-progress items?"* Then proceed with the answer for this session.

## Output format

```
# Session Briefing

## Active Work
[In-progress issues with IDs and titles, or "none"]

## Ready to Start
[Top 3-5 ready issues, ordered by priority, or "none"]

## Blocked
[Blocked issues with what's blocking them, or "none"]

## Recent Activity
[Last 5 git commits, one line each]

## Uncommitted Changes
[Modified/untracked files, if any]

## Quick Stats
- Open issues: N
- In progress: N
- Blocked: N

## Housekeeping
[Staleness signals, if any]
```

## Staleness signals

Check these during briefing assembly. Include relevant findings under `## Housekeeping` only if findings exist (omit the section otherwise).

| Signal | Check | Suggested phrasing |
|--------|-------|--------------------|
| Aging staging files | Files in the configured staging dir older than 7 days | "N files older than 7 days in `<dir>` — consider running `consolidate staging`" |
| Active working memory | Non-empty content in `.memory/` | "`.memory/` has active content — consider `working promote` if work is ready to graduate" |

These are suggestions, not actions. The skill never invokes another skill or writes anything.

## Constraints

| Rule | Why |
|------|-----|
| No file output — display inline only | Briefings are ephemeral; writing files adds noise |
| Under 40 lines total | Longer briefings defeat quick-scan orientation |
| Always run commands fresh | Stale cached data misleads re-orientation |
| Read-only — never modify state | The skill is purely informational |

If there are no open issues anywhere, note "Project is clear." If git is unavailable (not a repo), skip the git sections without erroring.
