#!/usr/bin/env bash
# Self-test for scripts/gates/structure.sh.
#
# Red/green harness: builds a throwaway fixture repo per case, runs the real
# gate against it, and checks the gate's exit code and output. bash + git +
# stdlib python3 only, no third-party dependencies.
#
# Every invocation of the gate made by this harness exports GATE_SELFTEST=1
# so the gate never re-enters its own self-test stage (Stage D is skipped
# whenever GATE_SELFTEST is non-empty) -- otherwise this script would recurse
# into itself via the gate it is testing.
#
# python3 is a hard requirement of this harness (several cases exercise
# Stage C, the python-suite stage). Rather than skip individual cases when
# python3 is missing -- which used to let some cases report false success
# and others fail with a misleading message -- the harness checks once, up
# front, and fails outright if python3 is not available.
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
#
# build_fixture and run_gate (below) deliberately do not declare their own
# `local tmp`/`out`/`rc`/`assertion`. Every case function below declares
# those names `local` itself; because bash resolves unqualified assignments
# dynamically up the call stack, an assignment inside build_fixture/run_gate
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

# run_gate <tmp> -> writes combined output to $out, exit code to $rc
# Verifies the fixture actually has a .git directory before running the gate
# so a build_fixture failure (e.g. `git init` failing) surfaces as a harness
# failure instead of being interpreted as the gate having gone red.
run_gate() {
  tmp="$1"
  if [ ! -d "$tmp/.git" ]; then
    out="fixture at $tmp has no .git directory (build_fixture likely failed)"
    rc=1
    return
  fi
  out=$(cd "$tmp" && GATE_SELFTEST=1 bash scripts/gates/structure.sh 2>&1)
  rc=$?
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

case_red_python() {
  local name="red-on-python (failing python suite, discovered via --others/untracked)"
  local tmp out rc
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gate-selftest.XXXXXX")
  trap 'rm -rf "$tmp"' RETURN
  build_fixture "$tmp" pass >/dev/null 2>&1 || { echo "FAIL  $name (fixture build failed)"; return 1; }
  # ADVISORY 8: exercise the --others (untracked) discovery path. Remove the
  # tracked passing suite and stage that removal, then drop a failing suite
  # into the working tree WITHOUT staging it. Stage C must find it via
  # `git ls-files --others --exclude-standard`; dropping --others from the
  # gate's glob would make this suite invisible and this case would go
  # green.
  rm -f "$tmp/plug/skills/demo/scripts/test_demo.py"
  git -C "$tmp" add -A >/dev/null 2>&1
  cat >"$tmp/plug/skills/demo/scripts/test_demo.py" <<'EOF'
#!/usr/bin/env python3
import unittest


class DemoTest(unittest.TestCase):
    def test_demo(self):
        self.assertEqual(1, 2)


if __name__ == "__main__":
    unittest.main()
EOF
  run_gate "$tmp"
  if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "FAIL  python suite: plug/skills/demo/scripts/test_demo.py"; then
    echo "ok  $name"
    return 0
  fi
  echo "FAIL  $name (exit=$rc, expected 1)"
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

case_green || overall=1
case_red_python || overall=1
case_red_skill || overall=1
case_red_json || overall=1
case_no_suites || overall=1
case_multi_failure || overall=1

if [ "$overall" -eq 0 ]; then
  echo "ok  all gate self-test cases passed"
else
  echo "FAIL  one or more gate self-test cases failed"
fi

exit $overall
