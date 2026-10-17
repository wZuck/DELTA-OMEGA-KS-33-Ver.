#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: setup_workspace.sh WORKSPACE_DIR [--init-only]" >&2
  exit 2
fi

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_DIR="$1"

mkdir -p "$WORKSPACE_DIR/config"
cp -R "$SOURCE_ROOT/config/." "$WORKSPACE_DIR/config/"
cp "$SOURCE_ROOT/build.yaml" "$WORKSPACE_DIR/build.yaml"

(
  cd "$WORKSPACE_DIR"
  west init -l config
  if [[ "${2:-}" != "--init-only" ]]; then
    west update
  fi
)
