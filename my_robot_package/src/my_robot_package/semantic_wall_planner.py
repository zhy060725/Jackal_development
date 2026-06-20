import math

import numpy as np

from my_robot_package.semantic_cruise_planner import (
    CruisePlannerConfig,
    SemanticCruisePlanner,
)
from my_robot_package.semantic_planner import Detection, MotionCommand


class WallPoint(object):
    def __init__(self, x, z):
        self.x = float(x)
        self.z = float(z)

    @property
    def is_valid(self):
        return math.isfinite(self.x) and math.isfinite(self.z) and self.z > 0.0


def resolve_depth_scale(configured_scale, detector_scale):
    configured = float(configured_scale)
    if configured > 0.0:
        return configured
    detector = float(detector_scale)
    if detector > 0.0:
        return detector
    raise ValueError("wall controller requires a positive depth scale")


def wall_points_from_depth(
    mask_depth,
    fx,
    cx,
    minimum_depth=0.1,
    maximum_depth=4.0,
    pixel_stride=4,
    angular_bins=90,
    depth_percentile=10.0,
    depth_scale=1.0,
):
    depth = np.asarray(mask_depth)
    if depth.ndim != 2:
        raise ValueError("wall mask depth must be a two-dimensional array")
    if float(fx) <= 0.0:
        raise ValueError("camera fx must be positive")

    height, width = depth.shape
    if height == 0 or width == 0:
        return []

    stride = max(int(pixel_stride), 1)
    bin_count = min(max(int(angular_bins), 1), width)
    minimum = float(minimum_depth)
    maximum = float(maximum_depth)
    percentile = min(max(float(depth_percentile), 0.0), 100.0)
    scale = float(depth_scale)
    points = []

    for index in range(bin_count):
        start = int(index * width / float(bin_count))
        end = int((index + 1) * width / float(bin_count))
        end = max(end, start + 1)
        block = depth[::stride, start:end:stride].astype(np.float64) * scale
        valid = block[
            np.isfinite(block)
            & (block > 0.0)
            & (block >= minimum)
            & (block <= maximum)
        ]
        if valid.size == 0:
            continue

        z = float(np.percentile(valid, percentile))
        pixel_x = 0.5 * (start + end - 1)
        x = (pixel_x - float(cx)) / float(fx) * z
        points.append(WallPoint(x, z))

    return points


class WallPlannerConfig(CruisePlannerConfig):
    WALL_LABEL = "__wall__"

    def __init__(
        self,
        wall_safety_margin=0.2,
        wall_stop_distance=0.5,
        wall_emergency_stop_distance=0.25,
        wall_turn_speed=0.5,
        **kwargs
    ):
        obstacle_labels = list(
            kwargs.pop("obstacle_labels", ["black_cone", "red_cone"])
        )
        if self.WALL_LABEL not in obstacle_labels:
            obstacle_labels.append(self.WALL_LABEL)
        robot_radius = float(kwargs.pop("robot_radius", 0.3))
        self.wall_safety_margin = max(float(wall_safety_margin), 0.0)
        super(WallPlannerConfig, self).__init__(
            obstacle_labels=obstacle_labels,
            robot_radius=robot_radius + self.wall_safety_margin,
            **kwargs
        )
        self.wall_stop_distance = max(float(wall_stop_distance), 0.0)
        self.wall_emergency_stop_distance = min(
            max(float(wall_emergency_stop_distance), 0.0),
            self.wall_stop_distance,
        )
        self.wall_turn_speed = min(
            max(float(wall_turn_speed), 0.0), self.max_angular_speed
        )


class SemanticWallPlanner(SemanticCruisePlanner):
    def __init__(self, config=None):
        super(SemanticWallPlanner, self).__init__(config or WallPlannerConfig())

    def plan(self, detections, wall_points):
        walls = [point for point in wall_points if point.is_valid]
        if self._has_emergency_wall(walls):
            return MotionCommand(reason="wall_emergency_stop")
        if self._has_close_forward_wall(walls):
            return self._wall_escape_command(walls)

        augmented = list(detections)
        augmented.extend(
            Detection(self.config.WALL_LABEL, 1.0, point.x, 0.0, point.z)
            for point in walls
        )
        return super(SemanticWallPlanner, self).plan(augmented)

    def _has_emergency_wall(self, walls):
        return any(
            math.hypot(point.x, point.z)
            <= self.config.wall_emergency_stop_distance
            for point in walls
        )

    def _has_close_forward_wall(self, walls):
        return any(
            point.z <= self.config.wall_stop_distance
            and abs(point.x) <= self.config.forward_corridor_half_width
            for point in walls
        )

    def _wall_escape_command(self, walls):
        maximum_clearance = self.config.obstacle_avoid_distance
        left_clearance = min(
            (math.hypot(point.x, point.z) for point in walls if point.x < 0.0),
            default=maximum_clearance,
        )
        right_clearance = min(
            (math.hypot(point.x, point.z) for point in walls if point.x > 0.0),
            default=maximum_clearance,
        )
        if left_clearance == right_clearance:
            turn_sign = 1.0
        else:
            turn_sign = 1.0 if left_clearance > right_clearance else -1.0
        return MotionCommand(
            linear_x=0.0,
            angular_z=turn_sign * self.config.wall_turn_speed,
            reason="wall_escape",
        )
