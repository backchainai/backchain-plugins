# Evaluating diogenes

The `audit` skill ships an `evals/evals.json` following the [agentskills.io evaluation spec](https://agentskills.io/skill-creation/evaluating-skills.md), extended with a **verdict label-accuracy** check on top of the report-structure checks.

The runner forks the [engram plugin evaluation framework](../../engram/evals/README.md) — same LLM-as-judge methodology, same `claude --bare` clean-room isolation, same git-shorthash iteration provenance. The audit is read-only (it reads a submission and emits a report, with no filesystem side effects), so the fs-snapshot machinery is dropped. Each scenario materializes a fixture directory containing a `submission.md` into a fresh per-run workspace, then runs the audit with that workspace as its working directory.

## What grading checks

Two concerns, graded together by the judge:

| Concern | How it is checked |
|---------|-------------------|
| **Report structure** | One `structural` assertion per required section: Verdict, Takeaways, Findings table (with the exact columns), Structural observations, Authenticity improvements, Human rewrite, Confidence. The section list is defined in `diogenes/skills/audit/SKILL.md`. |
| **Detection quality** | `analytical` assertions: the findings table quotes the actual tells present (no fabrication, no paraphrase), structural observations reflect real signals, and the report does not escalate to `ai-slop` on clean prose alone. |
| **Label accuracy** | A `label` assertion the runner injects automatically from each scenario's `verdict` field. The judge finds the Verdict section, reads the emitted label, and compares it to the expected label. An adjacent-but-wrong label (for example `ai-assisted-but-natural` where `ai-slop` was expected) is a FAIL. |

## Fixtures

Each scenario references a fixture directory under `diogenes/evals/fixtures/` by `fixture` slug. The directory holds a `submission.md` the audit reads as its input. The scenario `prompt` carries the audience and medium; the scenario `verdict` field carries the expected label.

Fixtures span all three verdict labels the skill emits:

| Scenario | Fixture | Expected verdict | What it is |
|----------|---------|------------------|------------|
| `eval-ai-slop` | `ai-slop` | `ai-slop` | A B2B SaaS landing page dense with `delve`/`leverage`/`unlock`/`tapestry`/`realm`/`seamless`, stacked tricolons, definitional throat-clearing, and vague superlatives. |
| `eval-human-voice` | `human-voice` | `human-voice` | An engineering blog post with specific numbers (430ms → 210ms, $1,400/month), named people, a dated incident, an admitted mistake, and varied sentence length. |
| `eval-ai-assisted-but-natural` | `ai-assisted-but-natural` | `ai-assisted-but-natural` | A clean engineering post that may have had LLM help but carries real specifics (2M tasks/day, SQS, `procrastinate`, a refunded idempotency bug) and a lived-experience arc. |

## Workspace structure

Eval results are ephemeral and gitignored.

```
diogenes-workspace/
└── iteration-N/
    ├── runs/
    │   └── audit/
    │       ├── eval-ai-slop/
    │       │   ├── with_skill/
    │       │   │   ├── output.md     # Raw audit report
    │       │   │   ├── timing.json   # { tokens, cost, duration_ms }
    │       │   │   └── grading.json  # Per-assertion PASS/FAIL with evidence
    │       │   └── without_skill/
    │       ├── eval-human-voice/
    │       └── eval-ai-assisted-but-natural/
    │
    ├── fixture-workspaces/           # Materialized fixtures (one per run)
    │   └── audit/
    │
    └── benchmark.json                # Top-level aggregate
```

Iterations are keyed by git shorthash. If `diogenes/` has uncommitted changes, the iteration is suffixed with `-dirty` and a warning is printed.

## Running evals

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- `claude` CLI available on `PATH`
- `ANTHROPIC_API_KEY` set in the environment or in `diogenes/evals/.env`

### Quick start

All commands run from the **repo root** (`backchain-plugins/`):

```bash
# Run the audit skill across all three fixtures, with grading
uv run --project diogenes/evals python diogenes/evals/run_evals.py

# Single scenario
uv run --project diogenes/evals python diogenes/evals/run_evals.py --scenario eval-ai-slop

# Collect outputs without grading (faster, review manually)
uv run --project diogenes/evals python diogenes/evals/run_evals.py --skip-grading

# Grade an existing iteration's outputs
uv run --project diogenes/evals python diogenes/evals/run_evals.py --grade-only --iteration abc1234

# Use a different model
uv run --project diogenes/evals python diogenes/evals/run_evals.py --model claude-opus-4-7
```

### CLI options

| Option | Description |
|--------|-------------|
| `--skill SKILL` | Filter to skill(s) (repeatable; only `audit` exists today) |
| `--scenario SLUG` | Filter to scenario slug(s) (repeatable) |
| `--iteration HASH` | Iteration ID (default: current git shorthash) |
| `--force` | Overwrite existing iteration directory |
| `--skip-grading` | Collect outputs only, skip grading |
| `--grade-only` | Grade existing iteration without re-running |
| `--model MODEL` | Override the model used for the assessment runs |
| `--grading-model MODEL` | Override the grading model |
| `--parallel N` | Max concurrent runs (default: 4) |
| `--config PATH` | Config file (default: `diogenes/evals/config.yaml`) |
| `--verbose` | Print claude responses to stderr |

### How it works

Each scenario runs twice — **with the skill** (SKILL.md injected as system prompt) and **without** (baseline prompt from `config.yaml`). Both runs use `claude --bare` for clean-room isolation: no hooks, no plugins, no CLAUDE.md auto-discovery.

Before each run, the fixture is materialized into a fresh per-run workspace and the audit runs with that workspace as its working directory, so it reads `submission.md` from there. After each run the report text is saved to `output.md`. The grading model receives that report plus the scenario's assertions (the structural and analytical ones from `evals.json`, plus the injected `label` assertion) and returns a per-assertion PASS/FAIL with evidence under a JSON schema.

Iterations are keyed by git shorthash. Uncommitted changes to `diogenes/` produce a `-dirty` suffix and a warning.

## Interpreting results

The summary table shows per-scenario `passed/total` for both modes plus a delta. The aggregate row gives the mean pass rate across all scenarios.

A meaningful delta on `audit` means the skill produces the full seven-section report with accurate verdict labels where a baseline prompt cannot — the with-skill run reliably emits the Findings table with the exact columns, the structural metrics, and the correct verdict; the without-skill run drifts on structure or mislabels. If the delta is small, the baseline is already strong and the skill mostly codifies the report contract and the detection framework.
