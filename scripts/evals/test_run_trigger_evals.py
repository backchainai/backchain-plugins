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
from pathlib import Path
from unittest import mock

import run_trigger_evals as rte


# --------------------------------------------------------------------------
# detect_trigger
# --------------------------------------------------------------------------


class DetectTriggerTest(unittest.TestCase):
    def test_skill_at_tool_position_three_behind_bash_and_read(self):
        # Probe B's stream, checked in as a fixture: Bash, Read, then Skill
        # as the third tool call. detect_trigger must not abort at the first
        # non-Skill tool the way the old harness's `else: return False` did.
        skill_id = "docsprobe-plugin:docsprobe"
        stream_lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}
                        ]
                    },
                }
            ),
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t2",
                                "name": "Read",
                                "input": {"file_path": "/tmp/x.md"},
                            }
                        ]
                    },
                }
            ),
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t3",
                                "name": "Skill",
                                "input": {"skill": skill_id},
                            }
                        ]
                    },
                }
            ),
        ]
        triggered, tools = rte.detect_trigger(stream_lines, skill_id)
        self.assertTrue(triggered)
        self.assertEqual(tools, ["Bash", "Read", "Skill"])

    def test_near_miss_different_skill_not_detected(self):
        # trigeval-x:docs vs trigeval-x:docsprobe: substring matching would
        # confuse these. Exact match must not.
        stream_lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t1",
                                "name": "Skill",
                                "input": {"skill": "trigeval-x:docsprobe"},
                            }
                        ]
                    },
                }
            )
        ]
        triggered, tools = rte.detect_trigger(stream_lines, "trigeval-x:docs")
        self.assertFalse(triggered)
        self.assertEqual(tools, ["Skill"])

    def test_near_miss_reverse_direction(self):
        stream_lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t1",
                                "name": "Skill",
                                "input": {"skill": "trigeval-x:docs"},
                            }
                        ]
                    },
                }
            )
        ]
        triggered, _ = rte.detect_trigger(stream_lines, "trigeval-x:docsprobe")
        self.assertFalse(triggered)

    def test_no_skill_call_returns_false(self):
        stream_lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}
                        ]
                    },
                }
            ),
            json.dumps({"type": "result", "total_cost_usd": 0.02}),
        ]
        triggered, tools = rte.detect_trigger(stream_lines, "trigeval-x:docs")
        self.assertFalse(triggered)
        self.assertEqual(tools, ["Bash"])

    def test_malformed_json_lines_are_skipped(self):
        stream_lines = [
            "not json at all {{{",
            "",
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t1",
                                "name": "Skill",
                                "input": {"skill": "trigeval-x:docs"},
                            }
                        ]
                    },
                }
            ),
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
        # plugin") rather than looping over rte.MANIFEST_FIELDS: comparing
        # against the constant the implementation itself owns would not
        # catch a field silently dropped from both the constant and the
        # manifest it builds.
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
        self.assertEqual(len(rte.MANIFEST_FIELDS), 9)
        self.assertEqual(sorted(rte.MANIFEST_FIELDS), expected_fields)

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


class MainHarnessErrorTest(unittest.TestCase):
    """`main([...])` returns 1 (never raises) for every harness-level
    failure: an unaccountable --max-cost, a malformed --eval-set, and a
    malformed --candidates file. No model call, no `claude` subprocess --
    every case here fails before any dispatch is ever submitted."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="trigeval-main-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        (self.workspace / "file.md").write_text("content\n", encoding="utf-8")

        self.eval_set_path = self.tmp / "trigger-evals.json"
        self.eval_set_path.write_text(
            json.dumps([{"query": "do a thing", "should_trigger": True}]),
            encoding="utf-8",
        )

        self.candidates_path = self.tmp / "candidates.json"
        self.candidates_path.write_text(
            json.dumps([{"name": "c1", "description": "A description."}]),
            encoding="utf-8",
        )

        self.skill_path = self.tmp / "skill"
        self.skill_path.mkdir()

        self.results_dir = self.tmp / "results"

    def _base_argv(self):
        return [
            "--skill-path", str(self.skill_path),
            "--eval-set", str(self.eval_set_path),
            "--workspace", str(self.workspace),
            "--candidates", str(self.candidates_path),
            "--results-dir", str(self.results_dir),
        ]

    def test_max_cost_without_api_key_auth_returns_one(self):
        argv = self._base_argv() + ["--max-cost", "5"]
        with mock.patch.dict("os.environ", {}, clear=True):
            rc = rte.main(argv)
        self.assertEqual(rc, 1)

    def test_malformed_eval_set_json_returns_one(self):
        self.eval_set_path.write_text("not json {{{", encoding="utf-8")
        self.assertEqual(rte.main(self._base_argv()), 1)

    def test_eval_set_item_missing_required_key_returns_one(self):
        self.eval_set_path.write_text(json.dumps([{"query": "x"}]), encoding="utf-8")
        self.assertEqual(rte.main(self._base_argv()), 1)

    def test_malformed_candidates_json_returns_one(self):
        self.candidates_path.write_text("not json {{{", encoding="utf-8")
        self.assertEqual(rte.main(self._base_argv()), 1)

    def test_candidates_item_missing_required_key_returns_one(self):
        self.candidates_path.write_text(json.dumps([{"name": "c1"}]), encoding="utf-8")
        self.assertEqual(rte.main(self._base_argv()), 1)


# --------------------------------------------------------------------------
# --max-cost abort behavior (Defect A)
# --------------------------------------------------------------------------


class MaxCostAbortTest(unittest.TestCase):
    """Drives `main()`'s dispatch loop with a fake, fixed-cost
    `run_single_query` (no model call, no subprocess, no network) and
    asserts that `--max-cost` actually bounds the number of dispatches made,
    rather than only printing a message after every query already ran."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="trigeval-maxcost-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        (self.workspace / "file.md").write_text("content\n", encoding="utf-8")

        # 6 positive + 6 negative queries: plenty of work to bound. At
        # $5/call and --max-cost 12, a correct harness stops well short of
        # running all 12.
        eval_set = [{"query": f"positive {i}", "should_trigger": True} for i in range(6)] + [
            {"query": f"negative {i}", "should_trigger": False} for i in range(6)
        ]
        self.eval_set_path = self.tmp / "trigger-evals.json"
        self.eval_set_path.write_text(json.dumps(eval_set), encoding="utf-8")

        self.candidates_path = self.tmp / "candidates.json"
        self.candidates_path.write_text(
            json.dumps([{"name": "c1", "description": "A description."}]),
            encoding="utf-8",
        )

        self.skill_path = self.tmp / "skill"
        self.skill_path.mkdir()

        self.results_dir = self.tmp / "results"

    def _argv(self, *, max_cost, num_workers):
        return [
            "--skill-path", str(self.skill_path),
            "--eval-set", str(self.eval_set_path),
            "--workspace", str(self.workspace),
            "--candidates", str(self.candidates_path),
            "--results-dir", str(self.results_dir),
            "--holdout", "0.0",
            "--num-workers", str(num_workers),
            "--max-cost", str(max_cost),
        ]

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


if __name__ == "__main__":
    unittest.main()
