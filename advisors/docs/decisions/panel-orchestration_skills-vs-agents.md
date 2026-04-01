---
title: Panel Orchestration — Skills vs Agents
prepared_by: Claude (Opus 4.6)
updated: 2026-04-01T14:29:39-04:00
purpose: A/B comparison of two correct orchestration approaches for the advisory panel, decided by eval data.
tags: []
aliases: []
---

# Panel Orchestration — Skills vs Agents

## Decision

**Use skills-based orchestration (Skill tool invocation) for the advisory panel.** Agent definitions do not improve quality and cost more.

## Context

The advisory-panel skill orchestrates four independent advisor analyses (visionary, skeptic, operator, ethicist) in parallel, then synthesizes their outputs. The original implementation read all four SKILL.md files and pasted their content into generic subagent prompts — wasteful and incorrect regardless of approach.

Two correct implementations were built and evaluated:

- **Phase A (Skills):** Panel launches generic subagents, each invokes its advisor skill via the Skill tool. The Skill tool loads the framework automatically.
- **Phase B (Agents):** Panel launches typed subagents (`subagent_type` per advisor). Each agent definition has `skills: [advisor-X]` in frontmatter, preloading the framework as system context at startup.

Both approaches eliminate the file-reading problem. Both achieve advisor isolation. The question was which produces better results.

## Evaluation Methodology

Three eval iterations run against the same test scenarios using `claude --bare` for clean-room isolation:

- **Model:** claude-sonnet-4-6 (assessment), claude-haiku-4-5 (grading)
- **Scenarios:** 3 per skill (boat-rental, content-writers, saas-pivot)
- **Skills evaluated:** 5 (4 individual advisors + panel orchestrator)
- **Modes:** with_skill and without_skill (baseline comparison)
- **Total runs per iteration:** 30 assessments + 30 gradings

## Results

### Aggregate

| Metric | Baseline (original) | Skills (A) | Agents (B) |
|--------|---------------------|------------|------------|
| Pass rate | 96% (107/112) | **97% (109/112)** | 96% (108/112) |
| Cost (with skill) | $0.99 | **$0.74** | $0.85 |
| Failures (with skill) | 5 | **3** | 4 |

### Panel Timing (orchestrator runs only)

| Scenario | Baseline | Skills (A) | Agents (B) |
|----------|----------|------------|------------|
| boat-rental | 209s / $0.18 | **120s / $0.10** | 206s / $0.17 |
| content-writers | 182s / $0.17 | **93s / $0.06** | 125s / $0.10 |
| saas-pivot | 221s / $0.18 | **127s / $0.09** | 139s / $0.12 |

### Per-Skill Pass Rates (with_skill)

| Skill / Scenario | Baseline | Skills (A) | Agents (B) |
|------------------|----------|------------|------------|
| ethicist/boat-rental | 6/7 | 6/7 | 7/7 |
| ethicist/content-writers | 7/7 | 7/7 | 7/7 |
| ethicist/saas-pivot | 7/7 | 6/7 | 5/7 |
| operator/boat-rental | 7/7 | 7/7 | 7/7 |
| operator/content-writers | 7/7 | 7/7 | 7/7 |
| operator/saas-pivot | 5/7 | 6/7 | 5/7 |
| skeptic/boat-rental | 7/7 | 7/7 | 7/7 |
| skeptic/content-writers | 7/7 | 7/7 | 7/7 |
| skeptic/saas-pivot | 5/7 | 7/7 | 7/7 |
| visionary (all) | 7/7 | 7/7 | 7/7 |
| panel (all) | perfect | perfect | perfect |

### Individual Advisor Timing (with_skill, representative)

| Advisor / Scenario | Baseline | Skills (A) | Agents (B) |
|--------------------|----------|------------|------------|
| ethicist/boat-rental | 42s | 54s | 43s |
| ethicist/content-writers | 33s | 33s | 28s |
| ethicist/saas-pivot | 49s | 52s | 51s |
| operator/boat-rental | 76s | 85s | 71s |
| operator/content-writers | 44s | 51s | 53s |
| operator/saas-pivot | 81s | 84s | 76s |
| skeptic/boat-rental | 70s | 69s | 66s |
| skeptic/content-writers | 57s | 57s | 55s |
| skeptic/saas-pivot | 58s | 69s | 77s |
| visionary/boat-rental | 49s | 57s | 48s |
| visionary/content-writers | 32s | 33s | 32s |
| visionary/saas-pivot | 53s | 52s | 60s |

Individual advisor timing is comparable across all three approaches (within normal LLM variance). The panel timing difference is where the architectural choice matters.

## Analysis

### Why skills won

1. **Cost efficiency.** Skills-correct is 25% cheaper than baseline and 13% cheaper than agents. The Skill tool invocation is lightweight — one tool turn per subagent, negligible cost.

2. **Panel speed.** Skills-correct panel runs are 42-49% faster than baseline and consistently faster than agents. The agents approach showed no speed advantage from framework preloading in the eval environment.

3. **Pass rate.** Skills-correct achieved the highest pass rate (97%), with the fewest failures (3). Agents matched baseline (96%) but didn't improve.

4. **Simplicity.** Zero new files. The panel skill and four advisor skills are the complete system. Agents would add four agent definition files that partially duplicate the skill content.

### Why agents didn't win

The eval runner uses `claude --bare` which provides a clean-room environment. The `subagent_type` instructions in the panel may not resolve typed agents the same way a full Claude Code session would. This means the agents approach was effectively falling back to generic subagent behavior, negating the preloading advantage.

Even in a full Claude Code session, the practical benefit of agents is narrow:
- **Standalone isolated dispatch** (`@agent-advisors:advisor-visionary`) — possible with agents, not with skills. But unclear if users need this when `/advisor-visionary` (inline) already works.
- **Per-advisor model control** — nice to have, but no current use case demands it.

### What both approaches fixed

Both correctly eliminate the original implementation's file-reading waste. The panel no longer reads SKILL.md files or pastes content into prompts. Each advisor loads its own framework through the appropriate mechanism.

## Consequences

- Advisory panel uses Skill tool invocation (Phase A implementation)
- No `agents/` directory in the advisors plugin
- Individual advisors remain skills only (no dual skill+agent identity)
- Panel frontmatter: `allowed-tools: Agent Skill`
- Eval config: `tools: "Agent,Skill"` for panel runs

## Revisit Conditions

Reconsider agents if:
- Users request standalone isolated advisor dispatch
- Per-advisor model tuning becomes valuable (e.g., Opus for visionary, Haiku for operator)
- The eval runner gains native plugin agent support, enabling a fair comparison of preloaded frameworks
