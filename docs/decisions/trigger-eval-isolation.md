---
title: Trigger Eval Isolation
prepared_by: Claude (Sonnet 5)
updated: 2026-08-05T08:17:10-04:00
purpose: Record the three compounding defects that held the skill-creator trigger harness at a 0% floor and the isolation design the replacement harness uses instead.
tags: []
aliases: []
---

# Trigger Eval Isolation

## Decision

`scripts/evals/run_trigger_evals.py` replaces the third-party skill-creator
harness (`skill-creator/scripts/run_loop.py`) for measuring whether a
candidate `description` makes the model reach for a skill on its own. It
installs the skill through a throwaway `--plugin-dir`, runs against a
disposable copy of a grounding workspace with no `--bare`, and detects a
trigger by an exact `<plugin>:<skill>` match rather than a substring match.
This record is repo-level because the harness is repo-level tooling, not a
scriptorium artifact.

## Context

Issue #35 found the skill-creator harness scoring five different candidate
descriptions identically at train 6/12 and held-out test 4/8: the floor,
every positive missed and every negative passed by never firing. The harness
is third-party, lives outside this repository at
`~/.claude/plugins/cache/claude-plugins-official/skill-creator/`, and a
one-off patch there is replaced on the next plugin update. Replacement was
the only durable option.

## Three compounding root causes

1. **Slash-command installation.** `run_single_query` wrote
   `<project_root>/.claude/commands/<name>.md`. A project slash command is
   not surfaced to the model as an invocable skill, so the Skill tool never
   fired regardless of description.
2. **Detection aborted on the first non-Skill tool call.** The stream
   handler read `if tool_name in ("Skill", "Read") ... else: return False`,
   so any third tool call (a `Bash` lookup, for instance) ended detection
   before the model reached the skill.
3. **The eval workspace held no document.** Every positive query in
   `trigger-evals.json` refers to a document that already exists. Run in an
   empty scratch directory, the model searched for the file, failed to find
   it, and asked the user to point at it. It never reached the Skill call.
   This cause was silent: nothing failed loudly, the score just read zero.

## Probe evidence

Three runs, same query (`trigger-evals.json` query 2, a positive), same
skill body, same model (`claude-sonnet-5`), differing only in environment.
The skill was loaded with `--plugin-dir` pointing at a throwaway plugin
directory carrying a copy of `scriptorium/skills/docs`.

| Probe | Environment | Tool sequence | Skill fired |
|---|---|---|---|
| A | `--plugin-dir`, empty workspace | `Bash`, `Bash` | no |
| B | `--plugin-dir`, document present | `Bash`, `Read`, `Skill`, `Read`x3, `Bash`x2, `Write`x2 | yes |
| C | `--bare --plugin-dir`, document present | `Bash`, `Read`, `Bash`x3, `Read`x2, `Bash` | no |

Probe A's closing text named the mechanism directly: the model wanted the
skill and had nowhere to apply it, and asked the user to point at a file
before it would use "the docs-triage skill." Probe A also disproved a
registration failure: `docsprobe-plugin:docsprobe` appeared in the
session-init event in all three probes, so `--plugin-dir` registers the
skill correctly on its own; the missing grounding document is what stopped
the model from reaching it. Probe B settled cause 2 quantitatively: `Skill`
was tool call three, behind `Bash` and `Read`, past the point where the old
harness's `else: return False` branch had already returned.

## `--plugin-dir` registration and the `--bare` divergence

`--plugin-dir` points the CLI at a directory shaped like a plugin
(`.claude-plugin/plugin.json` plus a `skills/<name>/SKILL.md` tree) and
registers every skill inside it for the session, the same mechanism the
three existing behavioral runners (`advisors`, `engram`, `diogenes`) use for
`--bare` isolation.

Probe C shows `--bare` must not be added on top of it for a trigger eval.
`claude --bare`'s help text says skills "still resolve via `/skill-name`",
and probe C confirms what that means in practice: the skill is registered
but never autonomously invoked, and the model performed the entire task by
hand instead of reaching for the Skill tool. A behavioral runner invokes the
skill explicitly and wants the clean room `--bare` gives it; a trigger eval
measures whether the model reaches for the skill on its own, which is
exactly the behavior `--bare` suppresses. This is the one place the trigger
harness diverges from the three behavioral runners' isolation pattern.
Isolation for a trigger eval comes from `--plugin-dir` plus a disposable
workspace copy instead, one parent temp directory per run with no siblings:
probe C also wandered into probe B's sibling directory and read its output,
which is why no two runs may share a parent.

## Exact-match detection

`detect_trigger` requires `name == "Skill"` and `input.skill` exactly equal
to the full `<plugin>:<skill>` id, never a substring match. Probe B returned
`"skill": "docsprobe-plugin:docsprobe"`; a substring test for `docs` would
also match `docsprobe`, `docs-writer`, and `mydocs`. The harness names each
throwaway plugin `trigeval-<uuid>`, so the id is unique per run, which
restores the disambiguation the old harness got from UUID skill names and
keeps the measurement correct if a second real `docs` skill is ever present
in the session.

## Consequences

- The trigger harness never passes `--bare`; a future contributor adding it
  "for consistency" with the behavioral runners should be routed to this
  record first.
- The grounding workspace is a required, non-empty `--workspace` argument,
  checked before the first model call; a missing or empty workspace fails
  the run loudly rather than producing a silent zero.
- `scripts/evals/README.md` carries the per-query checklist mapping each
  artifact-naming query to its fixture file, so a future query addition
  cannot reintroduce cause 3 for that one query.

## Revisit conditions

- The `claude` CLI's `--bare` or `--plugin-dir` behavior changes in a way
  that alters registration or invocability.
- The upstream skill-creator harness is patched and this repository chooses
  to track it again instead of the repo-level replacement.
