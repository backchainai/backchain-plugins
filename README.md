# backchain-plugins

Claude Code plugins by [Backchain](https://backchain.ai). All plugins in this repository conform to the [agentskills.io specification](https://agentskills.io/specification) and ship under [AGPL-3.0-only](./LICENSE) with a Backchain commercial-license reservation (see [License](#license) below).

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

This repository is licensed under [AGPL-3.0-only](./LICENSE). AGPL closes the SaaS loophole that permissive licenses leave open: a competitor offering a hosted version of any plugin in this repository must release their modifications.

## Commercial license

The contents of this repository are offered publicly under AGPL-3.0-only. Backchain LLC, as sole copyright holder, reserves the right to offer the same code under alternate commercial terms — including for proprietary or SaaS use that the AGPL would otherwise constrain.

If your use case requires a non-AGPL license, contact us at [backchain.ai](https://backchain.ai).

## Contributing

External contributions are welcome under [AGPL-3.0-only](./LICENSE) with a [Developer Certificate of Origin](https://developercertificate.org/) sign-off. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full posture and the per-PR checklist.

```bash
git commit -s -m "feat(<plugin>): describe your change"
```