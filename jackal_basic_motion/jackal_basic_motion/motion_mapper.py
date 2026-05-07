import math
from dataclasses import dataclass


VALID_DIRECTIONS = frozenset({"forward", "backward", "left", "right", "stop"})


@dataclass(frozen=True)
class MotionLimits:
    max_linear_speed: float
    max_angular_speed: float


@dataclass(frozen=True)
class MotionVector:
    linear_x: float
    angular_z: float


@dataclass(frozen=True)
class MotionMappingResult:
    vector: MotionVector
    is_valid: bool
    normalized_speed: float
    reason: str = ""


def stop_vector() -> MotionVector:
    return MotionVector(linear_x=0.0, angular_z=0.0)


def map_motion_command_to_vector(
    direction: str,
    speed: float,
    limits: MotionLimits,
) -> MotionMappingResult:
    normalized_direction = direction.strip().lower() if isinstance(direction, str) else ""
    if normalized_direction not in VALID_DIRECTIONS:
        return MotionMappingResult(stop_vector(), False, 0.0, "invalid_direction")

    if not math.isfinite(speed):
        return MotionMappingResult(stop_vector(), False, 0.0, "invalid_speed")

    normalized_speed = min(max(float(speed), 0.0), 1.0)

    if normalized_direction == "stop":
        return MotionMappingResult(stop_vector(), True, normalized_speed)
    if normalized_direction == "forward":
        vector = MotionVector(normalized_speed * limits.max_linear_speed, 0.0)
    elif normalized_direction == "backward":
        vector = MotionVector(-normalized_speed * limits.max_linear_speed, 0.0)
    elif normalized_direction == "left":
        vector = MotionVector(0.0, normalized_speed * limits.max_angular_speed)
    else:
        vector = MotionVector(0.0, -normalized_speed * limits.max_angular_speed)

    return MotionMappingResult(vector, True, normalized_speed)
