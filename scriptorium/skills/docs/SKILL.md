---
name: docs
description: "Routes one document to its Diataxis mode (tutorial, how-to guide, reference, explanation), drafts or edits it under that mode's constraints, and checks its markdown form against CommonMark 0.31.2. Use when: writing or generating documentation, deciding where a doc belongs, moving or reorganizing docs, splitting a document serving two audiences, reviewing docs for mode contamination, checking markdown form. Trigger phrases: what kind of doc is this, where does this doc belong, split this document, review this doc's placement, check this markdown, is this a tutorial or a how-to guide. Not for: ADRs and decision records, commit messages, changelogs and release notes, code comments and docstrings, CLAUDE.md and agent or tool config. Checks mode, placement, and markdown form only, never factual accuracy."
disable-model-invocation: false
metadata:
  author: Backchain
  version: 1.0.0
---

# Docs

Route one document to the mode it belongs in, write it under that mode's constraints, then check its markdown form.

The unit of work is one document and one next action. This skill does not plan a documentation set top-down, does not audit a whole `docs/` tree in one pass, and does not produce an outline for a future set of pages.

Two paths share the same routing step: writing a new document (the write path) and assessing one that already exists (the place path). Both start at the compass below, and both end at the same markdown-form check.

## Where this does not apply

Diataxis governs product documentation written for a user. It does not govern everything that happens to be a markdown file in a repository.

Check the request against this table before routing anything:

| Out of scope | Why |
|---|---|
| ADRs and decision records | A dated historical artifact, not one of the four modes |
| Commit messages, PR descriptions | Not user documentation |
| Changelogs, release notes | Chronological by nature; no mode applies |
| Code comments and docstrings | Belong to the code, not the documentation set |
| `CLAUDE.md`, agent and tool config | Instructions to a machine, not a user |

When the request names one of these, say which row applies and stop before opening the compass.

None of the four modes fits an artifact that is fundamentally dated, historical, or machine-facing.

READMEs are in scope: advise on README structure when asked (trim it, reorder it, link out more aggressively), but never propose extracting its parts into separate mode documents the way this skill would for a contaminated tutorial or how-to guide. A README is a landing page and legitimately hybrid.

### When scope is ambiguous

- A design doc that reads like project history belongs with ADRs, even if nobody labeled it one.
- A "docs" folder that turns out to hold internal runbooks for the team, not instructions for a product user, is out of scope until the request is reframed around an external reader.
- A file named `NOTES.md` sitting next to code is closer to a code comment than to any of the four modes; ask what reader it serves before routing it.

## The compass

Two questions settle a document's mode. Ask both, in order, before writing or moving anything, and answer them about the document itself, not about the topic it covers.

1. Does the reader need to *learn* a skill, or *apply* one they already have?
2. Does the document *walk the reader through doing something*, or *build their understanding*?

| Reader needs to... | ...and the document... | ...is a |
|---|---|---|
| learn a skill | walks them through doing it | tutorial |
| apply a skill they have | walks them through doing it | how-to guide |
| apply a skill they have | builds their understanding | reference |
| learn a skill | builds their understanding | explanation |

Both the write path and the place path start here. One pair of answers settles the mode either way: for a document not yet written, it names what to draft; for a document that already exists, it names what to check the current text against.

The same topic can produce all four documents. A configuration system alone can support:

- a tutorial that walks a newcomer through configuring one thing for the first time
- a how-to guide that gets a competent user through one specific configuration task
- a reference that lists every configuration field
- an explanation of why the configuration system is shaped the way it is

The compass routes the document, not the subject matter.

### Example requests mapped to a mode

| Request | Answer to Q1 | Answer to Q2 | Mode |
|---|---|---|---|
| "Walk a new user through their first setup" | learn | walks through | tutorial |
| "Show how to rotate an API key" | apply | walks through | how-to guide |
| "List every CLI flag and its default" | apply | builds understanding | reference |
| "Explain why we chose polling over webhooks" | learn | builds understanding | explanation |

Ask the two questions rather than pattern-matching on a single verb in the request; "explain" appears in both the reference row and the explanation row above, and the compass, not the word, decides which.

If a request doesn't land cleanly in one cell (it wants both a walkthrough and a rationale in the same document, or both a lookup table and a lesson), that is two documents, not one document straddling two cells. Name both, draft the one the requester needs first, and say explicitly that the second exists as separate follow-up work rather than silently folding it into the first.

### Reading the compass in reverse

The place path runs the same two questions against a document that already exists, rather than against a request:

1. Read the document's opening paragraph and ask whether it is teaching a skill or assuming one.
2. Read the body and ask whether it is narrating actions or describing facts.

A document whose opening paragraph assumes competence but whose body narrates a fixed sequence of actions answers "apply" and "walks through": a how-to guide, whatever its filename claims. When the two answers disagree with the document's current label or location, the label or location is what moves, not the compass.

