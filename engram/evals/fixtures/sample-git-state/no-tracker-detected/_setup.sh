#!/bin/bash
set -e
git init -q -b main
git config user.name "engram-eval"
git config user.email "eval@engram.local"
git add README.md
git commit -q -m "feat: initial commit"
echo "x" > x.md && git add x.md && git commit -q -m "task: add x"
echo "y" > y.md && git add y.md && git commit -q -m "task: add y"
