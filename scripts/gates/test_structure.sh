#!/usr/bin/env bash
# Self-test for scripts/gates/structure.sh.
#
# Red/green harness: builds a throwaway fixture repo per case, runs the real
# gate against it, and checks the gate's exit code and output. bash + git +
# stdlib python3 only, no third-party dependencies.
#
# This harness's own top-level invocation need not itself be guarded against
# recursion: the guard is depth-independent because Stage D re-exports
# GATE_SELFTEST=1 to whatever self-test it invokes (the gate header's
# `Recursion guard:` paragraph), and build_fixture (below) never copies this
# harness into a fixture, so the gate under test can never reach back into
# test_structure.sh. run_gate_stage_d exploits that: it is the one runner
# that clears GATE_SELFTEST, deliberately letting Stage D execute.
#
# python3 is a hard requirement of this harness (several cases exercise
# Stage C, the python-suite stage). Rather than skip individual cases when
# python3 is missing -- which used to let some cases report false success
# and others fail with a misleading message -- the harness checks once, up
# front, and fails outright if python3 is not available.
#
# Each Stage E case asserts on a diagnostic substring unique to the branch
# under test, not on a fixture literal (e.g. "demo-plugin") that other
# branches also echo back.
#
# Exit 0 iff every case passed. Exit 1 if any case failed.
set -uo pipefail

self_dir=$(cd "$(dirname "$0")" && pwd)
gate="$self_dir/structure.sh"

if [ ! -f "$gate" ]; then
  echo "FAIL  gate not found: $gate"
  exit 1
fi

command -v python3 >/dev/null 2>&1 || {
  echo "FAIL  python3 not found; this harness requires python3 to exercise the gate's Stage C (python suite) cases"
  exit 1
}

overall=0

# build_fixture <tmp> <assertion>
# Lays down a minimal plugin repo under $tmp:
#   plug/skills/demo/SKILL.md        -- valid frontmatter (name: demo)
#   plug/.claude-plugin/plugin.json  -- valid JSON
#   plug/skills/demo/scripts/test_demo.py -- stdlib unittest, assertion controlled by caller
#   .claude-plugin/marketplace.json  -- one entry: name demo-plugin, source ./plug
#   README.md                        -- lists "demo-plugin", so the fixture is
#                                        green for Stage E out of the box
#
# build_fixture and _run_gate (below) deliberately do not declare their own
# `local tmp`/`out`/`rc`/`assertion`. Every case function below declares
# those names `local` itself; because bash resolves unqualified assignments
# dynamically up the call stack, an assignment inside build_fixture/_run_gate
# lands in the nearest enclosing `local` of the same name -- i.e. the calling
# case's own variable -- rather than a shared global. That gives each case
# an isolated tmp/out/rc without having to thread return values through
# explicit output parameters.
build_fixture() {
  tmp="$1"
  assertion="$2" # "pass" -> 1 == 1, "fail" -> 1 == 2

  git init -q "$tmp"
  git -C "$tmp" config user.email "gate-selftest@example.invalid"
  git -C "$tmp" config user.name "gate-selftest"

  mkdir -p "$tmp/scripts/gates"
  cp "$gate" "$tmp/scripts/gates/structure.sh"
  chmod +x "$tmp/scripts/gates/structure.sh"

  mkdir -p "$tmp/plug/skills/demo/scripts"
  mkdir -p "$tmp/plug/.claude-plugin"

  cat >"$tmp/plug/skills/demo/SKILL.md" <<'EOF'
---
name: demo
description: A demo skill fixture used by the gate self-test.
---

# demo

Fixture content.
EOF

  cat >"$tmp/plug/.claude-plugin/plugin.json" <<'EOF'
{
  "name": "demo-plugin",
  "version": "0.0.0"
}
EOF

  mkdir -p "$tmp/.claude-plugin"
  cat >"$tmp/.claude-plugin/marketplace.json" <<'EOF'
{
  "plugins": [
    {
      "name": "demo-plugin",
      "source": "./plug"
    }
  ]
}
EOF

  cat >"$tmp/README.md" <<'EOF'
# fixture

demo-plugin is listed here.
EOF

  if [ "$assertion" = "pass" ]; then
    rhs=1
  else
    rhs=2
  fi

  cat >"$tmp/plug/skills/demo/scripts/test_demo.py" <<EOF
#!/usr/bin/env python3
import unittest


class DemoTest(unittest.TestCase):
    def test_demo(self):
        self.assertEqual(1, $rhs)


if __name__ == "__main__":
    unittest.main()
EOF

  git -C "$tmp" add -A
}

