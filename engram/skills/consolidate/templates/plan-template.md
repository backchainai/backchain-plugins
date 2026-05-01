---
title: Knowledge Audit
prepared_by: consolidate
updated: TIMESTAMP
purpose: Cleanup recommendations for human review and approval
---

# Knowledge Audit — DATE

## Instructions

Review the tables below. Edit the **Action** column to approve, change, or override each recommendation. Then run `/consolidate execute` to apply.

**Action codes:** `DELETE`, `ARCHIVE`, `DOCS`, `MEMORY`, `RULES`, `CLAUDEMD`, `SKILL`, `MOVE`, `KEEP`, `SKIP`

Rows with `KEEP` or `SKIP` are no-ops during execution. `CLAUDEMD` rows will present a diff for explicit approval before any change.

## Filesystem audit

(One section per declared scan root. Empty sections may be omitted or noted as "(empty)".)

### .memory/
| File | Age | Action | Reason |
|------|-----|--------|--------|

### docs/
| File | Age | Action | Reason |
|------|-----|--------|--------|

### outputs/
| File | Age | Status | Action | Suggested destination | Reason |
|------|-----|--------|--------|-----------------------|--------|

### archive/
| File | Age | Action | Reason |
|------|-----|--------|--------|

### Auto memory (~/.claude/projects/.../memory/)
| File | Age | Action | Reason |
|------|-----|--------|--------|

### Stray operational knowledge
| File | Age | Action | Reason |
|------|-----|--------|--------|

## Summary

| Action | Count |
|--------|-------|
| DELETE |  |
| ARCHIVE |  |
| DOCS |  |
| MOVE |  |
| RULES |  |
| CLAUDEMD |  |
| SKILL |  |
| KEEP |  |
| SKIP |  |
| **Total** |  |
