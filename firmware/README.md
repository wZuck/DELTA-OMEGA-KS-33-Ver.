[English](README.md) | [简体中文](README.zh-CN.md)

# Firmware Notes

The Rev5 PCB matrix is compatible with these reviewed ZMK sources:

- `unspecworks/zmk-keyboard-delta-omega` at
  `1df759db142469929841464905ec831ddb4e29b8`
- `unspecworks/zmk-delta-omega` at
  `0f5392e87467c06d0d23c321b1728cc1539be950`
- `caksoylar/zmk-rgbled-widget` at
  `e6b467792a1dabef8cfa5c9fd26bfefc9c16662b`

This directory is a controlled ZMK config snapshot. It contains the corrected
keymap and the pinned [west manifest](config/west.yml). The upstream config
followed moving `main` branches, so a reproducible build must use this snapshot
instead of the live upstream branches.

Create a workspace outside this repository:

```bash
./firmware/scripts/setup_workspace.sh "$HOME/zmk-workspaces/delta-omega"
cd "$HOME/zmk-workspaces/delta-omega"
west build -s zmk/app -d build/left -b seeeduino_xiao_ble \
  -- -DZMK_CONFIG="$PWD/config" \
  -DSHIELD=delta_omega_left
```

Build `delta_omega_right` and `settings_reset` in the same way.

## Matrix

| Signal | GPIO | Board mapping |
|---|---|---|
| Row 1 | `P0.05` | `D5` |
| Row 2 | `P0.06` | `D6` |
| Row 3 | `P0.08` | `D8` |
| Row 4 | `P0.07` | `D7` |
| Left columns 1-5 | `P0.00`-`P0.04` | `D0`-`D4` |
| Right columns 6-10 | `P0.04`-`P0.00` | `D4`-`D0`, with column offset 5 |

The matrix transform defines 4 rows and 10 columns. Every switch has one
series SOD-323 diode between the switch contact and its row; pad 1 is the row
side and pad 2 is the switch/column side. `diode-direction = "col2row"` is
therefore correct.

## Keymap Fix

The reviewed upstream keymap had one right-side modifier typo: `R_Gui_Alt`
used `LG(LALT)` instead of `RG(RALT)`. The checked-in config snapshot contains
the fix. [keymap.patch](zmk/keymap.patch) is retained as an audit patch for the
upstream repository.

The RGB LED data chain is on `P0.10` (`D9`), matching the PCB.

## Build Status

The matrix, diode orientation, GPIO mapping, and transform were checked against
the PCB. A full ZMK compile is not included in this repository because no west
workspace or Zephyr toolchain is installed in the project environment.
