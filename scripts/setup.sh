#!/usr/bin/env bash
# Thin wrapper → scripts/setup.py (macOS / Linux)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python 3.10+ is required." >&2
  exit 1
fi

exec "$PY" "$ROOT/scripts/setup.py" "$@"