If the two questions still don't produce a confident answer after one read-through, name the ambiguity to the requester rather than guessing: "this reads as either a how-to or a reference depending on whether the parameter list is the point or an aside" is a useful handoff, a silent guess is not.

### Frequently confused pairs

| Pair | Discriminating test |
|---|---|
| tutorial vs how-to guide | Is the reader learning, or already competent and just working? |
| how-to guide vs reference | Does the reader want a sequence of actions, or a fact to look up? |
| reference vs explanation | Is the reader mid-task looking something up, or away from the work building understanding? |
| explanation vs tutorial | Does the document ask the reader to do something and watch it work, or to sit with an idea? |

## Write path

1. Answer the compass's two questions for the document at hand. The answer names exactly one mode.
2. Load exactly one mode reference from `${CLAUDE_SKILL_DIR}/references/` (see References below).
3. Draft under that mode's key principles.
4. Name the file and write its frontmatter, loading `${CLAUDE_SKILL_DIR}/references/frontmatter.md` (see Document identity below).
5. Run the self-check before emitting (see Self-check before emitting below).
6. Emit the document, or stop and report per Escalation.

Loading more than one mode file before drafting mixes their constraints together, which is the failure this skill exists to prevent. If the compass answer feels uncertain, resolve it by re-reading the compass table, not by loading a second mode file to compare.

The loaded mode file states that mode's `## Key principles` and its `## Shape on the page`; draft under both.

### Document identity

Sourced to NARA Bulletin 2015-04, Appendix B. Every emitted file's name follows:

```
{type}_{subject}[_{qualifier}].md
```

Lowercase only. Hyphens separate words within a semantic field; underscores separate semantic fields. Nothing outside `[a-z0-9._-]`.

- **Living pages carry no date in the file name.** Dates live in `created` and `updated` instead: a renamed file breaks every inbound link and every cached retrieval chunk.
- **Immutable records are the sole exception** and take a trailing ISO 8601 date field: `release-notes_2026-07-24.md`.
- **The file name stem equals the frontmatter `id`.** Renaming an emitted file follows the `aliases` rule in `references/frontmatter.md`.

### Common misroutes

| Draft opens with... | Looks like | Actually belongs in |
|---|---|---|
| "In this guide you'll build..." with reassurance | tutorial framing | tutorial only if the reader is a newcomer |
| A numbered list assuming prior competence | how-to steps | how-to guide, not a tutorial |
| A complete table of every flag | reference | reference, not folded into a how-to |
| "The reason we designed it this way..." | explanation | explanation, not folded into reference |
| A worked example after a table of fields | reference drifting toward how-to | split into reference plus a linked how-to |
| A history of past API versions | explanation drifting into changelog territory | explanation if forward-looking; changelog if purely chronological |

### Mid-draft mode drift

If drafting surfaces material that belongs to a different mode (a how-to draft accumulating paragraphs of rationale between steps, a reference draft accumulating a worked example at the bottom), stop adding it to the current document mid-draft. Note it as a candidate for a second document in the mode it actually belongs to, per the compass, rather than absorbing it into the one already in progress. The moment to catch this is while drafting, not after the document ships and needs the place path applied to it retroactively.

## Self-check before emitting

This gate runs when a file is about to be written. The place path emits no file and does not run it. Verify nine items in order; any failure stops emission and names the failing item.

1. Compass applied, one type, mode boundaries respected.
2. File name matches the pattern in `### Document identity` above and equals `id`. Any new directory is created only in the same action that writes this document into it.
3. All required frontmatter present, types correct, dates ISO 8601.
4. Provenance complete if machine-authored.
5. No placeholder text remains: no `{curly braces}`, no `TBD`, no `TODO`, no lorem.
6. Every `##` opens by naming its own subject.
7. Body parses under CommonMark 0.31.2 plus GFM tables, nothing else.
8. All code fences carry a language and are complete.
9. All links inline and resolvable.

Run `${CLAUDE_SKILL_DIR}/scripts/check_markdown.py` on the drafted body and treat exit 1 as a stop, naming the failing check and line. The linter covers part of item 7 (unclosed fence, heading hash runs, backtick in an info string, trailing double-space) and part of item 9 (unresolved reference links, advisory), and **none** of item 8: it never checks whether an info string is present. It also does not flag raw HTML. Those remainders are verified by reading. Advisory findings do not change the exit code, and the pipe-table advisory is expected here because GFM tables are permitted.

## Escalation

Stop and report rather than guess when:

- the correct Diátaxis type is genuinely ambiguous (see the compass's ambiguity guidance above)
- a required frontmatter value is unknown after applying the sibling-resolution rule in `references/frontmatter.md`
- a reference file would need to be hand-authored because no machine-readable source exists
- the source code contradicts an existing published page
- the request would require violating a rule above

## Place path

Assess one existing document against its apparent mode, then decide a single next action. This is a per-document check, not a directory sweep: pick the one document in question, run the compass against it once, and work only against that document.

The highest-value check is contamination: a passage that belongs to a mode other than the document's own. Contamination is what turns a clean how-to into a page a competent reader has to wade through to find the actual steps, and what turns a tutorial into a lesson interrupted by a menu of options the newcomer isn't ready to evaluate yet.

| Mode leaking in | Tells that betray it | Move it to |
|---|---|---|
| tutorial | beginner's-first-run framing, reassurance, teaching asides, one path narrated as a lesson | its own tutorial |
| how-to guide | goal-directed numbered steps for an already-competent reader, "to do X, do Y", task setup | its own how-to guide |
| reference | exhaustive option, flag, parameter or field enumerations, signatures, complete tables | its own reference page |
| explanation | why, because, the reason, history, alternatives considered, trade-offs, opinion, analogy | its own explanation page |

Read this table two ways:

- Reading down the "Tells that betray it" column spots a contaminant inside a document under review: a reference page with three paragraphs of "the reason this default exists is..." is leaking explanation.
- Reading across from that row to "Move it to" names the contaminant's proper home once it's been spotted: that passage belongs on its own explanation page, not deleted and not left in place.

When a document serves two modes, propose a split that extracts the foreign material into its own document and links back to it, not a rewrite of the original in place.

### Signs a document already fits its mode

- A tutorial with no branch points and a stated result at each step needs no split.
- A how-to guide whose steps are all in the imperative mood, with no aside longer than one sentence, needs no split.
- A reference page whose every paragraph is a declarative fact about the system, with zero instances of "because," needs no split.
- An explanation page with no numbered action list anywhere in it needs no split.

### Worked split example

A how-to page titled "Rotate an API key" opens with three paragraphs on why key rotation matters, then five numbered steps.

- Before: one document, steps buried below rationale.
- After: the how-to keeps only its five numbered steps, opens with one link instead of three paragraphs.
- After: a new explanation page, "Why rotate API keys", carries the three paragraphs, linked from the how-to's opening line.
- The reader who wants the steps sees them first; the reader who wants the rationale follows the link.

A second case: a tutorial titled "Your first deployment" spends two paragraphs mid-walkthrough listing every deployment target the platform supports.

- Before: one document, the newcomer's single path interrupted by an options table meant for a different reader.
- After: the tutorial keeps its one path to one target, with a single line noting other targets exist.
- After: a new reference page lists every deployment target, linked from that single line.

### Checklist before proposing a split

- The contaminated passage is named and quoted or summarized, not just flagged as "some rationale in here somewhere."
- A destination document and its mode are named for the extracted passage.
- The link text that will replace the extracted passage is drafted.
- The original document's remaining content still stands alone and makes sense without the extracted part.
- The requester has confirmed before any file actually moves.

Propose the split; do not execute a large restructuring uninvited on a document nobody asked to have rewritten. A place-path assessment can end in a recommendation with no file changes at all, if that's what's asked for.

### Never-scaffold

> Create a directory only in the same action that writes a document into it.

A request to set up a docs folder ahead of content becomes a request to defer the directory's creation until there is a document ready to go into it.

## What this skill does not check

This skill checks three things: mode, placement, and markdown form. It does not check whether the content is accurate, complete, or current.

A document can pass every check here and still be wrong:

- Routed to reference, structured perfectly, describing a flag that was removed last release.
- Routed to how-to, steps in the right order, pointing at an endpoint that no longer exists.
- Routed to tutorial, one clean path, ending in a result the current version of the software no longer produces.
- Routed to explanation, well-bounded to one topic, giving a rationale that stopped being true after the last redesign.

Factual review is a separate pass, done by whoever currently knows the true behavior of the thing being documented, and it stays out of scope here regardless of how confidently a draft reads or how cleanly it routes.

This skill also does not check tone, brand voice, translation quality, or accessibility. Those are legitimate reviews; they belong to other passes, not to mode, placement, and form.

## References

- `${CLAUDE_SKILL_DIR}/references/tutorial.md`: load when the compass points to tutorial, drafting or reviewing a learning-by-doing walkthrough.
- `${CLAUDE_SKILL_DIR}/references/how-to.md`: load when the compass points to how-to guide, drafting or reviewing a goal-directed task sequence.
- `${CLAUDE_SKILL_DIR}/references/reference.md`: load when the compass points to reference, drafting or reviewing a lookup page.
- `${CLAUDE_SKILL_DIR}/references/explanation.md`: load when the compass points to explanation, drafting or reviewing a discussion page.
- `${CLAUDE_SKILL_DIR}/references/commonmark.md`: load for any markdown-form question, in either path, independent of which mode file loaded.
- `${CLAUDE_SKILL_DIR}/references/frontmatter.md`: load on the write path whenever a file is about to be emitted, for the field table and its rules (see Document identity above).

Exactly one mode reference loads per routing decision; loading a second before the first draft or assessment is finished is itself a sign the compass questions weren't fully answered yet, and the fix is to return to the compass, not to keep reading. `commonmark.md` and `frontmatter.md` are not mode references: each loads independently of mode, whenever its own question is at hand rather than the compass's.
