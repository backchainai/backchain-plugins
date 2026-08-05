#!/usr/bin/env python3
"""Stdlib unittest suite for run_trigger_evals.py.

No model calls, no network, no `claude` subprocess. Every case here is pure
data-in/data-out against the harness's independently testable functions:
`detect_trigger`, `substitute_description`, `build_plugin_dir`,
`split_eval_set`, `score`, and the workspace-isolation helper
`allocate_run_dirs`.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import tempfile
import threading
import unittest
import uuid as uuid_mod
from pathlib import Path
from unittest import mock

import run_trigger_evals as rte


# --------------------------------------------------------------------------
# detect_trigger
# --------------------------------------------------------------------------


def _tool_use_line(name, tool_input, block_id="t1"):
    """Build the `assistant` stream envelope wrapping a single `tool_use`
    content block, mirroring the shape `claude --output-format stream-json`
    emits for a tool call: `{"type": "assistant", "message": {"content":
    [{"type": "tool_use", "id": ..., "name": ..., "input": ...}]}}`. Callers
    that need a raw stream line pass the result through `json.dumps`."""
    return {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "id": block_id, "name": name, "input": tool_input}
            ]
        },
    }


class DetectTriggerTest(unittest.TestCase):
    def test_skill_at_tool_position_three_behind_bash_and_read(self):
        # Probe B's stream, checked in as a fixture: Bash, Read, then Skill
        # as the third tool call. detect_trigger must not abort at the first
        # non-Skill tool the way the old harness's `else: return False` did.
        skill_id = "docsprobe-plugin:docsprobe"
        stream_lines = [
            json.dumps(_tool_use_line("Bash", {"command": "ls"}, block_id="t1")),
            json.dumps(_tool_use_line("Read", {"file_path": "/tmp/x.md"}, block_id="t2")),
            json.dumps(_tool_use_line("Skill", {"skill": skill_id}, block_id="t3")),
        ]
        triggered, tools = rte.detect_trigger(stream_lines, skill_id)
        self.assertTrue(triggered)
        self.assertEqual(tools, ["Bash", "Read", "Skill"])

    def test_near_miss_different_skill_not_detected(self):
        # trigeval-x:docs vs trigeval-x:docsprobe: substring matching would
        # confuse these. Exact match must not.
        stream_lines = [json.dumps(_tool_use_line("Skill", {"skill": "trigeval-x:docsprobe"}))]
        triggered, tools = rte.detect_trigger(stream_lines, "trigeval-x:docs")
        self.assertFalse(triggered)
        self.assertEqual(tools, ["Skill"])

    def test_near_miss_reverse_direction(self):
        stream_lines = [json.dumps(_tool_use_line("Skill", {"skill": "trigeval-x:docs"}))]
        triggered, _ = rte.detect_trigger(stream_lines, "trigeval-x:docsprobe")
        self.assertFalse(triggered)

    def test_no_skill_call_returns_false(self):
        stream_lines = [
            json.dumps(_tool_use_line("Bash", {"command": "ls"})),
            json.dumps({"type": "result", "total_cost_usd": 0.02}),
        ]
        triggered, tools = rte.detect_trigger(stream_lines, "trigeval-x:docs")
        self.assertFalse(triggered)
        self.assertEqual(tools, ["Bash"])

    def test_malformed_json_lines_are_skipped(self):
        stream_lines = [
            "not json at all {{{",
            "",
            json.dumps(_tool_use_line("Skill", {"skill": "trigeval-x:docs"})),
        ]
        triggered, tools = rte.detect_trigger(stream_lines, "trigeval-x:docs")
        self.assertTrue(triggered)
        self.assertEqual(tools, ["Skill"])

    def test_trigger_present_only_in_stream_event_partials(self):
        # No complete `assistant` message anywhere in this stream -- only
        # stream_event content_block_start/delta events. The Skill tool_use
        # block's `input` is built up incrementally as partial_json chunks
        # and only becomes a valid, matching object once fully assembled.
        skill_id = "trigeval-abc123:docs"
        payload = json.dumps({"skill": skill_id})
        mid = len(payload) // 2
        stream_lines = [
            json.dumps(
                {
                    "type": "stream_event",
                    "event": {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "tool_use", "id": "t1", "name": "Skill", "input": {}},
                    },
                }
            ),
            json.dumps(
                {
                    "type": "stream_event",
                    "event": {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "input_json_delta", "partial_json": payload[:mid]},
                    },
                }
            ),
            json.dumps(
                {
                    "type": "stream_event",
                    "event": {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "input_json_delta", "partial_json": payload[mid:]},
                    },
                }
            ),
            json.dumps({"type": "stream_event", "event": {"type": "content_block_stop", "index": 0}}),
        ]
        triggered, tools = rte.detect_trigger(stream_lines, skill_id)
        self.assertTrue(triggered)
        self.assertEqual(tools, ["Skill"])

    def test_stream_event_partial_never_completes_no_match(self):
        stream_lines = [
            json.dumps(
                {
                    "type": "stream_event",
                    "event": {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "tool_use", "id": "t1", "name": "Skill", "input": {}},
                    },
                }
            ),
            json.dumps(
                {
                    "type": "stream_event",
                    "event": {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "input_json_delta", "partial_json": '{"skill": "trigeval-x:doc'},
                    },
                }
            ),
        ]
        triggered, _ = rte.detect_trigger(stream_lines, "trigeval-x:docs")
        self.assertFalse(triggered)


# --------------------------------------------------------------------------
# substitute_description
# --------------------------------------------------------------------------


SAMPLE_SKILL_MD = """---
name: docs
description: "Old description here."
disable-model-invocation: false
metadata:
  author: Backchain
  version: 1.0.0
---

# Docs

Body content stays untouched.

