#!/usr/bin/env python3
from __future__ import print_function

import time

import rospy
from geometry_msgs.msg import Twist

from my_robot_package.semantic_wall_planner import (
    SemanticWallPlanner,
    WallPlannerConfig,
    resolve_depth_scale,
    wall_points_from_depth,
)
from my_robot_package.yolo_capture_adapter import (
    capture_and_predict,
    create_detector,
    normalize_detections,
)


def twist_from_command(command):
    twist = Twist()
    twist.linear.x = command.linear_x
    twist.angular.z = command.angular_z
    return twist


def start_detector(detector):
    start = getattr(detector, "start", None)
    if callable(start):
        start()


def stop_detector(detector):
    stop = getattr(detector, "stop", None)
    if callable(stop):
        stop()


def planner_from_params():
    return SemanticWallPlanner(
        WallPlannerConfig(
            target_labels=rospy.get_param(
                "~target_labels", ["green_car", "truck", "vehicle"]
            ),
            obstacle_labels=rospy.get_param(
                "~obstacle_labels", ["black_cone", "red_cone"]
            ),
            max_linear_speed=rospy.get_param("~max_linear_speed", 0.25),
            max_angular_speed=rospy.get_param("~max_angular_speed", 0.8),
            desired_follow_distance=rospy.get_param("~desired_follow_distance", 1.2),
            minimum_target_distance=rospy.get_param("~minimum_target_distance", 0.6),
            obstacle_avoid_distance=rospy.get_param("~obstacle_avoid_distance", 1.2),
            obstacle_stop_distance=rospy.get_param("~obstacle_stop_distance", 0.45),
            forward_corridor_half_width=rospy.get_param(
                "~forward_corridor_half_width", 0.35
            ),
            target_heading_gain=rospy.get_param("~target_heading_gain", 1.5),
            obstacle_turn_gain=rospy.get_param("~obstacle_turn_gain", 1.0),
            linear_samples=rospy.get_param("~linear_samples", 5),
            angular_samples=rospy.get_param("~angular_samples", 9),
            simulation_horizon_sec=rospy.get_param(
                "~simulation_horizon_sec", 1.0
            ),
            simulation_dt_sec=rospy.get_param("~simulation_dt_sec", 0.1),
            robot_radius=rospy.get_param("~robot_radius", 0.3),
            cruise_linear_speed=rospy.get_param("~cruise_linear_speed", 0.25),
            cruise_heading_weight=rospy.get_param("~cruise_heading_weight", 1.0),
            cruise_speed_weight=rospy.get_param("~cruise_speed_weight", 1.0),
            cruise_clearance_weight=rospy.get_param(
                "~cruise_clearance_weight", 1.0
            ),
            wall_safety_margin=rospy.get_param("~wall_safety_margin", 0.2),
            wall_stop_distance=rospy.get_param("~wall_stop_distance", 0.5),
            wall_emergency_stop_distance=rospy.get_param(
                "~wall_emergency_stop_distance", 0.25
            ),
            wall_turn_speed=rospy.get_param("~wall_turn_speed", 0.5),
        )
    )


def camera_projection_params(detector):
    intrinsics = getattr(detector, "color_intrinsics", None)
    configured_fx = float(rospy.get_param("~camera_fx", 0.0))
    configured_cx = float(rospy.get_param("~camera_cx", -1.0))
    fx = configured_fx if configured_fx > 0.0 else getattr(intrinsics, "fx", 0.0)
    cx = configured_cx if configured_cx >= 0.0 else getattr(intrinsics, "ppx", -1.0)
    if fx <= 0.0 or cx < 0.0:
        raise ValueError("wall controller requires valid camera fx and cx")
    return float(fx), float(cx)


def main():
    rospy.init_node("semantic_wall_controller")

    cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
    publish_rate = float(rospy.get_param("~publish_rate", 10.0))
    capture_failure_sleep_sec = float(
        rospy.get_param("~capture_failure_sleep_sec", 0.5)
    )
    detector_import_path = rospy.get_param("~detector_import_path", "RealsenseYolo")
    detector_class_name = rospy.get_param(
        "~detector_class_name", "RealSenseYOLODetector"
    )
    detector_kwargs = rospy.get_param("~detector_kwargs", {})
    model_path = rospy.get_param("~model_path", "")
    if model_path:
        detector_kwargs["model_path"] = model_path
    if not detector_kwargs.get("model_path"):
        rospy.logfatal(
            "semantic_wall_controller requires model_path for RealSenseYOLODetector"
        )
        publisher = rospy.Publisher(cmd_vel_topic, Twist, queue_size=1)
        publisher.publish(Twist())
        return

    wall_depth_kwargs = {
        "minimum_depth": rospy.get_param("~wall_min_depth", 0.1),
        "maximum_depth": rospy.get_param("~wall_max_depth", 4.0),
        "pixel_stride": rospy.get_param("~wall_pixel_stride", 4),
        "angular_bins": rospy.get_param("~wall_angular_bins", 90),
        "depth_percentile": rospy.get_param("~wall_depth_percentile", 10.0),
        "depth_scale": rospy.get_param("~wall_depth_scale", 0.0),
    }

    publisher = rospy.Publisher(cmd_vel_topic, Twist, queue_size=1)
    planner = planner_from_params()
    detector = None
    stop_twist = Twist()
    publisher.publish(stop_twist)
    rospy.loginfo("semantic_wall_controller publishing to %s", cmd_vel_topic)

    try:
        detector = create_detector(
            module_name=detector_import_path,
            class_name=detector_class_name,
            detector_kwargs=detector_kwargs,
        )
        start_detector(detector)
        camera_fx, camera_cx = camera_projection_params(detector)
        wall_depth_kwargs["depth_scale"] = resolve_depth_scale(
            wall_depth_kwargs["depth_scale"], getattr(detector, "depth_scale", 0.0)
        )
        rate = rospy.Rate(publish_rate if publish_rate > 0.0 else 10.0)

        while not rospy.is_shutdown():
            try:
                capture_result, musk_depth = capture_and_predict(detector)
                detections = normalize_detections(capture_result.detections)
                wall_points = wall_points_from_depth(
                    musk_depth,
                    fx=camera_fx,
                    cx=camera_cx,
                    **wall_depth_kwargs
                )
                command = planner.plan(detections, wall_points)
                publisher.publish(twist_from_command(command))
                rospy.loginfo_throttle(
                    1.0,
                    "semantic wall reason=%s detections=%d wall_points=%d linear.x=%.3f angular.z=%.3f",
                    command.reason,
                    len(detections),
                    len(wall_points),
                    command.linear_x,
                    command.angular_z,
                )
                rate.sleep()
            except Exception as error:
                publisher.publish(stop_twist)
                rospy.logerr_throttle(
                    1.0,
                    "Wall capture, prediction, or planning failed; publishing stop: %s",
                    error,
                )
                time.sleep(max(capture_failure_sleep_sec, 0.0))
    except Exception as error:
        publisher.publish(stop_twist)
        rospy.logfatal("Failed to initialize wall detector; publishing stop: %s", error)
    finally:
        publisher.publish(stop_twist)
        if detector is not None:
            stop_detector(detector)


if __name__ == "__main__":
    main()
