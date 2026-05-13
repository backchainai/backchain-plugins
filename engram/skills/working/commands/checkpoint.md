<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Command: checkpoint

Create or update `.memory/` with current conversation state.

## Trigger

`/engram:working checkpoint` or natural language: "checkpoint our progress", "save working memory".

## Behavior

1. Determine the current working directory.
2. Check whether `.memory/` exists; create it if not.
3. For each template file (`todos.md`, `decisions.md`, `questions.md`):
   - If the file exists: read current contents, append new items, update the timestamp.
   - If it does not exist: create from the template in `${CLAUDE_SKILL_DIR}/templates/`.
4. Analyze the current conversation to extract:
   - **Todos:** action items, next steps, agreed-upon tasks.
   - **Decisions:** explicit choices with rationale, trade-off resolutions.
   - **Questions:** open issues, deferred decisions, knowledge gaps.
5. Update each file's `Last Updated` timestamp using `date -Iseconds`.
6. Confirm with a summary.

## Extraction guidelines

### Todos

Look for:
- Explicit action items ("we need to…", "next step is…").
- Agreed-upon tasks ("let's do X").
- Follow-up items ("we should also…").

Categorize as: In Progress, Blocked, Completed, Backlog.

### Decisions

Look for:
- Explicit choices ("we decided to use X").
- Trade-off resolutions ("X over Y because…").
- Architecture / design selections.
- Tool / library selections.

Capture: context, decision, rationale, alternatives considered.

### Questions

Look for:
- Unresolved discussions ("we still need to figure out…").
- Deferred decisions ("let's decide later…").
- Knowledge gaps ("I'm not sure about…").
- External dependencies ("we need to ask…").

Capture: question, context, what it blocks, candidate answers.

## Output format

```
Checkpointed working memory (.memory/):
- {N} todos ({new} new, {existing} existing)
- {N} decisions ({new} new, {existing} existing)
- {N} questions ({new} new, {existing} existing)
```

## Constraints

- Append; never overwrite. Preserving prior session context is the whole point.
- Preserve template structure (headings, formatting).
- Use RFC 3339 timestamps from `date -Iseconds`.
- Keep items concise but include enough context to resume cold.
- If no new items in a category, skip its file (do not create empty entries).
