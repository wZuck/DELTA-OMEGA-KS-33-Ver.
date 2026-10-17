[English](README.md) | [简体中文](README.zh-CN.md)

# Rev5 PCB Scripts

These scripts regenerate the Rev5 boards from the Rev4 hand-solder PCBs:

1. `build_ks33_rev5.py` replaces every ULP switch with the local KS-33
   five-pin footprint and adds one SOD-323 diode per key.
2. `route_ks33_rev5.py` runs the pinned Freerouting 2.5.0 JAR and fills zones
   after importing the session.
3. `fix_ks33_nets.py` routes the remaining constrained nets and explicitly
   connects split ground-zone islands.
4. `polish_ks33_rev5.py` widens constrained tracks, fixes known neck-downs,
   normalizes footprint/text annotations, and removes redundant vias.
5. `export_fab.sh` regenerates Gerbers, drill files, drill maps, and ZIP files.

Freerouting JAR SHA-256:

```text
f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7
```

Example:

```bash
KICAD_PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9
JAVA=/path/to/java
JAR=/path/to/freerouting-2.5.0.jar

"$KICAD_PY" pcb/scripts/build_ks33_rev5.py delta-omega-rev4-handsolder-left.kicad_pcb
"$KICAD_PY" pcb/scripts/route_ks33_rev5.py \
  pcb/delta-omega-rev5-ks33-left.kicad_pcb \
  --java "$JAVA" --freerouting-jar "$JAR"
"$KICAD_PY" pcb/scripts/fix_ks33_nets.py \
  pcb/delta-omega-rev5-ks33-left.kicad_pcb
"$KICAD_PY" pcb/scripts/polish_ks33_rev5.py \
  pcb/delta-omega-rev5-ks33-left.kicad_pcb
```

The checked-in board and fabrication files are the source of truth. Run the
project-specific KiCad DRC after any regeneration; the release files should
report zero violations and zero unconnected items.

Freerouting may produce electrically equivalent but geometrically different
routing between runs. Treat a regenerated board as a new candidate revision:
review the DRC result and 3D render before replacing the checked-in release
files.
