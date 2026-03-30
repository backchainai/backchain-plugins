# backchain-plugins

Claude Code plugins by [Backchain](https://backchain.ai)

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

## Marketplace Installation

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