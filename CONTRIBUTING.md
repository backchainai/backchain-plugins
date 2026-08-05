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
- [ ] If you change a skill's frontmatter `description`, rerun that skill's `evals/trigger-evals.json` (a labeled set of queries a user might type, each marked whether the skill should fire) with `python3 scripts/evals/run_trigger_evals.py --skill-path <plugin>/skills/<name> --eval-set <plugin>/skills/<name>/evals/trigger-evals.json --workspace <grounding-workspace> --candidates <candidates-file> --results-dir <results-dir>`, and include the before/after scores in the PR description. A trigger eval measures whether the model reaches for the skill unprompted, not how well the skill performs once invoked; that is a separate measurement from `evals/evals.json`. It calls the model and costs real money per run, so budget before a large candidate sweep; see `scripts/evals/README.md` for the cost table.
- [ ] No Backchain-internal references (client names, private directory layouts, internal tool paths) added to public skill files.
- [ ] If a skill needs a tool integration (issue tracker, ADR location, custom scan path), the SKILL.md prompts the user to confirm the choice rather than hard-coding a specific tool.

## Running the structure gate

Run the structural gate before opening a PR:

```
bash scripts/gates/structure.sh       # structural contracts + python unit suites
bash scripts/gates/test_structure.sh  # self-test of the gate itself
```

`scripts/gates/structure.sh` is what the repo's automated test gate runs: it checks SKILL.md frontmatter contracts and JSON validity, and runs every tracked stdlib-unittest `test_*.py` suite under a `skills/*/scripts/` directory. Discovery keys on git index membership: a tracked suite with unstaged working-tree edits still runs, but an untracked suite is reported as a FAIL and refused, so `git add` it before running the gate. The same refusal applies to an untracked `scripts/gates/test_*.sh` self-test. Staging is what makes the gate run a suite at all, and staging is also what puts that suite in the diff a reviewer actually reads.

## Questions

If a contribution does not fit the checklist or you want to discuss an approach first, open an issue. We would rather find a workable path than reject a useful contribution.
