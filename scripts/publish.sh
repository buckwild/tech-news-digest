#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_BIN="$REPO_DIR/.venv/bin"

"$VENV_BIN/python" "$REPO_DIR/src/fetch.py"

cd "$REPO_DIR"
if ! git diff --quiet docs; then
  git add docs/index.html docs/feeds.json
  git commit -m "chore: refresh headlines"
  git push origin main
else
  echo "No changes to publish"
fi
