#!/usr/bin/env python3
"""Check the Rev5 switch and keycap envelopes against the Rev2 case."""

import argparse
import os
import sys

from rev5_geometry import (
    BOARD_CASE_PAIRS,
    CAP_SKIRT_CORNER_RADIUS,
    CAP_SKIRT_SIZE,
    CAP_SKIRT_TOP_Z,
    CAP_TOP,
    CAP_TOP_CORNER_RADIUS,
    CASE_RIM_Z,
    MAX_INTERSECTION_MM3,
    SWITCH_HEIGHT,
    SWITCH_SIZE_X,
    SWITCH_SIZE_Y,
    intersection_volume,
    keycap_envelope,
    switch_body,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cadquery-path",
        default=os.environ.get("CADQUERY_SITE_PACKAGES"),
        help="site-packages directory containing CadQuery",
    )
    args = parser.parse_args()
    if args.cadquery_path:
        sys.path.insert(0, args.cadquery_path)

    import cadquery as cq
    import pcbnew

    failures = []
    for side, board_path, case_path, _ in BOARD_CASE_PAIRS:
        board = pcbnew.LoadBoard(str(board_path))
        case_shape = cq.importers.importStep(str(case_path)).val()
        case_box = case_shape.BoundingBox()
        if not case_shape.isValid() or len(case_shape.Solids()) != 1:
            failures.append(f"{side}: case STEP is not one valid solid")
        if abs(case_box.zmax - CASE_RIM_Z) > 0.01:
            failures.append(
                f"{side}: expected case rim z={CASE_RIM_Z:g}, "
                f"found z={case_box.zmax:.3f}"
            )
        switches = [
            footprint
            for footprint in board.GetFootprints()
            if footprint.GetReference().startswith("SW")
        ]
        if len(switches) != 17:
            failures.append(f"{side}: expected 17 switches, found {len(switches)}")

        caps = []
        for switch in switches:
            body = switch_body(cq, side, switch)
            body_overlap = intersection_volume(case_shape, body)

            cap = keycap_envelope(cq, side, switch)
            caps.append((switch.GetReference(), cap))
            cap_overlap = intersection_volume(case_shape, cap)

            if body_overlap > MAX_INTERSECTION_MM3:
                failures.append(
                    f"{side} {switch.GetReference()}: switch body overlap "
                    f"{body_overlap:.3f} mm^3"
                )
            if cap_overlap > MAX_INTERSECTION_MM3:
                failures.append(
                    f"{side} {switch.GetReference()}: keycap envelope overlap "
                    f"{cap_overlap:.3f} mm^3"
                )

        for index, (reference, cap) in enumerate(caps):
            for other_reference, other_cap in caps[index + 1:]:
                overlap = intersection_volume(cap, other_cap)
                if overlap > MAX_INTERSECTION_MM3:
                    failures.append(
                        f"{side} {reference}/{other_reference}: "
                        f"adjacent keycap overlap {overlap:.3f} mm^3"
                    )

        print(
            f"{side}: checked {len(switches)} switches; "
            f"KS-33 {SWITCH_SIZE_X:g} x {SWITCH_SIZE_Y:g} x {SWITCH_HEIGHT:g} mm; "
            f"rim z={case_box.zmax:.3f} mm"
        )

    print(
        "Keycap envelope: "
        f"{CAP_SKIRT_SIZE:g} mm square r{CAP_SKIRT_CORNER_RADIUS:g} "
        f"below z={CAP_SKIRT_TOP_Z:g}, {CAP_TOP[0]:g} x {CAP_TOP[1]:g} mm "
        f"r{CAP_TOP_CORNER_RADIUS:g} above z={CAP_SKIRT_TOP_Z:g}"
    )
    print(f"Target case rim: z={CASE_RIM_Z:g} mm")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("PASS: no case interference in the checked envelopes")


if __name__ == "__main__":
    main()
