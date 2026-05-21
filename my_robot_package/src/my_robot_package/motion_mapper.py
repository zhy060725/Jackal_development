import math


VALID_DIRECTIONS = frozenset(["forward", "backward", "left", "right", "stop"])


class MotionLimits(object):
    def __init__(self, max_linear_speed, max_angular_speed):
        self.max_linear_speed = float(max_linear_speed)
        self.max_angular_speed = float(max_angular_speed)


class MotionResult(object):
    def __init__(self, linear_x, angular_z, is_valid, normalized_speed, reason=""):
        self.linear_x = float(linear_x)
        self.angular_z = float(angular_z)
        self.is_valid = bool(is_valid)
        self.normalized_speed = float(normalized_speed)
        self.reason = reason


def _stop(is_valid=True, reason=""):
    return MotionResult(0.0, 0.0, is_valid, 0.0, reason)


def _normalize_direction(direction):
    if not isinstance(direction, str):
        return ""
    return direction.strip().lower()


def _clamp_speed(speed):
    value = float(speed)
    return min(max(value, 0.0), 1.0)


def map_motion_command(direction, speed, limits):
    normalized_direction = _normalize_direction(direction)
    if normalized_direction not in VALID_DIRECTIONS:
        return _stop(False, "invalid_direction")

    try:
        if not math.isfinite(float(speed)):
            return _stop(False, "invalid_speed")
        normalized_speed = _clamp_speed(speed)
    except (TypeError, ValueError):
        return _stop(False, "invalid_speed")

    if normalized_direction == "stop":
        return MotionResult(0.0, 0.0, True, normalized_speed)
    if normalized_direction == "forward":
        return MotionResult(normalized_speed * limits.max_linear_speed, 0.0, True, normalized_speed)
    if normalized_direction == "backward":
        return MotionResult(-normalized_speed * limits.max_linear_speed, 0.0, True, normalized_speed)
    if normalized_direction == "left":
        return MotionResult(0.0, normalized_speed * limits.max_angular_speed, True, normalized_speed)
    return MotionResult(0.0, -normalized_speed * limits.max_angular_speed, True, normalized_speed)
