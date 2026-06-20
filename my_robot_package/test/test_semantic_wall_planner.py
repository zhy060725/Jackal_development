import math
import pathlib
import sys

import numpy as np


PACKAGE_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from my_robot_package.semantic_planner import Detection
from my_robot_package.semantic_wall_planner import (
    SemanticWallPlanner,
    WallPlannerConfig,
    WallPoint,
    resolve_depth_scale,
    wall_points_from_depth,
)


def _planner(**overrides):
    values = {
        "max_linear_speed": 0.4,
        "max_angular_speed": 1.0,
        "cruise_linear_speed": 0.4,
        "obstacle_avoid_distance": 1.2,
        "obstacle_stop_distance": 0.3,
        "forward_corridor_half_width": 0.35,
        "robot_radius": 0.2,
        "wall_safety_margin": 0.1,
        "wall_stop_distance": 0.5,
        "wall_emergency_stop_distance": 0.25,
        "wall_turn_speed": 0.6,
    }
    values.update(overrides)
    return SemanticWallPlanner(WallPlannerConfig(**values))


def test_wall_depth_ignores_zero_nonfinite_and_negative_values():
    depth = np.array(
        [
            [0.0, np.inf, np.nan, -1.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )

    points = wall_points_from_depth(depth, fx=4.0, cx=2.0)

    assert points == []


def test_wall_depth_is_compressed_into_angular_bins():
    depth = np.zeros((4, 8), dtype=np.float32)
    depth[:, 0:2] = 1.0
    depth[:, 6:8] = 2.0

    points = wall_points_from_depth(
        depth,
        fx=4.0,
        cx=4.0,
        angular_bins=4,
        pixel_stride=1,
        depth_percentile=10.0,
    )

    assert len(points) == 2
    assert math.isclose(points[0].z, 1.0)
    assert points[0].x < 0.0
    assert math.isclose(points[1].z, 2.0)
    assert points[1].x > 0.0


def test_detector_depth_scale_is_used_when_configured_scale_is_zero():
    assert math.isclose(resolve_depth_scale(0.0, 0.001), 0.001)


def test_explicit_depth_scale_overrides_detector_scale():
    assert math.isclose(resolve_depth_scale(0.002, 0.001), 0.002)


def test_clear_wall_view_keeps_default_cruise():
    command = _planner().plan([], [])

    assert command.linear_x > 0.0
    assert abs(command.angular_z) < 0.1
    assert command.reason == "cruise"


def test_wall_on_left_biases_cruise_to_right():
    command = _planner().plan([], [WallPoint(-0.25, 0.8)])

    assert command.linear_x > 0.0
    assert command.angular_z < 0.0
    assert command.reason == "cruise"


def test_close_wall_stops_forward_motion_and_turns_toward_clear_side():
    command = _planner().plan([], [WallPoint(-0.1, 0.4)])

    assert command.linear_x == 0.0
    assert command.angular_z < 0.0
    assert command.reason == "wall_escape"


def test_emergency_wall_distance_returns_complete_stop():
    command = _planner().plan([], [WallPoint(0.0, 0.2)])

    assert command.linear_x == 0.0
    assert command.angular_z == 0.0
    assert command.reason == "wall_emergency_stop"


def test_green_car_pursuit_still_respects_wall_points():
    detections = [Detection("green_car", 0.9, 0.0, 0.0, 2.0)]

    clear = _planner().plan(detections, [])
    avoiding = _planner().plan(detections, [WallPoint(-0.25, 0.8)])

    assert clear.reason == "pursuit"
    assert avoiding.reason == "pursuit"
    assert avoiding.angular_z < clear.angular_z
