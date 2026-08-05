#!/usr/bin/env python3
"""Stdlib unittest suite for run_trigger_evals.py.

No model calls, no network, no `claude` subprocess. Every case here is pure
data-in/data-out against the harness's independently testable functions:
`detect_trigger`, `substitute_description`, `build_plugin_dir`,
`split_eval_set`, `score`, and the workspace-isolation helper
`allocate_run_dirs`.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

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

    def test_result_parses_as_yaml_frontmatter(self):
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
        dest = self.tmp / "trigeval-deadbeef1234"
        rte.build_plugin_dir(self.skill_path, "A candidate description.", dest)

        manifest_path = dest / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field in rte.MANIFEST_FIELDS:
            self.assertIn(field, manifest, f"manifest missing field {field!r}")
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
        eval_set = _make_eval_set(10, 10)
        train, test = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        self.assertEqual(len(train), 12)
        self.assertEqual(len(test), 8)

    def test_deterministic_under_fixed_seed(self):
        eval_set = _make_eval_set(10, 10)
        train1, test1 = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        train2, test2 = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        self.assertEqual([q["query"] for q in train1], [q["query"] for q in train2])
        self.assertEqual([q["query"] for q in test1], [q["query"] for q in test2])

    def test_different_seed_can_differ(self):
        eval_set = _make_eval_set(10, 10)
        train_a, _ = rte.split_eval_set(eval_set, holdout=0.4, seed=42)
        train_b, _ = rte.split_eval_set(eval_set, holdout=0.4, seed=7)
        self.assertNotEqual(
            [q["query"] for q in train_a],
            [q["query"] for q in train_b],
        )

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
    def test_two_concurrent_runs_get_different_non_sibling_parent_dirs(self):
        run1 = rte.allocate_run_dirs()
        run2 = rte.allocate_run_dirs()
        try:
            self.assertNotEqual(run1.parent, run2.parent)
            # Neither run's directory tree is nested inside the other's.
            self.assertNotIn(run2.parent, run1.parent.parents)
            self.assertNotIn(run1.parent, run2.parent.parents)
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


if __name__ == "__main__":
    unittest.main()
