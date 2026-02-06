# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Repository Overview

A Claude Code plugin marketplace by [Backchain](https://backchain.ai), published at `backchainai/backchain-plugins`. This is a content-only repository — no build system, no dependencies, no tests. All files are markdown and JSON.

## Plugins

- **advisors** — Decision analysis advisory panel (Team of Rivals)

## Architecture

```
.claude-plugin/marketplace.json    # Marketplace manifest (name: backchain-plugins)
advisors/
  .claude-plugin/plugin.json       # Plugin manifest
  skills/
    advisor-*/SKILL.md             # Four individual advisor skills
    advisory-panel/SKILL.md        # Panel orchestration skill
```

### Key patterns

- **Marketplace manifest** (`marketplace.json`) uses relative `source` paths to reference plugins. Each plugin is a self-contained directory.
- **Plugin manifests** (`plugin.json`) declare plugin metadata, discoverability fields, and components.
- **Skills** use YAML frontmatter with `disable-model-invocation: true` — they inject context into the conversation, not invoke models.

### Adding a new plugin

1. Create a directory at the repo root (e.g., `my-plugin/`)
2. Add `.claude-plugin/plugin.json` with name, description, version, author, license, and keywords
3. Add skills under `skills/<skill-name>/SKILL.md`
4. Register the plugin in the root `.claude-plugin/marketplace.json` `plugins` array
5. Update the root `README.md` to list the new plugin

## Editing guidelines

- When modifying advisor skills, maintain the structured output format section at the bottom of each SKILL.md — advisors are designed to produce consistent, parseable output.
- SKILL.md frontmatter must include `name` (matching directory name) and `description` per the [agentskills.io spec](https://agentskills.io/specification.md).
- Keep SKILL.md files under 500 lines. Move detailed reference material to separate files if needed.
