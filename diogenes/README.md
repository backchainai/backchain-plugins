# diogenes

> Senior-reviewer audit for AI-slop and LLM-generation tells in written content: a verdict, an attributable findings table, structural metrics, and a human rewrite.

`diogenes` is a [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin authored to the [agentskills.io specification](https://agentskills.io/specification). Named for the Cynic who walked Athens in daylight with a lit lamp looking for an honest man, it reads submitted writing the way he read Athens: skeptical of polished surfaces, loyal to material specifics, unimpressed by definitions that flatter the reader.

## What this is

One skill backed by one subagent:

- **`audit`** (invoked as `/diogenes:audit`) carries the six-category detection framework, the required output format, and the failure modes. It uses `context: fork` and `agent: diogenes:diogenes`, so every invocation runs in a clean subagent context with no access to the upstream conversation, immune to bias from whatever was being discussed before.
- **`diogenes`** is the subagent that runs the audit. Pinned to `model: sonnet` with read-only tools (`Read, Glob, Grep`) plus `WebFetch`, which lets the auditor read a published page directly when the submission is a URL. Its persona is the senior-reviewer voice that drives the verdict.

Findings cite a fixed set of three peer-reviewed papers, summarized in `skills/audit/references/research.md` (Juzek and Ward 2025, Muñoz-Ortiz 2024, Reinhart et al. 2025). The subagent reads that file when it needs to cite a pattern; citations outside the set are forbidden.

## Layout

```
diogenes/
├── .claude-plugin/plugin.json
├── README.md                           this file
├── agents/
│   └── diogenes.md                     subagent: persona, tools, model: sonnet
└── skills/
    └── audit/
        ├── SKILL.md                    fork target, six-category framework, output spec
        └── references/
            └── research.md             vetted citation set
```

## Installation

### From GitHub (recommended)

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install diogenes@backchain-plugins
```

### Local development

```bash
git clone https://github.com/backchainai/backchain-plugins.git
/plugin marketplace add ./backchain-plugins
/plugin install diogenes@backchain-plugins
```

## Invocation

Direct:

```
/diogenes:audit <text-or-file-or-url> <audience-and-medium>
```

Natural language also triggers the skill: "does this sound like AI", "audit this bio", "review my LinkedIn post for voice", "is this too ChatGPT". The trigger phrases live in the skill's `description` frontmatter.

Plugin skills are namespaced, so the bare `/audit` form is not available; the full invocation is `/diogenes:audit`. Namespacing prevents conflicts when multiple plugins ship skills with the same short name.

## Design

The pattern for "run a bounded operation on a target document in clean context" is a skill with `context: fork` plus an `agent:` reference, not a manually-spawned subagent from a thick SKILL.md. The skill content becomes the prompt for the forked subagent; the subagent's frontmatter supplies the model, tools, and system prompt. The fork sees only the arguments and the bundled research file.

This plugin separates the three concerns:

- **`agents/diogenes.md`** owns the persona, model, and tool surface.
- **`skills/audit/SKILL.md`** owns the task: the six-category detection framework, the required output template, and the failure modes.
- **`skills/audit/references/research.md`** is read on demand inside the fork when the auditor needs to cite a pattern.

## Evaluation

The `audit` skill ships an `evals/evals.json` following the [agentskills.io evaluation specification](https://agentskills.io/skill-creation/evaluating-skills.md), extended with a **verdict label-accuracy** check on top of the report-structure checks.

The runner forks the [engram plugin evaluation framework](../engram/evals/README.md) — same LLM-as-judge methodology, same `claude --bare` clean-room isolation, same git-shorthash iteration provenance. The audit is read-only, so the fs-snapshot machinery is dropped. Each scenario materializes a fixture directory holding a `submission.md` into a tmp workspace, runs the audit against it, and grades the report on two axes: the seven required sections exist (Verdict, Takeaways, Findings table, Structural observations, Authenticity improvements, Human rewrite, Confidence), and the emitted verdict matches the fixture's expected label.

Fixtures span all three verdict labels: `ai-slop` (machine-generated marketing language), `human-voice` (reads as a competent human), and `ai-assisted-but-natural` (LLM may have helped; reads as the author's voice).

See [`evals/README.md`](./evals/README.md) for the runner, fixtures, and how to interpret the with-skill / without-skill delta.

```bash
# From the repo root
uv run --project diogenes/evals python diogenes/evals/run_evals.py
```

## License and contributing

`diogenes` is released under [Apache-2.0](../LICENSE), the same license as the rest of this repository. Copyright (C) 2026 Backchain LLC. Contributions follow the repository [CONTRIBUTING.md](../CONTRIBUTING.md): Apache-2.0, contributors retain copyright, no CLA or DCO sign-off.
