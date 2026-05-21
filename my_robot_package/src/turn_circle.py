#!/usr/bin/env python3
from __future__ import print_function

import rospy
from geometry_msgs.msg import Twist


def main():
    rospy.init_node("turn_circle")

    cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
    linear_speed = rospy.get_param("~linear_speed", 0.0)
    angular_speed = rospy.get_param("~angular_speed", -0.2)
    duration = rospy.get_param("~duration", 0.0)
    publish_rate = rospy.get_param("~publish_rate", 20.0)
    publish_stop_on_exit = rospy.get_param("~publish_stop_on_exit", True)

    publisher = rospy.Publisher(cmd_vel_topic, Twist, queue_size=1)
    twist = Twist()
    twist.linear.x = linear_speed
    twist.angular.z = angular_speed

    rate = rospy.Rate(publish_rate if publish_rate > 0.0 else 20.0)
    start_time = rospy.Time.now()

    rospy.loginfo(
        "turn_circle publishing to %s linear.x=%.3f angular.z=%.3f",
        cmd_vel_topic,
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
            publisher.publish(Twist())


if __name__ == "__main__":
    main()
