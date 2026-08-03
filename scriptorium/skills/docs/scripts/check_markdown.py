#!/usr/bin/env python3
"""A CommonMark 0.31.2 authoring linter.

This is not a CommonMark parser. It does not build a document tree and does
not resolve every construct the spec defines. It is a line-based scanner for
the specific authoring pitfalls that recur in agent-generated markdown, each
one traceable to a section of the spec at https://spec.commonmark.org/0.31.2/.

Python 3 standard library only. No third-party imports, no install step.
Run `python3 check_markdown.py --llms` for a machine-readable self-description.
"""

from __future__ import annotations

import argparse
import enum
import re
import sys
from dataclasses import dataclass

PROG_NAME = "check_markdown.py"


# --------------------------------------------------------------------------
# Requirement 1: fence-state scanner. Built and tested before any check
# below. Every check that follows runs only on lines outside a fence, so a
# shell script, a C header, or a tab-indented Makefile rule inside a fenced
# block never trips the ATX heading, tab, or indentation checks.
# --------------------------------------------------------------------------

_OPEN_FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
_CLOSE_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")


@dataclass(frozen=True)
class Fence:
    """One fenced code block, open or closed, discovered by `scan_fences`."""

    start_line: int
    char: str
    length: int
    info_string: str
    end_line: int | None


def scan_fences(lines: list[str]) -> tuple[list[Fence], set[int]]:
    """Track fenced code blocks per CommonMark 4.5.

    An opening fence is 3+ backtick or tilde characters, indented 0-3
    spaces. A closing fence uses the same character, is at least as long as
    the opening fence, is indented 0-3 spaces, and carries no info string; a
    shorter run does not close the block, and a tilde fence is never closed
    by a backtick run or vice versa. A fence still open at end of file is
    unclosed and swallows every line after it.

    Returns the list of fences found (closed or not) and the set of 1-indexed
    line numbers that fall inside a fence, including both delimiter lines.
    Indented (non-fenced) code blocks are deliberately not tracked here: that
    would collide with the "heading indented 4+ spaces" advisory check, which
    depends on seeing those lines.
    """
    fences: list[Fence] = []
    fenced_lines: set[int] = set()

    open_start: int | None = None
    open_char = ""
    open_length = 0
    open_info = ""

    for index, raw_line in enumerate(lines):
        lineno = index + 1

        if open_start is None:
            match = _OPEN_FENCE_RE.match(raw_line)
            if match:
                fence_run = match.group(2)
                open_start = lineno
                open_char = fence_run[0]
                open_length = len(fence_run)
                open_info = match.group(3).strip()
                fenced_lines.add(lineno)
            continue

        fenced_lines.add(lineno)
        close_match = _CLOSE_FENCE_RE.match(raw_line)
        if close_match:
            close_run = close_match.group(1)
            if close_run[0] == open_char and len(close_run) >= open_length:
                fences.append(
                    Fence(
                        start_line=open_start,
                        char=open_char,
                        length=open_length,
                        info_string=open_info,
                        end_line=lineno,
                    )
                )
                open_start = None
                open_char = ""
                open_length = 0
                open_info = ""

    if open_start is not None:
        fences.append(
            Fence(
                start_line=open_start,
                char=open_char,
                length=open_length,
                info_string=open_info,
                end_line=None,
            )
        )

    return fences, fenced_lines


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


class Severity(str, enum.Enum):
    ERROR = "error"
    ADVISORY = "advisory"


@dataclass(frozen=True, order=True)
class Finding:
    """One reported pitfall. Sortable by (file, line, severity, section)."""

    file: str
    line: int
    severity: Severity
    section: str
    message: str


# --------------------------------------------------------------------------
# Requirement 2: the ten checks. Error severity fails the run; advisory
# severity never does.
# --------------------------------------------------------------------------

# --- Errors ---------------------------------------------------------------


def check_unclosed_fences(fences: list[Fence], filename: str) -> list[Finding]:
    """4.5: a fence never closed by a same-or-longer matching run."""
    findings = []
    for fence in fences:
        if fence.end_line is None:
            findings.append(
                Finding(
                    file=filename,
                    line=fence.start_line,
                    severity=Severity.ERROR,
                    section="4.5",
                    message=(
                        "Fence opened here is never closed by a matching "
                        "same-or-longer run; it swallows the rest of the "
                        "document."
                    ),
                )
            )
    return findings


