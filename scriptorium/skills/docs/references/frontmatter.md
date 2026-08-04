# Frontmatter

Every document the write path emits opens with a YAML frontmatter block of durable fields. Unknown keys are rejected. Dates are ISO 8601. Strings are plain and unquoted unless YAML itself requires quoting.

Fields fall into three groups: required on every document, conditional on a stated trigger, and optional. Load this file whenever the write path is about to emit a file, independent of which mode reference loaded for drafting.

## Required fields

Present on every document, with no exception.

| Field | Type | Rule |
|---|---|---|
| `id` | string | Equals file name stem. Immutable. |
| `title` | string | Sentence case. Matches the `#` heading exactly. |
| `description` | string | One line, 320 characters maximum, no line break. States subject and reader benefit. |
| `type` | enum | `tutorial`, `how-to`, `reference`, `explanation` |
| `template` | string | Template applied. |
| `status` | enum | `draft`, `review`, `current`, `deprecated`, `superseded` |
| `audience` | string | Named reader role and assumed competence. |
| `applies_to` | string | Version or range of the documented artifact. |
| `created` | date | First merge date. |
| `updated` | date | Last substantive content change. |
| `owner` | string | Accountable human or team. |
| `tags` | list | Controlled vocabulary only. No free-text tags. |

## Conditional fields

Present when their trigger applies, absent otherwise.

| Field | Type | Rule |
|---|---|---|
| `source` | list | Repo-relative paths this file documents. Required when `type` is `reference`. |
| `source_commit` | string | Full SHA of the commit the content was derived from. Required when `generator` is present. |
| `generator` | string | Tool that produced the file. Required for any machine-authored content. |
| `model` | string | Model identifier. Required when `generator` is present. |
| `reviewed_by` | string | Human reviewer. Required before `status: current`. |
| `reviewed_on` | date | Required with `reviewed_by`. |

## Optional fields

Present when useful, never invented to fill a gap.

| Field | Type | Rule |
|---|---|---|
| `related` | list | Ids of companion files. |
| `aliases` | list | Retired ids that redirect here. |
| `supersedes` | string | Id of the file this replaces. |
| `superseded_by` | string | Id of the replacement. Required when `status: superseded`. |

## Rules

- **Machine-authored content declares provenance, or states why it cannot.** `generator`, `model`, and `source_commit` are mandatory together whenever the target is under version control: everything the skill writes is machine-authored, so the triple is the default. Where the target is not under version control and no commit resolves, all three are omitted as a unit rather than partially filled, and the omission is reported to the requester. Content whose `source_commit` is no longer an ancestor of the default branch is stale and must not be served as `current`.
- **No file reaches `status: current`** without `reviewed_by` and `reviewed_on`.
- **`description` is the retrieval surface.** It is what an index, an `llms.txt` entry, and a search result display. Write it to stand alone with no access to the body: one line, 320 characters maximum.
- **`template` names the project's template set.** When the project has none, `template`'s value is unknown, and unknown means escalate rather than invent.
- **Renaming writes `aliases`, not a redirect.** The `id` is immutable once merged; to rename, add the old id to `aliases`. The redirect itself is the publishing system's responsibility, not this skill's: where the project has no redirect mechanism, the rename escalates instead of being performed with a dangling obligation.
- **A required value the project has already established elsewhere is read from a sibling document, not treated as unknown.** Project-scope values (`owner`, `applies_to`, `template`, `audience`, and the `tags` vocabulary) describe the project, so a sibling in the same docs tree settles them. Every other field describes this document and is unknown until this document sets it, whatever a sibling carries. Where a sibling's value follows from a per-document property, copy the pattern rather than the value: a sibling reference page carrying `template: reference` establishes mode-named template sets, so a how-to takes `template: how-to`. Read the sibling's frontmatter once and resolve every project-scope value from that single read. Escalate on an unknown value only when no sibling settles it by either route.

## Example

```yaml
---
id: how-to_rotate-service-credentials
title: Rotate service credentials
description: Rotate a service account credential without downtime, covering issuance, dual-key overlap, and revocation of the retired key.
type: how-to
template: how-to
status: current
audience: Platform engineers with existing access to the secrets store.
applies_to: ">=2.4.0"
created: 2026-07-01
updated: 2026-07-24
owner: platform-team
tags: [security, credentials, operations]
reviewed_by: r.okonkwo
reviewed_on: 2026-07-24
related: [reference_credential-api, explanation_credential-lifecycle]
---
```
