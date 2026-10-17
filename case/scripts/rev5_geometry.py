"""Shared Rev5 mechanical geometry and coordinate transforms."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

BOARD_CASE_PAIRS = (
    (
        "left",
        ROOT / "pcb/delta-omega-rev5-ks33-left.kicad_pcb",
        ROOT / "case/delta_omega_rev5_left.step",
        ROOT / "case/delta_omega_rev2_left.step",
    ),
    (
        "right",
        ROOT / "pcb/delta-omega-rev5-ks33-right.kicad_pcb",
        ROOT / "case/delta_omega_rev5_right.step",
        ROOT / "case/delta_omega_rev2_right.step",
    ),
)

# The standalone right PCB uses a different X origin from the standalone right
# case. These offsets align the PCB mounting holes with the case screw bosses.
CASE_OFFSET_X = {"left": 0.0, "right": 22.2}

PCB_TOP_Z = 1.6
REV2_RIM_Z = 7.0
CASE_RIM_Z = 8.8
SWITCH_SIZE_X = 14.6
SWITCH_SIZE_Y = 14.6
SWITCH_CORNER_RADIUS = 1.5
SWITCH_HEIGHT = 6.2

CASE_POCKET_SIZE = 15.2
CASE_POCKET_CORNER_RADIUS = 1.8
CASE_POCKET_BOTTOM_Z = 1.55
CASE_POCKET_TOP_Z = CASE_RIM_Z + 0.05

CAP_SKIRT_LOW_Z = 5.0
CAP_SKIRT_SIZE = 14.0
CAP_SKIRT_CORNER_RADIUS = 3.5
CAP_SKIRT_TOP_Z = REV2_RIM_Z
CAP_TOP = (16.6, 15.6)
CAP_TOP_Z = 9.0
CAP_TOP_CORNER_RADIUS = 7.0

MAX_INTERSECTION_MM3 = 0.001


def board_to_case(side, x, y):
    """Map KiCad coordinates (Y down) into the STEP case frame (Y up)."""
    return x + CASE_OFFSET_X[side], -y


def switch_rotation(pcb_rotation):
    """Reflect the footprint rotation together with the Y axis."""
    return -pcb_rotation


def rounded_box(cq, x, y, z0, z1, size_x, size_y, radius, rotation):
    workplane = cq.Workplane("XY").rect(size_x, size_y).extrude(z1 - z0)
    if radius:
        workplane = workplane.edges("|Z").fillet(radius)
    return (
        workplane.rotate((0, 0, 0), (0, 0, 1), rotation)
        .translate((x, y, z0))
        .val()
    )


def extend_case_rim(cq, case_shape):
    top_faces = [
        face
        for face in case_shape.Faces()
        if abs(face.Center().z - REV2_RIM_Z) < 0.001
        and face.normalAt().z > 0.99
    ]
    if len(top_faces) != 1:
        raise RuntimeError(
            f"expected one Rev2 top face at z={REV2_RIM_Z}, "
            f"found {len(top_faces)}"
        )
    if CASE_RIM_Z <= REV2_RIM_Z:
        raise RuntimeError("Rev5 case rim must be above the Rev2 rim")
    extension = (
        cq.Workplane("XY")
        .add(top_faces[0])
        .toPending()
        .extrude(CASE_RIM_Z - REV2_RIM_Z)
        .val()
    )
    return case_shape.fuse(extension)


def switch_body(cq, side, switch):
    position = switch.GetPosition()
    x, y = board_to_case(side, position.x / 1e6, position.y / 1e6)
    rotation = switch_rotation(switch.GetOrientation().AsDegrees())
    return rounded_box(
        cq,
        x,
        y,
        PCB_TOP_Z,
        PCB_TOP_Z + SWITCH_HEIGHT,
        SWITCH_SIZE_X,
        SWITCH_SIZE_Y,
        SWITCH_CORNER_RADIUS,
        rotation,
    )


def keycap_envelope(cq, side, switch):
    position = switch.GetPosition()
    x, y = board_to_case(side, position.x / 1e6, position.y / 1e6)
    rotation = switch_rotation(switch.GetOrientation().AsDegrees())
    lower = rounded_box(
        cq,
        x,
        y,
        CAP_SKIRT_LOW_Z,
        CAP_SKIRT_TOP_Z,
        CAP_SKIRT_SIZE,
        CAP_SKIRT_SIZE,
        CAP_SKIRT_CORNER_RADIUS,
        rotation,
    )
    upper = rounded_box(
        cq,
        x,
        y,
        CAP_SKIRT_TOP_Z,
        CAP_TOP_Z,
        CAP_TOP[0],
        CAP_TOP[1],
        CAP_TOP_CORNER_RADIUS,
        rotation,
    )
    return lower.fuse(upper)


def intersection_volume(shape, candidate):
    overlap = shape.intersect(candidate)
    return overlap.Volume() if overlap else 0.0
