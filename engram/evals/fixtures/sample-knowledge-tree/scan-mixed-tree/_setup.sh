#!/bin/bash
# Backdate mtimes to give the consolidate skill realistic ages
set -e
touch -d "2025-01-15T00:00:00" docs/old-decision-2025-01.md
touch -d "2026-04-19T00:00:00" outputs/morning-brief_2026-04-19.md
touch -d "2026-02-26T00:00:00" outputs/strategy-doc_2026-02-26.md
