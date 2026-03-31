# Evaluating Advisors

Each skill has an `evals/evals.json` following the [agentskills.io evaluation spec](https://agentskills.io/skill-creation/evaluating-skills.md). Three shared test scenarios test each skill at different scales: personal career decision, small business technology adoption, and B2B SaaS strategic pivot.

## Workspace structure

The workspace extends the agentskills.io single-skill eval pattern to handle multiple embedded skills and an orchestrator skill (advisory-panel). Eval results are ephemeral and gitignored. 

```
advisors-workspace/
└── iteration-N/
    │
    │   # Per-skill runs — one directory per skill, one subdirectory per scenario
    ├── runs/
    │   ├── advisor-visionary/
    │   │   ├── eval-boat-rental/
    │   │   │   ├── with_skill/
    │   │   │   │   ├── output.md          # Raw advisor output
    │   │   │   │   ├── timing.json        # { total_tokens, duration_ms }
    │   │   │   │   └── grading.json       # Per-assertion PASS/FAIL with evidence
    │   │   │   └── without_skill/
    │   │   │       ├── output.md
    │   │   │       ├── timing.json
    │   │   │       └── grading.json
    │   │   ├── eval-content-writers/
    │   │   └── eval-saas-pivot/
    │   ├── advisor-skeptic/
    │   ├── advisor-operator/
    │   ├── advisor-ethicist/
    │   │
    │   │   # Panel runs include extracted advisor sections for cross-comparison
    │   └── advisory-panel/
    │       └── eval-boat-rental/
    │           ├── with_skill/
    │           │   ├── output.md          # Full panel output (all 4 advisors + synthesis)
    │           │   ├── extracted/         # Advisor sections parsed from panel output
    │           │   │   ├── visionary.md
    │           │   │   ├── skeptic.md
    │           │   │   ├── operator.md
    │           │   │   └── ethicist.md
    │           │   ├── timing.json
    │           │   └── grading.json
    │           └── without_skill/
    │               ├── output.md          # Generic "multi-perspective analysis" baseline
    │               ├── timing.json
    │               └── grading.json
    │
    │   # Cross-cutting analysis — the multi-skill layer the spec doesn't cover
    ├── analysis/
    │   ├── skill-benchmarks.json          # Per-skill with/without pass rate deltas
    │   ├── perspective-diversity.json     # Same scenario × 4 advisors: are they distinct?
    │   └── panel-coherence.json           # Panel-embedded vs standalone advisor quality
    │
    ├── benchmark.json                     # Top-level aggregate across all skills
    └── feedback.json                      # Human review notes per eval
```

### Three levels of analysis

The agentskills.io spec covers single-skill evaluation. The advisors plugin needs three levels:

**Level 1 — Per-skill.** Standard with/without comparison per advisor. *"Does the structured framework improve output over a generic prompt?"* Results in `analysis/skill-benchmarks.json`.

**Level 2 — Cross-skill diversity.** Same scenario across all 4 advisors. *"Do the advisors produce genuinely different perspectives, or converge on the same take?"* This is the core Team of Rivals value proposition. Results in `analysis/perspective-diversity.json`.

**Level 3 — Panel integration.** The panel embeds 4 advisor analyses + synthesis. Extracted sections (split on `## {Role} Advisor Analysis` headers) are compared against standalone runs. *"Does orchestration degrade individual advisor quality? Does the synthesis add genuine value?"* Results in `analysis/panel-coherence.json`.

The `runs/` vs `analysis/` split keeps raw outputs (per-run, mechanical) separate from derived insights (cross-cutting, interpretive).

## Running evals

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- `ANTHROPIC_API_KEY` set in environment or in `advisors/evals/.env`

### Quick start

All commands run from the **repo root** (`backchain-plugins/`):

```bash
# Run all skills, all scenarios, with grading
uv run --project advisors/evals run_evals.py

# Single skill, single scenario
uv run --project advisors/evals run_evals.py --skill advisor-visionary --scenario eval-boat-rental

# Collect outputs without grading (faster, review manually)
uv run --project advisors/evals run_evals.py --skip-grading

# Grade an existing iteration's outputs
uv run --project advisors/evals run_evals.py --grade-only --iteration abc1234

# Use a different model
uv run --project advisors/evals run_evals.py --model claude-opus-4-6
```

Or from `advisors/evals/` directly:

```bash
uv run run_evals.py --skill advisor-visionary --scenario eval-boat-rental
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
| `--model MODEL` | Override model for assessment runs |
| `--grading-model MODEL` | Override model for grading |
| `--config PATH` | Config file (default: `advisors/evals/config.yaml`) |
| `--verbose` | Print claude responses to stderr |

### How it works

Each eval runs twice per scenario — **with the skill** (SKILL.md injected as system prompt) and **without** (baseline prompt from config.yaml). Both use `claude --bare` for clean-room isolation: no hooks, no plugins, no CLAUDE.md auto-discovery.

Iterations are keyed by git shorthash. If skill files have uncommitted changes, the iteration is suffixed with `-dirty` and a warning is printed.

### Grading

Assertions in each skill's `evals/evals.json` define pass/fail criteria. The runner grades each output using `claude --bare` with `--json-schema` to enforce structured results: per-assertion PASS/FAIL with evidence.

Per-run results go in `grading.json` alongside each run's output. The runner aggregates all results into `benchmark.json` and prints a summary table.

## Test scenarios

| # | Slug | Scenario | Tests |
|---|------|----------|-------|
| 1 | `eval-boat-rental` | Start boat rental business on popular lake ($50K, no experience) | Seasonal business dynamics, safety/environmental ethics, platform vs asset play |
| 2 | `eval-content-writers` | Replace content writers with AI (small biz) | Job displacement ethics, quality risks, transition planning |
| 3 | `eval-saas-pivot` | Pivot B2B SaaS to AI-native ($2M ARR) | Full-framework depth, genuine inter-advisor disagreement |
