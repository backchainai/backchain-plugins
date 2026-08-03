#!/usr/bin/env python3
"""Unit tests for check_markdown.py.

Stdlib `unittest` only, no third-party imports, no install step. Run from
this directory:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_check_markdown -v

All fixture and repo paths are resolved relative to `__file__`, never to the
process working directory, so the suite is safe to invoke from anywhere.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path


def _find_ancestor(start: Path, name: str) -> Path:
    """Walk up from `start` (inclusive) until a directory named `name`."""
    for candidate in (start, *start.parents):
        if candidate.name == name:
            return candidate
    raise RuntimeError(f"no ancestor directory named {name!r} above {start}")


SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTORIUM_DIR = _find_ancestor(SCRIPT_DIR, "scriptorium")
REPO_ROOT = SCRIPTORIUM_DIR.parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
SCRIPT_PATH = SCRIPT_DIR / "check_markdown.py"

# Make sure `import check_markdown` resolves regardless of the caller's cwd.
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_markdown as cm  # noqa: E402


def run_cli(
    args: list[str], input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run check_markdown.py as a subprocess with a clean, deterministic env."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        input=input_text,
        capture_output=True,
        text=True,
        env=env,
    )


# --------------------------------------------------------------------------
# 1. Fence-state scanner (load-bearing: every other check depends on it)
# --------------------------------------------------------------------------


class TestScanFences(unittest.TestCase):
    def test_backtick_fence_opens_and_closes(self):
        lines = ["```", "code", "```"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        fence = fences[0]
        self.assertEqual(fence.char, "`")
        self.assertEqual(fence.start_line, 1)
        self.assertEqual(fence.end_line, 3)
        self.assertEqual(fenced_lines, {1, 2, 3})

    def test_tilde_fence_opens_and_closes(self):
        lines = ["~~~", "code", "~~~"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        fence = fences[0]
        self.assertEqual(fence.char, "~")
        self.assertEqual(fence.end_line, 3)
        self.assertEqual(fenced_lines, {1, 2, 3})

    def test_shorter_closing_run_does_not_close(self):
        lines = ["````", "code", "```", "still open", "````"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].start_line, 1)
        self.assertEqual(fences[0].end_line, 5)
        self.assertEqual(fenced_lines, {1, 2, 3, 4, 5})

    def test_longer_closing_run_does_close(self):
        lines = ["```", "code", "````"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].end_line, 3)
        self.assertEqual(fenced_lines, {1, 2, 3})

    def test_tilde_fence_not_closed_by_backtick_run(self):
        lines = ["~~~", "code", "```", "still open", "~~~"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].char, "~")
        self.assertEqual(fences[0].end_line, 5)
        self.assertEqual(fenced_lines, {1, 2, 3, 4, 5})

    def test_backtick_fence_not_closed_by_tilde_run(self):
        lines = ["```", "code", "~~~", "still open", "```"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].char, "`")
        self.assertEqual(fences[0].end_line, 5)
        self.assertEqual(fenced_lines, {1, 2, 3, 4, 5})

    def test_fence_open_at_eof_is_unclosed(self):
        lines = ["```", "code"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        self.assertIsNone(fences[0].end_line)
        self.assertEqual(fenced_lines, {1, 2})

    def test_fences_indented_zero_to_three_spaces_open(self):
        for indent in range(0, 4):
            with self.subTest(indent=indent):
                lines = [
                    (" " * indent) + "```",
                    "code",
                    (" " * indent) + "```",
                ]
                fences, _ = cm.scan_fences(lines)
                self.assertEqual(
                    len(fences), 1, f"indent {indent} should open a fence"
                )
                self.assertEqual(fences[0].end_line, 3)

    def test_fence_indented_four_spaces_does_not_open(self):
        lines = ["    ```", "code"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(fences, [])
        self.assertEqual(fenced_lines, set())

    def test_closing_fence_with_info_string_does_not_close(self):
        lines = ["```", "code", "``` python", "still open", "```"]
        fences, fenced_lines = cm.scan_fences(lines)
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].end_line, 5)
        self.assertEqual(fenced_lines, {1, 2, 3, 4, 5})

    def test_info_string_is_captured(self):
        lines = ["```python", "code", "```"]
        fences, _ = cm.scan_fences(lines)
        self.assertEqual(fences[0].info_string, "python")

    def test_backtick_info_string_with_backtick_is_flagged(self):
        lines = ["```code`with`backticks", "content", "```"]
        fences, _ = cm.scan_fences(lines)
        findings = cm.check_backtick_info_string(fences, "test.md")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line, 1)
        self.assertEqual(findings[0].severity, cm.Severity.ERROR)

    def test_tilde_info_string_with_backtick_is_not_flagged(self):
        lines = ["~~~text with a ` backtick", "content", "~~~"]
        fences, _ = cm.scan_fences(lines)
        findings = cm.check_backtick_info_string(fences, "test.md")
        self.assertEqual(findings, [])


# --------------------------------------------------------------------------
# 2. Checks do not fire inside fences
# --------------------------------------------------------------------------


class TestChecksDoNotFireInsideFences(unittest.TestCase):
    def test_shebang_inside_fence_produces_no_findings(self):
        text = "```bash\n#!/usr/bin/env bash\necho hi\n```\n"
        self.assertEqual(cm.lint_text(text, "test.md"), [])

    def test_c_include_inside_fence_produces_no_findings(self):
        text = "```c\n#include <stdio.h>\nint main(void) { return 0; }\n```\n"
        self.assertEqual(cm.lint_text(text, "test.md"), [])

    def test_tab_indented_makefile_rule_inside_fence_produces_no_findings(self):
        text = "```makefile\nbuild:\n\tgo build ./...\n```\n"
        self.assertEqual(cm.lint_text(text, "test.md"), [])


# --------------------------------------------------------------------------
# 3 & 4. Fixture findings
# --------------------------------------------------------------------------


class TestFixtureFindings(unittest.TestCase):
    def test_clean_fenced_produces_zero_findings(self):
        findings = cm.lint_file(str(FIXTURES_DIR / "clean-fenced.md"))
        self.assertEqual(findings, [])

    def test_malformed_matches_verified_finding_set_exactly(self):
        findings = cm.lint_file(str(FIXTURES_DIR / "malformed.md"))
        actual = [(f.line, f.severity, f.section) for f in findings]
        expected = [
            (7, cm.Severity.ERROR, "4.2"),
            (9, cm.Severity.ERROR, "4.2"),
            (11, cm.Severity.ADVISORY, "4.4"),
            (13, cm.Severity.ADVISORY, "2.2"),
            (15, cm.Severity.ERROR, "6.7"),
            (20, cm.Severity.ADVISORY, "5.3"),
            (22, cm.Severity.ADVISORY, "4.7"),
            (24, cm.Severity.ADVISORY, "n/a"),
            (28, cm.Severity.ERROR, "4.5"),
            (32, cm.Severity.ERROR, "4.5"),
        ]
        self.assertEqual(actual, expected)


# --------------------------------------------------------------------------
# 5. Exit-code contract
# --------------------------------------------------------------------------


class TestExitCodeContract(unittest.TestCase):
    def test_advisory_only_file_exits_0(self):
        result = run_cli([str(FIXTURES_DIR / "clean-fenced.md")])
        self.assertEqual(result.returncode, 0)

    def test_file_with_an_error_exits_1(self):
        result = run_cli([str(FIXTURES_DIR / "malformed.md")])
        self.assertEqual(result.returncode, 1)

    def test_strict_commonmark_flips_pipe_table_only_file_to_exit_1(self):
        text = "# Heading\n\n| a | b |\n| - | - |\n| 1 | 2 |\n"
        default_result = run_cli(["-"], input_text=text)
        self.assertEqual(default_result.returncode, 0)
        strict_result = run_cli(["--strict-commonmark", "-"], input_text=text)
        self.assertEqual(strict_result.returncode, 1)


# --------------------------------------------------------------------------
# 6. Every shipped markdown file passes at ERROR severity
# --------------------------------------------------------------------------


class TestShippedMarkdownFiles(unittest.TestCase):
    def test_scriptorium_markdown_has_zero_error_findings(self):
        md_files = sorted(
            path
            for path in SCRIPTORIUM_DIR.rglob("*.md")
            if "fixtures" not in path.relative_to(SCRIPTORIUM_DIR).parts
        )
        self.assertTrue(md_files, "no markdown files found under scriptorium/")

        offenders = []
        for path in md_files:
            for finding in cm.lint_file(str(path)):
                if finding.severity is cm.Severity.ERROR:
                    offenders.append(f"{path}:{finding.line}: {finding.message}")

        self.assertEqual(
            offenders,
            [],
            "ERROR-severity findings in shipped scriptorium markdown:\n"
            + "\n".join(offenders),
        )


# --------------------------------------------------------------------------
# 7. Stdlib-only
# --------------------------------------------------------------------------


class TestStdlibOnly(unittest.TestCase):
    def test_check_markdown_imports_only_stdlib_modules(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SCRIPT_PATH))

        root_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None and node.level == 0:
                    root_modules.add(node.module.split(".")[0])

        self.assertTrue(root_modules, "found no imports to check")
        non_stdlib = root_modules - set(sys.stdlib_module_names)
        self.assertEqual(non_stdlib, set())


# --------------------------------------------------------------------------
# 8. --llms
# --------------------------------------------------------------------------


class TestLlmsFlag(unittest.TestCase):
    def test_llms_exits_0_and_documents_the_contract(self):
        result = run_cli(["--llms"])
        self.assertEqual(result.returncode, 0)

        text = result.stdout
        self.assertIn(cm.PROG_NAME, text)
        self.assertIn("Exit-code contract", text)
        self.assertIn("--strict-commonmark", text)
        self.assertIn("--llms", text)
        self.assertIn("-h", text)
        self.assertIn("--help", text)


# --------------------------------------------------------------------------
# 9. stdin
# --------------------------------------------------------------------------


class TestStdin(unittest.TestCase):
    def test_dash_reads_and_lints_stdin(self):
        result = run_cli(["-"], input_text="#NoSpace\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("<stdin>", result.stdout)
        self.assertIn("reading stdin", result.stderr)


# --------------------------------------------------------------------------
# 10. Narrowing regressions
# --------------------------------------------------------------------------


class TestNarrowingRegressions(unittest.TestCase):
    def test_bare_shortcut_reference_is_never_flagged(self):
        text = "See the [style guide] for details.\n"
        self.assertEqual(cm.lint_text(text, "test.md"), [])

    def test_full_and_collapsed_references_are_flagged_when_unresolved(self):
        text = "See the [style guide][style] and the [other][] link.\n"
        findings = cm.lint_text(text, "test.md")
        self.assertEqual(len(findings), 2)
        for finding in findings:
            self.assertEqual(finding.section, "4.7")
            self.assertEqual(finding.severity, cm.Severity.ADVISORY)

    def test_pipe_table_is_advisory_by_default_error_under_strict(self):
        text = "| a | b |\n| - | - |\n| 1 | 2 |\n"

        default_findings = cm.lint_text(text, "test.md")
        self.assertEqual(len(default_findings), 1)
        self.assertEqual(default_findings[0].severity, cm.Severity.ADVISORY)

        strict_findings = cm.lint_text(text, "test.md", strict_commonmark=True)
        self.assertEqual(len(strict_findings), 1)
        self.assertEqual(strict_findings[0].severity, cm.Severity.ERROR)


if __name__ == "__main__":
    unittest.main()
