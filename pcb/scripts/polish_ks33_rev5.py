#!/usr/bin/env python3
"""Apply final manufacturing and DRC polish to a routed Rev5 board."""

from pathlib import Path
import argparse
import math
import subprocess
import sys

import pcbnew


def point_mm(point):
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def endpoint_key(item):
    points = sorted((point_mm(item.GetStart()), point_mm(item.GetEnd())))
    return tuple(round(value, 4) for point in points for value in point)


def remove_tracks_with_endpoints(board, keys):
    removed = 0
    for track in list(board.GetTracks()):
        if isinstance(track, pcbnew.PCB_VIA):
            continue
        if endpoint_key(track) in keys:
            board.Remove(track)
            removed += 1
    return removed


def add_track(board, net_name, layer, start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(board.FindNet(net_name))
    track.SetLayer(layer)
    track.SetWidth(pcbnew.FromMM(0.2))
    track.SetStart(
        pcbnew.VECTOR2I(pcbnew.FromMM(start[0]), pcbnew.FromMM(start[1]))
    )
    track.SetEnd(
        pcbnew.VECTOR2I(pcbnew.FromMM(end[0]), pcbnew.FromMM(end[1]))
    )
    board.Add(track)


def fix_known_necks(board):
    # L_R1 exits beside MCU pad 8. Keep the bend clear of the adjacent pad.
    r1_keys = {
        (39.1591, 49.51, 39.3524, 49.7033),
        (39.3799, 49.7308, 39.5887, 49.7308),
        (39.3524, 49.7033, 39.3799, 49.7308),
        (39.5887, 49.7308, 40.0377, 50.1798),
    }
    if any(
        endpoint_key(track) in r1_keys
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA)
    ):
        remove_tracks_with_endpoints(board, r1_keys)
        add_track(board, "L_R1", pcbnew.F_Cu, (39.1591, 49.51), (40.0377, 49.51))
        add_track(
            board,
            "L_R1",
            pcbnew.F_Cu,
            (40.0377, 49.51),
            (40.0377, 50.1798),
        )

    # The panel autorouter can place L_C5 too close to MCU2 pad 10.
    c5_keys = {
        (36.21, 45.7, 37.572, 44.338),
        (37.572, 44.338, 39.8503, 44.338),
        (39.8503, 44.338, 40.021, 44.1673),
    }
    if any(
        endpoint_key(track) in c5_keys
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA)
    ):
        remove_tracks_with_endpoints(board, c5_keys)
        add_track(board, "L_C5", pcbnew.F_Cu, (36.21, 45.7), (36.21, 44.3))
        add_track(board, "L_C5", pcbnew.F_Cu, (36.21, 44.3), (39.85, 44.3))
        add_track(
            board,
            "L_C5",
            pcbnew.F_Cu,
            (39.85, 44.3),
            (40.021, 44.1673),
        )


def remove_battery_location_frame(board):
    battery_frames = (
        (59.677459, 97.100001, 83.91245, 113.8),
        (174.7197, 97.100001, 198.954691, 113.8),
    )
    targets = []
    for drawing in list(board.GetDrawings()):
        if (
            not isinstance(drawing, pcbnew.PCB_SHAPE)
            or drawing.GetLayer() != pcbnew.F_Fab
        ):
            continue
        box = drawing.GetBoundingBox()
        x = pcbnew.ToMM(box.GetX())
        y = pcbnew.ToMM(box.GetY())
        width = pcbnew.ToMM(box.GetWidth())
        height = pcbnew.ToMM(box.GetHeight())
        center_x = x + width / 2
        center_y = y + height / 2
        perimeter = False
        for left, top, right, bottom in battery_frames:
            within_x = left - 0.2 <= center_x <= right + 0.2
            within_y = top - 0.2 <= center_y <= bottom + 0.2
            on_horizontal_edge = within_x and (
                abs(center_y - top) < 0.2 or abs(center_y - bottom) < 0.2
            )
            on_vertical_edge = within_y and (
                abs(center_x - left) < 0.2 or abs(center_x - right) < 0.2
            )
            corner_arc = (
                drawing.GetShape() == pcbnew.SHAPE_T_ARC
                and 1.0 < width < 2.0
                and 1.0 < height < 2.0
                and within_x
                and within_y
                and min(
                    abs(center_x - left),
                    abs(center_x - right),
                )
                < 1.0
                and min(
                    abs(center_y - top),
                    abs(center_y - bottom),
                )
                < 1.0
            )
            dashed_hatch = (
                drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT
                and within_x
                and within_y
                and 0.5 < width < 2.0
                and 0.5 < height < 1.3
            )
            if (
                on_horizontal_edge
                or on_vertical_edge
                or corner_arc
                or dashed_hatch
            ):
                perimeter = True
                break
        if perimeter:
            targets.append(drawing)

    # Removing directly while bounding subsequent drawings can invalidate the
    # KiCad SWIG wrappers on some boards. Collect first, then mutate the board.
    for drawing in targets:
        board.Remove(drawing)
    return len(targets)