# _run_gate <tmp> <GATE_SELFTEST value> -> writes combined output to $out,
# exit code to $rc. Verifies the fixture actually has a .git directory before
# running the gate so a build_fixture failure (e.g. `git init` failing)
# surfaces as a harness failure instead of being interpreted as the gate
# having gone red.
_run_gate() {
  tmp="$1"
  local selftest="$2"
  if [ ! -d "$tmp/.git" ]; then
    out="fixture at $tmp has no .git directory (build_fixture likely failed)"
    rc=1
    return
  fi
  out=$(cd "$tmp" && GATE_SELFTEST="$selftest" bash scripts/gates/structure.sh 2>&1)
  rc=$?
}

# run_gate <tmp> -- runs the gate with GATE_SELFTEST=1, so Stage D is skipped
# by the recursion guard. This is the runner every case uses except the pair
# below that exercises Stage D directly.
run_gate() { _run_gate "$1" 1; }

# run_gate_stage_d <tmp> -- like run_gate, but clears GATE_SELFTEST so Stage
# D actually executes instead of being skipped by the recursion guard.
# GATE_SELFTEST= (not just omitted) clears any value this harness itself
# inherited -- e.g. when structure.sh's own Stage D invokes this harness
# with GATE_SELFTEST=1, that value is exported into this process's
# environment and would otherwise leak into every subshell here, silently
# skipping the Stage D behavior this runner exists to exercise.
#
# Invariant: build_fixture copies only structure.sh into the fixture's
# scripts/gates/, never this harness (test_structure.sh) -- and Stage D
# exports GATE_SELFTEST=1 for every self-test it invokes (the gate header's
# `Recursion guard:` paragraph), so the recursion guard is depth-independent
# rather than relying on this top-level invocation being guarded too. A
# fixture that ever copies this harness into scripts/gates/ must not use
# this runner, or the self-test would recurse into itself.
run_gate_stage_d() { _run_gate "$1" ""; }

# write_marketplace <tmp> -- reads manifest JSON on stdin, overwrites the
# fixture's .claude-plugin/marketplace.json, and restages the fixture tree.
write_marketplace() {
  cat >"$1/.claude-plugin/marketplace.json"
  git -C "$1" add -A
}

# write_selftest_fixture <tmp> <sentinel> -- writes an executable
# scripts/gates/test_fixture.sh into the fixture that touches <sentinel> and
# exits 0. Shared by the tracked-runs/untracked-refused control pair below,
# whose validity depends on the two fixtures being identical. Staging is
# left to the call site, since that is the one line that distinguishes the
# two cases.
write_selftest_fixture() {
  cat >"$1/scripts/gates/test_fixture.sh" <<EOF
#!/usr/bin/env bash
touch "$2"
exit 0
EOF
  chmod +x "$1/scripts/gates/test_fixture.sh"
}

