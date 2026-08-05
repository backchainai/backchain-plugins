#!/usr/bin/env python3
"""Stdlib-only trigger eval harness for a Claude Code skill.

Measures whether a candidate frontmatter `description` makes the model reach
for a skill's `Skill` tool call on its own, unprompted, across a labeled set
of positive and negative queries. It replaces the third-party skill-creator
harness (`skill-creator/scripts/run_loop.py`), which two confirmed defects
and a third silent one drove to a 0% floor: see `docs/decisions/
trigger-eval-isolation.md` for the root-cause writeup.

Design decisions this module encodes (see .daedalus/plans/issue-35.md,
"Design decisions" table, for the full rationale):

- No `--bare`. `claude --bare` registers a skill without making it
  autonomously invocable, which is the opposite of what a trigger eval
  measures. Isolation instead comes from a disposable `--plugin-dir` plus a
  disposable workspace copy, each run getting its own parent temp directory
  with no siblings.
- `detect_trigger` requires an EXACT `<plugin>:<skill>` match. A substring
  test would confuse `trigeval-x:docs` with `trigeval-x:docsprobe`.
- Kill the subprocess the instant a match is detected: the point of the
  measurement is reached, and every further turn only spends money.
- `--tools "Read,Grep,Glob,Bash,Skill"`: no Write/Edit, so a triggered run
  can never complete the expensive write half of a task either.

Usage:

    python3 scripts/evals/run_trigger_evals.py \
      --skill-path scriptorium/skills/docs \
      --eval-set scriptorium/skills/docs/evals/trigger-evals.json \
      --workspace scriptorium/evals/fixtures/trigger-workspace \
      --candidates scriptorium/evals/candidates/docs-2026-08.json \
      --model claude-sonnet-5 --runs-per-query 1 --holdout 0.4 \
      --results-dir scriptorium-workspace/trigger

Exit 0 on a completed run regardless of scores -- a low score is data, not a
harness failure. Exit 1 only when the harness itself could not run (a
missing/empty workspace, a malformed eval set or candidates file, an
unaccountable `--max-cost`, or a subprocess/IO failure).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from collections import namedtuple
from pathlib import Path
from typing import Any, Iterable

DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_TOOLS = "Read,Grep,Glob,Bash,Skill"
DEFAULT_HOLDOUT = 0.4
DEFAULT_SEED = 42
DEFAULT_NUM_WORKERS = 6
DEFAULT_TIMEOUT_S = 180

MANIFEST_FIELDS = (
    "name",
    "description",
    "version",
    "author",
    "license",
    "keywords",
    "category",
    "repository",
    "homepage",
)

RunDirs = namedtuple("RunDirs", ["parent", "plugin_dir", "workspace_dir"])


class HarnessError(RuntimeError):
    """Raised for a harness failure (as opposed to a low score)."""


# --------------------------------------------------------------------------
# Frontmatter handling
# --------------------------------------------------------------------------


def _split_frontmatter(skill_md_text: str) -> tuple[list[str], list[str]]:
    """Splits SKILL.md text into (frontmatter_lines, rest_lines).

    `rest_lines` starts at the closing '---' delimiter (inclusive), so
    `"\n".join(["---"] + frontmatter_lines + rest_lines)` reconstructs the
    original text exactly.
    """
    lines = skill_md_text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise HarnessError("SKILL.md does not begin with a YAML frontmatter delimiter '---'")
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise HarnessError("SKILL.md frontmatter has no closing '---' delimiter")
    return lines[1:end_idx], lines[end_idx:]


def _read_frontmatter_name(skill_md_text: str) -> str:
    frontmatter, _ = _split_frontmatter(skill_md_text)
    for line in frontmatter:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    raise HarnessError("SKILL.md frontmatter has no 'name' field")


def substitute_description(skill_md_text: str, new_description: str) -> str:
    """Frontmatter-only replacement of the `description` field.

    Preserves the body and every other frontmatter key (including `name`)
    byte-for-byte. The new value is emitted as a YAML double-quoted scalar
    with backslash, double-quote, newline, and tab escaped, rather than splicing the raw
    candidate text in -- a candidate description containing a quote, a
    colon, or a newline must not corrupt the frontmatter block.
    """
    frontmatter, rest = _split_frontmatter(skill_md_text)

    escaped = (
        new_description.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r\n", "\n")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    new_line = f'description: "{escaped}"'

    out: list[str] = []
    replaced = False
    for line in frontmatter:
        if line.startswith("description:"):
            out.append(new_line)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(new_line)

    return "\n".join(["---"] + out + rest)


# --------------------------------------------------------------------------
# Plugin materialization
# --------------------------------------------------------------------------


def build_plugin_dir(skill_path: Path | str, description: str, dest: Path | str) -> str:
    """Materializes a throwaway plugin at `dest` carrying one skill.

    Writes `dest/.claude-plugin/plugin.json` (the nine standard manifest
    fields) and copies the skill tree at `skill_path` to
    `dest/skills/<name>/`, substituting only the frontmatter `description`.
    The model sees the real skill body, not a stub.

    The plugin name is `dest.name`; the caller is responsible for making it
    unique across concurrent runs (`trigeval-<uuid>`), since the per-run
    unique plugin name is what makes the `<plugin>:<skill>` id exact-match
    disambiguation in `detect_trigger` work.

    Returns the exact `<plugin>:<skill>` id for the installed skill.
    """
    skill_path = Path(skill_path)
    dest = Path(dest)

    skill_md_src = skill_path / "SKILL.md"
    skill_md_text = skill_md_src.read_text(encoding="utf-8")
    skill_name = _read_frontmatter_name(skill_md_text)

    plugin_name = dest.name
    dest.mkdir(parents=True, exist_ok=True)

    manifest_dir = dest / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": plugin_name,
        "description": f"Throwaway trigger-eval plugin for the {skill_name} skill.",
        "version": "0.0.0",
        "author": {
            "name": "trigger-eval-harness",
            "email": "noreply@example.invalid",
            "url": "https://backchain.ai",
        },
        "license": "Apache-2.0",
        "keywords": ["trigger-eval"],
        "category": "productivity",
        "repository": "https://github.com/backchainai/backchain-plugins",
        "homepage": "https://github.com/backchainai/backchain-plugins",
    }
    assert set(MANIFEST_FIELDS) <= set(manifest)
    (manifest_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    skill_dest = dest / "skills" / skill_name
    if skill_dest.exists():
        shutil.rmtree(skill_dest)
    skill_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_path, skill_dest)

    new_text = substitute_description(skill_md_text, description)
    (skill_dest / "SKILL.md").write_text(new_text, encoding="utf-8")

    return f"{plugin_name}:{skill_name}"


def allocate_run_dirs(prefix: str = "trigeval-run-") -> RunDirs:
    """Allocates a fresh, isolated parent temp directory for one run.

    Each run gets its own top-level parent directory holding exactly two
    children: `plugin/` and `workspace/`. No two runs ever share a parent,
    so one run's workspace can never see a sibling run's directory the way
    probe C did (see the ADR). Callers `shutil.rmtree(dirs.parent)` when
    done, in a `finally`.
    """
    parent = Path(tempfile.mkdtemp(prefix=prefix))
    return RunDirs(parent=parent, plugin_dir=parent / "plugin", workspace_dir=parent / "workspace")


# --------------------------------------------------------------------------
# Trigger detection
# --------------------------------------------------------------------------


def _iter_tool_use_blocks(obj: Any) -> Iterable[dict]:
    """Recursively yields every dict with `type == "tool_use"` inside obj."""
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use":
            yield obj
        for value in obj.values():
            yield from _iter_tool_use_blocks(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_tool_use_blocks(item)


def detect_trigger(stream_lines: Iterable[str], skill_id: str) -> tuple[bool, list[str]]:
    """Scans a `claude -p --output-format stream-json` transcript for a match.

    Reads both complete `assistant` message events (each `tool_use` content
    block fully formed) and `stream_event` partial-message events (a tool_use
    block announced at `content_block_start`, its `input` built up across
    `content_block_delta` events as `partial_json` fragments). A match
    requires `name == "Skill"` and the accumulated `input.skill` EXACTLY
    equal to `skill_id`, the full `<plugin>:<skill>` form -- a substring
    test would let `trigeval-x:docs` match `trigeval-x:docsprobe`.

    Malformed JSON lines are skipped, not raised. Returns
    `(triggered, tools)` where `tools` is every tool name observed, in
    encounter order (diagnostic only). Returns `(False, tools)` if no match
    is found by the end of the stream.
    """
    tools: list[str] = []
    triggered = False
    block_names: dict[Any, str | None] = {}
    block_json: dict[Any, str] = {}

    def _note_match(name: Any, skill_input: Any) -> bool:
        return name == "Skill" and isinstance(skill_input, dict) and skill_input.get("skill") == skill_id

    for raw in stream_lines:
        line = (raw or "").strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(obj, dict):
            continue

        if obj.get("type") == "stream_event":
            event = obj.get("event")
            if not isinstance(event, dict):
                continue
            etype = event.get("type")
            index = event.get("index")

            if etype == "content_block_start":
                block = event.get("content_block")
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    name = block.get("name")
                    block_names[index] = name
                    block_json[index] = ""
                    if name:
                        tools.append(name)
                    if _note_match(name, block.get("input")):
                        triggered = True

            elif etype == "content_block_delta":
                delta = event.get("delta")
                if isinstance(delta, dict) and delta.get("type") == "input_json_delta" and index in block_json:
                    block_json[index] += delta.get("partial_json", "") or ""
                    name = block_names.get(index)
                    if name == "Skill":
                        try:
                            parsed = json.loads(block_json[index])
                        except (json.JSONDecodeError, TypeError, ValueError):
                            parsed = None
                        if _note_match(name, parsed):
                            triggered = True
            continue

        # Non-stream_event top-level messages: scan for complete tool_use
        # blocks anywhere in the payload (assistant messages nest them under
        # message.content[]).
        for block in _iter_tool_use_blocks(obj):
            name = block.get("name")
            if name:
                tools.append(name)
            if _note_match(name, block.get("input")):
                triggered = True

    return triggered, tools


# --------------------------------------------------------------------------
# Eval-set splitting and scoring
# --------------------------------------------------------------------------


def split_eval_set(
    eval_set: list[dict], holdout: float = DEFAULT_HOLDOUT, seed: int = DEFAULT_SEED
) -> tuple[list[dict], list[dict]]:
    """Stratified, seeded split by `should_trigger`. Ported from
    `run_loop.py`'s `split_eval_set` so the split methodology matches the
    original harness. Every item appears in exactly one of the two returned
    lists.
    """
    positives = [item for item in eval_set if item.get("should_trigger")]
    negatives = [item for item in eval_set if not item.get("should_trigger")]

    rng = random.Random(seed)

    def _split_group(group: list[dict]) -> tuple[list[dict], list[dict]]:
        group = list(group)
        rng.shuffle(group)
        n_test = round(len(group) * holdout)
        return group[n_test:], group[:n_test]

    pos_train, pos_test = _split_group(positives)
    neg_train, neg_test = _split_group(negatives)
    return pos_train + neg_train, pos_test + neg_test


def score(results: list[dict], threshold: float = 0.5) -> dict:
    """Scores per-query trigger rates against `threshold`.

    Each item in `results` carries `should_trigger` (bool) and either
    `triggered_runs`/`total_runs` or `trigger_count`/`runs` run-level
    counts. A query passes when `(rate >= threshold) == should_trigger`.
    Returns per-query pass/fail plus precision, recall, and accuracy
    computed over the run-level (predicted vs. actual) counts.
    """
    per_query = []
    tp = fp = fn = tn = 0

    for item in results:
        should = bool(item.get("should_trigger"))
        total = item.get("total_runs", item.get("runs", 1)) or 1
        triggered = item.get("triggered_runs", item.get("trigger_count", 0))
        rate = triggered / total
        predicted = rate >= threshold
        passed = predicted == should

        per_query.append(
            {
                "query": item.get("query"),
                "should_trigger": should,
                "rate": rate,
                "predicted": predicted,
                "passed": passed,
            }
        )

        if predicted and should:
            tp += 1
        elif predicted and not should:
            fp += 1
        elif not predicted and should:
            fn += 1
        else:
            tn += 1

    total_n = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    accuracy = (tp + tn) / total_n if total_n else 0.0

    return {
        "per_query": per_query,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "counts": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


# --------------------------------------------------------------------------
# Auth / cost accounting guards
# --------------------------------------------------------------------------


def detect_auth_mode(env: dict[str, str] | None = None) -> str:
    """Returns "api_key" when `ANTHROPIC_API_KEY` is set (it takes
    precedence over claude.ai OAuth login), else "oauth". Under OAuth,
    `total_cost_usd` may not track real spend, so callers must refuse
    `--max-cost` unless this returns "api_key".
    """
    env = env if env is not None else os.environ
    return "api_key" if env.get("ANTHROPIC_API_KEY") else "oauth"


def assert_workspace_grounded(workspace: Path) -> None:
    """Fails loudly if `workspace` is missing or empty.

    Root cause 3 of the original harness's zero score was exactly this,
    silently: an empty scratch directory gives the model nothing to act on,
    so every positive misses for the wrong reason (nothing to do) and every
    negative passes for the wrong reason (nothing to do). It must never be
    silent again.
    """
    if not workspace.is_dir():
        raise HarnessError(f"--workspace does not exist or is not a directory: {workspace}")
    if not any(workspace.iterdir()):
        raise HarnessError(f"--workspace is empty, the harness would measure nothing: {workspace}")


# --------------------------------------------------------------------------
# Single-query execution
# --------------------------------------------------------------------------


def run_single_query(
    *,
    skill_path: Path,
    description: str,
    workspace: Path,
    query: str,
    model: str = DEFAULT_MODEL,
    tools: str = DEFAULT_TOOLS,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Runs one query against one candidate description in an isolated
    workspace.

    Materializes a throwaway `trigeval-<uuid>` plugin directory and a fresh
    copy of `workspace` under their own parent temp directory (no
    siblings -- see `allocate_run_dirs`), runs `claude -p` with `CLAUDECODE`
    unset and `--tools` restricted so no run can complete the expensive
    write half of a task, and terminates the subprocess the instant
    `detect_trigger` reports a match. Both directories are torn down in a
    `finally`, regardless of outcome.

    Returns a dict with `skill_id`, `query`, `triggered`, `tools`,
    `cost_usd`, `auth_mode`, and `elapsed_s`.
    """
    run_id = uuid.uuid4().hex[:12]
    dirs = allocate_run_dirs(prefix=f"trigeval-{run_id}-")
    try:
        plugin_dir = dirs.parent / f"trigeval-{run_id}"
        skill_id = build_plugin_dir(skill_path, description, plugin_dir)

        workspace = Path(workspace)
        if workspace.is_dir():
            shutil.copytree(workspace, dirs.workspace_dir)
        else:
            dirs.workspace_dir.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env.pop("CLAUDECODE", None)
        auth_mode = detect_auth_mode(env)

        cmd = [
            "claude",
            "-p",
            query,
            "--plugin-dir",
            str(plugin_dir),
            "--tools",
            tools,
            "--model",
            model,
            "--output-format",
            "stream-json",
            "--verbose",
        ]

        start = time.monotonic()
        proc = subprocess.Popen(
            cmd,
            cwd=str(dirs.workspace_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stream_lines: list[str] = []
        triggered = False
        tools_seen: list[str] = []
        try:
            assert proc.stdout is not None
            while True:
                if timeout is not None and (time.monotonic() - start) > timeout:
                    raise HarnessError(f"run_single_query exceeded --timeout ({timeout}s): {query!r}")
                line = proc.stdout.readline()
                if line == "" and proc.poll() is not None:
                    break
                if not line:
                    continue
                stream_lines.append(line)
                triggered, tools_seen = detect_trigger(stream_lines, skill_id)
                if triggered:
                    break
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)

        cost = 0.0
        for raw in stream_lines:
            try:
                obj = json.loads(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
            if isinstance(obj, dict) and obj.get("type") == "result":
                cost = obj.get("total_cost_usd", cost) or cost

        return {
            "skill_id": skill_id,
            "query": query,
            "triggered": triggered,
            "tools": tools_seen,
            "cost_usd": cost,
            "auth_mode": auth_mode,
            "elapsed_s": time.monotonic() - start,
        }
    finally:
        shutil.rmtree(dirs.parent, ignore_errors=True)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _load_eval_set(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"could not read --eval-set {path}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise HarnessError(f"--eval-set must be a non-empty JSON array of query objects: {path}")
    for item in data:
        if "query" not in item or "should_trigger" not in item:
            raise HarnessError(f"--eval-set item missing 'query' or 'should_trigger': {item!r}")
    return data


def _load_candidates(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"could not read --candidates {path}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise HarnessError(f"--candidates must be a non-empty JSON array of {{name, description}}: {path}")
    for item in data:
        if "name" not in item or "description" not in item:
            raise HarnessError(f"--candidates item missing 'name' or 'description': {item!r}")
    return data


def _render_markdown_table(candidate_name: str, split_name: str, scored: dict) -> str:
    lines = [
        f"### {candidate_name} -- {split_name}",
        "",
        f"accuracy={scored['accuracy']:.2f} precision={scored['precision']:.2f} recall={scored['recall']:.2f}",
        "",
        "| query | should_trigger | rate | result |",
        "|---|---|---|---|",
    ]
    for row in scored["per_query"]:
        result = "PASS" if row["passed"] else "FAIL"
        query_short = (row["query"] or "")[:60]
        lines.append(f"| {query_short} | {row['should_trigger']} | {row['rate']:.2f} | {result} |")
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skill-path", required=True, type=Path)
    parser.add_argument("--eval-set", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--runs-per-query", type=int, default=1)
    parser.add_argument("--holdout", type=float, default=DEFAULT_HOLDOUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--max-cost", type=float, default=None)
    parser.add_argument("--num-workers", type=int, default=DEFAULT_NUM_WORKERS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--tools", default=DEFAULT_TOOLS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    try:
        assert_workspace_grounded(args.workspace)
        eval_set = _load_eval_set(args.eval_set)
        candidates = _load_candidates(args.candidates)

        auth_mode = detect_auth_mode()
        if args.max_cost is not None and auth_mode != "api_key":
            raise HarnessError(
                "--max-cost requires ANTHROPIC_API_KEY auth: total_cost_usd may not track real "
                "spend under subscription OAuth, which would silently disarm the cost cap"
            )

        train, test = split_eval_set(eval_set, holdout=args.holdout, seed=args.seed)
    except HarnessError as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return 1

    args.results_dir.mkdir(parents=True, exist_ok=True)

    total_cost = 0.0
    partial = False
    all_results: dict[str, dict] = {}

    from concurrent.futures import ThreadPoolExecutor, as_completed

    for candidate in candidates:
        name = candidate["name"]
        description = candidate["description"]
        budget_exceeded = False

        splits = {"train": train, "test": test}
        tasks = []
        for split_name, items in splits.items():
            for item in items:
                for _ in range(max(1, args.runs_per_query)):
                    tasks.append((split_name, item))

        per_query_counts: dict[tuple[str, str], dict] = {}

        with ThreadPoolExecutor(max_workers=max(1, args.num_workers)) as pool:
            futures = {}
            for split_name, item in tasks:
                if budget_exceeded:
                    break
                future = pool.submit(
                    run_single_query,
                    skill_path=args.skill_path,
                    description=description,
                    workspace=args.workspace,
                    query=item["query"],
                    model=args.model,
                    tools=args.tools,
                    timeout=args.timeout,
                )
                futures[future] = (split_name, item)

            for future in as_completed(futures):
                split_name, item = futures[future]
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001 -- surfaced as a per-run failure, not a crash
                    print(f"ERROR  run failed for {name!r} / {item['query']!r}: {exc}", file=sys.stderr)
                    result = {"triggered": False, "cost_usd": 0.0, "query": item["query"]}

                total_cost += result.get("cost_usd", 0.0) or 0.0
                key = (split_name, item["query"])
                bucket = per_query_counts.setdefault(
                    key,
                    {
                        "query": item["query"],
                        "should_trigger": item["should_trigger"],
                        "split": split_name,
                        "triggered_runs": 0,
                        "total_runs": 0,
                    },
                )
                bucket["total_runs"] += 1
                if result.get("triggered"):
                    bucket["triggered_runs"] += 1

                if args.max_cost is not None and total_cost > args.max_cost:
                    budget_exceeded = True
                    partial = True
                    print(
                        f"ERROR  --max-cost ${args.max_cost:.2f} exceeded (total ${total_cost:.2f}); "
                        "aborting remaining dispatches for this candidate",
                        file=sys.stderr,
                    )

        candidate_results = list(per_query_counts.values())
        all_results[name] = {
            "description": description,
            "results": candidate_results,
        }

        for split_name in ("train", "test"):
            split_results = [r for r in candidate_results if r["split"] == split_name]
            if not split_results:
                continue
            scored = score(split_results)
            all_results[name][f"{split_name}_score"] = scored
            print(_render_markdown_table(name, split_name, scored))
            print()

        if budget_exceeded:
            break

    output = {
        "model": args.model,
        "auth_mode": auth_mode,
        "total_cost_usd": total_cost,
        "partial": partial,
        "candidates": all_results,
    }
    (args.results_dir / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print(f"total cost: ${total_cost:.2f} (auth: {auth_mode})", file=sys.stderr)
    if partial:
        print("WARNING  run stopped early on --max-cost; results.json is partial", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
