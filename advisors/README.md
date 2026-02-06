# Advisors

Team of Rivals advisory skills — four specialized advisors that provide multi-dimensional decision analysis through productive disagreement.

The framework is built on a simple insight: the best decisions come from genuinely different perspectives arguing their positions, not from a single framework applied uniformly. Each advisor has distinct analytical frameworks, output formats, and blind spots by design.

## Skills

| Skill | Purpose |
|-------|---------|
| `advisory-panel` | Runs all four advisors independently, then synthesizes into a unified recommendation |
| `advisor-visionary` | Expands possibilities, challenges constraints, identifies moonshot opportunities |
| `advisor-skeptic` | Demands evidence, calculates failure probabilities, exposes hidden assumptions |
| `advisor-operator` | Maps resources, identifies dependencies, grounds vision in execution reality |
| `advisor-ethicist` | Evaluates stakeholder impact, assesses long-term consequences, applies moral frameworks |

## Installation

Add the marketplace and install the plugin:

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install advisors@backchain-plugins
```

## Usage

Each advisor can be invoked as a slash command. The more context you provide, the sharper the analysis.

```
# Full panel — all four advisors + synthesis
/advisory-panel "We're considering migrating our monolith to microservices.
Current state: 200k LOC Python monolith, 12 engineers, 3 teams.
Motivation: deployment bottlenecks, team autonomy. Budget: $500k over 18 months."

# Individual advisors for focused analysis
/advisor-visionary "We have a SaaS product doing $2M ARR in healthcare scheduling.
Should we pivot to a platform play and let third-party developers build on our API?"

/advisor-skeptic "Our sales team projects 3x revenue growth next year based on
a new enterprise tier. We currently have 0 enterprise customers and no dedicated
sales team. What are we missing?"

/advisor-operator "We need to ship a mobile app by Q3. We have 4 frontend engineers,
none with mobile experience. Options: hire native devs, use React Native, or outsource."

/advisor-ethicist "We're building a feature that uses employee Slack messages to
generate performance insights for managers. Legal says it's fine with disclosure.
Should we ship it?"
```