def check_backtick_info_string(fences: list[Fence], filename: str) -> list[Finding]:
    """4.5: a backtick-fenced info string may not itself contain a backtick."""
    findings = []
    for fence in fences:
        if fence.char == "`" and "`" in fence.info_string:
            findings.append(
                Finding(
                    file=filename,
                    line=fence.start_line,
                    severity=Severity.ERROR,
                    section="4.5",
                    message=(
                        "Backtick-fenced info string contains a backtick, "
                        "which CommonMark disallows; this is not a valid "
                        "fenced code block."
                    ),
                )
            )
    return findings


_HEADING_SHAPE_RE = re.compile(r"^( *)(#+)(.*)$")


def check_headings(
    lines: list[str], fenced_lines: set[int], filename: str
) -> list[Finding]:
    """4.2 (error) and 4.4 (advisory) heading shape checks, combined.

    A 1-6 `#` run followed by anything other than a space, tab, or end of
    line is not a heading (error). A 7+ `#` run followed by a space or end
    of line is also not a heading (error), because ATX headings cap at six.
    A bare `#` (or any hash run) with nothing following it is a valid,
    empty heading and is never flagged. The same heading-shaped text
    indented 4 or more spaces becomes an indented code block rather than a
    heading; that is advisory, since it is legitimate as a list
    continuation.
    """
    findings = []
    for index, line in enumerate(lines):
        lineno = index + 1
        if lineno in fenced_lines:
            continue
        match = _HEADING_SHAPE_RE.match(line)
        if not match:
            continue
        indent, hashes, rest = match.groups()
        indent_len = len(indent)
        count = len(hashes)
        followed_ok = rest == "" or rest[0] in (" ", "\t")

        if indent_len <= 3:
            if count <= 6:
                if not followed_ok:
                    findings.append(
                        Finding(
                            file=filename,
                            line=lineno,
                            severity=Severity.ERROR,
                            section="4.2",
                            message=(
                                f"ATX heading marker '{hashes}' is not "
                                "followed by a space, tab, or end of line; "
                                "renders as literal text, not a heading."
                            ),
                        )
                    )
            elif followed_ok:
                findings.append(
                    Finding(
                        file=filename,
                        line=lineno,
                        severity=Severity.ERROR,
                        section="4.2",
                        message=(
                            f"{count} '#' characters is more than the six "
                            "an ATX heading allows; not a heading."
                        ),
                    )
                )
        elif count <= 6 and followed_ok:
            findings.append(
                Finding(
                    file=filename,
                    line=lineno,
                    severity=Severity.ADVISORY,
                    section="4.4",
                    message=(
                        f"Heading indented {indent_len} spaces; renders as "
                        "an indented code block, not a heading."
                    ),
                )
            )
    return findings


_TRAILING_SPACES_RE = re.compile(r"  +$")


def check_trailing_hard_break(
    lines: list[str], fenced_lines: set[int], filename: str
) -> list[Finding]:
    """6.7: two or more trailing spaces on a non-blank line followed by a
    non-blank line is an invisible hard line break that a trim-on-save
    silently removes. Trailing spaces on a blank line, or at end of file,
    are not a hard break and are not flagged.
    """
    findings = []
    for index in range(len(lines) - 1):
        lineno = index + 1
        if lineno in fenced_lines:
            continue
        line = lines[index]
        if not _TRAILING_SPACES_RE.search(line):
            continue
        if line.strip() == "":
            continue
        next_line = lines[index + 1]
        if next_line.strip() == "":
            continue
        findings.append(
            Finding(
                file=filename,
                line=lineno,
                severity=Severity.ERROR,
                section="6.7",
                message=(
                    "Line ends with two or more trailing spaces; renders as "
                    "a hard line break that a trim-on-save silently removes."
                ),
            )
        )
    return findings


# --- Advisories -------------------------------------------------------------


_LEADING_WS_RE = re.compile(r"^[ \t]*")


