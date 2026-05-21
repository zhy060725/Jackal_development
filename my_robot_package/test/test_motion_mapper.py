import math
import pathlib
import sys


PACKAGE_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from my_robot_package.motion_mapper import MotionLimits, map_motion_command


def test_forward_maps_to_positive_linear_velocity():
    result = map_motion_command("forward", 0.5, MotionLimits(0.4, 1.0))

    assert result.linear_x == 0.2
    assert result.angular_z == 0.0
    assert result.is_valid


def test_backward_maps_to_negative_linear_velocity():
    result = map_motion_command("backward", 1.0, MotionLimits(0.4, 1.0))

    assert result.linear_x == -0.4
    assert result.angular_z == 0.0
    assert result.is_valid


def test_left_and_right_map_to_opposite_angular_velocity():
    limits = MotionLimits(0.4, 0.8)

    left = map_motion_command("left", 0.5, limits)
    right = map_motion_command("right", 0.5, limits)

    assert left.linear_x == 0.0
    assert left.angular_z == 0.4
    assert right.linear_x == 0.0
    assert right.angular_z == -0.4


def test_stop_and_invalid_commands_return_zero_motion():
    limits = MotionLimits(0.4, 0.8)

    stop = map_motion_command("stop", 1.0, limits)
    invalid_direction = map_motion_command("spin", 1.0, limits)
    invalid_speed = map_motion_command("forward", math.inf, limits)

    assert stop.is_valid
    assert stop.linear_x == 0.0
    assert stop.angular_z == 0.0
    assert not invalid_direction.is_valid
    assert invalid_direction.linear_x == 0.0
    assert invalid_direction.angular_z == 0.0
    assert not invalid_speed.is_valid
    assert invalid_speed.linear_x == 0.0
    assert invalid_speed.angular_z == 0.0


def test_speed_is_clamped_to_normalized_range():
    limits = MotionLimits(0.4, 0.8)

    below = map_motion_command("forward", -1.0, limits)
    above = map_motion_command("forward", 2.0, limits)

    assert below.linear_x == 0.0
    assert above.linear_x == 0.4