case_green() {
  local name="green (passing python suite)"
  local tmp out rc pycache
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  run_gate "$tmp"
  # ADVISORY 6: a suite that runs zero tests (e.g. `python3 -c ""` in place
  # of `unittest`) must not be indistinguishable from one that actually ran,
  # so also require an explicit "Ran N tests" line with N >= 1.
  # BLOCKING 2: PYTHONDONTWRITEBYTECODE=1 must keep __pycache__ out of the
  # fixture tree, since Stage C's own discovery glob later scans that same
  # tree with --others; a stray __pycache__ there would pollute it.
  pycache=$(find "$tmp" -name __pycache__ -type d)
  if [ "$rc" -eq 0 ] \
    && printf '%s' "$out" | grep -q "PASS  python suite" \
    && printf '%s' "$out" | grep -qE 'Ran [1-9][0-9]* tests?' \
    && printf '%s' "$out" | grep -q "PASS  marketplace entries resolve (1 plugins)" \
    && [ -z "$pycache" ]; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc)"
  printf '%s\n' "$out"
  if [ -n "$pycache" ]; then
    echo "FAIL  $name: __pycache__ written under fixture tree despite PYTHONDONTWRITEBYTECODE=1:"
    printf '%s\n' "$pycache"
  fi
  return 1
}

case_red_python_tracked() {
  # Retargeted from the old case_red_python, which proved untracked
  # discovery works -- the behavior this issue removes. This case now pins
  # the tracked-execution path: build_fixture "$tmp" fail stages a failing
  # suite via `git add -A`, so Stage C must still find and run it via
  # `git ls-files --cached`.
  local name="red-on-python (failing tracked python suite)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" fail >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "FAIL  python suite: plug/skills/demo/scripts/test_demo.py"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1)"
  printf '%s\n' "$out"
  return 1
}

case_untracked_python_refused() {
  # Acceptance criterion 4: an untracked python suite must be refused, not
  # executed. Remove the tracked suite and stage the removal, then write an
  # UNSTAGED test_demo.py whose first module-level statement writes a
  # sentinel file, so any execution at all -- including a bare import --
  # leaves evidence. The sentinel is the load-bearing assertion: absence of
  # output could be explained by a swallowed stream, absence of the sentinel
  # cannot. It also makes a future re-widening of the glob back to
  # --cached --others fail this case mechanically.
  local name="untracked-python-refused (unstaged python suite is refused, not executed)"
  local tmp out rc sentinel
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  rm -f "$tmp/plug/skills/demo/scripts/test_demo.py"
  git -C "$tmp" add -A >/dev/null 2>&1
  sentinel="$tmp/sentinel_untracked_python_ran"
  cat >"$tmp/plug/skills/demo/scripts/test_demo.py" <<EOF
#!/usr/bin/env python3
import pathlib
pathlib.Path("$sentinel").write_text("ran")
import unittest


class DemoTest(unittest.TestCase):
    def test_demo(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
EOF
  run_gate "$tmp"
  # The refusal text and the file path are asserted as a single anchored grep
  # (not two independent greps) so a gate that emits the refusal for one file
  # and the target path on an unrelated line cannot pass. The NOTE-suppression
  # check pins the other half of the Stage C change: "no python test suites
  # found" fires only when both the tracked and untracked lists are empty, so
  # reverting that condition to `[ -z "$py_tracked" ]` would print the NOTE
  # alongside the refusal (py_tracked is empty here, only py_untracked has an
  # entry) even though a suite plainly exists -- this assertion catches that.
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "untracked python suite, refusing to execute.*plug/skills/demo/scripts/test_demo.py" \
    && [ ! -f "$sentinel" ] \
    && ! printf '%s' "$out" | grep -qE 'Ran [0-9]+ test' \
    && ! printf '%s' "$out" | grep -q "no python test suites found"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with anchored refusal diagnostic, sentinel absent, no 'Ran N test' line, no NOTE suppression)"
  printf '%s\n' "$out"
  [ -f "$sentinel" ] && echo "FAIL  $name: sentinel file exists, suite was executed despite refusal: $sentinel"
  return 1
}

