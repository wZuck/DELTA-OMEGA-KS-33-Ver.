[English](REVIEW_REV5.md) | [简体中文](REVIEW_REV5.zh-CN.md)

# Rev5 Review Summary

## PCB and Circuit

- Left, right, and panel boards pass KiCad DRC with 0 violations and
  0 unconnected items.
- The 34 switch cells have no duplicate or missing matrix positions.
- Every switch has a series SOD-323 diode. Diode pad 1 is the row, pad 2 is
  the switch/column, and the firmware uses `col2row`.
- Left columns map to global columns 0-4. Right columns map to global columns
  5-9 with the required reversal.
- BATP, LED resistor, reset, C2 column chains, and split ground-zone islands
  have explicit connections.
- Minimum routed signal width is 0.2 mm.
- The XIAO edge-pad cutouts are the only copper-to-edge exception. This is
  scoped to `MCU1`/`MCU2` in the project custom rules rather than globally
  disabling the check.

## Case and Keycaps

- The Rev5 cases add `15.2 mm`, `r1.8 mm` CNC-compatible pockets at all 34
  positions. The rounded KS-33 body envelope has zero modeled interference.
- A rounded keycap is required: `14 x 14 mm`, `r3.5 mm` below `z = 7.0 mm`
  and `16.6 x 15.6 mm`, `r7.0 mm` above it. Adjacent-key collision checks pass.
- Electrical pins must be trimmed to at most 0.5 mm below the PCB and insulated
  before the bottom cover is installed.
- The Rev5 rim is raised to `z = 8.8 mm`, nearly level with the `z = 9.0 mm`
  keycap envelope top, while preserving the internal opening and mounting
  geometry.

See [Mechanical Notes](MECHANICAL.md) for the exact dimensions and validation
command.

## Firmware

- GPIO rows are `D5`, `D6`, `D8`, and `D7`; left columns are `D0`-`D4`; right
  columns are `D4`-`D0` with column offset 5.
- The RGB data net uses `D9` (`P0.10`).
- The reviewed external keymap contained one `R_Gui_Alt` modifier typo. The
  controlled [firmware snapshot](../firmware/README.md) contains the fix,
  pinned dependency revisions, and a workspace setup script.
- A full ZMK build was not run because this workspace does not contain a west
  workspace or Zephyr toolchain.

## First-Article Checks

Before a production run, verify:

1. KS-33 3.0 samples seat without force in all five holes.
2. Selected keycaps clear the case and adjacent keys through full travel.
3. Battery and bottom-cover clearance remains after pin trimming and
   insulation.
4. Panel mouse-bites separate without damaging edge traces or castellations.
5. The assembled left and right halves enumerate and pair with the pinned ZMK
   build.
