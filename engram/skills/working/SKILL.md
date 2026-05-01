<!-- SPDX-License-Identifier: AGPL-3.0-only -->
---
name: working
description: "Manage ephemeral .memory/ conversation state across multi-day sessions. Checkpoint todos, decisions, and questions; promote artifacts to permanent knowledge; clean up after promotion. Use when: the user says 'checkpoint', 'save working memory', 'promote working memory', 'clean up memory', wants to persist conversation artifacts for a future session, or resumes work and asks 'what were we working on' near a .memory/ directory. Do not trigger for native auto-memory operations."
disable-model-invocation: false
metadata:
  author: Backchain
  version: 1.0.0
---

# Working Memory

Manage ephemeral `.memory/` directories for persisting structured conversation state across multi-day Claude Code sessions. Three commands cover the full lifecycle:

| Command | Purpose |
|---------|---------|
| `/working checkpoint` | Create or update `.memory/` with current conversation state |
| `/working promote` | Move `.memory/` artifacts to permanent knowledge locations |
| `/working cleanup` | Delete promoted content, preserve the directory |

## Working memory vs auto memory

This skill complements [Claude Code's native auto memory](https://code.claude.com/docs/en/memory). They serve different purposes:

| | Working memory (this skill) | Auto memory (native) |
|---|---|---|
| **Trigger** | User-initiated (`/working checkpoint`) | Automatic (Claude decides what's worth remembering) |
| **Content** | Structured work state — todos, decisions, questions | Implicit learnings — corrections, preferences, patterns |
| **Lifecycle** | Ephemeral: checkpoint → promote → cleanup | Persistent until manually deleted |
| **Scope** | Per-directory (`.memory/` in CWD) | Per-project (`~/.claude/projects/<project>/`) |
| **Promotion path** | Explicit: ADRs, issue-tracker entries, docs | Implicit: stays in MEMORY.md / topic files |

**Use working memory for** structured in-flight work that warrants a deliberate promotion gate. **Let auto memory handle** preferences, build insights, and behavioral corrections that Claude discovers organically.

During `checkpoint`, **do not capture items that auto memory already handles** — user preferences, build commands, debugging shortcuts, code style. Focus on actionable work state.

During `promote`, decisions too small for a full ADR but worth persisting can be written into auto memory using its standard frontmatter format. Once written there, they are auto memory's responsibility; `working` does not re-modify them.

## How it works

`.memory/` directories are intended to be **gitignored** (the user is responsible for adding `.memory/` to their global or project gitignore). They hold ephemeral conversation artifacts that persist on disk between sessions but never enter version control.

The three commands form a lifecycle:

1. **Checkpoint** during or at the end of a work session.
2. **Promote** when artifacts are ready to become permanent (ADRs, issue-tracker entries, documentation, or auto-memory entries for context-only items).
3. **Cleanup** after promotion to reset for the next session.

## File structure

```
.memory/
├── todos.md       # Action items (in-progress, blocked, completed, backlog)
├── decisions.md   # Choices and rationale (ADR candidates)
└── questions.md   # Open questions and blockers
```

Templates for each file live in `${CLAUDE_SKILL_DIR}/templates/`. Per-command behavior detail lives in `${CLAUDE_SKILL_DIR}/commands/`.

## Promotion targets

The skill prompts the user to confirm each promotion target — it does not assume a specific issue tracker, ADR location, or documentation system.

| Artifact type | Default suggestion (override via prompt) |
|---------------|-----------------------------------------|
| Decision (significant) | New ADR in `docs/adr/` if present, otherwise ask |
| Decision (minor but persistent) | Auto-memory entry under `~/.claude/projects/<project>/memory/` |
| Todo (actionable) | An issue in the user's configured issue tracker |
| Todo (completed) | No promotion needed |
| Question (resolved) | Append Q&A to a relevant context document |
| Question (unresolved) | Either an issue or a context document — ask |

**Tool detection at promotion time:**
- Issue tracker: detect from project signals (e.g., `.beads/`, `.linear/`, `gh` auth, an explicit declaration in `CLAUDE.md`). If unclear, ask the user once for the session.
- ADR location: prefer `docs/adr/` if it exists. Otherwise ask.
- Context documents: prefer `docs/` or a user-declared location.

## Constraints

| Rule | Detail |
|------|--------|
| Location | `.memory/` is created in the current working directory |
| Git tracking | The skill expects `.memory/` to be gitignored; warn if the user has it tracked |
| Preservation | `checkpoint` *appends* to existing content — never overwrites |
| Confirmation | `promote` and `cleanup` require explicit user approval |
| Promotion before cleanup | Warn if `cleanup` is invoked while content has not been promoted |
| Directory preservation | `cleanup` empties files and keeps the `.memory/` directory in place |

## References

See `${CLAUDE_SKILL_DIR}/reference.md` for a worked example, integration notes, and error handling.
