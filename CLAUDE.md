# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Repository Overview

A Claude Code plugin marketplace by [Backchain](https://backchain.ai), published at `backchainai/backchain-plugins`. Skills and manifests are markdown and JSON, and some skills ship executable payload alongside them. `scripts/gates/structure.sh` runs the structural gate, which discovers and runs the tracked stdlib python test suites shipped alongside skill scripts; `claude plugin validate .` runs the lint gate. Most plugins' `evals/` directories are `uv` projects with their own `pyproject.toml` and lockfile.

## Plugins

- **advisors** — Decision analysis advisory panel (Team of Rivals)
- **engram** — Filesystem-backed agent memory (consolidate, briefing, working)
- **diogenes** — AI-slop content audit (senior-reviewer subagent)
- **brief** — Interactive HTML briefs for plans, specs, and decisions
- **scriptorium** — Diataxis-grounded documentation authoring and placement (docs skill)

## Architecture

```
.claude-plugin/marketplace.json    # Marketplace manifest (name: backchain-plugins)
scripts/gates/                     # Structural gate + its self-test (structure.sh, test_structure.sh)
advisors/
  .claude-plugin/plugin.json       # Plugin manifest
  skills/
    advisor-*/SKILL.md             # Four individual advisor skills
    advisory-panel/SKILL.md        # Panel orchestration skill
```

### Key patterns

- **Marketplace manifest** (`marketplace.json`) uses relative `source` paths to reference plugins. Each plugin is a self-contained directory.
- **Plugin manifests** (`plugin.json`) declare plugin metadata, discoverability fields, and components.
- **Skills** use YAML frontmatter per the [agentskills.io spec](https://agentskills.io/specification.md). `disable-model-invocation` decides who may invoke a skill. `true` means only the operator can, via `/<skill-name>`; Claude never loads it automatically and never preloads it into a subagent. The default `false` lets Claude invoke it when the description matches the conversation. Set `true` for a skill whose timing the operator controls, as the `advisors` skills do. Leave it `false` for a routing skill that has to fire on its own trigger context. Omitting the field is the same as `false`: `diogenes/skills/audit` omits it deliberately, because its description is written to auto-trigger.

### Adding a new plugin

1. Create a directory at the repo root (e.g., `my-plugin/`)
2. Add `.claude-plugin/plugin.json` with `name`, `description`, `version`, `author`, `license`, `keywords`, `category`, `repository`, and `homepage`. Copying an existing manifest is faster and less error-prone than writing the nine fields from scratch.
3. Add skills under `skills/<skill-name>/SKILL.md`
4. Register the plugin in the root `.claude-plugin/marketplace.json` `plugins` array
5. Update the root `README.md` to list the new plugin

## Editing guidelines

- When modifying advisor skills, maintain the structured output format section at the bottom of each SKILL.md — advisors are designed to produce consistent, parseable output.
- SKILL.md frontmatter must include `name` (matching directory name) and `description` per the [agentskills.io spec](https://agentskills.io/specification.md).
- Keep SKILL.md files under 500 lines. Move detailed reference material to separate files if needed.
