#!/usr/bin/env python3
"""Validate Rev5 switch count, diode orientation, matrix nets, and track widths."""

from pathlib import Path
import re
import sys

import pcbnew


ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "left": ROOT / "pcb/delta-omega-rev5-ks33-left.kicad_pcb",
    "right": ROOT / "pcb/delta-omega-rev5-ks33-right.kicad_pcb",
    "both": ROOT / "pcb/delta-omega-rev5-ks33-both.kicad_pcb",
}


def pad_net(footprint, number):
    nets = {
        pad.GetNetname()
        for pad in footprint.Pads()
        if pad.GetNumber() == str(number) and pad.GetNetname()
    }
    if len(nets) != 1:
        raise AssertionError(
            f"{footprint.GetReference()} pad {number}: nets={sorted(nets)}"
        )
    return nets.pop()


def validate_board(name, path):
    board = pcbnew.LoadBoard(str(path))
    switches = {
        footprint.GetReference(): footprint
        for footprint in board.GetFootprints()
        if re.fullmatch(r"SW\d+", footprint.GetReference())
    }
    diodes = {
        footprint.GetReference(): footprint
        for footprint in board.GetFootprints()
        if re.fullmatch(r"D\d+", footprint.GetReference())
    }
    expected = 34 if name == "both" else 17
    assert len(switches) == expected, (name, "switches", len(switches))
    assert len(diodes) == expected, (name, "diodes", len(diodes))

    for reference, switch in switches.items():
        number = reference[2:]
        diode = diodes[f"D{number}"]
        switch_net = pad_net(switch, 2)
        assert switch_net == f"SW{number}_1"
        assert pad_net(diode, 2) == switch_net
        assert pad_net(switch, 1).endswith(tuple(f"_C{column}" for column in range(1, 6)))
        assert pad_net(diode, 1).split("_", 1)[1].startswith("R")

    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_TRACK) and not isinstance(track, pcbnew.PCB_VIA):
            assert track.GetWidth() >= pcbnew.FromMM(0.2), (
                name,
                track.GetNetname(),
                pcbnew.ToMM(track.GetWidth()),
            )

    print(f"PASS {name}: {expected} switches, {expected} diodes, all widths >= 0.2 mm")


def main():
    for name, path in BOARDS.items():
        validate_board(name, path)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise
