---
title: Never-Scaffold Mode Trees
prepared_by: Claude (Sonnet 4.5)
updated: 2026-08-03T15:05:29-04:00
purpose: Record why scriptorium's docs skill treats mode-tree directory creation as a precondition on writing a document, not a prohibition or a sweep.
tags: []
aliases: []
---

# Never-Scaffold Mode Trees

## Decision

scriptorium's docs skill never creates an empty Diataxis mode tree (tutorial,
how-to guide, reference, explanation). It creates a directory only in the
same action that writes a document into it. This is the never-scaffold
precondition already carried in `scriptorium/skills/docs/SKILL.md`, in the
drafting checklist (line 129) and in its own "Never-scaffold" section (lines
186-190). This record states why the constraint exists.

## Source

The constraint traces to the source framework the docs skill implements, not
to an oversight in this plugin. Diataxis states the rule directly, in
`source/how-to-use-diataxis.rst` at line 35 of the framework's repository
([github.com/evildmp/diataxis-documentation-framework](https://github.com/evildmp/diataxis-documentation-framework)),
published at [diataxis.fr/how-to-use-diataxis](https://diataxis.fr/how-to-use-diataxis/),
licensed CC-BY-SA-4.0 by Daniele Procida:

> It certainly does not mean that you should create empty structures for
> tutorials/howto guides/reference/explanation with nothing in them. Don't do
> that. It's horrible.

The same passage states that getting started with Diataxis does not require
dividing documentation into four sections up front; the four-part structure
is an outcome of improving documentation, not a shape imposed on it before
any content exists.

This is the one quotation this record uses, kept short and attributed with a
source link, per the use `scriptorium/docs/decisions/third-party-content-licensing.md`
permits: "Short Diátaxis quotations that justify a design constraint |
Permitted sparingly, marked as a quotation, with a source link."

## Precondition framing, and why a prohibition was rejected

The constraint is written as a precondition on directory creation (create a
directory only in the same action that writes a document into it), not as a
prohibition (never create a docs/ folder). Three reasons favor the
precondition:

- A prohibition refuses a legitimate request outright. A precondition
  converts "set up a docs folder" into a deferral: the skill still serves the
  request, it waits until a document is ready to go into that folder.
  SKILL.md line 190 states this behavior.
- A prohibition leaves undefined what happens once a document is ready; the
  precondition covers the "not ready yet" case and the "ready now" case with
  one rule.
- A prohibition reaches past what the skill can observe: it cannot police
  directories it did not create. The precondition binds only the skill's own
  next action, which it can always evaluate before acting.

## Rejected alternative: full-tree reorganization

Sweeping an existing docs tree and sorting every document into
tutorial/how-to/reference/explanation directories in one pass was considered
and rejected:

- For any mode with no qualifying content, a sweep produces exactly the empty
  structure the source passage warns against.
- A sweep imposes the four-part structure before any document justifies it,
  inverting the source's ordering: structure follows improvement, not the
  reverse.
- A sweep executes a large restructuring nobody asked for. The skill's place
  path is per-document and confirmation-gated instead: SKILL.md line 136
  ("This is a per-document check, not a directory sweep"), line 182 ("The
  requester has confirmed before any file actually moves"), and line 184
  ("Propose the split; do not execute a large restructuring uninvited").

## Consequences

- The never-scaffold precondition appears twice in SKILL.md: once in the
  drafting checklist, once as its own named section.
- The place path stays per-document; the skill does not offer a
  directory-sweep mode.
- A request to set up a docs folder ahead of content is answered with a
  deferral, not a refusal and not an empty directory.
- A future contributor proposing a docs/ scaffolder, or a sweep-all-documents
  mode, should be routed to this record first.

## Revisit conditions

- The Diataxis source passage changes, or a later edition of the framework
  supersedes it.
- A future contribution needs to create a mode directory ahead of content for
  a reason this record does not anticipate (for example, a generated index
  file that must exist before any document does).