Second paragraph.
"""


class SubstituteDescriptionTest(unittest.TestCase):
    def test_body_and_name_preserved(self):
        result = rte.substitute_description(SAMPLE_SKILL_MD, "A new description.")
        self.assertIn("name: docs", result)
        self.assertIn("disable-model-invocation: false", result)
        self.assertIn("  author: Backchain", result)
        self.assertIn("# Docs\n\nBody content stays untouched.\n\nSecond paragraph.\n", result)

    def test_round_trips_quotes_colon_and_newline(self):
        candidate = 'Has a "quote", a colon: here, and\na newline.'
        result = rte.substitute_description(SAMPLE_SKILL_MD, candidate)

        frontmatter_text = result.split("\n---\n", 1)[0]
        match = re.search(r'^description: "((?:[^"\\]|\\.)*)"$', frontmatter_text, re.MULTILINE)
        self.assertIsNotNone(match, f"description line not found or not a quoted scalar in:\n{frontmatter_text}")

        raw = match.group(1)
        # Minimal YAML double-quoted-scalar unescape, mirroring the escaping
        # substitute_description performs, to confirm the round trip.
        unescaped = (
            raw.replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\\\", "\\")
        )
        self.assertEqual(unescaped, candidate)

    def test_result_frontmatter_lines_are_wellformed_mappings(self):
        result = rte.substitute_description(SAMPLE_SKILL_MD, "Simple description.")
        lines = result.split("\n")
        self.assertEqual(lines[0], "---")
        closing_indices = [i for i in range(1, len(lines)) if lines[i] == "---"]
        self.assertTrue(closing_indices, "no closing '---' delimiter found")
        frontmatter = lines[1 : closing_indices[0]]
        # Every non-indented, non-empty frontmatter line must look like a
        # YAML mapping entry ("key: value" or "key:").
        for line in frontmatter:
            if not line or line.startswith(" "):
                continue
            self.assertRegex(line, r"^[A-Za-z0-9_-]+:( .*)?$", f"not a valid YAML mapping line: {line!r}")

    def test_body_description_line_is_left_untouched(self):
        # A `description:`-looking line in the BODY (past the closing '---')
        # must not be touched by the frontmatter-only substitution -- only
        # the frontmatter block's own `description:` key is a target.
        text = (
            "---\nname: docs\ndescription: \"Old.\"\n---\n\n"
            "# Docs\n\ndescription: this is prose, not frontmatter.\n"
        )
        result = rte.substitute_description(text, "New description.")
        self.assertIn('description: "New description."', result)
        self.assertIn("description: this is prose, not frontmatter.", result)

    def test_missing_description_field_appends_one(self):
        text = "---\nname: docs\n---\n\nBody.\n"
        result = rte.substitute_description(text, "New description.")
        self.assertIn('description: "New description."', result)
        self.assertIn("name: docs", result)


# --------------------------------------------------------------------------
# build_plugin_dir
# --------------------------------------------------------------------------


class BuildPluginDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="trigeval-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.skill_path = self.tmp / "src-skill"
        (self.skill_path / "references").mkdir(parents=True)
        (self.skill_path / "SKILL.md").write_text(SAMPLE_SKILL_MD, encoding="utf-8")
        (self.skill_path / "references" / "note.md").write_text("reference content\n", encoding="utf-8")

    def test_manifest_is_valid_json_with_nine_fields(self):
        # Pin the literal nine field names from CLAUDE.md ("Adding a new
        # plugin") rather than looping over an implementation-owned
        # constant: comparing against a constant the implementation itself
        # owns would not catch a field silently dropped from both the
        # constant and the manifest it builds.
        expected_fields = [
            "author",
            "category",
            "description",
            "homepage",
            "keywords",
            "license",
            "name",
            "repository",
            "version",
        ]

        dest = self.tmp / "trigeval-deadbeef1234"
        rte.build_plugin_dir(self.skill_path, "A candidate description.", dest)

        manifest_path = dest / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(manifest.keys()), expected_fields)
        self.assertEqual(manifest["name"], "trigeval-deadbeef1234")

    def test_skill_lands_at_skills_name_skill_md(self):
        dest = self.tmp / "trigeval-abc"
        rte.build_plugin_dir(self.skill_path, "Another description.", dest)

        skill_md = dest / "skills" / "docs" / "SKILL.md"
        self.assertTrue(skill_md.is_file())
        self.assertIn("Another description.", skill_md.read_text(encoding="utf-8"))

    def test_references_directory_is_copied(self):
        dest = self.tmp / "trigeval-refs"
        rte.build_plugin_dir(self.skill_path, "Description.", dest)

        copied_ref = dest / "skills" / "docs" / "references" / "note.md"
        self.assertTrue(copied_ref.is_file())
        self.assertEqual(copied_ref.read_text(encoding="utf-8"), "reference content\n")

    def test_returns_exact_plugin_skill_id(self):
        dest = self.tmp / "trigeval-idcheck"
        skill_id = rte.build_plugin_dir(self.skill_path, "Description.", dest)
        self.assertEqual(skill_id, "trigeval-idcheck:docs")

    def _write_skill_with_name(self, skill_name: str) -> Path:
        skill_path = self.tmp / "hostile-skill"
        skill_path.mkdir(exist_ok=True)
        skill_md = SAMPLE_SKILL_MD.replace("name: docs", f"name: {skill_name}")
        (skill_path / "SKILL.md").write_text(skill_md, encoding="utf-8")
        return skill_path

    def test_traversal_name_raises_harness_error(self):
        skill_path = self._write_skill_with_name("../../../../tmp/evil")
        dest = self.tmp / "trigeval-traversal"
        with self.assertRaises(rte.HarnessError):
            rte.build_plugin_dir(skill_path, "Description.", dest)

    def test_absolute_name_raises_harness_error(self):
        skill_path = self._write_skill_with_name("/tmp/evil")
        dest = self.tmp / "trigeval-absolute"
        with self.assertRaises(rte.HarnessError):
            rte.build_plugin_dir(skill_path, "Description.", dest)

    def test_illegal_characters_in_name_raises_harness_error(self):
        skill_path = self._write_skill_with_name("Docs Skill!")
        dest = self.tmp / "trigeval-illegal"
        with self.assertRaises(rte.HarnessError):
            rte.build_plugin_dir(skill_path, "Description.", dest)

    def test_normal_name_still_succeeds(self):
        skill_path = self._write_skill_with_name("docs")
        dest = self.tmp / "trigeval-normal"
        skill_id = rte.build_plugin_dir(skill_path, "Description.", dest)
        self.assertEqual(skill_id, "trigeval-normal:docs")


# --------------------------------------------------------------------------
# split_eval_set
# --------------------------------------------------------------------------


def _make_eval_set(n_positive: int, n_negative: int) -> list[dict]:
    eval_set = []
    for i in range(n_positive):
        eval_set.append({"query": f"positive query {i}", "should_trigger": True})
    for i in range(n_negative):
        eval_set.append({"query": f"negative query {i}", "should_trigger": False})
    return eval_set


class SplitEvalSetTest(unittest.TestCase):
    def test_stratified_counts_at_holdout_point_four(self):
        # Pins PER-CLASS counts, not just the split totals: an unstratified
        # split (one shuffle over positives+negatives combined, instead of
        # two per-class shuffles) still lands on 12 train / 8 test totals
        # for an 11-positive/9-negative set, so a totals-only assertion
        # cannot distinguish a stratified split from a broken one. The
        # shipped eval set (scriptorium/skills/docs/evals/trigger-evals.json)
        # is 11 positive / 9 negative after the query-14 relabel; these
        # numbers are the real `split_eval_set` output for that shape,
        # confirmed by running it, not assumed.
        eval_set = _make_eval_set(11, 9)
        train, test = rte.split_eval_set(eval_set, holdout=0.4, seed=42)

        train_pos = sum(1 for q in train if q["should_trigger"])
        train_neg = sum(1 for q in train if not q["should_trigger"])
        test_pos = sum(1 for q in test if q["should_trigger"])
        test_neg = sum(1 for q in test if not q["should_trigger"])

        self.assertEqual((train_pos, train_neg), (7, 5))
        self.assertEqual((test_pos, test_neg), (4, 4))
        self.assertEqual(len(train), 12)
        self.assertEqual(len(test), 8)

    def test_stratified_counts_survive_unstratified_mutant(self):
        # A mutant that shuffles positives+negatives together (one `rng`
        # call over the combined list) instead of splitting each class
        # separately still produces 12/8 totals but the WRONG per-class
        # split for this shape (8/4 train, 3/5 test rather than 7/5 and
        # 4/4). This test fails against that mutant even though the totals
        # test would not.
        eval_set = _make_eval_set(11, 9)
        import random as _random

        def _unstratified_split(items, holdout, seed):
            group = list(items)
            rng = _random.Random(seed)
            rng.shuffle(group)
            n_test = round(len(group) * holdout)
            return group[n_test:], group[:n_test]

        mutant_train, mutant_test = _unstratified_split(eval_set, holdout=0.4, seed=42)
        mutant_train_pos = sum(1 for q in mutant_train if q["should_trigger"])
        mutant_test_pos = sum(1 for q in mutant_test if q["should_trigger"])

        real_train, real_test = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        real_train_pos = sum(1 for q in real_train if q["should_trigger"])
        real_test_pos = sum(1 for q in real_test if q["should_trigger"])

        self.assertNotEqual((mutant_train_pos, mutant_test_pos), (real_train_pos, real_test_pos))
        self.assertEqual((real_train_pos, real_test_pos), (7, 4))

    def test_deterministic_under_fixed_seed(self):
        eval_set = _make_eval_set(10, 10)
        train1, test1 = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        train2, test2 = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        self.assertEqual([q["query"] for q in train1], [q["query"] for q in train2])
        self.assertEqual([q["query"] for q in test1], [q["query"] for q in test2])

    def test_every_item_appears_exactly_once(self):
        eval_set = _make_eval_set(11, 9)
        train, test = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        seen = [q["query"] for q in train] + [q["query"] for q in test]
        expected = [q["query"] for q in eval_set]
        self.assertEqual(sorted(seen), sorted(expected))
        self.assertEqual(len(seen), len(set(seen)))


# --------------------------------------------------------------------------
# score
# --------------------------------------------------------------------------


class ScoreTest(unittest.TestCase):
    def test_positive_passes_at_rate_one(self):
        results = [{"query": "q1", "should_trigger": True, "triggered_runs": 1, "total_runs": 1}]
        scored = rte.score(results)
        self.assertTrue(scored["per_query"][0]["passed"])
        self.assertEqual(scored["accuracy"], 1.0)

    def test_positive_fails_at_rate_zero(self):
        results = [{"query": "q1", "should_trigger": True, "triggered_runs": 0, "total_runs": 1}]
        scored = rte.score(results)
        self.assertFalse(scored["per_query"][0]["passed"])
        self.assertEqual(scored["accuracy"], 0.0)

    def test_negative_passes_at_rate_zero(self):
        results = [{"query": "q1", "should_trigger": False, "triggered_runs": 0, "total_runs": 1}]
        scored = rte.score(results)
        self.assertTrue(scored["per_query"][0]["passed"])

    def test_negative_fails_at_rate_one(self):
        results = [{"query": "q1", "should_trigger": False, "triggered_runs": 1, "total_runs": 1}]
        scored = rte.score(results)
        self.assertFalse(scored["per_query"][0]["passed"])

    def test_threshold_boundary_at_exactly_point_five(self):
        # rate == threshold counts as triggered (>=), so a positive passes
        # and a negative fails at exactly the boundary.
        positive = [{"query": "p", "should_trigger": True, "triggered_runs": 1, "total_runs": 2}]
        negative = [{"query": "n", "should_trigger": False, "triggered_runs": 1, "total_runs": 2}]
        self.assertTrue(rte.score(positive, threshold=0.5)["per_query"][0]["passed"])
        self.assertFalse(rte.score(negative, threshold=0.5)["per_query"][0]["passed"])

    def test_precision_recall_accuracy_over_multiple_queries(self):
        results = [
            {"query": "tp", "should_trigger": True, "triggered_runs": 1, "total_runs": 1},
            {"query": "fn", "should_trigger": True, "triggered_runs": 0, "total_runs": 1},
            {"query": "tn", "should_trigger": False, "triggered_runs": 0, "total_runs": 1},
            {"query": "fp", "should_trigger": False, "triggered_runs": 1, "total_runs": 1},
        ]
        scored = rte.score(results)
        self.assertEqual(scored["counts"], {"tp": 1, "fp": 1, "fn": 1, "tn": 1})
        self.assertEqual(scored["precision"], 0.5)
        self.assertEqual(scored["recall"], 0.5)
        self.assertEqual(scored["accuracy"], 0.5)


# --------------------------------------------------------------------------
# Workspace isolation
# --------------------------------------------------------------------------


class WorkspaceIsolationTest(unittest.TestCase):
    def test_two_runs_get_different_non_sibling_parent_dirs(self):
        run1 = rte.allocate_run_dirs()
        run2 = rte.allocate_run_dirs()
        try:
            self.assertNotEqual(run1.parent, run2.parent)
            # The two workspace dirs do not share a parent directory --
            # i.e. they are not siblings of one another.
            self.assertNotEqual(run1.workspace_dir.parent, run2.workspace_dir.parent)
        finally:
            shutil.rmtree(run1.parent, ignore_errors=True)
            shutil.rmtree(run2.parent, ignore_errors=True)


# --------------------------------------------------------------------------
# Guards
# --------------------------------------------------------------------------


class WorkspaceGroundingTest(unittest.TestCase):
    def test_missing_workspace_raises(self):
        with self.assertRaises(rte.HarnessError):
            rte.assert_workspace_grounded(Path("/nonexistent/path/for/trigeval-test"))

    def test_empty_workspace_raises(self):
        tmp = Path(tempfile.mkdtemp(prefix="trigeval-empty-"))
        try:
            with self.assertRaises(rte.HarnessError):
                rte.assert_workspace_grounded(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_populated_workspace_does_not_raise(self):
        tmp = Path(tempfile.mkdtemp(prefix="trigeval-populated-"))
        try:
            (tmp / "file.md").write_text("content\n", encoding="utf-8")
            rte.assert_workspace_grounded(tmp)  # must not raise
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class AuthModeTest(unittest.TestCase):
    def test_api_key_present_reports_api_key(self):
        self.assertEqual(rte.detect_auth_mode({"ANTHROPIC_API_KEY": "sk-test"}), "api_key")

    def test_api_key_absent_reports_oauth(self):
        self.assertEqual(rte.detect_auth_mode({}), "oauth")


# --------------------------------------------------------------------------
# main() HarnessError paths
# --------------------------------------------------------------------------


class _MainHarnessTestBase(unittest.TestCase):
    """Shared `main()`-driving fixture: a temp workspace with one seed file,
    a candidates file with one candidate ("c1"), an empty skill directory,
    and a results dir. Subclasses that need a different labeled query set
    override the `EVAL_SET` class attribute; `_argv(**extra)` builds the
    five required flags plus one `--flag-name value` pair per keyword
    argument (underscores become dashes: `num_workers=1` -> `--num-workers
    1`)."""

    EVAL_SET = [{"query": "do a thing", "should_trigger": True}]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="trigeval-main-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        (self.workspace / "file.md").write_text("content\n", encoding="utf-8")

        self.eval_set_path = self.tmp / "trigger-evals.json"
        self.eval_set_path.write_text(json.dumps(self.EVAL_SET), encoding="utf-8")

        self.candidates_path = self.tmp / "candidates.json"
        self.candidates_path.write_text(
            json.dumps([{"name": "c1", "description": "A description."}]),
            encoding="utf-8",
        )

        self.skill_path = self.tmp / "skill"
        self.skill_path.mkdir()

        self.results_dir = self.tmp / "results"

    def _argv(self, **extra):
        argv = [
            "--skill-path", str(self.skill_path),
            "--eval-set", str(self.eval_set_path),
            "--workspace", str(self.workspace),
            "--candidates", str(self.candidates_path),
            "--results-dir", str(self.results_dir),
        ]
        for flag, value in extra.items():
            argv += [f"--{flag.replace('_', '-')}", str(value)]
        return argv


# --------------------------------------------------------------------------
# main() HarnessError paths
# --------------------------------------------------------------------------


class MainHarnessErrorTest(_MainHarnessTestBase):
    """`main([...])` returns 1 (never raises) for every harness-level
    failure: an unaccountable --max-cost, a malformed --eval-set, and a
    malformed --candidates file. No model call, no `claude` subprocess --
    every case here fails before any dispatch is ever submitted."""

    def test_max_cost_without_api_key_auth_returns_one(self):
        argv = self._argv() + ["--max-cost", "5"]
        with mock.patch.dict("os.environ", {}, clear=True):
            rc = rte.main(argv)
        self.assertEqual(rc, 1)

    def test_malformed_eval_set_json_returns_one(self):
        self.eval_set_path.write_text("not json {{{", encoding="utf-8")
        self.assertEqual(rte.main(self._argv()), 1)

    def test_eval_set_item_missing_required_key_returns_one(self):
        self.eval_set_path.write_text(json.dumps([{"query": "x"}]), encoding="utf-8")
        self.assertEqual(rte.main(self._argv()), 1)

    def test_malformed_candidates_json_returns_one(self):
        self.candidates_path.write_text("not json {{{", encoding="utf-8")
        self.assertEqual(rte.main(self._argv()), 1)

    def test_candidates_item_missing_required_key_returns_one(self):
        self.candidates_path.write_text(json.dumps([{"name": "c1"}]), encoding="utf-8")
        self.assertEqual(rte.main(self._argv()), 1)

    def test_eval_set_query_starting_with_dash_returns_one(self):
        self.eval_set_path.write_text(
            json.dumps([{"query": "--dangerous-flag", "should_trigger": True}]),
            encoding="utf-8",
        )
        self.assertEqual(rte.main(self._argv()), 1)


class LoadJsonRecordsQueryValidationTest(unittest.TestCase):
    """`_load_json_records` rejects a `query` field that starts with '-'
    before the eval set ever reaches subprocess dispatch, naming the
    offending query in the raised `HarnessError`."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="trigeval-loadrecords-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_query_starting_with_dash_raises_harness_error_naming_query(self):
        path = self.tmp / "eval-set.json"
        path.write_text(
            json.dumps([{"query": "--help", "should_trigger": True}]),
            encoding="utf-8",
        )
        with self.assertRaises(rte.HarnessError) as ctx:
            rte._load_json_records(path, "--eval-set", ("query", "should_trigger"), "query objects")
        self.assertIn("--help", str(ctx.exception))

    def test_ordinary_query_is_accepted(self):
        path = self.tmp / "eval-set.json"
        path.write_text(
            json.dumps([{"query": "write the docs", "should_trigger": True}]),
            encoding="utf-8",
        )
        records = rte._load_json_records(path, "--eval-set", ("query", "should_trigger"), "query objects")
        self.assertEqual(records[0]["query"], "write the docs")