case_untracked_skill_still_discovered() {
  # Acceptance criterion 3: Stages A and B must keep discovering untracked
  # files via `git ls-files --cached --others --exclude-standard` (unlike
  # Stage C/D, which narrow to tracked-only execution). Drops an UNSTAGED
  # SKILL.md with a mismatched frontmatter name into the fixture and asserts
  # Stage A still catches it. Narrowing Stage A's discovery glob to --cached
  # would leave plug/skills/demo2/SKILL.md invisible (it is never staged)
  # and the gate would wrongly report ok.
  local name="untracked-skill-still-discovered (unstaged mismatched SKILL.md still caught by Stage A)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  mkdir -p "$tmp/plug/skills/demo2"
  cat >"$tmp/plug/skills/demo2/SKILL.md" <<'EOF'
---
name: not-demo2
description: An unstaged skill fixture proving Stage A still discovers untracked SKILL.md files.
---

# demo2

Fixture content.
EOF
  # Deliberately left unstaged.
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "frontmatter name 'not-demo2' does not match directory 'demo2'"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with frontmatter mismatch naming demo2)"
  printf '%s\n' "$out"
  return 1
}

case_red_skill() {
  # Characterization test: Stage A (SKILL.md frontmatter contract) is ported
  # behavior, not behavior introduced by this gate -- this case pins it.
  local name="red-on-skill (SKILL.md name mismatch)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  sed -i.bak 's/^name: demo$/name: not-demo/' "$tmp/plug/skills/demo/SKILL.md"
  rm -f "$tmp/plug/skills/demo/SKILL.md.bak"
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "frontmatter name 'not-demo'"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1)"
  printf '%s\n' "$out"
  return 1
}

case_red_json() {
  # Characterization test: Stage B (tracked-JSON validity) is ported
  # behavior, not behavior introduced by this gate -- this case pins it.
  local name="red-on-json (corrupted tracked JSON)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  printf '{ not valid json' >"$tmp/plug/.claude-plugin/plugin.json"
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "invalid JSON"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1)"
  printf '%s\n' "$out"
  return 1
}

case_no_suites() {
  local name="no-suites (no test_*.py present)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  rm -f "$tmp/plug/skills/demo/scripts/test_demo.py"
  git -C "$tmp" add -A
  run_gate "$tmp"
  # BLOCKING 3: rc -eq 0 alone cannot distinguish "Stage C ran and found
  # nothing to do" from "Stage C is absent entirely" -- both are clean
  # exits. Require the specific NOTE line Stage C emits when it skips.
  if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q "no python test suites found"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 0 with 'no python test suites found')"
  printf '%s\n' "$out"
  return 1
}

case_multi_failure() {
  # ADVISORY 7: a gate whose stages short-circuit via `exit 1` instead of
  # accumulating `fail=1` looks identical to a correct gate under every
  # single-failure fixture above (both stop at exit 1). Only a fixture that
  # carries two independent failures at once can tell them apart: a
  # short-circuiting gate reports just the first failure it hits, while the
  # real gate reports both.
  local name="multi-failure (SKILL.md name mismatch + failing python suite together)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" fail >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  sed -i.bak 's/^name: demo$/name: not-demo/' "$tmp/plug/skills/demo/SKILL.md"
  rm -f "$tmp/plug/skills/demo/SKILL.md.bak"
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "frontmatter name 'not-demo'" \
    && printf '%s' "$out" | grep -q "FAIL  python suite: plug/skills/demo/scripts/test_demo.py"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with both the frontmatter and python-suite diagnostics)"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_source_missing() {
  # Stage E: marketplace entry whose source directory does not exist. An
  # unresolvable entry must FAIL loudly here, not get masked behind a
  # swallowed jq error.
  local name="red-on-marketplace (source directory does not exist)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": [
    {
      "name": "demo-plugin",
      "source": "./does-not-exist"
    }
  ]
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "source directory does not exist" \
    && printf '%s' "$out" | grep -q "does-not-exist"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 naming the missing source)"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_missing_source() {
  # Stage E: marketplace entry that has a name but no "source" field at all
  # (as opposed to case_red_marketplace_source_missing, where source is
  # present but points at a directory that does not exist). Pins the
  # `[ -z "$source" ]` branch, which no other case exercises.
  local name="red-on-marketplace (entry missing source field)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": [
    {
      "name": "demo-plugin"
    }
  ]
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "has no source" \
    && printf '%s' "$out" | grep -q "demo-plugin"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'has no source' naming demo-plugin)"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_missing_manifest() {
  # Stage E: marketplace entry whose source directory EXISTS but contains no
  # .claude-plugin/plugin.json. Distinct from
  # case_red_marketplace_source_missing (source directory absent): here the
  # source-directory-exists check passes, so control genuinely reaches the
  # `[ ! -f "$plugin_manifest" ]` branch rather than short-circuiting on the
  # earlier check.
  local name="red-on-marketplace (source directory exists but has no plugin manifest)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  mkdir -p "$tmp/plug3"
  cat >"$tmp/plug3/README.md" <<'EOF'
