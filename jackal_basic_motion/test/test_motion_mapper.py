import math

from jackal_basic_motion.motion_mapper import (
    MotionLimits,
    map_motion_command_to_vector,
)


def test_forward_command_maps_to_positive_linear_x():
    result = map_motion_command_to_vector("forward", 0.5, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == 1.0
    assert result.vector.angular_z == 0.0


def test_backward_command_maps_to_negative_linear_x():
    result = map_motion_command_to_vector("backward", 0.25, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == -0.5
    assert result.vector.angular_z == 0.0


def test_left_command_maps_to_positive_angular_z():
    result = map_motion_command_to_vector("left", 0.5, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == 0.0
    assert result.vector.angular_z == 2.0


def test_right_command_maps_to_negative_angular_z():
    result = map_motion_command_to_vector("right", 0.25, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == 0.0
    assert result.vector.angular_z == -1.0


def test_stop_command_maps_to_zero_motion():
    result = map_motion_command_to_vector("stop", 1.0, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == 0.0
    assert result.vector.angular_z == 0.0


def test_invalid_direction_returns_zero_motion_and_invalid_result():
    result = map_motion_command_to_vector("spin", 0.5, MotionLimits(2.0, 4.0))

    assert result.is_valid is False
    assert result.vector.linear_x == 0.0
    assert result.vector.angular_z == 0.0


def test_non_finite_speed_returns_zero_motion_and_invalid_result():
    result = map_motion_command_to_vector("forward", math.nan, MotionLimits(2.0, 4.0))

    assert result.is_valid is False
    assert result.vector.linear_x == 0.0
    assert result.vector.angular_z == 0.0


def test_speed_below_zero_is_clamped_to_zero():
    result = map_motion_command_to_vector("forward", -0.5, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == 0.0
    assert result.vector.angular_z == 0.0


def test_speed_above_one_is_clamped_to_one():
    result = map_motion_command_to_vector("forward", 2.0, MotionLimits(2.0, 4.0))

    assert result.is_valid is True
    assert result.vector.linear_x == 2.0
    assert result.vector.angular_z == 0.0
