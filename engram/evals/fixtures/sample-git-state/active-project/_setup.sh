#!/bin/bash
set -e
touch -d "2026-04-15" outputs/old-report_2026-04-15.md
git init -q -b main
git config user.name "engram-eval"
git config user.email "eval@engram.local"
git add README.md
git commit -q -m "feat: scaffold project README"
git add .memory/todos.md
git commit -q -m "task: capture initial token-validation todos"
git add .memory/decisions.md
git commit -q -m "task: record JWT-with-refresh decision"
git add outputs/old-report_2026-04-15.md
git commit -q -m "task: snapshot weekly report"
echo "draft" > draft.md
git add draft.md
git commit -q -m "feat: stub draft for review"
# notes-uncommitted.md stays uncommitted to give git status something to report
