---
name: advisory-panel
description: Use when you need comprehensive, multi-perspective analysis of a decision or idea — a full Team of Rivals assessment. Runs all four advisors independently (visionary, skeptic, operator, ethicist), then synthesizes their insights into a unified recommendation with areas of agreement, disagreement, and a risk-adjusted verdict.
disable-model-invocation: true
argument-hint: <idea or decision to analyze>
allowed-tools: Agent Read
metadata:
  author: Backchain
  version: 2.0.0
---

# Advisory Panel: Comprehensive Decision Analysis

You will analyze the following concept through four independent advisory perspectives using subagents for true isolation, then synthesize their insights into a unified recommendation.

## Input

**Decision/Idea to Analyze:** $ARGUMENTS

## Workflow

### Phase 1: Read Advisor Skills

Read all four advisor SKILL.md files to get their complete frameworks:

1. `advisors/skills/advisor-visionary/SKILL.md`
2. `advisors/skills/advisor-skeptic/SKILL.md`
3. `advisors/skills/advisor-operator/SKILL.md`
4. `advisors/skills/advisor-ethicist/SKILL.md`

### Phase 2: Run Four Independent Advisor Analyses

Launch all four advisors as **parallel subagents in a single message**. Each advisor receives:
- The decision/idea to analyze (the full input above)
- The complete SKILL.md content for that advisor's framework
- Instructions to produce their structured output (200-400 words, all Output Format fields)

Each subagent runs in its own isolated context — it cannot see the other advisors' analyses.

### Phase 3: Synthesize

After all four subagents return their results, synthesize the findings:

#### Areas of Agreement
List insights where **3 or more advisors converge** on the same conclusion, recommendation, or concern. For each area:
- State the common finding
- Note which advisors agree (by name)
- Include the strength of consensus (e.g., "All four advisors" vs "Three advisors")

#### Areas of Disagreement
List direct conflicts or tensions between advisors. For each disagreement:
- State the conflicting positions clearly
- Identify which advisors hold each position
- Explain the root cause of the disagreement (different priorities, risk models, timeframes, etc.)

#### Critical Callouts
One-line highlight from each advisor capturing their most important unique insight:
- **Visionary Advisor**: [single most transformative opportunity or constraint challenge]
- **Skeptic Advisor**: [single most critical risk or evidence gap]
- **Operator Advisor**: [single most critical execution concern or resource constraint]
- **Ethicist Advisor**: [single most important stakeholder impact or ethical consideration]

#### Risk-Adjusted Recommendation

Provide a final verdict in this exact format:

**Confidence Level:** [HIGH | MEDIUM | LOW]

**Key Conditions:**
[List 2-4 must-satisfy conditions, or state "N/A"]

**Primary Risk:**
[Single sentence describing the most critical risk if proceeding]

**Recommended Next Step:**
[Single concrete action to take immediately]

**Rationale:**
[2-3 sentences explaining how you weighed the four perspectives to reach this verdict]

## Output Format

Your complete output should follow this structure:

```
# Advisory Panel: [Brief Decision Title]

## Visionary Advisor Analysis
[Subagent result — complete structured output]

## Skeptic Advisor Analysis
[Subagent result — complete structured output]

## Operator Advisor Analysis
[Subagent result — complete structured output]

## Ethicist Advisor Analysis
[Subagent result — complete structured output]

---

# Synthesis

## Areas of Agreement
[As specified above]

## Areas of Disagreement
[As specified above]

## Critical Callouts
[As specified above]

## Risk-Adjusted Recommendation
[As specified above]
```

## Important Notes

- **True isolation**: Each advisor runs as a separate subagent with its own context window — no cross-contamination between perspectives
- **Parallel execution**: All four subagents launch simultaneously for efficiency
- **Complete frameworks**: Pass the full SKILL.md body to each subagent, not a summary
- **Synthesis integrity**: Base the synthesis only on what the advisors actually returned
- **Verdict precision**: The final recommendation must reflect the balance of all four perspectives
- **Synthesis length**: The synthesis should be 300-500 words. Focus on genuine tensions and agreements, not a rote summary of each advisor.
