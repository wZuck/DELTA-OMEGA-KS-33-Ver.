#!/usr/bin/env python3
"""Route the Rev5 nets that Freerouting cannot finish on a two-layer board."""

from collections import defaultdict
from dataclasses import dataclass
from heapq import heappop, heappush
from pathlib import Path
import argparse
import math
import subprocess
import sys

import pcbnew


GRID = 0.1
TRACE_WIDTH = 0.2
CLEARANCE = 0.2
TRACE_RADIUS = TRACE_WIDTH / 2
TRACE_MARGIN = CLEARANCE + TRACE_RADIUS + 0.01
VIA_DIAMETER = 0.6
VIA_DRILL = 0.3
VIA_MARGIN = CLEARANCE + VIA_DIAMETER / 2 + 0.01
NPTH_HOLE_CLEARANCE = 0.25
EDGE_MARGIN = 0.6


@dataclass(frozen=True)
class NetRoute:
    name: str
    start: tuple[float, float]
    goal: tuple[float, float]
    start_layers: tuple = None
    goal_layers: tuple = None


ROUTES = {
    "left": [
        NetRoute(
            "L_C2",
            (22.49, 38.08),
            (49.805262, 51.133049),
            start_layers=(pcbnew.F_Cu,),
            goal_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
        ),
        NetRoute(
            "L_C2",
            (49.805262, 51.133049),
            (53.339762, 67.761649),
            start_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
            goal_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
        ),
        NetRoute(
            "L_C2",
            (53.339762, 67.761649),
            (56.874262, 84.390149),
            start_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
            goal_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
        ),
        NetRoute("L_BATP", (26.0, 42.86), (99.3661, 35.7746)),
        NetRoute("L_LED_R3", (36.4, 52.66), (50.2320, 39.75)),
        NetRoute("L_RST", (29.175, 37.36), (107.7911, 33.7146)),
    ],
    "right": [
        NetRoute(
            "R_C2",
            (220.1222, 38.08),
            (201.373453, 49.548763),
            start_layers=(pcbnew.F_Cu,),
            goal_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
        ),
        NetRoute(
            "R_C2",
            (201.373453, 49.548763),
            (197.838953, 66.177363),
            start_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
            goal_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
        ),
        NetRoute(
            "R_C2",
            (197.838953, 66.177363),
            (194.304453, 82.805863),
            start_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
            goal_layers=(pcbnew.F_Cu, pcbnew.B_Cu),
        ),
        NetRoute("R_BATP", (223.6322, 42.86), (154.7661, 35.7746)),
        NetRoute("R_LED_R3", (234.0322, 52.66), (208.4, 39.75)),
        NetRoute("R_RST", (226.8072, 37.36), (150.8411, 33.7146)),
    ],
}
ROUTES["both"] = ROUTES["left"] + ROUTES["right"]

RST_PAD_LINKS = {
    "left": [((107.7911, 33.7146), (113.0411, 33.7146))],
    "right": [((145.5911, 33.7146), (150.8411, 33.7146))],
}
RST_PAD_LINKS["both"] = RST_PAD_LINKS["left"] + RST_PAD_LINKS["right"]


def mm_point(point):
    return pcbnew.VECTOR2I(pcbnew.FromMM(point[0]), pcbnew.FromMM(point[1]))