placeholder file so plug3 exists as a real directory with no plugin manifest
EOF
  cat >"$tmp/.claude-plugin/marketplace.json" <<'EOF'
{
  "plugins": [
    {
      "name": "demo-plugin",
      "source": "./plug3"
    }
  ]
}
EOF
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "missing plugin manifest" \
    && printf '%s' "$out" | grep -q "plug3/.claude-plugin/plugin.json"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'missing plugin manifest' naming plug3/.claude-plugin/plugin.json)"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_wrong_dir() {
  # Stage E: marketplace entry name does not match the plugin manifest at
  # its source. Pins the name-mismatch diagnostic against a fixture that is
  # otherwise byte-identical to a correct one.
  local name="red-on-marketplace (entry name does not match plugin manifest name)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  mkdir -p "$tmp/plug2/.claude-plugin"
  cat >"$tmp/plug2/.claude-plugin/plugin.json" <<'EOF'
{
  "name": "other-plugin",
  "version": "0.0.0"
}
EOF
  cat >"$tmp/.claude-plugin/marketplace.json" <<'EOF'
{
  "plugins": [
    {
      "name": "demo-plugin",
      "source": "./plug2"
    }
  ]
}
EOF
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "demo-plugin" \
    && printf '%s' "$out" | grep -q "other-plugin" \
    && printf '%s' "$out" | grep -q "does not match plugin manifest name"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 naming both demo-plugin and other-plugin, with 'does not match plugin manifest name')"
  printf '%s\n' "$out"
  return 1
}

case_red_readme_missing_entry() {
  # Stage E: marketplace entry not listed in root README.md. README.md
  # stays present and non-empty; only the listing for this entry is
  # removed.
  local name="red-on-marketplace (entry not listed in README.md)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  cat >"$tmp/README.md" <<'EOF'
# fixture

nothing listed here.
EOF
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "not listed in README.md" \
    && printf '%s' "$out" | grep -q "demo-plugin"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 naming demo-plugin as not listed in README.md)"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_dash_name() {
  # Stage E: marketplace entry name begins with '-' ("-r"). Pins the missing
  # `--` end-of-options separator in the README-listing grep: without it,
  # grep parses "$name" as the "-r" (recursive) option instead of a pattern,
  # leaving "$readme" as the sole remaining argument -- which grep then
  # treats as the PATTERN, recursively scanning the fixture tree instead of
  # searching README.md's contents. leak.txt embeds the fixture's own
  # resolved README.md path so that recursive scan finds a spurious match,
  # concretely reproducing the silent-PASS the missing `--` allows: without
  # the fix this case observes a PASS instead of the expected FAIL.
  local name="red-on-marketplace (entry name '-r' not listed in README.md)"
  local tmp out rc root_resolved
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  cat >"$tmp/plug/.claude-plugin/plugin.json" <<'EOF'
{
  "name": "-r",
  "version": "0.0.0"
}
EOF
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": [
    {
      "name": "-r",
      "source": "./plug"
    }
  ]
}
EOF
  root_resolved=$(git -C "$tmp" rev-parse --show-toplevel)
  printf '%s/README.md\n' "$root_resolved" >"$tmp/plug/leak.txt"
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "not listed in README.md"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'not listed in README.md')"
  printf '%s\n' "$out"
  return 1
}

