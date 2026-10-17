[English](MECHANICAL.md) | [简体中文](MECHANICAL.zh-CN.md)

# Rev5 Mechanical Notes

Rev5 uses the Gateron KS-33 Low Profile 3.0 five-pin switch. The Rev5 case
keeps the Rev2 outline and screw pattern but adds a `15.2 mm`, `r1.8 mm` relief
pocket around every switch. This radius is compatible with a normal CNC
endmill and matches the rounded KS-33 body corners.

## Official Switch Dimensions

Source: [Gateron drawing `SPEC-KS-33B-014`](https://www.gateron.com/u_file/2610/12/file/GATERONKS-33LowProfile30MechanicalSilverSwitchSet.pdf),
version 2, issued 2026-08-22.

| Feature | Dimension |
|---|---:|
| Switch body | 14.60 x 14.60 mm |
| Body height above PCB | 6.20 +/- 0.05 mm |
| Overall stem height above PCB | 13.10 mm |
| Center hole | 5.00 +/- 0.10 mm |
| Locator holes | 1.70 +/- 0.05 mm, at +/-5.08 mm |
| Electrical holes | 1.50 +/- 0.05 mm |
| Electrical pin length | 3.00 mm |
| Locator peg length | 1.20 mm |

The locator pegs do not pass through a 1.6 mm PCB. The electrical pins do:
approximately 1.4 mm remains below a fully seated switch before trimming.

## Case Result

The validation checks all 34 switch positions using:

- PCB top at `z = 1.6 mm`
- Switch body envelope of `14.6 x 14.6 x 6.2 mm` with `r1.5 mm` corners
- A rounded 1u keycap envelope with a `14 x 14 mm`, `r3.5 mm` lower skirt
  below `z = 7.0 mm` and a `16.6 x 15.6 mm`, `r7.0 mm` upper section above it

![Rev5 keycap fit envelope](./images/rev5_keycap_envelope.svg)

Result: zero modeled interference for the switch body, keycap-to-case fit, and
all adjacent keycap pairs. The complete check now includes the reflected
rotation, CNC-compatible pocket corners, and neighboring-key collisions.

The Rev5 rim is raised from the Rev2 height of `z = 7.0 mm` to
`z = 8.8 mm`. It is therefore nearly level with the `z = 9.0 mm` keycap
envelope top, producing the intended enclosed typing feel. The generator
extends the existing top-wall cross-section vertically instead of scaling the
whole case, so the internal openings, screw bosses, and lower mounting
geometry remain unchanged.

Run the check with:

```bash
CADQUERY_SITE_PACKAGES=/path/to/cadquery/site-packages \
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 \
  case/scripts/check_rev5_clearance.py
```

The allowable 1u keycap volume is provided as
`case/delta_omega_rev5_keycap_envelope.step`. Its coordinates match the case
STEP files (`z = 5.0` to `z = 9.0`). It is a fit envelope, not a print-ready
keycap or an MX stem socket model.

## Direct-Solder Requirements

1. Dry-fit all five posts before soldering.
2. Solder only the two electrical pins.
3. Trim both electrical pins to no more than 0.5 mm below the PCB.
4. Inspect for solder spikes and cover exposed metal with insulating tape or
   conformal coating before installing the bottom cover or battery.
5. Do not force the switch over the locator posts and do not fill the center
   or locator holes with solder.

## Keycap Rule

Do not assume that an MX-compatible stem means an MX keycap fits. At the
`18 x 17 mm` key pitch, the skirt and upper corners must remain within the
rounded envelope. Square-corner keycaps, standard 18 mm keycaps, and caps
designed for 19.05 mm spacing can collide with the case or adjacent keys.

The supplied PCB intentionally uses direct solder and does not contain
hot-swap sockets.
