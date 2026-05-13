# engram

> Filesystem-backed agent memory for Claude Code: explicit consolidation, session briefing, and ephemeral working state — complementary to native auto memory and `/recap`.

`engram` is a [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin authored to the [agentskills.io specification](https://agentskills.io/specification). It packages three skills that operate at boundaries native auto memory does not address.

## What this is

Three skills, one plugin:

- **`consolidate`** — Audit knowledge directories and Claude Code auto memory for stale, misplaced, or duplicated content. Generates an editable plan file the user reviews; executes only approved actions. Treats native `MEMORY.md` as read-only and focuses on *graduation* (promoting stable feedback memories to `.claude/rules/` or `CLAUDE.md`) and on knowledge directories outside auto memory's scope (`docs/`, staging, archive).
- **`briefing`** — Produce a concise session-start orientation from issue tracker, git history, working memory, and staleness signals. Read-only. Complements native `/recap` (which auto-triggers after extended idle) by aggregating cross-tool signals on demand.
- **`working`** — Manage an explicit `.memory/` directory for structured in-flight work — todos, decisions, questions. Three-command lifecycle: checkpoint (capture), promote (move to permanent locations such as ADRs or issue-tracker entries), cleanup (clear after promotion).

## Division of labor vs Claude Code native

As of [Claude Code 2.1.108+](https://code.claude.com/docs/en/changelog), native memory ships:

- **Auto memory** (v2.1.59+, [docs](https://code.claude.com/docs/en/memory)) — implicit learnings written to `~/.claude/projects/<project>/memory/MEMORY.md` plus topic files. First 200 lines / 25KB of `MEMORY.md` load each session.
- **`/recap`** (v2.1.108+) — auto-triggered session summary after 75+ minutes of idle, manually invocable.

`engram` adds three things native does not provide:

| Concern | Native | engram |
|---------|--------|--------|
| Implicit learning capture | Auto memory | (defer to native) |
| Session-start narrative recap | `/recap` | (defer to native) |
| Knowledge-directory audit (project `docs/`, staging, archive) | — | `consolidate` |
| Graduate stable auto-memory entries to permanent rules | — | `consolidate` |
| Cross-tool session briefing (issue tracker + git + staleness) | — | `briefing` |
| Structured working state with explicit promotion lifecycle | — | `working` |

Full design rationale, native feature surface, and configuration interactions: [`docs/division-of-labor.md`](./docs/division-of-labor.md).

## Skills

### consolidate

Triggers on phrases like *"consolidate knowledge,"* *"audit knowledge directories,"* *"clean up outputs,"* *"triage staging."*

```
> consolidate knowledge
[reads declared scan roots; generates outputs/consolidate-plan-2026-04-26.md]
[user reviews and edits the Action column]
> consolidate execute
[applies approved moves, then deletes; reports counts]
```

Action codes: `DELETE`, `ARCHIVE`, `DOCS`, `MEMORY`, `RULES`, `CLAUDEMD`, `SKILL`, `MOVE`, `KEEP`, `SKIP`. The `CLAUDEMD` action presents a diff and requires explicit approval.

See [`skills/consolidate/SKILL.md`](./skills/consolidate/SKILL.md) for the scan algorithm, classification rules, and execution-safety guarantees.

### briefing

Triggers on phrases like *"catch me up,"* *"what was I working on,"* *"where did I leave off,"* *"session briefing,"* *"context recovery."*

```
> what was I working on
# Session Briefing

## Active Work
- prof-9q3.3: Publish unified memory plugin (in progress)

## Ready to Start
- prof-9q3.4: Publish worktree-merge as standalone repo (P2)

## Recent Activity
- e37af95 Merge pull request #4 from backchainai/worktree-subagent-contexts
- 13d0730 task: add decision record for skills vs agents orchestration
...
## Housekeeping
- 3 files older than 7 days in outputs/ — consider running `consolidate staging`
```

Read-only. Detects the user's issue tracker from project signals (Beads, Linear, GitHub Issues, or asks once if ambiguous).

See [`skills/briefing/SKILL.md`](./skills/briefing/SKILL.md).

### working

Triggers on phrases like *"checkpoint,"* *"save working memory,"* *"promote working memory,"* *"clean up memory."*

```
> /engram:working checkpoint
Checkpointed working memory (.memory/):
- 2 todos added (1 new, 1 existing)
- 1 decision documented
- 1 question captured

[3 days later]
> /engram:working promote
Promotion plan for .memory/:
## Decisions (1 item)
1. "Use JWT with refresh tokens" -> new ADR (where do ADRs live? defaulting to docs/adr/042-...)
## Todos (2 items)
1. "Implement token validation" -> [tracker] task
[user confirms]
Promoted. Ready for cleanup: /engram:working cleanup
```

The skill prompts the user for promotion targets — it does not assume a specific issue tracker, ADR location, or documentation system.

See [`skills/working/SKILL.md`](./skills/working/SKILL.md), [`skills/working/reference.md`](./skills/working/reference.md), and the per-command files in [`skills/working/commands/`](./skills/working/commands/).

## Installation

### From GitHub (recommended)

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install engram@backchain-plugins
```

### Local development

```bash
git clone https://github.com/backchainai/backchain-plugins.git
/plugin marketplace add ./backchain-plugins
/plugin install engram@backchain-plugins
```

## Evaluation

Each skill ships an `evals/evals.json` following the [agentskills.io evaluation specification](https://agentskills.io/skill-creation/evaluating-skills.md), extended with **filesystem-state assertions** for skills that produce side effects.

The runner forks the [Advisors plugin evaluation framework](../advisors/evals/README.md) — same LLM-as-judge methodology, same `claude --bare` clean-room isolation, same git-shorthash iteration provenance. The extension materializes a fixture tree into a tmp workspace before each run, and grading checks both text output and filesystem state after the run.

### First-iteration results

9 scenarios × with-skill / without-skill, graded by `claude-haiku-4-5` against assertions in each scenario's `evals.json`:

| Skill | Scenario | With | Without | Delta |
|-------|----------|-----:|--------:|------:|
| briefing | eval-active-project | 5/6 | 2/6 | **+50%** |
| briefing | eval-clean-project | 4/4 | 4/4 | +0% |
| briefing | eval-no-tracker-detected | 4/4 | 4/4 | +0% |
| consolidate | eval-respect-auto-memory | 5/5 | 5/5 | +0% |
| consolidate | eval-scan-mixed-tree | 5/6 | 4/6 | **+17%** |
| consolidate | eval-staging-triage | 4/5 | 4/5 | +0% |
| working | eval-checkpoint-append | 6/6 | 6/6 | +0% |
| working | eval-checkpoint-fresh | 4/6 | 2/6 | **+33%** |
| working | eval-promote-plan | 6/6 | 6/6 | +0% |
| **Aggregate** | mean pass rate | **90%** | 77% | **+13%** |

Run model: `claude-sonnet-4-6`. Total cost across all 18 runs + 18 grading calls: $1.07. Wall clock: ~5 minutes at `--parallel 4`.

The +0% scenarios document where the baseline already produces good output without the skill. The +17% to +50% scenarios are where the structure the skill adds — explicit checkpoint format, division-of-labor with auto memory, staleness signals integrated into the briefing — produces measurably better filesystem-state outcomes than a baseline prompt alone.

See [`evals/README.md`](./evals/README.md) for the runner, fixtures, and how to interpret the with-skill / without-skill delta.

```bash
# From the repo root
uv run --project engram/evals python engram/evals/run_evals.py
```

## License and contributing

`engram` ships under [AGPL-3.0-only](../LICENSE) with a Backchain commercial-license reservation, the same posture as the rest of this repository. See the [repository root README](../README.md#license) for the rationale and the commercial-license contact path. External contributions follow the repository [CONTRIBUTING.md](../CONTRIBUTING.md).

`engram` runs as agent-skill files (system-prompt injection, not statically linked code). The AGPL's "Corresponding Source" requirement reaches the plugin and its modifications, not arbitrary platform code that uses the plugin at runtime.

## Credits

Built by [Backchain](https://backchain.ai). Conforms to the [agentskills.io specification](https://agentskills.io/specification). Evaluation framework borrowed from the sibling [Advisors plugin](../advisors/).
