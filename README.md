# backchain-plugins

Claude Code plugins by [Backchain](https://backchain.ai) — practical frameworks for AI-enabled decision-assistance.

## Plugins

### [Advisors](./advisors)

**Team of Rivals**

AI assistants tend to agree with you, even when your idea is terrible. This skill set provides a panel of specialized advisors who argue from genuine conviction, not deference.

Inspired by Lincoln's cabinet strategy: appoint your most formidable opponents to senior roles, not loyalists, so you receive direct and honest feedback from genuinely different perspectives.

The Visionary pushes boundaries. The Skeptic demands evidence. The Operator grounds ideas in execution reality. The Ethicist maps long-term consequences. They disagree with each other, and they will disagree with you. The result is synthesized into a single, honest recommendation design to uncover blind spots and inspire critical thinking for the operator.

| Advisor | Perspective |
|---------|-------------|
| **Visionary** | Expands possibilities, challenges constraints, identifies moonshot opportunities |
| **Skeptic** | Demands evidence, calculates failure probabilities, exposes hidden assumptions |
| **Operator** | Maps resources, identifies dependencies, grounds vision in execution reality |
| **Ethicist** | Evaluates stakeholder impact, assesses long-term consequences, applies moral frameworks |

## Installation

### From GitHub (recommended)

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install advisors@backchain-plugins
```

### Local Development

```bash
git clone https://github.com/backchainai/backchain-plugins.git
/plugin marketplace add ./backchain-plugins
/plugin install advisors@backchain-plugins
```

## Usage

```
# Run the full advisory panel — all four advisors + synthesis
/advisory-panel "Should we migrate our monolith to microservices?"

# Or invoke individual advisors for focused analysis
/advisor-visionary "Should we build an in-house ML platform?"
/advisor-skeptic "Can we hit 10M users in 12 months?"
/advisor-operator "What's required to ship v2.0 by Q3?"
/advisor-ethicist "What are the implications of this data collection policy?"
```

The **advisory panel** runs all four advisors independently, then synthesizes their insights into a unified recommendation with areas of agreement, disagreement, and a risk-adjusted verdict.

Each **individual advisor** provides structured analysis through their specialized lens — designed for productive disagreement, not false consensus.

## Structure

```
backchain-plugins/
├── .claude-plugin/
│   └── marketplace.json           # Marketplace manifest
├── advisors/                      # Advisory panel plugin
│   ├── .claude-plugin/
│   │   └── plugin.json            # Plugin manifest
│   └── skills/
│       ├── advisory-panel/        # Full panel orchestration
│       ├── advisor-visionary/     # Individual advisors
│       ├── advisor-skeptic/
│       ├── advisor-operator/
│       └── advisor-ethicist/
├── CLAUDE.md                      # Development guidance
├── LICENSE                        # MIT License
└── README.md
```

## Contributing

Contributions welcome. To add a new plugin or improve existing ones:

1. Fork the repository
2. Create a feature branch
3. Follow the existing structure — each plugin is self-contained under its own directory with a `.claude-plugin/plugin.json` manifest
4. Submit a pull request

## License

MIT — see [LICENSE](./LICENSE).

## Resources

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — documentation
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — how to create and share plugins
- [Issues](https://github.com/backchainai/backchain-plugins/issues) — report bugs or request features
- [Backchain](https://backchain.ai) — AI transformation consulting
