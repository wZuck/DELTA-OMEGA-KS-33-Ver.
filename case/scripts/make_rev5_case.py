#!/usr/bin/env python3
"""Generate Rev5 cases by adding KS-33 clearance pockets to the Rev2 STEP."""

import argparse
import os
import sys

from rev5_geometry import (
    BOARD_CASE_PAIRS,
    CASE_POCKET_BOTTOM_Z,
    CASE_POCKET_CORNER_RADIUS,
    CASE_POCKET_SIZE,
    CASE_POCKET_TOP_Z,
    board_to_case,
    rounded_box,
    switch_rotation,
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

    for side, board_path, output_path, source_path in BOARD_CASE_PAIRS:
        board = pcbnew.LoadBoard(str(board_path))
        case_shape = cq.importers.importStep(str(source_path)).val()
        cutters = []
        for switch in board.GetFootprints():
            if not switch.GetReference().startswith("SW"):
                continue
            position = switch.GetPosition()
            x, y = board_to_case(
                side,
                pcbnew.ToMM(position.x),
                pcbnew.ToMM(position.y),
            )
            rotation = switch_rotation(switch.GetOrientation().AsDegrees())
            cutter = rounded_box(
                cq,
                x,
                y,
                CASE_POCKET_BOTTOM_Z,
                CASE_POCKET_TOP_Z,
                CASE_POCKET_SIZE,
                CASE_POCKET_SIZE,
                CASE_POCKET_CORNER_RADIUS,
                rotation,
            )
            cutters.append(cutter)

        if not cutters:
            raise RuntimeError(f"{side}: no switch positions found")
        result = case_shape.cut(cutters[0].fuse(*cutters[1:]))
        if len(result.Solids()) != 1:
            raise RuntimeError(
                f"{side}: case relief produced {len(result.Solids())} solids"
            )
        cq.exporters.export(cq.Workplane(obj=result), str(output_path))
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
