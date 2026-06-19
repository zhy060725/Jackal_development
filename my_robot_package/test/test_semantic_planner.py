import pathlib
import sys


PACKAGE_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from my_robot_package.semantic_planner import Detection, PlannerConfig, SemanticPlanner


def _planner():
    return SemanticPlanner(
        PlannerConfig(
            max_linear_speed=0.4,
            max_angular_speed=1.0,
            desired_follow_distance=1.2,
            minimum_target_distance=0.6,
            obstacle_avoid_distance=1.2,
            obstacle_stop_distance=0.45,
            forward_corridor_half_width=0.35,
        )
    )


def test_target_ahead_produces_forward_motion():
    command = _planner().plan([Detection("green_car", 0.9, 0.0, 0.0, 2.0)])

    assert command.linear_x > 0.0
    assert abs(command.angular_z) < 0.1
    assert command.reason == "pursuit"


def test_target_to_left_produces_left_turn():
    command = _planner().plan([Detection("green_car", 0.9, -0.5, 0.0, 2.0)])

    assert command.linear_x > 0.0
    assert command.angular_z > 0.0


def test_close_cone_in_forward_corridor_forces_stop():
    command = _planner().plan(
        [
            Detection("green_car", 0.9, 0.0, 0.0, 2.0),
            Detection("black_cone", 0.9, 0.1, 0.0, 0.3),
        ]
    )

    assert command.linear_x == 0.0
    assert command.angular_z == 0.0
    assert command.reason == "obstacle_stop"


def test_cone_on_left_biases_motion_to_right():
    clear = _planner().plan([Detection("green_car", 0.9, 0.0, 0.0, 2.0)])
    avoiding = _planner().plan(
        [
            Detection("green_car", 0.9, 0.0, 0.0, 2.0),
            Detection("red_cone", 0.9, -0.25, 0.0, 0.8),
        ]
    )

    assert avoiding.angular_z < clear.angular_z
    assert avoiding.angular_z < 0.0


def test_no_valid_target_returns_stop():
    command = _planner().plan([Detection("black_cone", 0.9, 0.8, 0.0, 2.0)])

    assert command.linear_x == 0.0
    assert command.angular_z == 0.0
    assert command.reason == "no_target"
