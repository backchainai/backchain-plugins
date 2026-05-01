<!-- SPDX-License-Identifier: AGPL-3.0-only -->
---
title: Knowledge Directory Registry
purpose: Common knowledge-directory patterns and exclusion rules for the consolidate skill.
---

# Knowledge Directory Registry

Reference for the `consolidate` skill. Describes the common directory shapes the scan algorithm recognizes, default scan priorities, and the exclusion list. **The registry is descriptive, not prescriptive** — every project declares its own scan roots; this file documents what those roots typically look like.

## Common knowledge-directory patterns

| Pattern | Purpose | Default priority |
|---------|---------|------------------|
| `.memory/` | Ephemeral session state (see the `working` skill) | High — check for stale checkpoints |
| `~/.claude/projects/<project>/memory/` | Native Claude Code auto memory | Medium — graduation candidates only; never delete or modify |
| `docs/` | Persistent project documentation | Medium — check for outdated content |
| `outputs/` (or `staging/`, `out/`) | Generated artifacts awaiting permanent home | High — files needing destination decisions |
| `archive/` (or `.archive/`) | Inactive items | Low — check size growth, sanity |
| `inputs/` (or `inbox/`) | Inbound data awaiting processing | High — unconsumed items signal stalled work |
| `reference/` | External materials (links, downloads, third-party docs) | Low — generally stable |

## Stray detection scope

When scanning for "stray operational knowledge" — methodology / decision / planning / standards / patterns / workflow files **outside** the declared knowledge dirs — the skill should focus on:

- Project root (top-level `.md` files)
- Domain-area subtrees the user designates as in-scope

It should **not** scan:

- `clients/*/projects/`, `customers/*/projects/`, or similar customer-deliverable trees
- `source-data/`, `raw/`, or similar raw-input trees
- `agents/changelogs/`, `agents/validations/`, or similar execution-log trees
- `meeting-notes/`, `correspondence/`, or similar domain-record trees
- `.claude/skills/`, `.claude/rules/` (already structured knowledge)
- `.archive/` (already archived)

If the user's project has different directory names for these patterns, ask before assuming they should be skipped.

## Exclusion list (always skip)

```
.git/
.svn/
.hg/
node_modules/
.venv/
venv/
.claude/                 # configuration, not content
dist/
build/
target/
*.pdf  *.docx  *.xlsx    # binary; skip content analysis
```

`MEMORY.md` inside any auto-memory directory is read-only as far as `consolidate` is concerned: read for context, never modify.