# --------------------------------------------------------------------------
# --max-cost abort behavior (Defect A)
# --------------------------------------------------------------------------


class MaxCostAbortTest(_MainHarnessTestBase):
    """Drives `main()`'s dispatch loop with a fake, fixed-cost
    `run_single_query` (no model call, no subprocess, no network) and
    asserts that `--max-cost` actually bounds the number of dispatches made,
    rather than only printing a message after every query already ran."""

    # 6 positive + 6 negative queries: plenty of work to bound. At $5/call
    # and --max-cost 12, a correct harness stops well short of running all
    # 12.
    EVAL_SET = [{"query": f"positive {i}", "should_trigger": True} for i in range(6)] + [
        {"query": f"negative {i}", "should_trigger": False} for i in range(6)
    ]

    def _argv(self, *, max_cost, num_workers):
        return super()._argv(holdout=0.0, num_workers=num_workers, max_cost=max_cost)

    def test_max_cost_bounds_the_number_of_dispatches(self):
        call_count = 0
        lock = threading.Lock()

        def fake_run_single_query(**kwargs):
            nonlocal call_count
            with lock:
                call_count += 1
            return {"triggered": False, "cost_usd": 5.0, "query": kwargs["query"]}

        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), mock.patch.object(
            rte, "run_single_query", side_effect=fake_run_single_query
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = rte.main(self._argv(max_cost=12, num_workers=1))

        self.assertEqual(rc, 0)
        # 12 queries total (holdout=0.0 puts everything in train). At
        # $5/call the running total exceeds $12 after the 3rd call
        # ($15 > $12), so exactly 3 calls should be made -- never all 12.
        self.assertLess(call_count, 12)
        self.assertEqual(call_count, 3)

        results_path = self.results_dir / "results.json"
        self.assertTrue(results_path.is_file(), "results.json must exist on the abort path")
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["partial"])
        self.assertGreater(payload["total_cost_usd"], 12)

    def test_bounded_in_flight_window_respects_num_workers(self):
        call_count = 0
        in_flight = 0
        max_in_flight = 0
        lock = threading.Lock()

        def fake_run_single_query(**kwargs):
            nonlocal call_count, in_flight, max_in_flight
            with lock:
                call_count += 1
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
            try:
                return {"triggered": False, "cost_usd": 5.0, "query": kwargs["query"]}
            finally:
                with lock:
                    in_flight -= 1

        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}), mock.patch.object(
            rte, "run_single_query", side_effect=fake_run_single_query
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = rte.main(self._argv(max_cost=12, num_workers=2))

        self.assertEqual(rc, 0)
        # Never more than num_workers dispatches outstanding at once --
        # the old behavior submitted every task up front, with no window
        # at all.
        self.assertLessEqual(max_in_flight, 2)
        self.assertLess(call_count, 12)

# --------------------------------------------------------------------------
# run_single_query returncode handling (Finding 1)
# --------------------------------------------------------------------------


class _FakeStream:
    """Minimal stand-in for `proc.stdout` / `proc.stderr`: a line queue with
    a `.readline()` that returns "" once drained, matching the real
    `subprocess.Popen(..., text=True)` stream contract closely enough for
    `run_single_query`'s reader loop."""

    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self):
        if self._lines:
            return self._lines.pop(0)
        return ""


