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
#   Stage E -- .claude-plugin/marketplace.json entries resolve: each
#              entry's source directory exists, contains a
#              .claude-plugin/plugin.json whose name matches the entry
#              name, and the entry name is listed in root README.md.
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

# Stage E -- marketplace entry resolution and README listing.
mp="$root/.claude-plugin/marketplace.json"
if [ ! -f "$mp" ]; then
  echo "NOTE  no marketplace manifest found, skipping Stage E"
else
  # Stage B already jq-validates every tracked *.json file, including this
  # manifest, so a corrupt manifest emits a FAIL there too. Re-validating
  # here is deliberate: Stage B discovers via `git ls-files --cached
  # --others --exclude-standard` (so a gitignored manifest escapes it) and
  # only sets a flag, whereas Stage E needs a local decision about whether
  # to attempt resolution at all.
  if ! jq empty "$mp" >/dev/null 2>&1; then
    # Exception: this branch sits outside the `else` below where e_fail is
    # initialized, so it sets fail=1 only, not e_fail.
    echo "FAIL  invalid JSON, cannot resolve marketplace entries: $mp"
    fail=1
  else
    e_fail=0
    n=0
    # efail: Stage E's failure sink. Not `local` -- bash resolves unqualified
    # assignments dynamically, so this must land on the enclosing fail/e_fail
    # rather than shadow them.
    efail() { echo "FAIL  $*"; fail=1; e_fail=1; }
    # A manifest that exists but resolves to zero plugin entries (missing
    # "plugins" key or an empty array) is a structural defect, not a clean
    # skip -- distinct from case_no_marketplace, where the manifest file
    # itself is absent. `length` succeeds on objects, strings, and numbers,
    # not just arrays, so plugins_count coming back empty only catches a
    # narrow class of malformed shapes (e.g. `null` or a boolean). The
    # general case -- a `.plugins` shape that `length` can measure but
    # `.plugins[]` cannot iterate, or a single bad entry that aborts the
    # loop partway through and silently drops the remaining entries -- is
    # caught below by comparing plugins_count against the number of entries
    # the loop actually read.
    plugins_count=$(jq -r '(.plugins // []) | length' "$mp" 2>/dev/null)
    if [ -z "$plugins_count" ]; then
      efail "marketplace manifest plugins field could not be resolved: $mp"
    elif [ "$plugins_count" -eq 0 ]; then
      efail "marketplace manifest has no plugin entries: $mp"
    else
      # Delimit with \u001f (unit separator) rather than a tab: tab
      # is an IFS-whitespace character, so `IFS=$'\t' read` still trims a
      # leading empty field (an entry with a missing/empty name) instead of
      # preserving it, silently misattributing the source value to $name.
      # \u001f is not IFS whitespace, so empty fields are preserved.
      while IFS=$'\x1f' read -r name source; do
        n=$((n + 1))
        if [ -z "$name" ]; then
          efail "marketplace entry #$n has no name: $mp"
          continue
        fi
        if [ -z "$source" ]; then
          efail "marketplace entry '$name' has no source: $mp"
          continue
        fi
        src_dir="$root/${source#./}"
        if [ ! -d "$src_dir" ]; then
          efail "marketplace entry '$name' source directory does not exist: $source"
          continue
        fi
        plugin_manifest="$src_dir/.claude-plugin/plugin.json"
        if [ ! -f "$plugin_manifest" ]; then
          efail "marketplace entry '$name' missing plugin manifest: $source/.claude-plugin/plugin.json"
          continue
        fi
        # Use jq's `empty` (no output), not a "null" string sentinel: a
        # manifest with no .name and an entry literally named "null" would
        # otherwise both resolve to the string "null" and compare equal.
        plugin_name=$(jq -r '.name // empty' "$plugin_manifest" 2>/dev/null)
        if [ -z "$plugin_name" ]; then
          efail "marketplace entry '$name' plugin manifest has no name: $plugin_manifest"
        elif [ "$plugin_name" != "$name" ]; then
          efail "marketplace entry '$name' does not match plugin manifest name '$plugin_name': $plugin_manifest"
        fi
        readme="$root/README.md"
        if [ ! -f "$readme" ]; then
          efail "marketplace entry '$name' cannot be verified against README.md, file not found: $readme"
        elif ! grep -q -F "$name" "$readme"; then
          efail "marketplace entry '$name' not listed in README.md: $readme"
        fi
      done < <(jq -r '.plugins[] | ((.name // "")) + "\u001f" + ((.source // ""))' "$mp" 2>/dev/null)
      if [ "$n" -ne "$plugins_count" ]; then
        efail "marketplace manifest declares $plugins_count plugin entries but only $n could be read: $mp"
      fi
    fi
    [ "$e_fail" -eq 0 ] && echo "PASS  marketplace entries resolve ($n plugins)"
  fi
fi

[ "$fail" -eq 0 ] && echo "PASS  structural contracts hold"
exit $fail
