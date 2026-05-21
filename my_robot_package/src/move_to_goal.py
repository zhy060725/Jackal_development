#!/usr/bin/env python3
from __future__ import print_function

import rospy
from geometry_msgs.msg import Twist

from my_robot_package.motion_mapper import MotionLimits, map_motion_command


def _twist_from_result(result):
    twist = Twist()
    twist.linear.x = result.linear_x
    twist.angular.z = result.angular_z
    return twist


def _publish_stop(publisher):
    publisher.publish(Twist())


def main():
    rospy.init_node("move_to_goal")

    cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
    direction = rospy.get_param("~direction", "forward")
    speed = rospy.get_param("~speed", 1.0)
    max_linear_speed = rospy.get_param("~linear_speed", 0.1)
    max_angular_speed = rospy.get_param("~angular_speed", 0.2)
    duration = rospy.get_param("~duration", 0.0)
    publish_rate = rospy.get_param("~publish_rate", 20.0)
    publish_stop_on_exit = rospy.get_param("~publish_stop_on_exit", True)

    publisher = rospy.Publisher(cmd_vel_topic, Twist, queue_size=1)
    limits = MotionLimits(max_linear_speed, max_angular_speed)
    result = map_motion_command(direction, speed, limits)
    twist = _twist_from_result(result)

    if not result.is_valid:
        rospy.logwarn(
            "Invalid motion command direction=%r speed=%r reason=%s; publishing stop",
            direction,
            speed,
            result.reason,
        )

    rate = rospy.Rate(publish_rate if publish_rate > 0.0 else 20.0)
    start_time = rospy.Time.now()

    rospy.loginfo(
        "move_to_goal publishing to %s direction=%s linear.x=%.3f angular.z=%.3f",
        cmd_vel_topic,
        direction,
        twist.linear.x,
        twist.angular.z,
    )

    try:
        while not rospy.is_shutdown():
            publisher.publish(twist)
            if duration > 0.0 and (rospy.Time.now() - start_time).to_sec() >= duration:
                break
            rate.sleep()
    finally:
        if publish_stop_on_exit:
            _publish_stop(publisher)


if __name__ == "__main__":
    main()