def remove_redundant_vias(board):
    removed = 0
    for via in list(board.GetTracks()):
        if not isinstance(via, pcbnew.PCB_VIA):
            continue
        net = via.GetNetname()
        position = via.GetPosition()
        layers = set()
        for track in board.GetTracks():
            if (
                track is via
                or isinstance(track, pcbnew.PCB_VIA)
                or track.GetNetname() != net
            ):
                continue
            if track.GetStart() == position or track.GetEnd() == position:
                layers.add(track.GetLayer())

        if len(layers) != 1:
            continue
        missing_layer = (
            pcbnew.B_Cu if next(iter(layers)) == pcbnew.F_Cu else pcbnew.F_Cu
        )
        connects_smd_pad = any(
            pad.GetNetname() == net
            and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
            and pad.IsOnLayer(missing_layer)
            and pad.GetBoundingBox().Contains(position)
            for footprint in board.GetFootprints()
            for pad in footprint.Pads()
        )
        if not connects_smd_pad and not net.endswith("_GND"):
            board.Remove(via)
            removed += 1
    return removed


def ensure_diode_polarity_marks(board):
    existing = set()
    for drawing in board.GetDrawings():
        if (
            isinstance(drawing, pcbnew.PCB_SHAPE)
            and drawing.GetLayer() == pcbnew.F_SilkS
            and drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT
        ):
            existing.add(endpoint_key(drawing))

    added = 0
    for footprint in board.GetFootprints():
        if not footprint.GetReference().startswith("D"):
            continue
        if any(
            item.GetLayer() == pcbnew.F_SilkS
            for item in footprint.GraphicalItems()
        ):
            continue
        position = footprint.GetPosition()
        x0 = pcbnew.ToMM(position.x)
        y0 = pcbnew.ToMM(position.y)
        angle = math.radians(footprint.GetOrientation().AsDegrees())

        def transform(local_x, local_y):
            return (
                x0 + local_x * math.cos(angle) + local_y * math.sin(angle),
                y0 - local_x * math.sin(angle) + local_y * math.cos(angle),
            )

        start = transform(-1.9, -0.82)
        end = transform(-1.35, -0.82)
        key = tuple(
            round(value, 4)
            for point in sorted((start, end))
            for value in point
        )
        if key in existing:
            continue

        drawing = pcbnew.PCB_SHAPE(board)
        drawing.SetShape(pcbnew.SHAPE_T_SEGMENT)
        drawing.SetLayer(pcbnew.F_SilkS)
        drawing.SetWidth(pcbnew.FromMM(0.12))
        drawing.SetStart(
            pcbnew.VECTOR2I(pcbnew.FromMM(start[0]), pcbnew.FromMM(start[1]))
        )
        drawing.SetEnd(
            pcbnew.VECTOR2I(pcbnew.FromMM(end[0]), pcbnew.FromMM(end[1]))
        )
        board.Add(drawing)
        existing.add(key)
        added += 1
    return added


def polish_footprints_and_text(board):
    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT):
            drawing.SetFontProp("")
            drawing.SetAutoThickness(True)
        elif isinstance(drawing, pcbnew.PCB_SHAPE):
            if drawing.GetLayer() == pcbnew.B_SilkS:
                drawing.SetLayer(pcbnew.B_Fab)
            elif drawing.GetLayer() == pcbnew.F_SilkS:
                box = drawing.GetBoundingBox()
                center_y = pcbnew.ToMM(box.GetY() + box.GetHeight() / 2)
                if center_y > 96:
                    drawing.SetLayer(pcbnew.F_Fab)

    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT) and "RIGHT_REV" in drawing.GetText():
            drawing.SetPosition(
                pcbnew.VECTOR2I(pcbnew.FromMM(218.5), pcbnew.FromMM(112.1))
            )

    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if reference.startswith(("SW", "D")):
            for field in footprint.GetFields():
                field.SetVisible(False)
            for item in footprint.GraphicalItems():
                if item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                    item.SetLayer(pcbnew.F_Fab)
        if reference.startswith("MCU"):
            for item in footprint.GraphicalItems():
                if item.GetLayer() == pcbnew.F_SilkS:
                    item.SetLayer(pcbnew.F_Fab)
        footprint.SetFPID(pcbnew.LIB_ID())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    parser.add_argument(
        "--stage",
        choices=("fix-necks", "battery-frame", "vias"),
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    path = Path(args.board).resolve()
    if "rev5-ks33" not in path.name:
        raise SystemExit("board must be a Rev5 KS-33 board")

    if args.stage:
        board = pcbnew.LoadBoard(str(path))
        if args.stage == "fix-necks":
            for track in board.GetTracks():
                if (
                    isinstance(track, pcbnew.PCB_TRACK)
                    and not isinstance(track, pcbnew.PCB_VIA)
                    and track.GetWidth() < pcbnew.FromMM(0.2)
                ):
                    track.SetWidth(pcbnew.FromMM(0.2))
            fix_known_necks(board)
        elif args.stage == "battery-frame":
            remove_battery_location_frame(board)
        else:
            remove_redundant_vias(board)
        if args.stage != "battery-frame":
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(str(path), board)
        return

    for stage in ("fix-necks", "battery-frame", "vias"):
        subprocess.run(
            [sys.executable, __file__, str(path), "--stage", stage],
            check=True,
        )

    board = pcbnew.LoadBoard(str(path))
    added_marks = ensure_diode_polarity_marks(board)
    polish_footprints_and_text(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(path), board)
    print(
        f"polished {path.name}; added {added_marks} diode polarity mark(s)"
    )


if __name__ == "__main__":
    main()
