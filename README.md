# backchain-plugins

Claude Code plugins by [Backchain](https://backchain.ai). All plugins in this repository conform to the [agentskills.io specification](https://agentskills.io/specification) and are released as open source under [Apache-2.0](./LICENSE).

## Plugins

### [Advisors](./advisors)

**Team of Rivals**

AI assistants tend to agree with you, even when your idea is... ill-advised. This skill set provides a panel of role-specific advisory agents that argue from focussed perspectives. Inspired by Lincoln's executive cabinet strategy: appoint your most challenging opponents to senior roles, rather than loyalists, so you receive direct and honest feedback from different perspectives. They will disagree with each other and they will disagree with you. The result is synthesized into a single honest recommendation designed to help identify blind spots and promote critical thinking.

| Agent | Perspective |
|---------|-------------|
| **Visionary** | Expands possibilities, challenges constraints, identifies moonshot opportunities |
| **Skeptic** | Demands evidence, calculates failure probabilities, exposes hidden assumptions |
| **Operator** | Maps resources, identifies dependencies, grounds vision in execution reality |
| **Ethicist** | Evaluates stakeholder impact, assesses long-term consequences, applies moral frameworks |

### [Engram](./engram)

**Filesystem-backed agent memory**

Three skills for explicit memory operations that complement Claude Code's native auto memory and `/recap`. `consolidate` audits knowledge directories and graduates stable feedback memories to permanent rules. `briefing` produces a cross-tool session-start orientation from your issue tracker, git history, and staleness signals. `working` manages an ephemeral `.memory/` directory with an explicit checkpoint → promote → cleanup lifecycle.

| Skill | Purpose |
|-------|---------|
| **consolidate** | Audit knowledge dirs and auto memory; produce an editable cleanup plan; execute approved actions |
| **briefing** | Session-start briefing from issue tracker + git + working memory + staleness signals |
| **working** | Structured ephemeral state — todos, decisions, questions — with promotion to permanent locations |

Tool-agnostic: prompts the user for issue-tracker / ADR / docs locations rather than assuming a specific stack.

## Marketplace Installation

### From GitHub (recommended)

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install advisors@backchain-plugins
/plugin install engram@backchain-plugins
```

### Local Development

```bash
git clone https://github.com/backchainai/backchain-plugins.git
/plugin marketplace add ./backchain-plugins
/plugin install advisors@backchain-plugins
/plugin install engram@backchain-plugins
```

## License

Licensed under the [Apache License 2.0](./LICENSE). Copyright (C) 2026 Backchain LLC.

Use, modify, and redistribute these plugins freely, including in commercial and proprietary work, under the terms of the license. See [NOTICE](./NOTICE) for attribution that travels with redistribution.

## About

Published by [Backchain](https://backchain.ai): **Discover Where AI Works**. Backchain builds practical agent tooling for Claude Code. Authored by [Chris Krough](https://dev.krough.org) ([LinkedIn](https://www.linkedin.com/in/ckrough)).

If these plugins are useful, install them, star the repo, and explore more at [backchain.ai](https://backchain.ai).

## Contributing

Contributions are welcome under [Apache-2.0](./LICENSE); contributors retain copyright on their work. No CLA and no DCO sign-off required. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the per-PR checklist.