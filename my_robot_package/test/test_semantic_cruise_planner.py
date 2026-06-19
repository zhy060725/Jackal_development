import pathlib
import sys


PACKAGE_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from my_robot_package.semantic_cruise_planner import (
    CruisePlannerConfig,
    SemanticCruisePlanner,
)
from my_robot_package.semantic_planner import Detection


def _planner(**overrides):
    values = {
        "max_linear_speed": 0.4,
        "max_angular_speed": 1.0,
        "obstacle_avoid_distance": 1.2,
        "obstacle_stop_distance": 0.45,
        "forward_corridor_half_width": 0.35,
    }
    values.update(overrides)
    return SemanticCruisePlanner(CruisePlannerConfig(**values))


def test_clear_path_cruises_forward_without_target():
    command = _planner().plan([])

    assert command.linear_x > 0.0
    assert abs(command.angular_z) < 0.1
    assert command.reason == "cruise"


def test_green_car_uses_existing_pursuit_behavior():
    command = _planner().plan([Detection("green_car", 0.9, -0.5, 0.0, 2.0)])

    assert command.linear_x > 0.0
    assert command.angular_z > 0.0
    assert command.reason == "pursuit"


def test_black_cone_on_left_biases_cruise_to_right():
    command = _planner().plan([Detection("black_cone", 0.9, -0.25, 0.0, 0.8)])

    assert command.linear_x > 0.0
    assert command.angular_z < 0.0
    assert command.reason == "cruise"


def test_red_cone_is_also_used_for_avoidance():
    command = _planner().plan([Detection("red_cone", 0.9, 0.25, 0.0, 0.8)])

    assert command.linear_x > 0.0
    assert command.angular_z > 0.0


def test_close_cone_in_forward_corridor_stops_cruise():
    command = _planner().plan([Detection("black_cone", 0.9, 0.1, 0.0, 0.3)])

    assert command.linear_x == 0.0
    assert command.angular_z == 0.0
    assert command.reason == "obstacle_stop"


def test_no_collision_free_trajectory_stops():
    command = _planner(robot_radius=3.0).plan(
        [Detection("red_cone", 0.9, 0.0, 0.0, 2.0)]
    )

    assert command.linear_x == 0.0
    assert command.angular_z == 0.0
    assert command.reason == "no_safe_trajectory"
