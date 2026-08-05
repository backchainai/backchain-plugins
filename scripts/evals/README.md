# Trigger evals

`scripts/evals/run_trigger_evals.py` measures whether a skill's frontmatter
`description` makes the model reach for the `Skill` tool on its own,
unprompted, across a labeled set of positive and negative queries. It is
repo-level tooling, not scoped to one plugin, because it takes
`--skill-path`, `--eval-set`, and `--workspace` as arguments rather than
assuming a fixed layout. See `docs/decisions/trigger-eval-isolation.md` for
the root-cause writeup this design responds to.

## Trigger evals versus behavioral evals

A trigger eval and a behavioral eval (`<plugin>/evals/run_evals.py`, where
it exists) measure different things. A trigger eval asks whether the model
picks up the skill unprompted, given only a query and a set of tools; the
`Skill` call itself, not what happens after it, is the measurement. A
behavioral eval invokes the skill directly and grades the quality of its
output against assertions in `evals/evals.json`. A description change needs
a trigger-eval delta; a skill-body change needs a behavioral-eval delta.
They are not substitutes for each other.

## Why `--bare` is absent

The three existing behavioral runners (`advisors`, `engram`, `diogenes`) run
under `claude --bare` for clean-room isolation. The trigger harness does
not. `--bare` registers a skill (it still resolves via `/skill-name`) but
does not make it autonomously invocable, so a run under `--bare` never
exercises the thing being measured. Isolation instead comes from a
throwaway `--plugin-dir` per run plus a disposable copy of the grounding
workspace, each run getting its own parent temp directory with no siblings.

## The workspace-grounding rule

Every query in a trigger-eval set implicitly assumes a working directory
with something real for the model to act on. An empty workspace makes every
positive miss for the wrong reason (nothing to find) and every negative
pass for the wrong reason (nothing to do), which is silent and looks like a
working, low-scoring harness rather than a broken one. `run_trigger_evals.py`
refuses to start against a missing or empty `--workspace`, but it cannot
detect a workspace that is merely missing the one file a specific query
needs. Adding a query to `trigger-evals.json` without adding its seed file
to the workspace reintroduces that failure mode for that query alone.

### Per-query grounding checklist (`scriptorium/skills/docs`)

Sixteen of the twenty queries in `scriptorium/skills/docs/evals/
trigger-evals.json` name an artifact the model is expected to find in
`scriptorium/evals/fixtures/trigger-workspace/`. The other four (queries 5,
7, 9, and 15) ask for something to be written or answered and need no seed
file.

| Query | Fixture file |
|---|---|
| 1 | `install-postgres.md` |
| 2 | `docs/restart-stalled-pod.md` |
| 3 | `docs/understanding-our-event-bus.md` |
| 4 | `docs/local-environment-setup.md` |
| 6 | `docs/why-event-sourcing.md` |
| 8 | `docs/api-reference.md` |
| 10 | `docs/advanced-usage.md` |
| 11 | `docs/decisions/0004-rest-to-grpc.md` |
| 12 | `CHANGELOG.md` |
| 13 | `src/auth_middleware.py`, `src/session_store.py` |
| 14 | `README.md` |
| 16 | `src/payments.py` |
| 17 | `CLAUDE.md` |
| 18 | `docs/cli-reference.md` |
| 19 | `runbooks/*.md` |
| 20 | `docs/troubleshooting-faq.md` |

Verify this table by reading, not mechanically: no automated check maps a
query's prose to the file it depends on.

## Exact-match detection

`detect_trigger` scans every `tool_use` block in the model's turn for
`name == "Skill"` with `input.skill` exactly equal to the full
`<plugin>:<skill>` id. A substring match is wrong: it would let
`trigeval-x:docs` match `trigeval-x:docsprobe`. Each run's throwaway plugin
is named `trigeval-<uuid>`, so the id is unique to that run. The subprocess
is killed the instant a match is detected; every further turn only spends
money without changing the measurement.

## Running a trigger eval

```
python3 scripts/evals/run_trigger_evals.py \
  --skill-path scriptorium/skills/docs \
  --eval-set scriptorium/skills/docs/evals/trigger-evals.json \
  --workspace scriptorium/evals/fixtures/trigger-workspace \
  --candidates scriptorium/evals/candidates/docs-2026-08.json \
  --model claude-sonnet-5 --runs-per-query 1 --holdout 0.4 \
  --results-dir trigger-evals-workspace/docs
```

`--candidates` is a JSON array of `{"name": ..., "description": ...}`
objects; candidate descriptions are supplied, not generated in-loop.
`--max-cost` requires `ANTHROPIC_API_KEY` auth, since `total_cost_usd` may
not track real spend under subscription OAuth.

## Cost

Kill-on-detection and `--tools "Read,Grep,Glob,Bash,Skill"` (no Write or
Edit) bound the cost of a run: the first stops the moment the answer is
known, the second stops any run from completing the expensive write half of
a task. Measured probe cost for one query was $0.249 for a run that
declined early and $0.486 for one that triggered and ran to completion; an
unmodified harness would run near $0.35 per query blended. These are
projections from two probes, not a guarantee, so run a smoke check (one
known positive, one known negative) before a full sweep and read its actual
per-query cost before committing to `--max-cost` for the rest of the run.