def check_tab_indentation(
    lines: list[str], fenced_lines: set[int], filename: str
) -> list[Finding]:
    """2.2: a tab in a line's leading whitespace, outside a fence."""
    findings = []
    for index, line in enumerate(lines):
        lineno = index + 1
        if lineno in fenced_lines:
            continue
        leading = _LEADING_WS_RE.match(line).group(0)
        if "\t" in leading:
            findings.append(
                Finding(
                    file=filename,
                    line=lineno,
                    severity=Severity.ADVISORY,
                    section="2.2",
                    message=(
                        "Line indented with a tab; a tab advances to the "
                        "next 4-column stop rather than a fixed width."
                    ),
                )
            )
    return findings


_BULLET_RE = re.compile(r"^([ \t]*)([-*+])(?:[ \t]|$)")
_ORDERED_RE = re.compile(r"^([ \t]*)(\d{1,9})([.)])(?:[ \t]|$)")
_HEADING_LINE_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
_THEMATIC_BREAK_RE = re.compile(r"^ {0,3}([-_*])[ \t]*(?:\1[ \t]*){2,}$")


def check_list_markers(
    lines: list[str], fenced_lines: set[int], filename: str
) -> list[Finding]:
    """5.3: a bullet character or ordered delimiter change between adjacent
    items at the same indent level silently starts a new list. Bullet-family
    and ordered-family are tracked separately per indent level, so a switch
    from a bullet list to an ordered list (an intentional, ordinary
    transition) is never flagged; only a change within the same family is.
    """
    findings: list[Finding] = []
    current: dict[int, tuple[str, str]] = {}

    for index, line in enumerate(lines):
        lineno = index + 1
        if lineno in fenced_lines:
            continue

        if _HEADING_LINE_RE.match(line) or _THEMATIC_BREAK_RE.match(line):
            current.clear()
            continue

        if line.strip() == "":
            continue

        bullet_match = _BULLET_RE.match(line)
        ordered_match = None if bullet_match else _ORDERED_RE.match(line)

        if bullet_match:
            indent = len(bullet_match.group(1))
            kind = "bullet"
            marker = bullet_match.group(2)
        elif ordered_match:
            indent = len(ordered_match.group(1))
            kind = "ordered"
            marker = ordered_match.group(3)
        else:
            if not line[0].isspace():
                current.clear()
            continue

        for deeper in [level for level in current if level > indent]:
            del current[deeper]

        previous = current.get(indent)
        if previous is not None and previous[0] == kind and previous[1] != marker:
            findings.append(
                Finding(
                    file=filename,
                    line=lineno,
                    severity=Severity.ADVISORY,
                    section="5.3",
                    message=(
                        f"List marker changed from '{previous[1]}' to "
                        f"'{marker}' mid-list; CommonMark starts a new list "
                        "here."
                    ),
                )
            )
        current[indent] = (kind, marker)

    return findings


_CODE_SPAN_RE = re.compile(r"`+.*?`+")
_FULL_OR_COLLAPSED_REF_RE = re.compile(r"\[([^\]\n]+)\]\[([^\]\n]*)\]")
_DEFINITION_RE = re.compile(r"^ {0,3}\[([^\]\n]+)\]:\s*\S")


def _normalize_label(label: str) -> str:
    """Case-fold and collapse internal whitespace, per CommonMark 4.7."""
    return " ".join(label.split()).casefold()


def _collect_reference_definitions(
    lines: list[str], fenced_lines: set[int]
) -> set[str]:
    labels = set()
    for index, line in enumerate(lines):
        lineno = index + 1
        if lineno in fenced_lines:
            continue
        match = _DEFINITION_RE.match(line)
        if match:
            labels.add(_normalize_label(match.group(1)))
    return labels


