# brief

> Interactive HTML briefs for the moment before you act: plans, specs, option comparisons, annotated reviews, and recommendations rendered as a single self-contained page with inline decision controls and a copy-to-prompt button.

`brief` is a [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin authored to the [agentskills.io specification](https://agentskills.io/specification). It packages one skill that replaces the markdown-plan-in-chat default with an interactive artifact you can read, navigate, and decide inside.

## What this is

Plans, specs, decision matrices, and annotated reviews are spatial information that a markdown wall flattens. The `brief` skill renders them as a single `.html` file that preserves dimensionality (side-by-side cards, collapsible detail, jump links, severity tags) and lets you interact before the next agent runs: toggle options, pick a preset, leave per-decision comments. Whatever you choose returns as a focused execution prompt you paste into a fresh context window. The brief is never the end state; it is a step into the next prompt.

The skill activates by description whenever the work is an intermediate discussion artifact ("give me a plan", "compare X vs Y", "help me decide", "draft a spec", "annotate this"), or explicitly as `/brief:brief`.

## What it produces

A single self-contained page — no CDN loads, no remote fonts — with, in order:

- a rendered-frontmatter header (`prepared_by`, `model`, `timestamp`, `description`);
- a full-width context paragraph stating what you are deciding and why;
- a preset bar (e.g. Lean / Standard / Comprehensive) with the recommended preset pre-selected;
- decision cards with radios, checkboxes, or ranges, each carrying a per-decision comment field;
- an operator-notes textarea;
- a sticky bottom panel that ships collapsed, holding a live execution-prompt preview, a **Copy execution prompt** button, and a **Download as Markdown** action.

The exported prompt is natural language: only non-default choices appear, comments and notes flow in verbatim, and every filesystem path is a clickable `file:///` URL that survives copy-paste.

## Portable by inheritance, not by a fixed palette

The skill hardcodes no brand. At invocation it reads the current project's `CLAUDE.md` and `.claude/rules/*.md` for a visual-identity rule, inlines any design tokens it finds, and falls back to neutral system defaults when none is in scope. A brief looks at home in whatever repo it lands in.

See [`skills/brief/SKILL.md`](./skills/brief/SKILL.md) for the full component contract, the two-track prompt rendering, and the anti-patterns. A working, self-contained model brief ships at [`skills/brief/reference/example.html`](./skills/brief/reference/example.html) — open it in a browser to see every required component live.

## Installation

```
/plugin marketplace add backchainai/backchain-plugins
/plugin install brief@backchain-plugins
```

For local development, add the marketplace from a clone (`/plugin marketplace add ./backchain-plugins`) before the install line.

## Evaluation

The skill ships scenario definitions at [`skills/brief/evals/evals.json`](./skills/brief/evals/evals.json) following the [agentskills.io evaluation specification](https://agentskills.io/skill-creation/evaluating-skills.md), with filesystem-state assertions that check a self-contained `.html` is written (and that trivial lookups produce no brief). The shared Python runner used by the sibling plugins is not yet forked into this plugin.

## License and contributing

`brief` is released under [Apache-2.0](../LICENSE), the same license as the rest of this repository. Copyright (C) 2026 Backchain LLC. Contributions follow the repository [CONTRIBUTING.md](../CONTRIBUTING.md): Apache-2.0, contributors retain copyright, no CLA or DCO sign-off.

## Credits

Published by [Backchain](https://backchain.ai). Authored by [Chris Krough](https://dev.krough.org). Conforms to the [agentskills.io specification](https://agentskills.io/specification).
