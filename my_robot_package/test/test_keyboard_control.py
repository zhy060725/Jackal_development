import pathlib
import sys


PACKAGE_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from my_robot_package.keyboard_control_state import KeyboardControlState, apply_key


def test_arrow_keys_update_direction_without_changing_speed():
    state = KeyboardControlState(direction="stop", speed=0.4, speed_step=0.1)

    assert apply_key(state, "\x1b[A").direction == "forward"
    assert apply_key(state, "\x1b[B").direction == "backward"
    assert apply_key(state, "\x1b[D").direction == "left"
    right = apply_key(state, "\x1b[C")

    assert right.direction == "right"
    assert right.speed == 0.4


def test_space_stops_and_zeroes_speed():
    state = KeyboardControlState(direction="forward", speed=0.4, speed_step=0.1)

    stopped = apply_key(state, " ")

    assert stopped.direction == "stop"
    assert stopped.speed == 0.0


def test_plus_and_minus_adjust_speed_by_fixed_step():
    state = KeyboardControlState(direction="forward", speed=0.4, speed_step=0.1)

    faster = apply_key(state, "+")
    slower = apply_key(faster, "-")

    assert faster.speed == 0.5
    assert slower.speed == 0.4
    assert slower.direction == "forward"


def test_speed_adjustment_is_clamped_to_normalized_range():
    almost_max = KeyboardControlState(direction="forward", speed=0.95, speed_step=0.1)
    almost_min = KeyboardControlState(direction="forward", speed=0.05, speed_step=0.1)

    assert apply_key(almost_max, "+").speed == 1.0
    assert apply_key(almost_min, "-").speed == 0.0
