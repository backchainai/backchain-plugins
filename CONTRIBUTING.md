# Contributing to backchain-plugins

Thanks for considering a contribution. This document covers how contributions are licensed and the checklist to run before opening a pull request. It applies to every plugin in this repository: `advisors`, `engram`, and any future plugins published under `backchainai/backchain-plugins`.

## License of Contributions

This repository is released under the [Apache License 2.0](./LICENSE). Contributions are accepted under the same license.

- Contributions are licensed under Apache-2.0.
- Contributors retain copyright on their contributions.
By opening a pull request, you agree that your contribution is licensed under Apache-2.0.

## Pull request checklist

Before opening a PR:

- [ ] New skills include an `evals/evals.json` with at least one structural assertion.
- [ ] If you change a skill's behavior, run the relevant plugin eval harness (`uv run --project <plugin>/evals python <plugin>/evals/run_evals.py --skill <name>`) and include the delta in the PR description.
- [ ] Trigger phrases in `description` frontmatter remain compatible with model-invocation routing.
- [ ] No Backchain-internal references (client names, private directory layouts, internal tool paths) added to public skill files.
- [ ] If a skill needs a tool integration (issue tracker, ADR location, custom scan path), the SKILL.md prompts the user to confirm the choice rather than hard-coding a specific tool.

## Questions

If a contribution does not fit the checklist or you want to discuss an approach first, open an issue. We would rather find a workable path than reject a useful contribution.
