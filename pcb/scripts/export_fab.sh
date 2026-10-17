#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KICAD_CLI="${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}"
LAYERS="F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts"

for side in left right both; do
  board="$ROOT/pcb/delta-omega-rev5-ks33-${side}.kicad_pcb"
  output="$ROOT/pcb/gerbers/rev5-ks33-${side}"
  archive="$ROOT/pcb/gerbers/delta-omega-rev5-ks33-${side}.zip"

  mkdir -p "$output"
  find "$output" -maxdepth 1 -type f -delete
  "$KICAD_CLI" pcb export gerbers \
    --layers "$LAYERS" \
    --check-zones \
    --output "$output" \
    "$board"
  "$KICAD_CLI" pcb export drill \
    --format excellon \
    --excellon-units mm \
    --generate-map \
    --map-format pdf \
    --output "$output" \
    "$board"
  if [[ -f "$archive" ]]; then
    unlink "$archive"
  fi
  (
    cd "$output"
    zip -q -r "$archive" .
  )
done
