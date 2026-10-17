#!/usr/bin/env python3
"""Build the Rev5 Gateron KS-33 Low Profile 3.0 PCB variants."""

from pathlib import Path
import math
import sys

import pcbnew


ROOT = Path(__file__).resolve().parents[2]
PCB_DIR = ROOT / "pcb"
FOOTPRINT_DIR = PCB_DIR / "footprints" / "delta_omega.pretty"
FOOTPRINT_IO = pcbnew.PCB_IO_KICAD_SEXPR()

# These outer-column switches need the diode shifted to the outside and rotated
# to keep the SOD-323 body clear of the adjacent switch courtyard.
OUTER_COLUMN_SWITCHES = {4, 5, 21, 22}

SOURCE_TARGETS = {
    "delta-omega-rev4-handsolder-left.kicad_pcb": "delta-omega-rev5-ks33-left.kicad_pcb",
    "delta-omega-rev4-handsolder-right.kicad_pcb": "delta-omega-rev5-ks33-right.kicad_pcb",
    "delta-omega-rev4-handsolder-both.kicad_pcb": "delta-omega-rev5-ks33-both.kicad_pcb",
}


def mm(value):
    return pcbnew.FromMM(value)


def load_footprint(name):
    footprint = FOOTPRINT_IO.FootprintLoad(str(FOOTPRINT_DIR), name)
    if footprint is None:
        raise RuntimeError(f"Unable to load footprint {name}")
    return footprint


def switch_number(reference):
    if not reference.startswith("SW"):
        return None
    suffix = reference[2:]
    return int(suffix) if suffix.isdigit() else None


def get_single_net(footprint, pad_number):
    names = {
        pad.GetNetname()
        for pad in footprint.Pads()
        if pad.GetNumber() == str(pad_number) and pad.GetNetname()
    }
    if len(names) != 1:
        raise RuntimeError(
            f"{footprint.GetReference()} pad {pad_number} has nets {sorted(names)}"
        )
    return names.pop()


def locate_diode(switch, number):
    angle = math.radians(switch.GetOrientationDegrees())
    if number in OUTER_COLUMN_SWITCHES:
        local_y = 8.45
        angle_offset = 180
    else:
        local_y = -8.55
        angle_offset = 0
    x, y = pcbnew.ToMM(switch.GetPosition())
    position = pcbnew.VECTOR2I(
        mm(x + local_y * math.sin(angle)),
        mm(y + local_y * math.cos(angle)),
    )
    orientation = switch.GetOrientationDegrees() + angle_offset
    return position, orientation


def build(source_name, target_name):
    source = PCB_DIR / source_name
    target = PCB_DIR / target_name
    board = pcbnew.LoadBoard(str(source))

    switches = sorted(
        (
            footprint
            for footprint in board.GetFootprints()
            if switch_number(footprint.GetReference()) is not None
        ),
        key=lambda footprint: switch_number(footprint.GetReference()),
    )
    if len(switches) not in (17, 34):
        raise RuntimeError(f"{source_name}: found {len(switches)} switches")

    switch_data = []
    for switch in switches:
        switch_data.append(
            {
                "reference": switch.GetReference(),
                "position": switch.GetPosition(),
                "orientation": switch.GetOrientationDegrees(),
                "column_net": get_single_net(switch, 1),
                "switch_net": get_single_net(switch, 2),
                "row_net": get_single_net(switch, 4),
            }
        )

    # KiCad 9's SWIG bindings lose object type information after removals, so
    # prepare and add every new footprint before removing the old geometry.
    for data in switch_data:
        number = switch_number(data["reference"])

        switch = load_footprint("Gateron_KS33_LP_3.0_5Pin")
        switch.SetReference(data["reference"])
        switch.SetValue("KS33_LP_3.0_5Pin")
        switch.SetPosition(data["position"])
        switch.SetOrientationDegrees(data["orientation"])
        for pad in switch.Pads():
            if pad.GetNumber() == "1":
                pad.SetNet(board.FindNet(data["column_net"]))
            elif pad.GetNumber() == "2":
                pad.SetNet(board.FindNet(data["switch_net"]))
        board.Add(switch)

        diode = load_footprint("D_SOD-323")
        diode.SetReference(f"D{number}")
        diode.SetValue("1N4148WS")
        diode_position, diode_orientation = locate_diode(switch, number)
        diode.SetPosition(diode_position)
        diode.SetOrientationDegrees(diode_orientation)
        for pad in diode.Pads():
            if pad.GetNumber() == "1":
                pad.SetNet(board.FindNet(data["row_net"]))
            elif pad.GetNumber() == "2":
                pad.SetNet(board.FindNet(data["switch_net"]))
        board.Add(diode)

    title = board.GetTitleBlock()
    title.SetTitle("delta-omega-rev5-ks33")
    title.SetRevision("v5.0.0")
    title.SetDate("2026-10-17")
    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT):
            text = drawing.GetText()
            if "LEFT_REV_4" in text:
                drawing.SetText(text.replace("LEFT_REV_4", "LEFT_REV_5_KS33"))
            elif "RIGHT_REV_4" in text:
                drawing.SetText(text.replace("RIGHT_REV_4", "RIGHT_REV_5_KS33"))

    for item in list(board.GetTracks()):
        board.Remove(item)
    for switch in switches:
        board.Remove(switch)

    pcbnew.SaveBoard(str(target), board)
    print(f"{source_name} -> {target_name}: {len(switch_data)} switches")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: build_ks33_rev5.py "
            "delta-omega-rev4-handsolder-{left,right,both}.kicad_pcb"
        )

    source_name = sys.argv[1]
    if source_name not in SOURCE_TARGETS:
        raise SystemExit(f"unknown source board: {source_name}")
    build(source_name, SOURCE_TARGETS[source_name])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
