# CommonMark form

This is the authoring reference for markdown form in this repository, checked against the CommonMark 0.31.2 specification at https://spec.commonmark.org/0.31.2/.

## Rules

Each row states the rule in original wording (not quoted from the spec) and the authoring pitfall the rule prevents. Section numbers refer to the CommonMark 0.31.2 spec.

| Section | Rule | Pitfall it prevents |
|---|---|---|
| 2.2 | A tab advances to the next tab stop at a multiple of 4 columns; it is not expanded to a fixed number of spaces. | Tab-indented content shifts to an unintended tab stop, changing whether it lands inside or outside a list item or code block. |
| 2.4 | A backslash before an ASCII punctuation character produces that character literally, removing its markup meaning. | An unescaped punctuation character (such as `*` or `_`) gets parsed as emphasis or another construct instead of appearing as plain text. |
| 4.1 | A line of three or more matching `-`, `_`, or `*` characters, with optional spaces or tabs between them, forms a thematic break. | A `---` line placed directly under a text line parses as a setext heading underline instead of a rule. |
| 4.2 | The opening run of an ATX heading is 1 to 6 `#` characters and must be followed by a space or tab (or the end of the line); a run of more than six is not a heading. | `#tag` renders as literal text because no space follows the hash, and `#######` renders as a paragraph, not a heading. |
| 4.3 | A paragraph immediately followed by a line of one or more `=` characters becomes a level-1 heading; followed by a line of `-` characters, a level-2 heading. | An underline typed under a plain paragraph turns it into a heading the author did not intend. |
| 4.4 | A line indented four or more spaces (or an equivalent tab) that is not part of a list item or other container starts an indented code block. | Four-space indentation, used for visual alignment rather than code, silently becomes a code block. |
| 4.5 | A fenced code block's closing fence must contain at least as many backtick or tilde characters as the opening fence, and a backtick-delimited info string may not itself contain a backtick. | An unclosed or too-short closing fence pulls the rest of the document into the code block. |
| 4.7 | A link reference definition supplies a destination and optional title for a label; reference-style links elsewhere in the document resolve against that label. | A reference link with no matching definition renders as literal bracket text instead of a link. |
| 5.2 | Content after a list item's first line stays part of that item only when indented to the column where the item's content begins, past the marker and its following whitespace. | Inconsistent continuation indentation drops a nested item out of its parent list, flattening the structure. |
| 5.3 | Changing the bullet character or the delimiter style of an ordered list starts a new list; a list is loose (paragraphs get spacing) if a blank line separates any of its items, tight otherwise. | Switching marker mid-list splits it into two lists unintentionally; an incidental blank line converts a tight list to a loose one, adding paragraph spacing throughout. |
| 6.1 | A code span opens and closes with backtick strings of equal length; the first later backtick string of that same length closes it. | A code span fails to close where intended when the surrounding text contains a shorter or differently placed backtick run. |
| 6.7 | A hard line break is produced by ending a line with two or more trailing spaces, or by ending it with a backslash. | Two trailing spaces are invisible in a diff or review pass and many editors strip trailing whitespace on save, so the break silently disappears; a trailing backslash survives both. |

## Examples

A short example for each of the trickiest rules above shows the failure mode directly.

**ATX heading missing a space (4.2):**

```markdown
##Not a heading
## A heading
```

The first line renders as a paragraph starting with `##`; the second renders as a heading, because a space follows the hash run.

**Setext heading created by an adjacent underline (4.1, 4.3):**

```markdown
Status
------
```

Without a blank line separating them, `Status` becomes a level-2 heading. A blank line before `------` makes it a paragraph followed by a thematic break instead.

**Fenced code block with a too-short closing fence (4.5):**

````markdown
```python
def f():
    return 1
``
Still inside the code block.
```
````

The two-backtick line does not close a three-backtick opening fence, so the following prose line stays inside the code block along with it.

**List marker changed mid-list (5.3):**

```markdown
- one
- two
* three
```

The `*` on the third item does not continue the first list; it starts a second, separate list.

**Hard line break by backslash instead of trailing spaces (6.7):**

```markdown
First line\
Second line
```

The trailing backslash forces a line break inside one paragraph. Two trailing spaces do the same, but the spaces are easy to lose to an editor's trim-on-save and invisible in a diff.

**Unmatched link reference definition (4.7):**

```markdown
See the [style guide][style].
```

Without a `[style]: <url>` definition elsewhere in the document, this renders as the literal text `[style guide][style]` rather than a link.

## Tables

CommonMark 0.31.2 defines no table syntax. The pipe-delimited table (`| a | b |` with a `---` separator row) is a GitHub Flavored Markdown extension layered on top of the base spec, not part of it. Writing a pipe table is a deliberate choice to depend on GFM rather than CommonMark alone. Before using one, confirm the rendering target (GitHub, a static-site generator, a docs pipeline) implements the GFM table extension; a renderer that only implements base CommonMark prints the pipes and dashes as plain text instead of a table.

## Authoring pitfalls

These recur in agent-generated markdown, and each maps to a rule above:

- An unclosed or too-short closing fence (4.5) absorbs everything after it into one code block, including headings and prose that follow.
- A heading hash with no following space or tab (4.2) renders as a literal `#word` instead of a heading.
- Four-space indentation applied to prose for visual effect (4.4) turns that prose into a code block instead of an indented paragraph.
- A trailing double-space line break (6.7) does not survive a review pass or an editor's trim-on-save; write a trailing backslash instead when a hard break is intended.

## Scope note

Severity assignment for violations of these rules, and the `check_markdown.py` linter that checks for them, land in issue #19. This file is the authoring reference: it states the rules and the pitfalls they prevent, not how a linter scores or reports them.
