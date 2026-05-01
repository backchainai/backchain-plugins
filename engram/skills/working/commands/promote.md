<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Command: promote

Move `.memory/` artifacts to permanent knowledge locations.

## Trigger

`/working promote` or natural language: "promote working memory", "move memory to permanent".

## Behavior

1. Verify `.memory/` exists in the current directory.
2. Read all `.memory/` files (`todos.md`, `decisions.md`, `questions.md`).
3. Analyze each artifact and **prompt the user** to confirm the promotion target. Do not assume a specific tool.
4. Present the full plan for review.
5. Execute approved promotions.
6. Report results.

## Promotion analysis

### Decisions → ADRs or auto memory

For each decision in `decisions.md`, classify by significance:

**ADR-worthy** (significant architectural / design choice):
1. Detect a likely ADR location (`docs/adr/` if present). Otherwise ask the user where ADRs live in this project.
2. Determine the next ADR number by scanning existing ADRs.
3. Format using the project's ADR template if one exists, otherwise a standard one (context, decision, rationale, consequences).

**Auto-memory-worthy** (project context worth remembering, but too small for an ADR):
1. Write to a new file in the auto-memory directory (`~/.claude/projects/<project>/memory/`).
2. Use the auto-memory frontmatter format (`name`, `description`, `type: project`).
3. Add a one-line pointer in `MEMORY.md` if the user has set up an index — confirm with the user before modifying it.

**Skip** trivial decisions (tool version choices, formatting preferences). Auto memory captures these organically; promoting them is noise.

### Todos → issues

For each incomplete todo in `todos.md`:
1. Detect the user's issue tracker from project signals. If undetected or ambiguous, **ask once** for the session: "Which issue tracker should I use? (Beads, Linear, GitHub Issues, other)"
2. Suggest issue type, priority, and labels based on the todo content. Confirm before creating.
3. Create the issue using the tool's standard CLI or API.

Skip:
- Completed todos (already done).
- Trivial items (handle inline).

### Questions → documentation or issues

**Resolved questions:** append the Q&A to a relevant context document. Ask the user where if not obvious.

**Unresolved questions:**
- If blocking work: create an issue.
- If informational: append to a context document.
- If unsure: ask the user.

## User interaction

Present the full promotion plan before executing:

```
Promotion plan for .memory/:

## Decisions (3 items)
1. "Use JWT with refresh tokens" -> new ADR (where do ADRs live? defaulting to docs/adr/042-...)
2. "PostgreSQL over MongoDB" -> new ADR (next: 043)
3. "Async standups preferred" -> auto memory (project type)

## Todos (3 items)
1. "Implement token validation" -> [tracker] task (P2)
2. "Write integration tests" -> [tracker] task (P2)
3. "Update API docs" -> [tracker] task (P3)

## Questions (1 item)
1. "Multi-issuer support?" (unresolved) -> [tracker] issue (P3)

Confirm each, all, or skip individual items?
```

Allow the user to:
- Approve all.
- Skip specific items.
- Modify targets before execution.

## Output format

```
Promoted from .memory/:
- 2 decisions -> ADRs (042, 043)
- 3 todos -> tracker issues (IDs as returned by the tracker)
- 1 question -> tracker issue

Ready for cleanup: /working cleanup
```

## Constraints

- Always require user approval before creating files or issues.
- Never assume a specific tracker or ADR location — detect or ask.
- Preserve the original wording from `.memory/` in promoted artifacts.
- Add a provenance note in promoted artifacts: "Promoted from working memory on {date}".
- If `.memory/` is empty or missing, suggest running `checkpoint` first.
