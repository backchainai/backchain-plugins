#!/bin/bash
set -e
git init -q -b main
git config user.name "engram-eval"
git config user.email "eval@engram.local"
git add README.md
git commit -q -m "chore: initial commit"
