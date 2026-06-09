# diogenes (plugin)

A Claude Code plugin that audits written content for AI-slop and LLM-generation tells. Named for Diogenes the Cynic, who walked Athens in daylight with a lit lamp looking for an honest man.

## Surface

- **Skill:** `slop-audit` (invoked as `/diogenes:slop-audit`). Carries the detection framework, output format, and failure modes. Uses `context: fork` and `agent: diogenes:diogenes` so every invocation runs in a clean subagent context, immune to upstream conversation bias.
- **Subagent:** `diogenes`. Pinned to `model: sonnet`. Tools: `Read, Glob, Grep, WebFetch` (the WebFetch tool lets the auditor read a URL directly when the submission is a published page). Persona is the senior-reviewer voice that drives the audit.
- **References:** `skills/slop-audit/references/research.md` carries three peer-reviewed citation sources (Juzek and Ward 2025, Munoz-Ortiz 2024, Reinhart 2025). The subagent reads this file when it needs to cite a pattern. Citations outside this set are forbidden.

## Files

```
diogenes/
├── .claude-plugin/plugin.json
├── README.md                           ← this file
├── agents/
│   └── diogenes.md                     ← subagent: persona, tools, model: sonnet
└── skills/
    └── slop-audit/
        ├── SKILL.md                    ← fork target, six-category framework, output spec
        └── references/
            └── research.md             ← vetted citation set
```

## Invocation

Direct: `/diogenes:slop-audit <file or text> <audience>`

Natural language ("does this sound like AI", "audit this bio", "review my LinkedIn post for voice", "is this too ChatGPT") triggers the skill automatically. The trigger phrases live in the skill's `description` frontmatter.

## Design notes

The Anthropic-recommended pattern for "run a bounded operation on a target document in clean context" is a skill with `context: fork` plus an `agent:` reference, not a manually-spawned subagent from a thick SKILL.md. The skill content becomes the prompt for the forked subagent; the subagent's frontmatter provides the model, tools, and system prompt. The fork has no access to the upstream conversation.

This plugin implements that pattern directly:

- **`agents/diogenes.md`** owns the persona, model, and tool surface.
- **`skills/slop-audit/SKILL.md`** owns the task: the six-category detection framework, the required output template, and the failure modes.
- **`references/research.md`** is read on demand inside the fork when the auditor needs to cite a pattern.

Plugin skills are always namespaced. The bare `/slop-audit` form is not available; the full invocation is `/diogenes:slop-audit`. The namespacing prevents conflicts when multiple plugins ship skills with the same short name.
