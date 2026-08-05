# scriptorium

> Diataxis-grounded documentation authoring and placement: route a document to the mode it belongs in, write it under that mode's constraints, and check its markdown form against CommonMark 0.31.2.

`scriptorium` is a [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin authored to the [agentskills.io specification](https://agentskills.io/specification). It targets a specific failure: agents generate and relocate documentation without a theory of what kind of document they are writing, and the result mixes modes inside a single file: a how-to carrying half a page of rationale, a tutorial offering options instead of one path, a reference page carrying opinion.

## What this is

[Diataxis](https://diataxis.fr/) sorts documentation into four modes by crossing what the reader needs against what the document does:

| Reader needs to... | ...and the document... | ...is a |
|---|---|---|
| learn a skill | walks them through doing it | tutorial |
| apply a skill they have | walks them through doing it | how-to guide |
| apply a skill they have | builds their understanding | reference |
| learn a skill | builds their understanding | explanation |

A tutorial teaches a newcomer by walking one fixed path. A how-to guide gets a competent user through a specific task, not a lesson. A reference states facts about the system so a working user can look them up. An explanation clarifies why the system works the way it does, for a reader who is not mid-task. Mixing modes inside one document leaves the reader unable to tell which promise the document is making.

The second check is markdown form. Once a document's mode is settled, its markdown needs to parse and render correctly. [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) is the specification this plugin checks documents against.

### Out of scope

Diataxis governs product documentation written for users. It does not govern:

- ADRs and decision records
- commit messages and PR descriptions
- changelogs and release notes
- code comments and docstrings
- CLAUDE.md and agent/tool configuration

## Status

The `docs` skill routes a document to its Diataxis mode, writes it under that mode's constraints, names the file and its frontmatter per `references/frontmatter.md`, runs an ordered self-check before emitting, and escalates rather than guessing when a required value is unknown. It also carries a CommonMark authoring reference and the `check_markdown.py` linter for checking markdown form, plus an eval suite covering routing, markdown linting, contamination, scaffolding, out-of-scope requests, and frontmatter emission. Issue [#21](https://github.com/backchainai/backchain-plugins/issues/21), tightening the skill's own `description` frontmatter, is the one item still open under epic [#15](https://github.com/backchainai/backchain-plugins/issues/15).

## License and contributing

`scriptorium` is released under [Apache-2.0](../LICENSE), the same license as the rest of this repository. Copyright (C) 2026 Backchain LLC. Contributions follow the repository [CONTRIBUTING.md](../CONTRIBUTING.md): Apache-2.0, contributors retain copyright, no CLA or DCO sign-off.

## Attribution

scriptorium references and paraphrases two third-party frameworks rather than redistributing their text. scriptorium's own text, including the routing table above, is original wording released under Apache-2.0. See `docs/decisions/third-party-content-licensing.md` for the full license verification and the per-element decision on what may be quoted versus what must be paraphrased.

**Diátaxis** ([diataxis.fr](https://diataxis.fr/))
Licensor: Daniele Procida. License: Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0), `https://creativecommons.org/licenses/by-sa/4.0/`. Source (license): `https://github.com/evildmp/diataxis-documentation-framework/blob/main/LICENSE.rst`. Source (licensor): `https://github.com/evildmp/diataxis-documentation-framework/blob/main/CITATION.cff`.

**CommonMark 0.31.2 specification** ([spec.commonmark.org/0.31.2](https://spec.commonmark.org/0.31.2/))
Licensor: John MacFarlane. License: Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0), `https://creativecommons.org/licenses/by-sa/4.0/`. Source: `https://github.com/commonmark/commonmark-spec/blob/0.31.2/LICENSE`.

## Credits

Published by [Backchain](https://backchain.ai). Authored by [Chris Krough](https://dev.krough.org). Conforms to the [agentskills.io specification](https://agentskills.io/specification).
