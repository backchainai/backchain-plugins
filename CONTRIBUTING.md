# Contributing to backchain-plugins

Thanks for considering a contribution. This document covers the licensing structure for contributions, why it works the way it does, and how to sign off on commits. It applies to every plugin in this repository — `advisors`, `engram`, and any future plugins published under `backchainai/backchain-plugins`.

## License

This repository is licensed under [AGPL-3.0-only](./LICENSE). All contributions are accepted under that same license unless otherwise agreed in writing.

Backchain LLC, the original author and sole copyright holder, reserves the right to offer the same code under alternate commercial terms. This is the standard "asymmetric dual license" posture used by projects like MongoDB, Mattermost, and Element. It means:

- **Public users** receive the code under AGPL-3.0-only.
- **Backchain LLC** retains the rights of the copyright holder — including the right to license its own code under non-AGPL terms for proprietary or SaaS use.
- **External contributions** must come with a Developer Certificate of Origin sign-off so that Backchain can include them under the same dual-license structure.

If you cannot or do not want to sign off, please open an issue first to discuss. We'd rather find a workable path than reject a useful contribution.

## Developer Certificate of Origin (DCO)

Every commit must carry a `Signed-off-by:` line. By signing off on a commit, you certify the [Developer Certificate of Origin v1.1](https://developercertificate.org/) — that you have the right to submit the change under the project's license.

Use `git commit -s` to add the sign-off automatically:

```bash
git commit -s -m "feat(engram/consolidate): add support for custom scan roots"
```

That produces a commit message ending with:

```
Signed-off-by: Your Name <your-email@example.com>
```

The name and email must match a real identity (yours or your employer's, depending on who holds rights to your work). Anonymous or pseudonymous sign-offs are not accepted.

To set up sign-off as a default for a single repo:

```bash
git config commit.gpgsign true       # optional but recommended
git config format.signOff true       # auto-add Signed-off-by on every commit
```

## Pull request checklist

Before opening a PR:

- [ ] All commits carry a `Signed-off-by:` trailer.
- [ ] New skills include an `evals/evals.json` with at least one structural assertion.
- [ ] If you change a skill's behavior, run the relevant plugin eval harness (`uv run --project <plugin>/evals python <plugin>/evals/run_evals.py --skill <name>`) and include the delta in the PR description.
- [ ] Trigger phrases in `description` frontmatter remain compatible with model-invocation routing.
- [ ] No Backchain-internal references (client names, private directory layouts, internal tool paths) added to public skill files.
- [ ] If a skill needs a tool integration (issue tracker, ADR location, custom scan path), the SKILL.md prompts the user to confirm the choice rather than hard-coding a specific tool.

## Commercial inquiries

If your use case requires a non-AGPL license — for example, embedding code from this repository in proprietary software you cannot or do not wish to release — contact us at [backchain.ai](https://backchain.ai). The asymmetric dual license preserves that path for everyone, including future commercial users.
