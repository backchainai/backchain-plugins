---
name: brief
description: Produce an interactive HTML brief when the operator needs to read, decide, or discuss before acting. Use it as the default for plans, specs, design explorations, comparison tables, option lists, annotated reviews, and recommendations. Use it instead of a markdown plan in chat, an ExitPlanMode plan, or a comparison in prose, even when the user does not say HTML. Triggers include "give me a plan", "what are the options", "compare X vs Y", "help me decide", "what's your recommendation", "draft a spec", "design this", "annotate this", "side-by-side", and any case where Claude would otherwise write a markdown plan for the operator to review. Skip it for yes/no questions, routine recaps, final deliverables, and config files.
disable-model-invocation: false
---

# brief

Produce an interactive HTML brief as the medium for an intermediate operator-agent discussion. The brief is a single self-contained `.html` file. Where the artifact has decisions to make, it carries inline controls (radios, checkboxes, sliders, free-text fields). Whether or not it has decisions, it always ends with a sticky "Copy execution prompt" button: the operator reviews the artifact, optionally commits to choices and notes, and pastes a clean execution prompt into a fresh context window where another agent acts on it.

The pattern exists because plans, specs, design explorations, annotated diffs, decision matrices, and navigable reports are spatial information that markdown flattens. HTML preserves dimensionality (side-by-side comparison, collapsible detail, jump links, tabs, swatches, severity tags) and lets the operator interact with the artifact (toggle options, expand sections, scrub a slider) before the next agent runs. The export-button feedback loop is the second half of the pattern: whatever the operator did in the UI returns to the agent as a focused prompt, instead of leaving ambiguity in prose.

## When this skill applies

This skill is the **default format** for any intermediate operator-agent discussion artifact. The pattern's value is spatial layout, interactivity, and the export-button feedback loop into the next prompt. Trigger whenever **any** of these are true:

- **Intermediate discussion document.** The artifact is a plan, spec, draft proposal, design exploration, decision matrix, annotated review, recommendation, or report the operator will read carefully and discuss before acting on it.
- **Forkable decisions.** The work has multiple options that are easier grasped side-by-side than described in prose, and the operator will commit to specific choices.
- **Spatial information.** The content is structural and markdown would flatten it: design tokens as swatches, diffs with margin notes and severity tags, architecture or call-graph layouts, comparison tables that benefit from interaction.
- **Navigable scaffolding.** The operator wants collapsible sections, tabs, jump links, or side-by-side comparison rather than linear top-to-bottom reading.
- **Follow-on prompt.** The next step is a fresh context window, so the artifact must produce a prompt that stands alone.

Triggering phrases include "give me a plan", "let me see the plan first", "what are the options", "compare X vs Y", "side-by-side", "help me decide", "review this and tell me what you think", "what's your recommendation", "draft a spec", "design this", "annotate this", "I want to discuss this before you act", "html brief", "interactive brief", "html plan", "spec this in HTML", "render the plan as HTML", "options for me to pick", "copy-to-prompt", "give me a plan I can review", "annotate this diff", "show me the design tokens as swatches", "explore X interactively", "intermediate document", or anything that frames the work as a discussion artifact rather than a final deliverable. The substance matters more than the wording: prefer this skill over a markdown wall any time the operator will read carefully, navigate, compare, or feed the result back into a next-step prompt.

The export button is non-negotiable. Even briefs without explicit decisions still emit a follow-on prompt the operator can paste into the next session (e.g. "I have read the plan; proceed with it.", "Use these design tokens for the implementation."). The brief is never the end state: it is always a step into the next prompt.

## Prefer this skill over these defaults

Claude Code's default behavior for intermediate discussion artifacts is to write a markdown plan or analysis directly in chat, or to return an ExitPlanMode markdown plan. **Replace those defaults with a brief.** Specifically:

| Default Claude reaches for | Replace with a brief because |
|---|---|
| "Here is my plan: ..." markdown response in chat | The operator will review and decide; controls + export button beat prose every time |
| ExitPlanMode with a markdown plan | The plan is an intermediate discussion artifact; render it as a brief and let the operator approve by copying the prompt |
| Comparison table or option list in chat ("Option A vs Option B") | Side-by-side cards with radio controls carry the comparison better than a flat table |
| Multi-paragraph "what do you think of these approaches" prose | The operator needs to choose; give them controls, not paragraphs |
| Markdown spec or PRD draft for review | Specs are quintessentially intermediate; collapsible sections and inline decision controls make them scan-able |
| Annotated code review or copy critique posted in chat | Severity tags, margin notes, and jump links live natively in HTML |
| Recommendation document the operator will react to | Pre-select the recommended path; surface alternatives as alternate presets |
| Decision matrix or scoring rubric | Interactive cells and toggles beat a static table |