def check_unresolved_references(
    lines: list[str], fenced_lines: set[int], filename: str
) -> list[Finding]:
    """4.7: a full `[text][ref]` or collapsed `[ref][]` reference link with
    no matching `[ref]: dest` definition renders as literal bracket text.

    Narrowed to these two forms only. The bare `[text]` shortcut form is
    ordinary literal text most of the time and collides with code spans,
    array indexing, wikilinks, and footnotes, so it is never flagged.
    Inline code spans are stripped before scanning, so a code sample like
    `` `list[key][0]` `` is not mistaken for a reference link.
    """
    definitions = _collect_reference_definitions(lines, fenced_lines)
    findings = []
    for index, line in enumerate(lines):
        lineno = index + 1
        if lineno in fenced_lines:
            continue
        stripped = _CODE_SPAN_RE.sub("", line)
        for match in _FULL_OR_COLLAPSED_REF_RE.finditer(stripped):
            text, label = match.group(1), match.group(2)
            resolved_label = label if label else text
            if _normalize_label(resolved_label) in definitions:
                continue
            findings.append(
                Finding(
                    file=filename,
                    line=lineno,
                    severity=Severity.ADVISORY,
                    section="4.7",
                    message=(
                        f"Reference link '[{text}][{label}]' has no "
                        f"matching '[{resolved_label}]: ...' definition."
                    ),
                )
            )
    return findings


_TABLE_SEPARATOR_RE = re.compile(
    r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$"
)


def check_pipe_tables(
    lines: list[str],
    fenced_lines: set[int],
    filename: str,
    strict_commonmark: bool,
) -> list[Finding]:
    """No CommonMark section: 0.31.2 defines no table syntax at all. A pipe
    table (a header row followed by a `---`-style separator row) is a
    GitHub Flavored Markdown extension layered on top of the base spec.

    Advisory by default, because every SKILL.md in this repository and all
    of scriptorium's own references use pipe tables; an error default would
    make this linter fail its own shipped files. `--strict-commonmark`
    promotes it to an error.
    """
    findings = []
    severity = Severity.ERROR if strict_commonmark else Severity.ADVISORY
    for index in range(len(lines) - 1):
        lineno = index + 1
        if lineno in fenced_lines or (lineno + 1) in fenced_lines:
            continue
        header = lines[index]
        separator = lines[index + 1]
        if "|" not in header or header.strip() == "":
            continue
        if not _TABLE_SEPARATOR_RE.match(separator):
            continue
        findings.append(
            Finding(
                file=filename,
                line=lineno,
                severity=severity,
                section="n/a",
                message=(
                    "Pipe table detected; CommonMark 0.31.2 defines no "
                    "table syntax (GitHub Flavored Markdown extension)."
                ),
            )
        )
    return findings


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


def lint_text(text: str, filename: str, strict_commonmark: bool = False) -> list[Finding]:
    """Run every check against one document's text and return its findings,
    sorted by (file, line, severity, section, message).
    """
    lines = text.splitlines()
    fences, fenced_lines = scan_fences(lines)

    findings: list[Finding] = []
    findings.extend(check_unclosed_fences(fences, filename))
    findings.extend(check_backtick_info_string(fences, filename))
    findings.extend(check_headings(lines, fenced_lines, filename))
    findings.extend(check_tab_indentation(lines, fenced_lines, filename))
    findings.extend(check_trailing_hard_break(lines, fenced_lines, filename))
    findings.extend(check_list_markers(lines, fenced_lines, filename))
    findings.extend(check_unresolved_references(lines, fenced_lines, filename))
    findings.extend(
        check_pipe_tables(lines, fenced_lines, filename, strict_commonmark)
    )
    findings.sort()
    return findings


def lint_file(path: str, strict_commonmark: bool = False) -> list[Finding]:
    """Read one file (or stdin, for `-`) and lint it. Raises OSError or
    UnicodeDecodeError on an unreadable file; the caller reports that as a
    diagnostic and exits 2.
    """
    if path == "-":
        print(f"{PROG_NAME}: reading stdin", file=sys.stderr)
        text = sys.stdin.read()
        display_name = "<stdin>"
    else:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        display_name = path
    return lint_text(text, display_name, strict_commonmark=strict_commonmark)