class Router:
    def __init__(self, board, bounds=None, safe_outline=None):
        self.board = board
        if bounds is None or safe_outline is None:
            raw_bounds = board.GetBoardEdgesBoundingBox()
            bounds = (
                pcbnew.ToMM(raw_bounds.GetX()),
                pcbnew.ToMM(raw_bounds.GetY()),
                pcbnew.ToMM(raw_bounds.GetX() + raw_bounds.GetWidth()),
                pcbnew.ToMM(raw_bounds.GetY() + raw_bounds.GetHeight()),
            )
            outline = pcbnew.SHAPE_POLY_SET()
            if not board.GetBoardPolygonOutlines(outline, True):
                raise RuntimeError("KiCad could not resolve the board outline")
            safe_outline = pcbnew.SHAPE_POLY_SET(outline)
            safe_outline.Deflate(
                pcbnew.FromMM(EDGE_MARGIN),
                pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,
                pcbnew.FromMM(0.005),
            )
        self.xmin, self.ymin, self.xmax, self.ymax = bounds
        self.safe_outline = safe_outline
        self.width = int(math.ceil((self.xmax - self.xmin) / GRID)) + 1
        self.height = int(math.ceil((self.ymax - self.ymin) / GRID)) + 1
        self.size = self.width * self.height
        self.layers = {
            pcbnew.F_Cu: bytearray(self.size),
            pcbnew.B_Cu: bytearray(self.size),
        }
        self.via_layers = {
            pcbnew.F_Cu: bytearray(self.size),
            pcbnew.B_Cu: bytearray(self.size),
        }
        self.routed_segments = defaultdict(list)
        self.build_obstacles()

    def index(self, ix, iy):
        return iy * self.width + ix

    def grid_xy(self, point):
        ix = round((point[0] - self.xmin) / GRID)
        iy = round((point[1] - self.ymin) / GRID)
        return max(0, min(self.width - 1, ix)), max(0, min(self.height - 1, iy))

    def world_xy(self, ix, iy):
        return self.xmin + ix * GRID, self.ymin + iy * GRID

    def raster_disc(self, mask, x, y, radius, value=1):
        ix, iy = self.grid_xy((x, y))
        cells = int(math.ceil(radius / GRID))
        radius_sq = radius * radius
        for yy in range(max(0, iy - cells), min(self.height, iy + cells + 1)):
            wy = self.ymin + yy * GRID
            for xx in range(max(0, ix - cells), min(self.width, ix + cells + 1)):
                wx = self.xmin + xx * GRID
                if (wx - x) ** 2 + (wy - y) ** 2 <= radius_sq:
                    mask[self.index(xx, yy)] = value

    def raster_segment(self, mask, start, end, radius, value=1):
        x1, y1 = start
        x2, y2 = end
        length = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(math.ceil(length / (GRID * 0.4))))
        for step in range(steps + 1):
            ratio = step / steps
            self.raster_disc(
                mask,
                x1 + (x2 - x1) * ratio,
                y1 + (y2 - y1) * ratio,
                radius,
                value,
            )

    def pad_layers(self, pad):
        layers = []
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if pad.IsOnLayer(layer):
                layers.append(layer)
        return layers

    def build_obstacles(self, ignore_net=None):
        self.layers = {
            pcbnew.F_Cu: bytearray(self.size),
            pcbnew.B_Cu: bytearray(self.size),
        }
        self.via_layers = {
            pcbnew.F_Cu: bytearray(self.size),
            pcbnew.B_Cu: bytearray(self.size),
        }
        self.routed_segments = defaultdict(list)
        for track in self.board.GetTracks():
            net = track.GetNetname()
            if net == ignore_net:
                continue
            start = pcbnew.ToMM(track.GetStart())
            end = pcbnew.ToMM(track.GetEnd())
            self.routed_segments[net].append((start, end))
            if isinstance(track, pcbnew.PCB_VIA):
                point = pcbnew.ToMM(track.GetPosition())
                radius = pcbnew.ToMM(track.GetWidth(pcbnew.F_Cu)) / 2
                for layer in track.GetLayerSet().Seq():
                    if layer in self.layers:
                        self.raster_disc(self.layers[layer], *point, radius + TRACE_MARGIN)
                        self.raster_disc(self.via_layers[layer], *point, radius + VIA_MARGIN)
            else:
                layer = track.GetLayer()
                if layer in self.layers:
                    half_width = pcbnew.ToMM(track.GetWidth()) / 2
                    self.raster_segment(
                        self.layers[layer],
                        start,
                        end,
                        half_width + TRACE_MARGIN,
                    )
                    self.raster_segment(
                        self.via_layers[layer],
                        start,
                        end,
                        half_width + VIA_MARGIN,
                    )

        for footprint in self.board.GetFootprints():
            for pad in footprint.Pads():
                if pad.GetNetname() == ignore_net:
                    continue
                box = pad.GetBoundingBox()
                layers = self.pad_layers(pad)
                is_npth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
                if is_npth:
                    layers = [pcbnew.F_Cu, pcbnew.B_Cu]
                trace_margin = (
                    max(
                        TRACE_MARGIN,
                        NPTH_HOLE_CLEARANCE + TRACE_RADIUS + 0.01,
                    )
                    if is_npth
                    else TRACE_MARGIN
                )
                via_margin = (
                    max(
                        VIA_MARGIN,
                        NPTH_HOLE_CLEARANCE + VIA_DIAMETER / 2 + 0.01,
                    )
                    if is_npth
                    else VIA_MARGIN
                )
                for margin, masks in (
                    (trace_margin, self.layers),
                    (via_margin, self.via_layers),
                ):
                    x0 = pcbnew.ToMM(box.GetX()) - margin
                    y0 = pcbnew.ToMM(box.GetY()) - margin
                    x1 = x0 + pcbnew.ToMM(box.GetWidth()) + 2 * margin
                    y1 = y0 + pcbnew.ToMM(box.GetHeight()) + 2 * margin
                    ix0, iy0 = self.grid_xy((x0, y0))
                    ix1, iy1 = self.grid_xy((x1, y1))
                    for yy in range(iy0, iy1 + 1):
                        for xx in range(ix0, ix1 + 1):
                            value = self.index(xx, yy)
                            for layer in layers:
                                masks[layer][value] = 1

    def valid(self, ix, iy, layer):
        x, y = self.world_xy(ix, iy)
        if not self.safe_outline.Contains(mm_point((x, y))):
            return False
        value = self.index(ix, iy)
        if self.layers[layer][value]:
            return False
        return True

    def nearest_valid_grids(self, point, layers, radius=2.0):
        ix, iy = self.grid_xy(point)
        cells = int(math.ceil(radius / GRID))
        candidates = {layer: None for layer in layers}
        for yy in range(max(0, iy - cells), min(self.height, iy + cells + 1)):
            for xx in range(max(0, ix - cells), min(self.width, ix + cells + 1)):
                wx, wy = self.world_xy(xx, yy)
                distance = math.hypot(wx - point[0], wy - point[1])
                if distance > radius:
                    continue
                if not self.safe_outline.Contains(mm_point((wx, wy))):
                    continue
                for layer in layers:
                    if self.valid(xx, yy, layer):
                        candidate = (distance, xx, yy, layer)
                        current = candidates[layer]
                        if current is None or candidate < current:
                            candidates[layer] = candidate
        return [candidate for candidate in candidates.values() if candidate is not None]

    def route(self, route, start_layers=None, goal_layers=None):
        self.build_obstacles(ignore_net=route.name)

        if start_layers is None:
            start_layers = [pcbnew.F_Cu, pcbnew.B_Cu]
        if goal_layers is None:
            goal_layers = [pcbnew.F_Cu]
        start_grids = self.nearest_valid_grids(route.start, start_layers)
        goal_grids = self.nearest_valid_grids(route.goal, goal_layers)
        if not start_grids:
            raise RuntimeError(f"no valid escape from {route.name} start")
        if not goal_grids:
            raise RuntimeError(f"no valid escape to {route.name} goal")
        start_states = [(xx, yy, layer) for _, xx, yy, layer in start_grids]
        goal_states = {
            (xx, yy, layer) for _, xx, yy, layer in goal_grids
        }
        _, gx, gy, _ = goal_grids[0]
        queue = []
        distance = {}
        previous = {}
        for state in start_states:
            distance[state] = 0
            heappush(queue, (0, 0, state))

        directions = [
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (1, 1, math.sqrt(2)),
        ]

        final_state = None
        serial = 0
        while queue:
            _, _, state = heappop(queue)
            ix, iy, layer = state
            if state in goal_states:
                final_state = state
                break

            base = distance[state]
            for dx, dy, move_cost in directions:
                nx, ny = ix + dx, iy + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if not self.valid(nx, ny, layer):
                    continue
                if dx and dy:
                    if not self.valid(ix + dx, iy, layer):
                        continue
                    if not self.valid(ix, iy + dy, layer):
                        continue
                next_state = (nx, ny, layer)
                next_distance = base + move_cost
                if next_distance < distance.get(next_state, math.inf):
                    distance[next_state] = next_distance
                    previous[next_state] = state
                    heuristic = math.hypot(gx - nx, gy - ny)
                    serial += 1
                    heappush(queue, (next_distance + heuristic, serial, next_state))

            value = self.index(ix, iy)
            if not self.via_layers[pcbnew.F_Cu][value] and not self.via_layers[pcbnew.B_Cu][value]:
                other_layer = pcbnew.B_Cu if layer == pcbnew.F_Cu else pcbnew.F_Cu
                next_state = (ix, iy, other_layer)
                next_distance = base + 18
                if next_distance < distance.get(next_state, math.inf):
                    distance[next_state] = next_distance
                    previous[next_state] = state
                    heuristic = math.hypot(gx - ix, gy - iy)
                    serial += 1
                    heappush(queue, (next_distance + heuristic, serial, next_state))

        if final_state is None:
            raise RuntimeError(f"unable to route {route.name}")

        path = [final_state]
        while path[-1] in previous:
            path.append(previous[path[-1]])
        path.reverse()
        return path

    def add_track(self, net_name, layer, start, end):
        track = pcbnew.PCB_TRACK(self.board)
        track.SetNet(self.board.FindNet(net_name))
        track.SetLayer(layer)
        track.SetStart(mm_point(start))
        track.SetEnd(mm_point(end))
        track.SetWidth(pcbnew.FromMM(TRACE_WIDTH))
        self.board.Add(track)
        self.routed_segments[net_name].append((start, end))

    def add_path(self, route, path):
        layer_runs = []
        current_run = [path[0]]
        for current in path[1:]:
            if current[2] != current_run[-1][2]:
                layer_runs.append(current_run)
                current_run = [current]
            else:
                current_run.append(current)
        layer_runs.append(current_run)

        runs = []
        for layer_run in layer_runs:
            points = [layer_run[0]]
            for index in range(1, len(layer_run) - 1):
                a, b, c = layer_run[index - 1], layer_run[index], layer_run[index + 1]
                dx1, dy1 = b[0] - a[0], b[1] - a[1]
                dx2, dy2 = c[0] - b[0], c[1] - b[1]
                if dx1 * dy2 != dy1 * dx2:
                    points.append(b)
            if len(layer_run) > 1:
                points.append(layer_run[-1])
            for first, second in zip(points, points[1:]):
                runs.append((first, second, first[2]))

        for first_run, second_run in zip(layer_runs, layer_runs[1:]):
            run_end = first_run[-1]
            via_position = self.world_xy(run_end[0], run_end[1])
            via_point = mm_point(via_position)
            duplicate = any(
                isinstance(item, pcbnew.PCB_VIA)
                and item.GetNetname() == route.name
                and item.GetPosition() == via_point
                for item in self.board.GetTracks()
            )
            if not duplicate:
                via = pcbnew.PCB_VIA(self.board)
                via.SetNet(self.board.FindNet(route.name))
                via.SetPosition(via_point)
                via.SetWidth(pcbnew.FromMM(VIA_DIAMETER))
                via.SetDrill(pcbnew.FromMM(VIA_DRILL))
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                self.board.Add(via)
            via_radius = VIA_DIAMETER / 2
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                self.raster_disc(
                    self.layers[layer],
                    *via_position,
                    via_radius + TRACE_MARGIN,
                )
                self.raster_disc(
                    self.via_layers[layer],
                    *via_position,
                    via_radius + VIA_MARGIN,
                )

        for start_state, end_state, layer in runs:
            if start_state[:2] != end_state[:2]:
                start = self.world_xy(start_state[0], start_state[1])
                end = self.world_xy(end_state[0], end_state[1])
                self.add_track(route.name, layer, start, end)

        first_state = path[0]
        if first_state[:2] != self.grid_xy(route.start):
            start_grid = self.world_xy(first_state[0], first_state[1])
            self.add_track(route.name, first_state[2], route.start, start_grid)

        last_state = path[-1]
        if last_state[:2] != self.grid_xy(route.goal):
            end_grid = self.world_xy(last_state[0], last_state[1])
            self.add_track(route.name, last_state[2], end_grid, route.goal)

        for first, second in zip(path, path[1:]):
            if first[2] == second[2]:
                start = self.world_xy(first[0], first[1])
                end = self.world_xy(second[0], second[1])
                half_width = TRACE_RADIUS
                self.raster_segment(
                    self.layers[first[2]],
                    start,
                    end,
                    half_width + TRACE_MARGIN,
                )
                self.raster_segment(
                    self.via_layers[first[2]],
                    start,
                    end,
                    half_width + VIA_MARGIN,
                )


