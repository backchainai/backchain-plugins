<!-- SPDX-License-Identifier: AGPL-3.0-only -->
---
name: consolidate
description: "Audit knowledge directories (.memory/, docs/, staging/, archive/) and Claude Code auto memory for stale, misplaced, or duplicated content. Generates an editable cleanup plan file, then executes approved actions after review. Use when: periodic knowledge cleanup, after project milestones, files feel scattered or disorganized, output staging feels cluttered, moving deliverables to permanent homes. Trigger phrases: consolidate knowledge, knowledge cleanup, audit knowledge directories, find stray docs, tidy up knowledge, triage outputs, review staging, clean up outputs."
disable-model-invocation: false
metadata:
  author: Backchain
  version: 1.0.0
---

# Consolidate

Audit knowledge directories and Claude Code auto memory for stale, misplaced, or duplicated content. Produce an editable plan file the user reviews, then execute approved actions. Designed to **complement**, not replace, native auto-memory: this skill never modifies `MEMORY.md` directly and never deletes auto-memory entries — it focuses on graduation (promoting stable entries to permanent rules) and on knowledge directories outside auto-memory's scope.

## Relationship with auto memory

Native [Claude Code auto memory](https://code.claude.com/docs/en/memory) writes implicit learnings to `~/.claude/projects/<project>/memory/`. This skill **complements** it:

| Concern | Native auto memory | `consolidate` (this skill) |
|---------|-------------------|---------------------------|
| Capture implicit learnings | Yes | No — defer to native |
| Maintain `MEMORY.md` index | Yes (manual edits via `/memory`) | No — never modify directly |
| Graduate feedback → rules / CLAUDE.md | No | Yes — primary responsibility |
| Audit project knowledge directories | No | Yes — user-declared scan roots |
| Manage staging-directory lifecycle | No | Yes — age-based classification |
| Detect stray operational knowledge | No | Yes |

**Do not:**
- Recommend `DELETE` or `ARCHIVE` for files inside `~/.claude/projects/<project>/memory/`. Use the `RULES` or `CLAUDEMD` actions to *graduate* stable entries; deletion of the source file then happens as part of graduation, not as cleanup.
- Modify `MEMORY.md`.
- Touch any lock files in the auto-memory directory.

## Scan roots

Before scanning, the skill needs a list of knowledge directories to inspect. **If the user has not declared scan roots in their project's `CLAUDE.md` or in conversation, ask them.** Sensible defaults to suggest:

```
.memory/
docs/
outputs/                                    # or whatever the project uses for staging
archive/                                    # or whatever the project uses for archive
~/.claude/projects/<project>/memory/
```

Skip these directory patterns unconditionally:

```
.git/                node_modules/          .venv/
.claude/             dist/                  build/
*.pdf  *.docx  *.xlsx                       # binary files — no content analysis
```

If a directory the user named does not exist, surface that in the report rather than failing silently.

## Commands

| Command | Purpose |
|---------|---------|
| `/consolidate` or `/consolidate scan` | Full audit: scan all declared knowledge dirs, generate plan file |
| `/consolidate staging` | Quick triage of one designated staging directory with age classification + destination prompts (inline report, no plan file) |
| `/consolidate execute` | Read the user-edited plan file and execute approved actions |
| `/consolidate status` | Inline health summary: file count and age per declared directory, stray count |

## Scan algorithm

### Step 1 — Discover

Walk each declared scan root recursively. Collect: path, age, size, content summary. Skip the unconditional-skip patterns above.

### Step 2 — Classify each file

**Auto-memory files** (`~/.claude/projects/<project>/memory/`) use **graduation-only** classification:

1. `MEMORY.md` or any lock file → `KEEP` (auto-memory infrastructure — never touch)
2. Feedback memory, ≥14 days old, stable across sessions → `RULES` or `CLAUDEMD` (graduate)
3. Project memory, now obsolete (completed work, resolved decision) → `DELETE` (only after asking the user — graduating these to a finished-work archive is often better)
4. Otherwise → `KEEP`

**All other files** use the general classification (evaluate in order; first match wins):

1. System artifact (`.DS_Store`, `.gitkeep`) → `DELETE`
2. Superseded (newer version exists, or content captured in rules / CLAUDE.md / skills) → `DELETE` or `ARCHIVE`
3. Implementation note for completed work → `DELETE`
4. Point-in-time snapshot → `DELETE` if >30 days, `ARCHIVE` if ≤30 days
5. Misplaced (operational knowledge in wrong knowledge directory) → `MOVE`
6. Promotable (in-flight work ready for permanent home) → `DOCS`, `RULES`, `CLAUDEMD`, or `SKILL`
7. Otherwise → `KEEP`

### Step 3 — Detect strays

A "stray" is operational knowledge (methodology, decisions, planning, standards, patterns, workflows) found outside the declared scan roots. Heuristics for "operational":

- Filename contains: `guide`, `plan`, `strategy`, `standard`, `pattern`, `workflow`, `decision`, `adr`
- Content contains methodology, process, architectural decisions, design rationale, planning, conventions, or reusable patterns

Skip directories that legitimately hold non-operational content (project deliverables, raw input data, execution logs, meeting records, the `.claude/` configuration tree). When in doubt, surface in the report and let the user classify rather than guess.

### Step 4 — Generate plan file

Write a plan to a path the user has designated for staging output (or `<scan-root>/plans/consolidate-plan-YYYY-MM-DD.md` if undeclared) using the template at `${CLAUDE_SKILL_DIR}/templates/plan-template.md`. The plan is editable: the user changes the **Action** column to approve, override, or skip each row before running `execute`.

## Action codes

| Code | Effect |
|------|--------|
| `DELETE` | Remove permanently |
| `ARCHIVE` | Move to the project's archive directory with mirrored source path |
| `DOCS` | Move to the project's `docs/` |
| `MEMORY` | Move to the project's `.memory/` |
| `RULES` | Move to `.claude/rules/` |
| `CLAUDEMD` | Incorporate into `CLAUDE.md` (present diff, require explicit approval) |
| `SKILL` | Move into a skill directory under `.claude/skills/` |
| `MOVE` | Relocate (destination given in the Reason column) |
| `KEEP` | No action |
| `SKIP` | Defer decision |

## Execution safety rules (`/consolidate execute`)

1. Parse the edited plan; extract all rows where Action is not `KEEP` or `SKIP`.
2. Create destination directories first.
3. Execute moves before deletes (`MOVE`, `ARCHIVE`, `DOCS`, `RULES`, `SKILL`). Prevents data loss when a path appears in both a move and a delete row.
4. Execute deletes last.
5. `CLAUDEMD` rows present a proposed diff and require an explicit `yes` before applying.
6. Clean empty directories produced by moves and deletes — empty directories mislead future scans.
7. Verify final counts match the plan summary; report discrepancies.

## Staging triage (`/consolidate staging`)

A focused, quick-check variant for a single designated staging directory. Produces an inline report — no plan file. Age thresholds:

| Age | Status | Default action |
|-----|--------|---------------|
| <7 days | Current | None |
| 7–30 days | Aging | Suggest a permanent destination |
| >30 days | Stale | Suggest archive or move |

For each file the user wants to act on, prompt for the destination. **Do not guess destinations** unless the user has declared a destination map in conversation or `CLAUDE.md`.

## Status output

`/consolidate status` produces inline text only: file count and age per declared directory, stray count with up to three example paths.

## Error states

| Condition | Response |
|-----------|----------|
| No scan roots declared and user declines to declare | Print the request, exit cleanly |
| A declared scan root does not exist | Note in report, continue with the rest |
| Plan file already exists for today | Overwrite; note "overwrote earlier plan from today" |
| Designated staging directory empty | "No files found. Nothing to triage." |
| Designated staging directory missing | "Staging directory does not exist." |

## References

- `${CLAUDE_SKILL_DIR}/references/directory-registry.md` — common knowledge-directory patterns and exclusion rules
- `${CLAUDE_SKILL_DIR}/templates/plan-template.md` — plan file scaffold
