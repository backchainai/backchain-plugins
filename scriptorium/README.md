# scriptorium

> Diataxis-grounded documentation authoring and placement: route a document to the mode it belongs in, write it under that mode's constraints, and check its markdown form against CommonMark 0.31.2.

`scriptorium` is a [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin authored to the [agentskills.io specification](https://agentskills.io/specification). It targets a specific failure: agents generate and relocate documentation without a theory of what kind of document they are writing, and the result mixes modes inside a single file: a how-to carrying half a page of rationale, a tutorial offering options instead of one path, a reference page carrying opinion.

## What this is

[Diataxis](https://diataxis.fr/) sorts documentation into four modes along two axes: whether the content serves action or cognition, and whether it serves the user's acquisition of a skill or their application of a skill they already have.

| If the content... | ...and serves the user's... | ...then it belongs to... |
|---|---|---|
| informs action | acquisition of skill | tutorial |
| informs action | application of skill | how-to guide |
| informs cognition | application of skill | reference |
| informs cognition | acquisition of skill | explanation |

A tutorial teaches a newcomer by walking one fixed path. A how-to guide gets a competent user through a specific task, not a lesson. A reference states facts about the system so a working user can look them up. An explanation clarifies why the system works the way it does, for a reader who is not mid-task. Mixing modes inside one document leaves the reader unable to tell which promise the document is making.

The second check is markdown form. Once a document's mode is settled, its markdown needs to parse and render correctly. [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) is the specification this plugin checks documents against.

### Out of scope

Diataxis governs product documentation written for users. It does not govern:

- ADRs and decision records
- commit messages and PR descriptions
- changelogs and release notes
- code comments and docstrings
- CLAUDE.md and agent/tool configuration
- READMEs

## Status

This plugin is a scaffold. No skill ships yet: the routing logic, the authoring workflow, and the CommonMark check described above are tracked under epic [#15](https://github.com/backchainai/backchain-plugins/issues/15) and its child issues, not implemented in this tree. Installing `scriptorium` today registers the plugin manifest only.

## License and contributing

`scriptorium` is released under [Apache-2.0](../LICENSE), the same license as the rest of this repository. Copyright (C) 2026 Backchain LLC. Contributions follow the repository [CONTRIBUTING.md](../CONTRIBUTING.md): Apache-2.0, contributors retain copyright, no CLA or DCO sign-off.

## Credits

Published by [Backchain](https://backchain.ai). Authored by [Chris Krough](https://dev.krough.org). Conforms to the [agentskills.io specification](https://agentskills.io/specification).