def connect_ground_islands(router, board, net_name):
    zone = next(
        (candidate for candidate in board.Zones() if candidate.GetNetname() == net_name),
        None,
    )
    if zone is None:
        raise RuntimeError(f"missing ground zone {net_name}")

    polygons = zone.GetFilledPolysList(pcbnew.F_Cu)
    if polygons.OutlineCount() <= 1:
        return 0

    router.build_obstacles(ignore_net=net_name)

    def candidates(outline):
        center = outline.Centre()
        cx = pcbnew.ToMM(center.x)
        cy = pcbnew.ToMM(center.y)
        box = outline.BBox()
        ix0, iy0 = router.grid_xy(
            (pcbnew.ToMM(box.GetX()), pcbnew.ToMM(box.GetY()))
        )
        ix1, iy1 = router.grid_xy(
            (
                pcbnew.ToMM(box.GetX() + box.GetWidth()),
                pcbnew.ToMM(box.GetY() + box.GetHeight()),
            )
        )
        result = []
        for iy in range(iy0, iy1 + 1):
            for ix in range(ix0, ix1 + 1):
                x, y = router.world_xy(ix, iy)
                point = mm_point((x, y))
                if not outline.PointInside(point):
                    continue
                if router.layers[pcbnew.F_Cu][router.index(ix, iy)]:
                    continue
                result.append((math.hypot(x - cx, y - cy), x, y))
        return result

    main_candidates = candidates(polygons.Outline(0))
    if not main_candidates:
        raise RuntimeError(f"no routing point in main {net_name} island")
    _, main_x, main_y = min(main_candidates)

    routed = 0
    for index in range(1, polygons.OutlineCount()):
        island_candidates = candidates(polygons.Outline(index))
        if not island_candidates:
            raise RuntimeError(f"no routing point in {net_name} island {index}")
        _, x, y = min(island_candidates)
        route = NetRoute(
            net_name,
            (x, y),
            (main_x, main_y),
            start_layers=(pcbnew.F_Cu,),
            goal_layers=(pcbnew.F_Cu,),
        )
        path = router.route(
            route,
            start_layers=[pcbnew.F_Cu],
            goal_layers=[pcbnew.F_Cu],
        )
        router.add_path(route, path)
        routed += 1
    return routed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    parser.add_argument("--strip", action="store_true")
    args = parser.parse_args()

    board_path = Path(args.board).resolve()
    side = (
        "both"
        if "both" in board_path.stem
        else "left"
        if "left" in board_path.stem
        else "right"
        if "right" in board_path.stem
        else None
    )
    if side is None:
        raise SystemExit("board name must contain left or right")

    if not args.strip:
        subprocess.run(
            [sys.executable, __file__, str(board_path), "--strip"],
            check=True,
        )

    board = pcbnew.LoadBoard(str(board_path))
    if args.strip:
        route_nets = {route.name for route in ROUTES[side]}
        for item in list(board.GetTracks()):
            if item.GetNetname() in route_nets:
                board.Remove(item)
        pcbnew.SaveBoard(str(board_path), board)
        print(f"stripped remaining-net routing from {board_path.name}")
        return

    raw_bounds = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(raw_bounds.GetX()),
        pcbnew.ToMM(raw_bounds.GetY()),
        pcbnew.ToMM(raw_bounds.GetX() + raw_bounds.GetWidth()),
        pcbnew.ToMM(raw_bounds.GetY() + raw_bounds.GetHeight()),
    )
    outline = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(outline, True):
        raise RuntimeError("KiCad could not resolve the board outline")
    safe_outline = pcbnew.SHAPE_POLY_SET(outline)
    safe_outline.Deflate(
        pcbnew.FromMM(EDGE_MARGIN),
        pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,
        pcbnew.FromMM(0.005),
    )

    router = Router(board, bounds, safe_outline)
    for route in ROUTES[side]:
        path = router.route(
            route,
            start_layers=route.start_layers,
            goal_layers=route.goal_layers,
        )
        router.add_path(route, path)
        print(f"{route.name}: {len(path)} grid points")

    for rst_net, pad_link in (
        [("L_RST", RST_PAD_LINKS[side][0])]
        if side == "left"
        else [("R_RST", RST_PAD_LINKS[side][0])]
        if side == "right"
        else [
            ("L_RST", RST_PAD_LINKS[side][0]),
            ("R_RST", RST_PAD_LINKS[side][1]),
        ]
    ):
        reset_link = NetRoute(rst_net, *pad_link)
        path = router.route(
            reset_link,
            start_layers=[pcbnew.F_Cu],
            goal_layers=[pcbnew.F_Cu],
        )
        router.add_path(reset_link, path)
    ground_nets = (
        ["L_GND", "R_GND"] if side == "both" else
        ["L_GND"] if side == "left" else
        ["R_GND"]
    )
    for ground_net in ground_nets:
        count = connect_ground_islands(router, board, ground_net)
        print(f"{ground_net}: connected {count} split zone island(s)")

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(board_path), board)
    print(f"routed remaining nets on {board_path.name}")


if __name__ == "__main__":
    main()
