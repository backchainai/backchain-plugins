#!/usr/bin/env bash
# Tracked daedalus structural + unit-test gate for backchain-plugins.
#
# This is a content-only repository (markdown + JSON) plus a handful of
# stdlib-only python test suites shipped alongside skill scripts. This gate
# asserts:
#   Stage A -- SKILL.md frontmatter contracts (name matches directory,
#              description present, file <= 500 lines).
#   Stage B -- every tracked *.json file is valid JSON.
#   Stage C -- every tracked test_*.py suite under a skills/*/scripts/
#              directory (any plugin, not just scriptorium) is discovered
#              and run via `python3 -m unittest`.
#   Stage D -- every tracked scripts/gates/test_*.sh self-test is run,
#              recursion-guarded by GATE_SELFTEST (see below).
#
# Exit-code table:
#   0 = all contracts hold and all suites pass
#   1 = a contract violation, a failing python suite, or a failing self-test
#   2 = cannot run (no git root, jq missing, python3 missing while suites exist)
#
# Recursion guard: when GATE_SELFTEST is set to a non-empty value, Stage D is
# skipped entirely. scripts/gates/test_structure.sh exports GATE_SELFTEST=1
# before invoking any copy of this gate, so the gate never re-enters its own
# self-test while being self-tested. Stage D itself also exports
# GATE_SELFTEST=1 for every self-test it invokes, so the guard is
# depth-independent rather than relying on each future self-test author
# remembering to export it.
set -uo pipefail

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 2
cd "$root" || exit 2
command -v jq >/dev/null 2>&1 || { echo "ERROR  jq not found"; exit 2; }

fail=0

# Stage A -- SKILL.md frontmatter contracts.
while IFS= read -r f; do
  [ -n "$f" ] || continue
  dir=$(basename "$(dirname "$f")")
  name=$(awk '/^---$/{c++; next} c==1 && /^name:/{sub(/^name:[[:space:]]*/,""); print; exit}' "$f")
  [ "$name" = "$dir" ] || {
    echo "FAIL  frontmatter name '$name' does not match directory '$dir': $f"
    fail=1
  }
  awk '/^---$/{c++; next} c==1 && /^description:/{found=1} END{if (found==0) exit 1}' "$f" || {
    echo "FAIL  frontmatter missing description: $f"
    fail=1
  }
  lines=$(wc -l < "$f" | tr -d ' ')
  [ "$lines" -le 500 ] || {
    echo "FAIL  SKILL.md exceeds 500 lines ($lines): $f"
    fail=1
  }
done < <(git ls-files --cached --others --exclude-standard '*SKILL.md')

# Stage B -- JSON validity.
while IFS= read -r j; do
  [ -n "$j" ] || continue
  jq empty "$j" >/dev/null 2>&1 || {
    echo "FAIL  invalid JSON: $j"
    fail=1
  }
done < <(git ls-files --cached --others --exclude-standard '*.json')

# Stage C -- python unit suites. Generalized past scriptorium/ on purpose so
# a future plugin's suites cannot silently go uncollected.
py_suites=$(git ls-files --cached --others --exclude-standard '*/skills/*/scripts/test_*.py')
if [ -z "$py_suites" ]; then
  echo "NOTE  no python test suites found, skipping Stage C"
else
  command -v python3 >/dev/null 2>&1 || { echo "ERROR  python3 not found"; exit 2; }
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    dir=$(dirname "$f")
    mod=$(basename "$f" .py)
    py_out=$(mktemp "${TMPDIR:-/tmp}/gate-py.XXXXXX")
    if ( cd "$dir" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest "$mod" ) >"$py_out" 2>&1; then
      echo "PASS  python suite: $f"
      tail -n 3 "$py_out"
    else
      echo "FAIL  python suite: $f"
      cat "$py_out"
      fail=1
    fi
    rm -f "$py_out"
  done <<< "$py_suites"
fi

# Stage D -- gate self-tests. Skipped when GATE_SELFTEST is set (recursion
# guard; see header comment). scripts/gates/test_structure.sh sets it.
if [ -n "${GATE_SELFTEST:-}" ]; then
  echo "NOTE  GATE_SELFTEST set, skipping Stage D self-tests"
else
  selftests=$(git ls-files --cached --others --exclude-standard 'scripts/gates/test_*.sh')
  if [ -n "$selftests" ]; then
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      st_out=$(mktemp "${TMPDIR:-/tmp}/gate-st.XXXXXX")
      if GATE_SELFTEST=1 bash "$f" >"$st_out" 2>&1; then
        :
      else
        echo "FAIL  self-test: $f"
        cat "$st_out"
        fail=1
      fi
      rm -f "$st_out"
    done <<< "$selftests"
  fi
fi

[ "$fail" -eq 0 ] && echo "PASS  structural contracts hold"
exit $fail
