#!/usr/bin/env python3
"""Generate the Rev5 1u keycap fit envelope as a STEP model."""

import argparse
import os
from pathlib import Path
import sys

from rev5_geometry import (
    CAP_SKIRT_CORNER_RADIUS,
    CAP_SKIRT_LOW_Z,
    CAP_SKIRT_SIZE,
    CAP_SKIRT_TOP_Z,
    CAP_TOP,
    CAP_TOP_CORNER_RADIUS,
    CAP_TOP_Z,
    ROOT,
    rounded_box,
)

DEFAULT_OUTPUT = ROOT / "case/delta_omega_rev5_keycap_envelope.step"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--cadquery-path",
        default=os.environ.get("CADQUERY_SITE_PACKAGES"),
        help="site-packages directory containing CadQuery",
    )
    args = parser.parse_args()
    if args.cadquery_path:
        sys.path.insert(0, args.cadquery_path)

    import cadquery as cq

    lower = rounded_box(
        cq,
        0,
        0,
        CAP_SKIRT_LOW_Z,
        CAP_SKIRT_TOP_Z,
        CAP_SKIRT_SIZE,
        CAP_SKIRT_SIZE,
        CAP_SKIRT_CORNER_RADIUS,
        0,
    )
    upper = rounded_box(
        cq,
        0,
        0,
        CAP_SKIRT_TOP_Z,
        CAP_TOP_Z,
        CAP_TOP[0],
        CAP_TOP[1],
        CAP_TOP_CORNER_RADIUS,
        0,
    )
    envelope = cq.Workplane(obj=lower.fuse(upper))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(envelope, str(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