def format_markdown(findings: list[Finding]) -> str:
    """Render findings as markdown: one table per file, grouped and ordered
    by the sort already applied in `lint_text`.
    """
    if not findings:
        return "No findings.\n"

    lines: list[str] = []
    current_file: str | None = None
    for finding in findings:
        if finding.file != current_file:
            if current_file is not None:
                lines.append("")
            lines.append(f"## {finding.file}")
            lines.append("")
            lines.append("| Line | Severity | Section | Message |")
            lines.append("|---|---|---|---|")
            current_file = finding.file
        lines.append(
            f"| {finding.line} | {finding.severity.value.upper()} | "
            f"{finding.section} | {finding.message} |"
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Requirement 3: CLI surface
# --------------------------------------------------------------------------

LLMS_DESCRIPTION = """\
# check_markdown.py

## Name and purpose
check_markdown.py: a CommonMark 0.31.2 authoring linter, Python 3 standard
library only, no install step. It flags the specific authoring pitfalls the
spec defines that are easy to write by accident and hard to spot by eye.

## What it does
- Tracks fenced code blocks first (backtick and tilde, per CommonMark 4.5)
  and runs every check below only on lines outside a fence.
- Reports five error-severity checks (fail the run): an unclosed or too-short
  closing fence (4.5), an ATX heading hash run with no following space (4.2),
  more than six leading '#' characters (4.2), a backtick in a backtick fence's
  info string (4.5), and a trailing double-space hard line break (6.7).
- Reports five advisory-severity checks (never fail the run): a heading
  indented four or more spaces (4.4), tab indentation (2.2), a list marker
  changed mid-list (5.3), an unresolved `[text][ref]` or `[ref][]` reference
  link (4.7), and a pipe table (no CommonMark section; a GFM extension).

## What it does not do
- It is not a CommonMark parser. It does not build a document tree, does not
  resolve every construct in the spec, and does not render markdown.
- It does not check prose quality, tone, accuracy, or link reachability.
- It does not flag the bare `[text]` shortcut reference form; that form is
  ordinary literal text most of the time and collides with code spans, array
  indexing, wikilinks, and footnotes.

## Input forms
- One or more file paths as positional arguments.
- `-` as a file argument reads that document from stdin (diagnostic
  "reading stdin" is written to stderr when this happens).
- Multiple files may be mixed with `-` in one invocation.

## Output format
- Findings render as a markdown table (or tables, one per file) on stdout.
  Columns: Line, Severity, Section, Message. "No findings." is printed on
  stdout when a run produces none.
- Diagnostics (an unreadable file, the checked/error/advisory counts, the
  stdin notice) are written to stderr, never to stdout.

## Flags
- `--strict-commonmark`: promotes the pipe-table advisory to an error.
- `--llms`: prints this self-description to stdout and exits 0.
- `-h` / `--help`: standard argparse usage.

## Exit-code contract
Exit codes key on errors only; advisory findings never change the exit code.
- 0: the run completed and produced zero error-severity findings (advisory
  findings may still be present).
- 1: the run completed and produced at least one error-severity finding.
- 2: the run could not complete (an unreadable file, or no input given).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=(
            "A CommonMark 0.31.2 authoring linter for the specific pitfalls "
            "the spec defines. Not a full parser."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Markdown file(s) to check. Use - to read one from stdin.",
    )
    parser.add_argument(
        "--strict-commonmark",
        action="store_true",
        help="Promote the pipe-table advisory to an error.",
    )
    parser.add_argument(
        "--llms",
        action="store_true",
        help="Print a machine-readable self-description and exit 0.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.llms:
        sys.stdout.write(LLMS_DESCRIPTION)
        return 0

    if not args.files:
        print(
            f"{PROG_NAME}: no input files given (pass a path, or - for stdin)",
            file=sys.stderr,
        )
        return 2

    all_findings: list[Finding] = []
    cannot_run = False

    for path in args.files:
        try:
            all_findings.extend(
                lint_file(path, strict_commonmark=args.strict_commonmark)
            )
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{PROG_NAME}: cannot read '{path}': {exc}", file=sys.stderr)
            cannot_run = True

    all_findings.sort()
    sys.stdout.write(format_markdown(all_findings))

    error_count = sum(1 for f in all_findings if f.severity is Severity.ERROR)
    advisory_count = len(all_findings) - error_count
    print(
        f"{PROG_NAME}: {len(args.files)} file(s) checked, "
        f"{error_count} error(s), {advisory_count} advisory finding(s)",
        file=sys.stderr,
    )

    if cannot_run:
        return 2
    if error_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
