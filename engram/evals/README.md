# Evaluating engram

Each skill ships an `evals/evals.json` following the [agentskills.io evaluation spec](https://agentskills.io/skill-creation/evaluating-skills.md), extended with **filesystem-state assertions** for skills that produce side effects.

The runner forks the [Advisors plugin evaluation framework](../../advisors/evals/README.md) — same LLM-as-judge methodology, same `claude --bare` clean-room isolation, same git-shorthash iteration provenance. The extension materializes a fixture tree into a tmp workspace before each run, and grading checks both text output and post-run filesystem state.

## Workspace structure

Eval results are ephemeral and gitignored.

```
engram-workspace/
└── iteration-N/
    ├── runs/
    │   ├── consolidate/
    │   │   ├── eval-scan-mixed-tree/
    │   │   │   ├── with_skill/
    │   │   │   │   ├── output.md       # Raw skill output
    │   │   │   │   ├── fs_snapshot.txt # Post-run filesystem state
    │   │   │   │   ├── timing.json     # { tokens, cost, duration_ms }
    │   │   │   │   └── grading.json    # Per-assertion PASS/FAIL with evidence
    │   │   │   └── without_skill/
    │   │   ├── eval-staging-triage/
    │   │   └── eval-respect-auto-memory/
    │   ├── briefing/
    │   └── working/
    │
    ├── fixture-workspaces/             # Materialized fixtures (one per run)
    │   ├── consolidate/
    │   ├── briefing/
    │   └── working/
    │
    └── benchmark.json                  # Top-level aggregate
```

Iterations are keyed by git shorthash. If `engram/` has uncommitted changes, the iteration is suffixed with `-dirty` and a warning is printed.

## Three assertion types

| Type | Evaluated against | Use for |
|------|-------------------|---------|
| `structural` | Output text shape | "Output contains a section titled X", "Output is under 40 lines" |
| `analytical` | Output reasoning quality | "The recommendation engages with the specific constraints", "No fabricated activity" |
| `fs` | Post-run filesystem snapshot | "A plan file exists in the workspace", "The .memory/ directory was not modified" |

Mixed assertions (those that legitimately reference both output and filesystem state) work too — the grading model receives both the model output and the snapshot in the prompt and decides what's relevant.

## Fixtures

Each skill has a `fixture_root` declared in `config.yaml`. Each scenario in `evals.json` references a fixture subdirectory by `fixture` slug. The runner copies the fixture into a fresh tmp workspace before each run, then sets that workspace as the skill's working directory.

Fixtures may ship a `_setup.sh` script. If present, the runner executes it inside the workspace after copying — useful for initializing git repos, backdating mtimes, or other state setup that does not survive a plain copy. The script is deleted from the workspace after running so it does not appear in the filesystem snapshot.

Fixture inventory:

| Skill | Scenario | Fixture | Tests |
|-------|----------|---------|-------|
| `consolidate` | `eval-scan-mixed-tree` | `scan-mixed-tree` | Mixed-age knowledge tree, system artifacts, staleness detection, plan-file generation |
| `consolidate` | `eval-staging-triage` | `staging-triage` | Staging directory with files of varying ages; inline triage report, no plan file |
| `consolidate` | `eval-respect-auto-memory` | `respect-auto-memory` | Auto-memory directory must remain unmodified; only graduation classifications |
| `briefing` | `eval-active-project` | `active-project` | Real git repo with commits, active `.memory/`, stale `outputs/` — full briefing structure |
| `briefing` | `eval-no-tracker-detected` | `no-tracker-detected` | Git repo with no detectable issue tracker — graceful handling, no fabrication |
| `briefing` | `eval-clean-project` | `clean-project` | Trivial repo, nothing in flight — terse output, no Housekeeping section |
| `working` | `eval-checkpoint-fresh` | `checkpoint-fresh` | Empty workspace; checkpoint creates `.memory/` from scratch |
| `working` | `eval-checkpoint-append` | `checkpoint-append` | Pre-populated `.memory/`; new checkpoint appends without overwriting |
| `working` | `eval-promote-plan` | `promote-plan` | Pre-populated `.memory/`; promote produces a plan and waits for approval (no side effects) |

## Running evals

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- `claude` CLI available on `PATH`
- `ANTHROPIC_API_KEY` set in the environment or in `engram/evals/.env`

### Quick start

All commands run from the **repo root** (`backchain-plugins/`):

```bash
# Run all skills, all scenarios, with grading
uv run --project engram/evals python engram/evals/run_evals.py

# Single skill, single scenario
uv run --project engram/evals python engram/evals/run_evals.py --skill consolidate --scenario eval-scan-mixed-tree

# Collect outputs without grading (faster, review manually)
uv run --project engram/evals python engram/evals/run_evals.py --skip-grading

# Grade an existing iteration's outputs
uv run --project engram/evals python engram/evals/run_evals.py --grade-only --iteration abc1234

# Use a different model
uv run --project engram/evals python engram/evals/run_evals.py --model claude-opus-4-7
```

### CLI options

| Option | Description |
|--------|-------------|
| `--skill SKILL` | Filter to skill(s) (repeatable) |
| `--scenario SLUG` | Filter to scenario slug(s) (repeatable) |
| `--iteration HASH` | Iteration ID (default: current git shorthash) |
| `--force` | Overwrite existing iteration directory |
| `--skip-grading` | Collect outputs only, skip grading |
| `--grade-only` | Grade existing iteration without re-running |
| `--model MODEL` | Override the model used for the assessment runs |
| `--grading-model MODEL` | Override the grading model |
| `--parallel N` | Max concurrent runs (default: 4) |
| `--config PATH` | Config file (default: `engram/evals/config.yaml`) |
| `--verbose` | Print claude responses to stderr |

### How it works

Each scenario runs twice — **with the skill** (SKILL.md injected as system prompt) and **without** (baseline prompt from `config.yaml`). Both runs use `claude --bare` for clean-room isolation: no hooks, no plugins, no CLAUDE.md auto-discovery.

Before each run, the fixture is materialized into a fresh per-run workspace. If the fixture ships a `_setup.sh`, it executes inside that workspace. The skill runs with the workspace as its working directory — anything it reads or writes happens there.

After each run, the runner snapshots the workspace's filesystem state (file paths, sizes, and content for small text files) into `fs_snapshot.txt`. The grading model receives both the model output and this snapshot, so `fs`-typed assertions can be evaluated alongside `structural` and `analytical` ones.

Iterations are keyed by git shorthash. Uncommitted changes to `engram/` produce a `-dirty` suffix and a warning.

### Grading

Assertions in each `evals.json` define pass / fail criteria, each tagged with a `type` of `structural`, `analytical`, or `fs`. The runner sends them to the grading model with a JSON schema that enforces `{ passed: bool, evidence: string }` per assertion.

Per-run results land in `grading.json` next to each run. The runner aggregates everything into `benchmark.json` and prints a summary table.

## Interpreting results

The summary table shows per-scenario `passed/total` for both modes plus a delta. The aggregate row gives the mean pass rate across all scenarios.

A meaningful delta on `engram` means the skill improves filesystem-state outcomes that a baseline prompt cannot match — e.g., the with-skill run reliably produces a plan file with all required sections; the without-skill run does not. If the delta is small, that's signal too: the baseline is already strong and the skill mostly codifies discipline rather than capability.
