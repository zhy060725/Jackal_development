from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from jackal_basic_motion.motion_mapper import (
    MotionLimits,
    MotionMappingResult,
    map_motion_command_to_vector,
)


class BasicMotionNode(Node):
    """Map high-level Jackal motion commands to cmd_vel Twist messages."""

    def __init__(self) -> None:
        super().__init__("jackal_basic_motion_node")

        self.declare_parameter("motion_command_topic", "/jackal/motion/command")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("max_linear_speed", 0.5)
        self.declare_parameter("max_angular_speed", 1.0)
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("enable_timeout_stop", True)

        self._motion_command_topic = self._get_string_parameter("motion_command_topic")
        self._cmd_vel_topic = self._get_string_parameter("cmd_vel_topic")
        self._limits = MotionLimits(
            max_linear_speed=self._get_float_parameter("max_linear_speed"),
            max_angular_speed=self._get_float_parameter("max_angular_speed"),
        )
        self._command_timeout_sec = self._get_float_parameter("command_timeout_sec")
        self._enable_timeout_stop = self._get_bool_parameter("enable_timeout_stop")

        publish_rate_hz = self._get_float_parameter("publish_rate_hz")
        timer_period_sec = 1.0 / publish_rate_hz if publish_rate_hz > 0.0 else 0.05

        self._cmd_vel_publisher = self.create_publisher(Twist, self._cmd_vel_topic, 10)
        self._last_command_time = None
        self._last_result: Optional[MotionMappingResult] = None

        from jackal_motion_interfaces.msg import MotionCommand

        self._motion_command_subscription = self.create_subscription(
            MotionCommand,
            self._motion_command_topic,
            self.motion_command_callback,
            10,
        )
        self._timeout_timer = self.create_timer(timer_period_sec, self.timer_callback)

        self.get_logger().info(
            "Basic motion node listening on "
            f"{self._motion_command_topic} and publishing to {self._cmd_vel_topic}"
        )

    def motion_command_callback(self, msg) -> None:
        result = map_motion_command_to_vector(msg.direction, msg.speed, self._limits)
        self._last_command_time = self.get_clock().now()
        self._last_result = result

        if not result.is_valid:
            self.get_logger().warn(
                f"Invalid motion command direction={msg.direction!r} "
                f"speed={msg.speed!r} reason={result.reason}; publishing stop"
            )

        self._publish_motion_result(result)

    def timer_callback(self) -> None:
        if not self._enable_timeout_stop or self._last_command_time is None:
            return

        elapsed_sec = (
            self.get_clock().now() - self._last_command_time
        ).nanoseconds / 1_000_000_000.0
        if elapsed_sec > self._command_timeout_sec:
            self._publish_stop()
            self._last_command_time = None
            self._last_result = None
            self.get_logger().warn("Motion command timeout exceeded; publishing stop")

    def _publish_motion_result(self, result: MotionMappingResult) -> None:
        twist = Twist()
        twist.linear.x = result.vector.linear_x
        twist.angular.z = result.vector.angular_z
        self._cmd_vel_publisher.publish(twist)

    def _publish_stop(self) -> None:
        twist = Twist()
        self._cmd_vel_publisher.publish(twist)

    def _get_string_parameter(self, name: str) -> str:
        return str(self.get_parameter(name).value)

    def _get_float_parameter(self, name: str) -> float:
        return float(self.get_parameter(name).value)

    def _get_bool_parameter(self, name: str) -> bool:
        return bool(self.get_parameter(name).value)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BasicMotionNode()
    try:
        rclpy.spin(node)
    finally:
        node._publish_stop()
        node.destroy_node()
        rclpy.shutdown()
