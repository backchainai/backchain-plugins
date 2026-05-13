<!-- SPDX-License-Identifier: AGPL-3.0-only -->
---
title: Working Memory Reference
purpose: Worked example, integration notes, and error handling for the working skill.
---

# Working Memory Reference

## Worked example

### Day 1: start a multi-day task

```
cd ~/projects/api-redesign/

User: "Let's design the API authentication"
[discussion happens]
User: "/engram:working checkpoint"
Claude: [creates .memory/ with todos, decisions, questions]
Checkpointed working memory:
- 2 todos added
- 1 decision documented
- 1 question captured
```

### Day 3: resume

```
cd ~/projects/api-redesign/

User: "What were we working on?"
Claude: [reads .memory/ files; also checks native auto memory MEMORY.md for related context]
"We were designing API authentication. Where we left off:
- Decision: JWT with refresh tokens
- Todo: implement token validation middleware
- Question: support multiple issuers?
(Auto memory also notes a project preference for async standups.)"
```

### Day 5: promote and clean up

```
User: "/engram:working promote"
Claude: "I see these artifacts. Where should they go?
1. 1 decision -> ADR. I see docs/adr/ in this project — use it?
2. 3 todos -> issues. Detected .beads/ — use Beads, or another tracker?
3. 1 unresolved question -> issue or context.md?

Confirm each before I create files."
[user confirms each]
Claude: [creates files / issues per user direction]
"Promoted. Ready for cleanup."

User: "/engram:working cleanup"
Claude: [deletes contents, keeps .memory/ directory]
"Working memory cleaned up. Directory preserved for future use."
```

## Integration notes

### With native auto memory

Native auto memory (`~/.claude/projects/<project>/memory/`) captures *implicit* learnings automatically. Working memory captures *explicit* work state.

During `promote`, decisions too small for a full ADR but worth persisting can be written into auto memory using the standard auto-memory frontmatter:

```
---
name: <short slug>
description: <one-line summary>
type: project
---
```

When recalling context ("what were we working on"), check both `.memory/` and the auto memory `MEMORY.md` for a complete picture.

### With CLAUDE.md hierarchy

`.memory/` can exist at any directory level. Each level is independent:

```
~/projects/.memory/                       # cross-project context
~/projects/client-a/.memory/              # client-specific context
~/projects/client-a/api-redesign/.memory/ # task-specific context
```

The skill operates on the `.memory/` in the current working directory.

### With search indexing tools

If you index documentation locally (search tools like Khoj, ripgrep configurations, etc.), exclude `.memory/` from indexes. Promoted artifacts (ADRs, docs, issues) are what should be searchable; in-flight working memory should not be.

## Promotion classification

| Artifact | Significance | Promotion target (default suggestion) |
|----------|-------------|---------------------------------------|
| Decision | Architectural / structural | New ADR (prompt for location) |
| Decision | Minor but persistent project context | Auto-memory entry (`type: project`) |
| Decision | Trivial (tool versions, formatting) | No promotion — auto memory handles these organically |
| Todo | Actionable, owned | Issue in the user's tracker |
| Todo | Completed | No promotion |
| Question | Resolved | Q&A appended to a relevant context document |
| Question | Unresolved | Issue (if blocking) or context document (if informational) |

## Error handling

| Condition | Response |
|-----------|----------|
| `.memory/` missing during `checkpoint` | Create directory, initialize from templates |
| No content to promote | "No artifacts in `.memory/`. Run `checkpoint` first." |
| `cleanup` with unpromoted content | Warn: "These items have not been promoted. Proceed with deletion?" Require explicit confirmation. |
| `.memory/` missing during `cleanup` | "No `.memory/` found. Nothing to clean up." |
| Template file missing | Regenerate from skill templates |
| `.memory/` is tracked by git | Warn the user and recommend adding to `.gitignore` before checkpointing |

## File naming

- Directory: `.memory/` (hidden, lowercase, dot-prefixed)
- Files: `todos.md`, `decisions.md`, `questions.md` — lowercase, no dates (timestamps live inside files)

## Backup posture

- `.memory/` is intended to be gitignored.
- Contents are local-only; no cloud sync, no version control history.
- If content is important enough to survive disk loss, promote it before that becomes a question.