Side-by-side comparisons and multi-option decisions go to a brief, never to a markdown table in chat.

Do not produce a brief for:

- Yes/no questions or single-decision asks where `AskUserQuestion` is sufficient
- Routine recaps or summaries the operator will read once and discard
- Final deliverables (client artifacts, published content) — those follow their own pipelines
- Configuration files (settings, plugin manifests, rules) — config, not deliverables
- Trivial answers (a one-line fact, a path lookup, a quick confirmation)

## Output

| Item | Value |
|------|-------|
| Path | Default `outputs/briefs/brief_<descriptor>_YYYY-MM-DD.html`, relative to the agent's current working directory. If the project defines its own outputs location or file-naming convention (in `CLAUDE.md` or a `.claude/rules/*.md` rule), follow that instead. |
| Naming | `<descriptor>` is a short kebab-case topic identifier. Lowercase, hyphen-separated words, underscore field separators. |
| Format | Single self-contained `.html`. No external CDN loads. No remote font loads. Everything inlined. |
| Open behavior | Save the file, then report its `file:///...` URL to the operator so the brief stays clickable from the transcript. If a `cmux` binary is on `PATH`, also open it in the cmux browser surface with `cmux browser open file:///<absolute-cwd-path>` (use the agent's current working directory as the absolute root: the worktree path when in a worktree). Do not launch a system browser; reporting the URL is the fallback when no in-workspace browser surface is available. |

## Visual identity is inherited, not hardcoded

Do not bake any specific palette, typography, or design tokens into a brief. Instead, at invocation time:

1. Read the agent's current working-directory `CLAUDE.md` and any `.claude/rules/*.md` rules in scope. Look for a brand or visual-identity rule (commonly `.claude/rules/brand.md` or similar) and follow the references it provides.
2. If a design-tokens file exists (commonly `brand/design-tokens.css` or similar; the path is repo-specific), read it and **inline** the relevant tokens into the brief's `<style>` block. The brief must remain self-contained, so links to external token files do not work; the tokens have to live in the file.
3. If a brand-voice or visual-identity reference exists (e.g. `brand/visual-identity.md`), use its palette, typography, and elevation guidance to drive the brief's CSS.
4. If no design rules are in scope, fall back to neutral defaults: `system-ui` for prose, `ui-monospace` for code, light theme, conservative spacing, no gratuitous color. Note the absence to the operator when reporting the URL ("no project visual-identity rule was found; brief uses neutral defaults").

The brief should look at home in the project it lives in. Cross-project portability comes from this inheritance, not from a one-size palette.

## Required components

Every brief includes these elements, in this order:

1. **Header** — rendered-frontmatter pane: a `<pre class="frontmatter">` block styled as a soft-tinted monospace panel (think rendered YAML frontmatter), carrying four keys in this order: `prepared_by` (agent identifier, e.g. `Claude Code`), `model` (model id including any version suffix, e.g. `claude-opus-4-8[1m]`), `timestamp` (full RFC 3339 with minutes and offset, captured from `date -Iseconds` at write time), and `description` (one-sentence focus summary). No wordmark, no tagline, no display title — the description carries the brief's identity. See the snippet at the bottom of this section.
2. **Context paragraph** — one full-container-width paragraph (drop the default 70ch prose cap) stating what the operator is deciding and why
3. **Preset bar** — a `<fieldset>` of named decision-set radios (e.g. `Lean / Standard / Comprehensive`) above the decision cards; the recommended preset is pre-selected on load; switching presets writes every decision in one click
4. **Body sections** — plan or spec content with inline `<fieldset>` controls at each decision point: radio groups for mutually exclusive options, checkboxes for multi-select, range or number inputs where applicable. **Every decision card carries a single-line `<input type="text">` comment field below its options**; non-empty values flow into the prompt under a `Comments:` block keyed by decision name.
5. **Optional live preview** — only when a style choice has visual consequence (design briefs, copy briefs); otherwise omit
6. **Operator notes textarea** — a free-text `<textarea>` at the bottom of the decision flow; contents pass verbatim into the prompt as a `> `-prefixed block
7. **Sticky bottom panel** — live prompt preview in a monospace block, regenerated on every state change. The panel ships **minimized on first paint** with a clear `Expand` / `Collapse` toggle button in its header row. When minimized, only the monospace prompt preview is hidden; the panel header (title + minimize toggle) and the primary CTA remain visible and clickable so the operator can copy without expanding. Expanding reveals the full live preview. Use an `aria-expanded` attribute on the toggle, set `aria-controls` to the preview block's id, and animate the height transition behind a `prefers-reduced-motion` guard so motion-sensitive operators get an instant state swap. Persist the open/closed state across `updateAll()` renders — re-rendering the prompt text must not re-collapse a panel the operator just expanded.
8. **Single primary CTA: "Copy execution prompt"** — `navigator.clipboard.writeText`, `Copied` toast, no page reload. Lives in the panel header row alongside the minimize toggle so it stays reachable in both states.
9. **Secondary action: "Download as Markdown"** — saves the same prompt as `.md` for archival. Also lives in the panel header row so it stays reachable when the preview is minimized.

### Header snippet

```html
<header class="brief-header">
  <pre class="frontmatter"><span class="k">prepared_by</span>: Claude Code
<span class="k">model</span>: claude-opus-4-8[1m]
<span class="k">timestamp</span>: 2026-07-24T09:44:05-04:00
<span class="k">description</span>: One-sentence focus summary.</pre>
</header>
```

```css
pre.frontmatter {
  background: color-mix(in srgb, var(--color-heading) 6%, var(--color-surface));
  color: var(--color-heading);
  font-family: var(--font-mono);
  font-size: var(--text-small);
  line-height: 1.7;
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
```

The `<span class="k">` wrappers on keys are optional — they exist so a future style change can emphasize keys without rewriting markup. The token names above (`--color-heading`, `--color-surface`, `--font-mono`, `--space-md`) are illustrative: substitute the project's own surface, heading, and spacing tokens when a brand rule defines different ones, or concrete neutral values when none is in scope.

## Prompt construction

The exported prompt is natural language, not a value dump. Use this format:

```
Continue from brief: <title> (<file:///absolute-cwd-path-to-html>).

Decisions:
- <decision 1, only if non-default>
- <decision 2, only if non-default>
...

Notes from operator:
> <free-text input verbatim, fenced if multi-line>

<Closing instruction tailored to this brief.>
```

Rules:

- **Defaults stay silent.** Only non-default selections appear as bullets. If everything is default, emit a single line like `- (all defaults; see brief for the recommended path)`.
- **Notes are verbatim.** Multi-line free-text gets `> ` prefixed on each line. Do not paraphrase or summarize.
- **The closing instruction is brief-specific.** Write it so a fresh agent in a clean context can act without re-reading the brief unless they choose to. Examples: "Begin implementation. Confirm before any destructive change.", "File an issue with these decisions and start it.", "Before implementing, ask any clarifying questions about the decisions above."
- **Path form.** The brief path on the first line, and any other filesystem path that appears in the prompt, is rendered as a `file:///...` URL. Use the agent's current working directory as the absolute root. Bare paths get auto-https-prepended by rendering surfaces (terminals, transcript UIs, embedded webviews), producing errors like `https://users/... refused to connect`. The `file://` scheme prefix tells the surface to honor the URL rather than guess one, and it survives copy-paste so the same prompt text remains clickable wherever it lands.

## Link conventions

Every reference inside a brief is a clickable link except literal commands (e.g. `git status`, `npm test`).

| Reference | Markup | Notes |
|-----------|--------|-------|
| External URL | `<a href="https://..." target="_blank" rel="noopener">` | Always opens in a new tab |
| Filesystem path | `<a href="file:///<absolute-cwd-path>" target="_blank" rel="noopener"><code>path/relative/to/cwd</code></a>` | href is the absolute path from the agent's current working directory; visible text is the path relative to that root, wrapped in `<code>` |
| Command or literal | `<code>git status</code>` | Plain `<code>`, not a link |

Rules:

- Every link carries `target="_blank"` and `rel="noopener"` so the operator never loses the brief context when following a citation.
- Use absolute paths from the agent's current working directory. From a worktree, that means the worktree path; from main, the project-root path. Newly-created files only exist where the agent created them; project-root links to them would 404 until merge.
- Do not script-launch a specific browser from inside a brief. The OS default browser handles `file://` and `https://` via `target="_blank"`.

## Two-track rendering for the prompt preview

The prompt has two simultaneous representations:

- **Visible track (in the sticky panel):** a DOM tree where every `file:///...` URL becomes a real `<a href="...">` anchor. Rendering surfaces (browsers, embedded webviews) honor the href instead of guessing a scheme.
- **Copied/downloaded track (clipboard, .md):** plain text whose embedded paths are still `file:///...` URLs, so the scheme survives paste into terminals or other rendering surfaces.

Build the visible track via DOM construction:

```javascript
function renderPromptInto(el, text) {
  const re = /file:\/\/\/[^\s)<>"']+/g;
  const parts = [];
  let lastIndex = 0;
  for (const m of text.matchAll(re)) {
    if (m.index > lastIndex) {
      parts.push(document.createTextNode(text.slice(lastIndex, m.index)));
    }
    const a = document.createElement('a');
    a.href = m[0];
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = m[0];
    parts.push(a);
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(document.createTextNode(text.slice(lastIndex)));
  }
  el.replaceChildren(...parts);
}
```

Do not use `innerHTML` with operator-supplied content (free-text notes flow into the prompt). DOM construction sidesteps the XSS surface entirely.

## State management

Use a single state object as the source of truth.

- `const state = { ... }` with sensible defaults that reflect the recommended path
- Every control writes to `state` on its `change` event
- One `updateAll()` function regenerates the live prompt panel and any preview
- Provide 3 to 5 named presets (radios at the top of the brief, e.g. "Lean / Standard / Comprehensive") that overwrite `state` in one click
- First paint must look polished. Defaults reflect the path the agent recommends; presets let the operator switch context cheaply

## Anti-patterns to avoid

- **External font, CSS, or JS loads.** The brief must work offline and survive being archived. Inline everything.
- **`innerHTML` with operator-supplied content.** Use `createTextNode` and `createElement('a')` plus `replaceChildren(...)`.
- **Bare absolute paths in operator-visible text.** Always use the `file://` scheme. Bare paths get auto-https-prepended by rendering surfaces.
- **Launching a detached system browser with `open` (macOS) or `xdg-open` (Linux).** If an in-workspace browser surface exists (e.g. `cmux browser open file:///...`), use it so the brief lands where the operator is working. Otherwise just report the `file://` URL and let the operator open it — do not spawn a system browser that detaches from the workspace.
- **Hardcoded brand styling.** Inherit from in-scope project rules. The skill is portable across repos.
- **Skipping the `prefers-reduced-motion` block.** Operators with motion sensitivity exist; respect them. Wrap transitions and animations in the standard guard.
- **Sub-48px touch targets** or missing `:focus-visible` outlines. Briefs are interactive artifacts; basic accessibility is non-negotiable.
- **Prompt panel expanded on first paint, or no minimize toggle at all.** The sticky panel must start collapsed and carry a visible expand/collapse control. A brief that opens with the preview already covering the body section forces the operator to scroll past it before reading the brief.

## Reference example

A self-contained canonical example ships with this skill at [`reference/example.html`](./reference/example.html) (relative to this skill directory). It demonstrates: the rendered-frontmatter header, the full-width intro paragraph, the preset bar with a pre-selected recommended preset, decision cards with per-decision comment inputs, the operator-notes textarea, the two-track prompt rendering with `Comments:` and `Notes from operator:` blocks, the sticky panel that ships minimized with an expand/collapse toggle, and the link conventions. It uses neutral defaults because this plugin repo defines no brand rule.

When producing a new brief, read the bundled example as a model, but do not copy it wholesale: the descriptor, decisions, presets, comment-input copy, and closing instruction are brief-specific, and the visual identity must be re-derived from the in-scope rules at the moment of generation. In a repo with a brand rule, the example's neutral tokens are replaced by the project's own.

## Reporting back

After writing the file:

1. Report the `file:///...` URL of the brief to the operator so the link stays clickable from the transcript.
2. If a `cmux` binary is on `PATH`, open the brief in the cmux browser surface with `cmux browser open file:///<absolute-cwd-path>`. Otherwise skip this step — do not launch a system browser.
3. Give a one-sentence summary of which preset and decisions are pre-selected.
4. (If applicable) note that no project visual-identity rule was found and the brief uses neutral defaults.

Do not run further post-write actions unless the operator asks.
