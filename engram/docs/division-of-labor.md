# Division of Labor: engram and Claude Code Native Memory

<!-- SPDX-License-Identifier: AGPL-3.0-only -->

This document describes what Claude Code handles natively, what `engram` adds on top, and how the two are designed to coexist without stepping on each other.

## What Claude Code does natively

As of [Claude Code 2.1.108+](https://code.claude.com/docs/en/changelog), the harness ships two memory-related features:

### Auto memory

Source: [Claude Code memory documentation](https://code.claude.com/docs/en/memory#auto-memory). Available in v2.1.59+.

- **What it is:** A directory of markdown files that Claude writes to itself across sessions. Captures *learnings and patterns* — "use pnpm not npm," "the API tests need a local Redis," debugging insights, code-style preferences.
- **Storage:** `~/.claude/projects/<project>/memory/` (or `autoMemoryDirectory` if reconfigured). Each project shares one auto-memory dir across worktrees, derived from the git repo root.
- **Loaded on session start:** First 200 lines or 25KB of `MEMORY.md` (the index file). Topic files in the same directory are read on demand.
- **Trigger surface:** Implicit. Claude decides when to write. The user can toggle on/off via `/memory` or `autoMemoryEnabled` in settings.
- **Native maintenance:** None automated. The user can browse and edit via `/memory`. Files are plain markdown.

### Session recap (`/recap`)

Source: changelog v2.1.108 (April 2026), v2.1.110 (April 2026).

- **What it is:** A summary of prior session activity that surfaces when returning to a session after a 75+ minute absence. Manually invocable with `/recap`.
- **Trigger surface:** Time-based (extended idle return) or manual.
- **Configuration:** `/config` menu, or `CLAUDE_CODE_ENABLE_AWAY_SUMMARY` environment variable to force-enable for telemetry-disabled installs.

### What is *not* in native Claude Code

Three things `engram` users sometimes assume are native but are not (as of the most recent changelog reviewed):

- **No automatic auto-memory consolidation in the current official changelog.** Native auto-memory accumulates files; nothing in the current official changelog prunes stale entries, merges overlaps, or maintains the `MEMORY.md` index automatically. Pruning and consolidation remain a user-driven activity.
- **No knowledge-directory audit.** Native memory is scoped to `~/.claude/projects/<project>/memory/`. It does not scan project-level `docs/`, generated outputs, or archives.
- **No structured working-memory lifecycle.** Native auto-memory is implicit and cumulative. There is no native equivalent for "checkpoint a structured snapshot of in-progress todos / decisions / questions and explicitly promote them to permanent locations later."

## What engram adds

`engram` provides three skills that operate at boundaries native auto-memory does not address. Each is independently invocable.

### Per-skill mapping

| Skill | Relationship to native | What it adds |
|-------|------------------------|--------------|
| `consolidate` | **Extends** auto-memory (graduation) and **adjacent** to it (knowledge-directory audit) | Identifies auto-memory entries stable enough to graduate to `.claude/rules/` or `CLAUDE.md`. Audits user-declared knowledge directories (`docs/`, output staging areas, archives) for stale, misplaced, or duplicated content. Produces an editable plan file the user reviews before any destructive action. |
| `briefing` | **Complements** `/recap` | Produces a concise, scannable briefing assembled from issue-tracker state, recent git activity, in-progress signals, and staleness flags. Where `/recap` is auto-triggered after extended idle, `briefing` is on-demand and configurable per the user's tools. Useful at session start, after compaction, or when a user explicitly asks "what was I working on?" |
| `working` | **Complements** auto-memory | Manages an explicit `.memory/` directory for structured in-flight work — todos, decisions, questions. Three-command lifecycle: checkpoint (capture), promote (move to permanent locations such as ADRs or issue-tracker entries), cleanup (clear after promotion). Designed for multi-day work that warrants a deliberate promotion gate, not the implicit drip-capture native auto-memory provides. |

### Where the boundaries are

**`consolidate` rule:** Treat native auto-memory as the source of truth for what Claude has learned. Do not delete or rewrite auto-memory entries; the appropriate action is *graduation* (move to `.claude/rules/` or `CLAUDE.md`) followed by deletion of the now-redundant source file in auto-memory. Do not modify `MEMORY.md` directly.

**`briefing` rule:** Read-only. Reads issue-tracker state and git history, never writes. Surfaces "consider running `/working:promote`" or "consider `/consolidate`" as suggestions, never as automatic actions.

**`working` rule:** Operates on `.memory/` (project-relative, gitignored), not on `~/.claude/projects/`. During promotion, decisions small enough not to warrant an ADR can be written into auto-memory using the standard auto-memory frontmatter format — but content written there is then native auto-memory's responsibility and `working` will not re-modify it.

### Configuration interactions

| Concern | Native | engram |
|---------|--------|--------|
| Default memory location | `~/.claude/projects/<project>/memory/` | `.memory/` (project-relative) for `working`; user-declared knowledge dirs for `consolidate` |
| Override location | `autoMemoryDirectory` setting | Skill prompts the user when a directory choice is required |
| Toggle | `autoMemoryEnabled`, `/memory` | Skills are invoked explicitly; not always-on |
| Loaded at session start | First 200 lines / 25KB of `MEMORY.md` | Nothing — skills load on invocation only |

## Recommended setup

Use both. The two systems are designed to be used together:

1. Leave native auto-memory enabled (`autoMemoryEnabled: true`). Let Claude accumulate implicit learnings as it works.
2. Run `consolidate` periodically (after milestones, when knowledge directories feel cluttered) to graduate stable auto-memory entries to permanent rules and audit project knowledge directories. The skill produces a plan file you review before any action.
3. Run `briefing` when starting or resuming a session to get a quick scan of issue-tracker state, recent activity, and any housekeeping prompts.
4. Use `working` for multi-day tasks where you want explicit, structured state: a deliberate checkpoint at session end, a promotion step before things get lost in conversation history.

## Native feature changes that would affect this division

If a future Claude Code release ships:

- **Native automatic auto-memory consolidation**, `consolidate` would shift to focus solely on knowledge-directory audit and graduation — and step further away from auto-memory's internal lifecycle.
- **Richer native session recap that integrates issue trackers and git state**, `briefing` would shift to focus on aspects native cannot reach: cross-tool aggregation, custom staleness signals, and tool-agnostic prompts.
- **Native structured working memory**, `working` would either retire or shift to focus on the promotion-to-permanent-knowledge step, which is `engram`'s most distinctive contribution.

We'll track changelog entries against this section and adjust skill scopes to keep `engram` complementary, not redundant.

## References

- [Claude Code Memory Documentation](https://code.claude.com/docs/en/memory)
- [Claude Code Changelog](https://code.claude.com/docs/en/changelog)
- [agentskills.io Specification](https://agentskills.io/specification)
