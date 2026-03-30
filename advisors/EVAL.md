# Evaluating Advisors

Each skill has an `evals/evals.json` following the [agentskills.io evaluation spec](https://agentskills.io/skill-creation/evaluating-skills.md). Three shared test scenarios test each skill at different scales: personal career decision, small business technology adoption, and B2B SaaS strategic pivot.

## Workspace structure

Eval results are ephemeral and gitignored. The workspace extends the agentskills.io single-skill pattern to handle multiple skills and a meta-skill (the panel).

```
advisors-workspace/
└── iteration-N/
    │
    │   # Per-skill runs — one directory per skill, one subdirectory per scenario
    ├── runs/
    │   ├── advisor-visionary/
    │   │   ├── eval-career-decision/
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
    │       └── eval-career-decision/
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

Each eval runs twice — **with the skill** (structured framework) and **without** (baseline) — to measure what the skill adds.

**Individual advisor (with skill):**
```
# Spawn a subagent with the SKILL.md content + test prompt
# Output → advisors-workspace/iteration-N/runs/advisor-{role}/eval-{slug}/with_skill/
```

**Individual advisor (without skill / baseline):**
```
# Spawn a subagent with just: "You are a {role} advisor. Analyze this decision."
# Output → advisors-workspace/iteration-N/runs/advisor-{role}/eval-{slug}/without_skill/
```

**Advisory panel:** Same pattern — with the panel skill vs. a generic "multi-perspective analysis" prompt. Panel runs additionally populate `extracted/` with individual advisor sections parsed from the output.

## Grading

Assertions in each `evals.json` define pass/fail criteria. Grade using LLM-as-judge (provide output + assertions, evaluate each as PASS/FAIL with evidence) or programmatic pattern matching for structural checks.

Per-run results go in `grading.json` alongside each run's output. Cross-cutting analysis goes in the `analysis/` directory.

## Test scenarios

| # | Slug | Scenario | Tests |
|---|------|----------|-------|
| 1 | `eval-career-decision` | Quit job to start AI consulting (personal) | Scale adaptation, ethical tension, operational realities |
| 2 | `eval-content-writers` | Replace content writers with AI (small biz) | Job displacement ethics, quality risks, transition planning |
| 3 | `eval-saas-pivot` | Pivot B2B SaaS to AI-native ($2M ARR) | Full-framework depth, genuine inter-advisor disagreement |