class _FakeStderr:
    def __init__(self, text):
        self._text = text

    def read(self):
        return self._text


class _FakeProc:
    """Stand-in for `subprocess.Popen`. `returncode` is fixed at
    construction time and `poll()` always returns it -- i.e. the fake
    process is already "finished" the instant it's created. That is enough
    for `run_single_query`'s logic: it only ever consults `poll()` after
    `readline()` returns "" (EOF) or when deciding whether to `terminate()`
    in its `finally`, and a pre-finished process correctly skips that
    `terminate()` call, exactly like a process that exited on its own before
    the harness got to it."""

    def __init__(self, stdout_lines, stderr_text, returncode):
        self.stdout = _FakeStream(stdout_lines)
        self.stderr = _FakeStderr(stderr_text)
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def terminate(self):  # pragma: no cover -- not exercised, poll() already non-None
        pass

    def kill(self):  # pragma: no cover
        pass

    def wait(self, timeout=None):  # pragma: no cover
        return self.returncode


class RedactSecretsTest(unittest.TestCase):
    """`_redact_secrets` masks obvious credential shapes before a stderr
    tail is embedded in a `HarnessError` message or written into a
    results.json artifact, while leaving ordinary stderr text untouched."""

    def test_masks_sk_prefixed_token(self):
        text = "auth failed with token sk-abcdefghijklmnop1234 during request"
        redacted = rte._redact_secrets(text)
        self.assertNotIn("sk-abcdefghijklmnop1234", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_masks_anthropic_api_key_assignment(self):
        text = "env dump: ANTHROPIC_API_KEY=sk-verysecretvalue1234 other=1"
        redacted = rte._redact_secrets(text)
        self.assertNotIn("sk-verysecretvalue1234", redacted)
        self.assertIn("ANTHROPIC_API_KEY=[REDACTED]", redacted)

    def test_leaves_ordinary_stderr_text_intact(self):
        text = "Error: workspace directory not found" + chr(10) + "exit code 2"
        self.assertEqual(rte._redact_secrets(text), text)


class RunSingleQueryReturncodeTest(unittest.TestCase):
    """`run_single_query` must never score a nonzero subprocess exit as a
    clean non-trigger: the `claude` process may have died on an auth
    failure, a bad flag, or a crash before producing any usable stdout, and
    `detect_trigger` cannot tell that apart from an honest negative. It
    must ALSO never raise when the nonzero/negative exit follows the
    harness's own `terminate()` on a detected trigger -- that path is
    expected, not a failure. No network call, no real `claude` subprocess:
    `subprocess.Popen` is replaced with `_FakeProc` end to end."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="trigeval-rsq-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.skill_path = self.tmp / "skill"
        self.skill_path.mkdir()
        (self.skill_path / "SKILL.md").write_text(SAMPLE_SKILL_MD, encoding="utf-8")

        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        (self.workspace / "file.md").write_text("content\n", encoding="utf-8")

    def test_nonzero_exit_without_trigger_raises_with_returncode_and_stderr(self):
        with mock.patch.object(
            rte.subprocess,
            "Popen",
            return_value=_FakeProc(stdout_lines=[], stderr_text="auth error: invalid API key", returncode=1),
        ):
            with self.assertRaises(rte.HarnessError) as ctx:
                rte.run_single_query(
                    skill_path=self.skill_path,
                    description="A description.",
                    workspace=self.workspace,
                    query="do a thing",
                )
        message = str(ctx.exception)
        # "exited 1" (not a bare "1") binds the returncode to its context --
        # a bare digit check would still pass if the returncode were
        # dropped from the message and only a timeout-in-seconds happened
        # to remain.
        self.assertIn("exited 1", message)
        self.assertIn("auth error: invalid API key", message)

    def test_stderr_tail_is_bounded_not_the_full_text(self):
        # The delta's `_STDERR_TAIL_CHARS` bound on the stderr tail is
        # otherwise unverified: a regression to unbounded `stderr_text`
        # (e.g. dropping the `[-_STDERR_TAIL_CHARS:]` slice) would ship
        # green with no test catching it. 10000 chars of stderr, well past
        # the 4000-char bound, must land in the raised message truncated to
        # at most `_STDERR_TAIL_CHARS`, not in full.
        huge_stderr = "x" * 10000
        with mock.patch.object(
            rte.subprocess,
            "Popen",
            return_value=_FakeProc(stdout_lines=[], stderr_text=huge_stderr, returncode=1),
        ):
            with self.assertRaises(rte.HarnessError) as ctx:
                rte.run_single_query(
                    skill_path=self.skill_path,
                    description="A description.",
                    workspace=self.workspace,
                    query="do a thing",
                )
        message = str(ctx.exception)
        # "exited" itself contains an "x", so split off the stderr-tail
        # portion of the message before counting -- a bare `message.count`
        # would silently include that one unrelated "x" and mask an
        # off-by-one in the bound.
        _, _, tail_in_message = message.partition("stderr tail:\n")
        self.assertEqual(len(tail_in_message), rte._STDERR_TAIL_CHARS)
        self.assertEqual(tail_in_message, huge_stderr[-rte._STDERR_TAIL_CHARS:])
        self.assertLess(len(message), len(huge_stderr))

    def test_secret_straddling_tail_boundary_is_fully_redacted(self):
        # A secret that straddles the `_STDERR_TAIL_CHARS` cut point is the
        # security-review defect: slicing BEFORE redacting truncates the
        # token before the redaction regex ever sees it, so the surviving
        # suffix (missing its "sk-" prefix) matches no pattern and lands in
        # the raised HarnessError -- and from there into results.json --
        # unredacted. The fix redacts the full text first, then slices.
        boundary = 10000 - rte._STDERR_TAIL_CHARS
        secret_body = "UNIQSECRETSUFFIXABCDEFGHIJKLMNOPQRSTUV1234567890"
        secret = "sk-" + secret_body
        secret_start = boundary - 10  # secret begins 10 chars before the cut
        prefix = "x" * secret_start
        suffix = "y" * (10000 - secret_start - len(secret))
        huge_stderr = prefix + secret + suffix
        self.assertEqual(len(huge_stderr), 10000)
        # The fragment that lands inside the tail slice once the leading
        # "sk-" (and a few body chars) are cut away by a pre-redaction
        # slice -- exactly what must never survive into the error message.
        leaked_fragment = secret[boundary - secret_start :]
        with mock.patch.object(
            rte.subprocess,
            "Popen",
            return_value=_FakeProc(stdout_lines=[], stderr_text=huge_stderr, returncode=1),
        ):
            with self.assertRaises(rte.HarnessError) as ctx:
                rte.run_single_query(
                    skill_path=self.skill_path,
                    description="A description.",
                    workspace=self.workspace,
                    query="do a thing",
                )
        message = str(ctx.exception)
        self.assertNotIn(leaked_fragment, message)
        self.assertNotIn(secret_body, message)

    def test_zero_exit_without_trigger_does_not_raise(self):
        # Ordinary negative case must keep working: a clean exit 0 with no
        # Skill call is a real non-trigger, not a harness failure.
        # Never-red by design: this is the intended negative branch of the
        # new `if not triggered and proc.returncode:` condition, guarding
        # against a future over-broad version of that check (e.g. one that
        # raises on ANY non-triggering run regardless of returncode). A
        # passing result here is not evidence this delta did nothing.
        with mock.patch.object(
            rte.subprocess,
            "Popen",
            return_value=_FakeProc(stdout_lines=[], stderr_text="", returncode=0),
        ):
            result = rte.run_single_query(
                skill_path=self.skill_path,
                description="A description.",
                workspace=self.workspace,
                query="do a thing",
            )
        self.assertFalse(result["triggered"])

    def test_nonzero_or_terminated_exit_after_trigger_does_not_raise(self):
        # A negative returncode here (e.g. -15 for SIGTERM) is EXPECTED --
        # the harness itself terminates the subprocess the instant a
        # trigger is detected -- and must not be mistaken for a failure.
        # Never-red by design: this is the intended negative branch of the
        # new `if not triggered and proc.returncode:` condition, guarding
        # against a future over-broad version of that check (e.g. one that
        # raises on any nonzero/negative returncode regardless of whether a
        # trigger was already detected). A passing result here is not
        # evidence this delta did nothing.
        fixed_uuid = uuid_mod.UUID("12345678-1234-5678-1234-567812345678")
        run_id = fixed_uuid.hex[:12]
        skill_id = f"trigeval-{run_id}:docs"

        with mock.patch.object(rte.uuid, "uuid4", return_value=fixed_uuid), mock.patch.object(
            rte.subprocess,
            "Popen",
            return_value=_FakeProc(
                stdout_lines=[json.dumps(_tool_use_line("Skill", {"skill": skill_id})) + "\n"],
                stderr_text="",
                returncode=-15,
            ),
        ):
            result = rte.run_single_query(
                skill_path=self.skill_path,
                description="A description.",
                workspace=self.workspace,
                query="do a thing",
            )
        self.assertTrue(result["triggered"])


# --------------------------------------------------------------------------
# main() error-recording and mid-run results.json accuracy (Findings 1 & 2)
# --------------------------------------------------------------------------


class DispatchErrorRecordingTest(_MainHarnessTestBase):
    """A dispatch whose `run_single_query` raises (e.g. the `HarnessError`
    a nonzero subprocess exit now produces) must land in its own "errors"
    list in results.json, mark the run partial, and NOT be counted in
    per_query_counts as a clean non-trigger. `main()` must still return 0 --
    a dispatch failure is a per-run failure, not a harness crash."""

    def _argv(self):
        return super()._argv(holdout="0.0", num_workers=1)

    def test_errored_dispatch_marks_partial_and_is_not_a_clean_non_trigger(self):
        def fake_run_single_query(**kwargs):
            raise rte.HarnessError(
                "claude subprocess exited 1 without triggering a skill call "
                "(query='do a thing'); stderr tail:\nauth error"
            )

        with mock.patch.object(
            rte, "run_single_query", side_effect=fake_run_single_query
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = rte.main(self._argv())

        self.assertEqual(rc, 0)

        payload = json.loads((self.results_dir / "results.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["partial"])

        candidate = payload["candidates"]["c1"]
        # The errored run must NOT show up as a clean, zero-rate non-trigger
        # in the scored results -- that's exactly the silent-poisoning bug
        # this fix closes.
        self.assertEqual(candidate["results"], [])
        self.assertEqual(len(candidate.get("errors", [])), 1)
        error_entry = candidate["errors"][0]
        self.assertEqual(error_entry["query"], "do a thing")
        self.assertEqual(error_entry["split"], "train")
        self.assertIn("auth error", error_entry["error"])

    def test_errored_dispatch_warns_with_dispatch_error_cause_not_max_cost(self):
        # Defect (GitHub issue #35): the terminal stderr warning hardcoded
        # "--max-cost" wording regardless of WHY the run went partial. A
        # run invoked WITHOUT --max-cost that suffers a single dispatch
        # error must not claim it "stopped early on --max-cost" -- it
        # didn't -- and must instead name the dispatch-error cause.
        def fake_run_single_query(**kwargs):
            raise rte.HarnessError(
                "claude subprocess exited 1 without triggering a skill call "
                "(query='do a thing'); stderr tail:\nauth error"
            )

        stderr = io.StringIO()
        with mock.patch.object(
            rte, "run_single_query", side_effect=fake_run_single_query
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            rc = rte.main(self._argv())

        self.assertEqual(rc, 0)
        output = stderr.getvalue()
        self.assertNotIn("--max-cost", output)
        self.assertIn("1 dispatch error", output)


class WriteResultsMidRunTest(_MainHarnessTestBase):
    """The per-dispatch `_write_results()` call in `main()` is the whole
    reason a `kill -9` mid-run still leaves an accurate on-disk
    `results.json` -- the observed live-money incident produced zero
    artifact for a $16.06 run because the only write happened after the
    collection loop, which the process never reached. This drives `main()`
    with `--num-workers 1` (so dispatches are strictly sequential) and a
    fake `run_single_query` that, on the SECOND dispatch, reads
    results.json off disk and asserts the FIRST dispatch's data is already
    there, correct, and complete -- before `main()` itself has returned.

    `test_earlier_dispatch_result_on_disk_before_later_dispatch_completes`
    below is a characterization/regression guard for 38e0d25's per-dispatch
    write on the SUCCESS path: that write already existed, unconditionally,
    before this delta, so the test passes verbatim against pre-change
    `run_trigger_evals.py` and pins existing behavior rather than an
    acceptance criterion of this delta.

    `test_earlier_dispatch_error_on_disk_before_later_dispatch_completes`
    below IS this delta's acceptance criterion: the per-dispatch
    `_write_results()` call inside the ERROR handler must land an `errors`
    entry (and `partial=True`) on disk before the next dispatch is
    submitted, and the failed dispatch must never be folded into `results`
    as a silent, poisoning non-trigger. Confirmed red against `git show
    HEAD:scripts/evals/run_trigger_evals.py` (pre-change: the except-block
    there has no `errors` bookkeeping and no per-dispatch write, so
    `payload["partial"]` reads `False` and the exception is instead folded
    into `per_query_counts` as a fake `{"triggered": False, "cost_usd":
    0.0}` result) and green against this delta, before being added here."""

    EVAL_SET = [
        {"query": "first query", "should_trigger": True},
        {"query": "second query", "should_trigger": False},
    ]

    def setUp(self):
        super().setUp()
        self.results_path = self.results_dir / "results.json"

    def _argv(self):
        return super()._argv(holdout="0.0", num_workers=1)

    def test_earlier_dispatch_result_on_disk_before_later_dispatch_completes(self):
        call_order = []
        failures = []

        def fake_run_single_query(**kwargs):
            call_order.append(kwargs["query"])
            if kwargs["query"] == "second query":
                # num_workers=1 guarantees this dispatch was only submitted
                # after the first dispatch's completion handler --
                # including its _write_results() call -- already ran, so
                # results.json must already reflect the first dispatch here.
                try:
                    payload = json.loads(self.results_path.read_text(encoding="utf-8"))
                    candidate = payload["candidates"]["c1"]
                    results_by_query = {r["query"]: r for r in candidate["results"]}
                    self.assertIn("first query", results_by_query)
                    first = results_by_query["first query"]
                    self.assertEqual(first["triggered_runs"], 1)
                    self.assertEqual(first["total_runs"], 1)
                    self.assertEqual(payload["total_cost_usd"], 3.0)
                except Exception as exc:  # noqa: BLE001 -- re-raised on the main thread below
                    # Broad on purpose: this runs inside a worker thread
                    # dispatched by main(), which now catches ANY exception
                    # from a dispatch (that's Finding 1's fix) and records
                    # it instead of crashing. A narrower `except
                    # AssertionError` would let a FileNotFoundError from a
                    # missing results.json (the exact failure mode this
                    # test exists to catch) get silently swallowed by
                    # main()'s per-dispatch error handling instead of
                    # failing this test.
                    failures.append(exc)
                return {"triggered": False, "cost_usd": 2.0, "query": kwargs["query"]}
            return {"triggered": True, "cost_usd": 3.0, "query": kwargs["query"]}

        with mock.patch.object(
            rte, "run_single_query", side_effect=fake_run_single_query
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = rte.main(self._argv())

        self.assertEqual(rc, 0)
        if failures:
            raise failures[0]
        self.assertEqual(call_order, ["first query", "second query"])

    def test_earlier_dispatch_error_on_disk_before_later_dispatch_completes(self):
        # This is the branch this delta actually added: the ERROR handler's
        # own `_write_results()` call. On the SECOND dispatch, reads
        # results.json off disk and asserts the FIRST dispatch's *error* is
        # already there -- `partial=True`, an "errors" entry recording the
        # split/query/message, and the failed query NOT silently folded
        # into "results" as a clean non-trigger -- before main() itself has
        # returned. Confirmed red against `git show
        # HEAD:scripts/evals/run_trigger_evals.py`, where the except-block
        # has no error bookkeeping and no per-dispatch write at all: it
        # instead substitutes a fake `{"triggered": False, "cost_usd": 0.0}`
        # result and lets the normal success-path code (and its own
        # _write_results() call further down) record that as if it were a
        # real, clean negative run.
        call_order = []
        failures = []

        def fake_run_single_query(**kwargs):
            call_order.append(kwargs["query"])
            if kwargs["query"] == "first query":
                raise rte.HarnessError(
                    "claude subprocess exited 1 without triggering a skill call "
                    "(query='first query'); stderr tail:\nauth error"
                )
            # num_workers=1 guarantees this dispatch was only submitted
            # after the first dispatch's error handler -- including its
            # _write_results() call -- already ran, so results.json must
            # already reflect the first dispatch's error here.
            try:
                payload = json.loads(self.results_path.read_text(encoding="utf-8"))
                candidate = payload["candidates"]["c1"]
                self.assertTrue(payload["partial"])
                errors_by_query = {e["query"]: e for e in candidate.get("errors", [])}
                self.assertIn("first query", errors_by_query)
                self.assertEqual(errors_by_query["first query"]["split"], "train")
                self.assertIn("auth error", errors_by_query["first query"]["error"])
                results_by_query = {r["query"]: r for r in candidate.get("results", [])}
                self.assertNotIn("first query", results_by_query)
            except Exception as exc:  # noqa: BLE001 -- re-raised on the main thread below
                # Broad on purpose, for the same reason as the sibling test
                # above: this runs inside a worker thread dispatched by
                # main(), which catches ANY exception from a dispatch and
                # records it instead of crashing. A narrower `except
                # AssertionError` would let a FileNotFoundError from a
                # missing results.json get silently swallowed by main()'s
                # per-dispatch error handling instead of failing this test.
                failures.append(exc)
            return {"triggered": False, "cost_usd": 2.0, "query": kwargs["query"]}

        with mock.patch.object(
            rte, "run_single_query", side_effect=fake_run_single_query
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = rte.main(self._argv())

        self.assertEqual(rc, 0)
        if failures:
            raise failures[0]
        self.assertEqual(call_order, ["first query", "second query"])


if __name__ == "__main__":
    unittest.main()
