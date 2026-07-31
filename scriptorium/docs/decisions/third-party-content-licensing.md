---
title: Third-Party Content Licensing (Diátaxis, CommonMark)
prepared_by: Claude (Sonnet 5)
updated: 2026-07-31T15:27:01-04:00
purpose: Record verified license findings for Diátaxis and the CommonMark spec, and the per-element decision to paraphrase rather than reproduce.
tags: []
aliases: []
---

# Third-Party Content Licensing (Diátaxis, CommonMark)

## Decision

scriptorium paraphrases both source frameworks in original wording rather than
reproducing their text. Short, explicitly marked quotations are permitted
where a design constraint needs direct support. Section numbers and names are
used freely as citations; a citation is not a reproduction.

## Context

scriptorium builds documentation-routing and markdown-validation skills on two
external frameworks: Diátaxis (routing logic) and the CommonMark 0.31.2
specification (markdown form). This repository distributes under Apache-2.0.
Issue #17 asked to verify the licensing of both sources before scriptorium's
skills reproduce any of their content, and to record the finding.

## License findings

### Diátaxis (https://diataxis.fr/)

Licensed under Creative Commons Attribution-ShareAlike 4.0 International
(CC-BY-SA-4.0). Licensor: Daniele Procida.

Authoritative source (license): [github.com/evildmp/diataxis-documentation-framework/blob/main/LICENSE.rst](https://github.com/evildmp/diataxis-documentation-framework/blob/main/LICENSE.rst),
the canonical source repository behind diataxis.fr. Its first line reads
"Creative Commons Attribution-ShareAlike 4.0 International". The file names
no copyright holder.

Authoritative source (licensor): [github.com/evildmp/diataxis-documentation-framework/blob/main/CITATION.cff](https://github.com/evildmp/diataxis-documentation-framework/blob/main/CITATION.cff)
(`given-names: Daniele`, `family-names: Procida`), corroborated by
[github.com/evildmp/diataxis-documentation-framework/blob/main/conf.py](https://github.com/evildmp/diataxis-documentation-framework/blob/main/conf.py)
line 21 (`copyright = "Daniele Procida"`).

Verified: 2026-07-31.

### CommonMark 0.31.2 specification (https://spec.commonmark.org/0.31.2/)

Licensed under Creative Commons Attribution-ShareAlike 4.0 International
(CC-BY-SA-4.0). Licensor: John MacFarlane.

Authoritative source: [github.com/commonmark/commonmark-spec/blob/0.31.2/LICENSE](https://github.com/commonmark/commonmark-spec/blob/0.31.2/LICENSE), the LICENSE file pinned to the 0.31.2 tag this record cites (also present, unpinned, on [master](https://github.com/commonmark/commonmark-spec/blob/master/LICENSE)), which states:

> The CommonMark spec (spec.txt) and DTD (CommonMark.dtd) are
>
> Copyright (C) 2014-16 John MacFarlane
>
> Released under the Creative Commons CC-BY-SA 4.0 license:
> <https://creativecommons.org/licenses/by-sa/4.0/>.

The same LICENSE file places the test software in `test/` and the programs in
`tools/` under BSD-2-Clause, and the normalization code in `runtests.py` under
MIT. scriptorium reproduces none of that code, only ideas drawn from the spec
text, so CC-BY-SA-4.0 is the license that governs here.

Verified: 2026-07-31.

### GitHub API discrepancy

GitHub's repository API reports `license: NOASSERTION` for both repositories.
This reflects GitHub's license classifier not recognizing these non-code
license files (a `.rst` file for Diátaxis, a LICENSE file mixing three
licenses by directory for CommonMark), not an absence of licensing terms. The
LICENSE file text quoted above is the authority, not the API field.

## Conflict: share-alike terms versus Apache-2.0 distribution

CC-BY-SA-4.0 section 3(b)(1) requires the Adapter's License applied to
Adapted Material to be "a Creative Commons license with the same License
Elements, this version or later, or a BY-SA Compatible License." This
repository distributes all its own content, including scriptorium's skills,
under Apache-2.0.

The BY-SA Compatible Licenses list was retrieved on 2026-07-31 at
[creativecommons.org/compatible-licenses](https://creativecommons.org/compatible-licenses/)
(the canonical URL that
[creativecommons.org/compatiblelicenses](https://creativecommons.org/compatiblelicenses)
redirects to). It names two licenses: GPLv3 and the Free Art License 1.3.
Apache-2.0 is neither a Creative Commons license with the same License
Elements, this version or later, nor one of the two licenses on that list.
Section 3(b)(1) requires an Adapter's License that is one of those two forms;
Apache-2.0 satisfies neither. Substantial verbatim reproduction of either
source, arranged as Adapted Material, would place BY-SA-obligated expression
inside an Apache-2.0 distribution under terms the two licenses do not
reconcile.

**This question is surfaced to the human for decision on issue #17. The
paraphrase-not-reproduce approach below is a conservative engineering
response to that finding, not a legal conclusion, and this record is not
legal advice. This record does not conclude what is legally permissible for
BY-SA and Apache-2.0 combinations in general, only what the two license texts
say for this specific pairing.**

## Per-element decisions

| Element | Decision | Rationale |
|---|---|---|
| Diátaxis compass table (the two-axis mode-routing table) | Paraphrase | Paraphrasing carries the routing structure without carrying upstream's wording. |
| Per-mode language markers | Paraphrase | Same as above: paraphrasing carries the classification without carrying upstream's phrasing. |
| Diátaxis principle and prohibition lists | Paraphrase | Restating the rules in original wording keeps the idea without carrying the BY-SA expression. |
| Short Diátaxis quotations that justify a design constraint | Permitted sparingly, marked as a quotation, with a source link | A short, attributed quotation used to support a stated constraint is a narrower use than reproducing structural content, and stays clearly sourced. |
| CommonMark spec rule statements (for example, an ATX heading's opening `#` run must be followed by a space or tab, or by end of line (4.2)) | Paraphrase; cite the section number (4.2 for ATX headings, 4.5 for fenced code blocks) instead of reproducing spec prose | The rule is a technical fact; the spec's prose describing it is BY-SA expression. Citing the section number over reproducing the sentence keeps the reference verifiable without carrying the expression. |
| CommonMark section numbers and names used as citations | Free to use | A citation identifies a source; it does not reproduce the source's expression. |

## Consequences

- scriptorium's skills will state routing logic and markdown rules in
  original wording, with citations to [diataxis.fr](https://diataxis.fr/) and
  [spec.commonmark.org/0.31.2](https://spec.commonmark.org/0.31.2/) by section
  where relevant.
- `NOTICE` at the repository root and `scriptorium/README.md` both carry
  attribution for the two frameworks: licensor, license, license URL, and
  authoritative source link.
- Any future skill draft that reproduces upstream table structure, list
  wording, or spec prose verbatim should be routed back to this record before
  merging.

## Revisit conditions

- Either upstream project changes its license.
- A future contribution needs a reproduction broader than the short,
  attributed quotations this record permits.