case_red_readme_missing() {
  # Stage E: no README.md exists at the repo root at all. Distinct from
  # case_red_readme_missing_entry, which deliberately keeps README.md
  # present and only removes the entry's listing -- that case exercises
  # only the `elif` sibling. Flipping `[ ! -f "$readme" ]` to false leaves
  # every other case green, so only this case pins the branch.
  local name="red-on-marketplace (README.md file not found)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  rm -f "$tmp/README.md"
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "cannot be verified against README.md"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'cannot be verified against README.md')"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_empty_plugins() {
  # Stage E: marketplace manifest present but resolving to zero plugin
  # entries (empty "plugins" array). Distinct from case_no_marketplace,
  # where the manifest file itself is absent -- a manifest that exists with
  # no entries is a structural defect, not a clean skip.
  local name="red-on-marketplace (empty plugins array)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": []
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "marketplace manifest has no plugin entries"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'marketplace manifest has no plugin entries')"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_plugins_unresolvable() {
  # Stage E: marketplace manifest's "plugins" field is present but is not an
  # array (e.g. a bare boolean), so `jq '(.plugins // []) | length'` errors
  # and plugins_count comes back empty. Distinct from
  # case_red_marketplace_empty_plugins, where "plugins": [] resolves cleanly
  # to a genuine zero; this case pins that the two paths are
  # distinguishable.
  local name="red-on-marketplace (plugins field could not be resolved)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": true
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "could not be resolved"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'could not be resolved')"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_missing_name() {
  # Stage E: marketplace entry missing its name field. An entry with no
  # name must FAIL naming its position, not be silently skipped.
  local name="red-on-marketplace (entry missing name)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": [
    {
      "source": "./plug"
    }
  ]
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "entry #1 has no name"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'entry #1 has no name')"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_entry_dropped() {
  # Stage E: well-formed 2-entry plugins array whose second entry has a
  # non-string "name" (a number). jq prints the first entry's line, then
  # aborts with a type error on the second before it can emit anything, so
  # the loop must not silently read only 1 of 2 entries and report a
  # truncated PASS.
  local name="red-on-marketplace (jq aborts partway through, one entry silently dropped)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": [
    {
      "name": "demo-plugin",
      "source": "./plug"
    },
    {
      "name": 123,
      "source": "./plug2"
    }
  ]
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "declares 2 plugin entries but only 1 could be read"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'declares 2 plugin entries but only 1 could be read')"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_plugins_object() {
  # Stage E: "plugins" is a JSON object rather than an array. `length`
  # succeeds on an object (key count), so plugins_count resolves to a
  # nonzero number and the earlier `-z "$plugins_count"` branch never fires
  # -- but `.plugins[]` then errors on the first value it tries to index,
  # so the loop reads zero entries. This must FAIL, not report a truncated
  # PASS.
  local name="red-on-marketplace (plugins field is an object, not an array)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": {
    "a": 1,
    "b": 2
  }
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "declares 2 plugin entries but only 0 could be read"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'declares 2 plugin entries but only 0 could be read')"
  printf '%s\n' "$out"
  return 1
}

case_red_marketplace_plugins_string() {
  # Stage E: "plugins" is a JSON string rather than an array. `length`
  # succeeds on a string (character count), so plugins_count again resolves
  # to a nonzero number, but `.plugins[]` errors on "cannot iterate over
  # string" before yielding anything, so the loop reads zero entries. This
  # must FAIL, not report a truncated PASS.
  local name="red-on-marketplace (plugins field is a string, not an array)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  write_marketplace "$tmp" <<'EOF'
{
  "plugins": "abc"
}
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "declares 3 plugin entries but only 0 could be read"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with 'declares 3 plugin entries but only 0 could be read')"
  printf '%s\n' "$out"
  return 1
}

