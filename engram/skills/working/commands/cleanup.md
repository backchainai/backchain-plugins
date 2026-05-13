<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Command: cleanup

Delete promoted content from the `.memory/` directory.

## Trigger

`/engram:working cleanup` or natural language: "clean up working memory", "clear memory".

## Behavior

1. Verify `.memory/` exists in the current directory.
2. Read and display current contents (item counts per file).
3. Check whether promotion has happened (warn if not).
4. Request explicit user confirmation.
5. Delete file contents (keep the directory and the file headers).
6. Confirm.

## Pre-cleanup check

Before deleting, show what will be removed:

```
Current .memory/ contents:
- todos.md: 5 items (2 in-progress, 1 blocked, 2 completed)
- decisions.md: 3 decisions
- questions.md: 2 questions (1 resolved, 1 unresolved)

This action cannot be undone. Delete all contents?
```

## Promotion warning

If unpromoted items exist:

```
Warning: .memory/ contains items that have not been promoted:
- 2 decisions (no corresponding ADRs)
- 1 unresolved question (no issue created)

Run /engram:working promote first, or confirm deletion to proceed.
```

Require explicit confirmation to delete unpromoted content.

## Cleanup actions

For each file, delete contents but preserve a single header line:
- `todos.md` → keep `# Action Items`
- `decisions.md` → keep `# Decisions`
- `questions.md` → keep `# Open Questions`

Keep the `.memory/` directory itself. Its presence signals that this project uses working memory; only the contents get cleared.

## Output format

```
Working memory cleaned up:
- Deleted 5 todos, 3 decisions, 2 questions
- Directory .memory/ preserved for future use
```

## Constraints

- Always require explicit user confirmation.
- Warn about unpromoted content.
- Never delete the `.memory/` directory itself.
- Keep file headers intact (ready for the next checkpoint).
- Action is irreversible (no archive mode in v1).