case_no_marketplace() {
  # Stage E: no marketplace manifest at the repo root. rc must stay 0 AND
  # the specific NOTE must be present, so "Stage E skipped" is
  # distinguishable from "Stage E absent". Mirrors case_no_suites.
  local name="no-marketplace (no .claude-plugin/marketplace.json present)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  rm -f "$tmp/.claude-plugin/marketplace.json"
  git -C "$tmp" add -A
  run_gate "$tmp"
  if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q "no marketplace manifest found"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 0 with 'no marketplace manifest found')"
  printf '%s\n' "$out"
  return 1
}

case_tracked_selftest_runs() {
  # Control for case_untracked_selftest_refused below, and Stage D's first
  # direct coverage: every other case runs the gate with GATE_SELFTEST=1,
  # which skips Stage D entirely, so no other case can reach it. Without
  # this control, the refusal case below would pass even if Stage D were
  # broken outright.
  local name="tracked-selftest-runs (tracked scripts/gates/test_*.sh self-test executes)"
  local tmp out rc sentinel
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  sentinel="$tmp/sentinel_tracked_selftest_ran"
  write_selftest_fixture "$tmp" "$sentinel"
  git -C "$tmp" add -A >/dev/null 2>&1
  run_gate_stage_d "$tmp"
  if [ "$rc" -eq 0 ] && [ -f "$sentinel" ]; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 0 with sentinel present)"
  printf '%s\n' "$out"
  return 1
}

case_untracked_selftest_refused() {
  # Acceptance criterion 2: an untracked scripts/gates/test_*.sh self-test
  # must be refused, not executed. Same fixture as the control above, left
  # unstaged.
  local name="untracked-selftest-refused (unstaged gate self-test is refused, not executed)"
  local tmp out rc sentinel
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  sentinel="$tmp/sentinel_untracked_selftest_ran"
  write_selftest_fixture "$tmp" "$sentinel"
  # Deliberately left unstaged.
  run_gate_stage_d "$tmp"
  # Anchored grep (not two independent greps) so a gate emitting the refusal
  # for one file and the target path on an unrelated line cannot pass.
  if [ "$rc" -eq 1 ] \
    && printf '%s' "$out" | grep -q "untracked gate self-test, refusing to execute.*scripts/gates/test_fixture.sh" \
    && [ ! -f "$sentinel" ]; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1 with refusal diagnostic and sentinel absent)"
  printf '%s\n' "$out"
  [ -f "$sentinel" ] && echo "FAIL  $name: sentinel file exists, self-test was executed despite refusal: $sentinel"
  return 1
}

case_green || overall=1
case_red_python_tracked || overall=1
case_untracked_python_refused || overall=1
case_untracked_skill_still_discovered || overall=1
case_red_skill || overall=1
case_red_json || overall=1
case_no_suites || overall=1
case_multi_failure || overall=1
case_red_marketplace_source_missing || overall=1
case_red_marketplace_missing_source || overall=1
case_red_marketplace_missing_manifest || overall=1
case_red_marketplace_wrong_dir || overall=1
case_red_readme_missing_entry || overall=1
case_red_marketplace_dash_name || overall=1
case_red_readme_missing || overall=1
case_red_marketplace_empty_plugins || overall=1
case_red_marketplace_plugins_unresolvable || overall=1
case_red_marketplace_missing_name || overall=1
case_red_marketplace_entry_dropped || overall=1
case_red_marketplace_plugins_object || overall=1
case_red_marketplace_plugins_string || overall=1
case_no_marketplace || overall=1
case_tracked_selftest_runs || overall=1
case_untracked_selftest_refused || overall=1

if [ "$overall" -eq 0 ]; then
  echo "ok  all gate self-test cases passed"
else
  echo "FAIL  one or more gate self-test cases failed"
fi

exit $overall
