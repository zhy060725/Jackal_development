#!/usr/bin/env python3
from __future__ import print_function

import rospy
from nav_msgs.msg import Odometry


def odom_callback(msg):
    position = msg.pose.pose.position
    orientation = msg.pose.pose.orientation
    linear = msg.twist.twist.linear
    angular = msg.twist.twist.angular
    rospy.loginfo_throttle(
        1.0,
        "odom position=(%.3f, %.3f, %.3f) orientation_z=%.3f linear.x=%.3f angular.z=%.3f",
        position.x,
        position.y,
        position.z,
        orientation.z,
        linear.x,
        angular.z,
    )


def main():
    rospy.init_node("odom_test")
    odom_topic = rospy.get_param("~odom_topic", "/odometry/filtered")
    rospy.Subscriber(odom_topic, Odometry, odom_callback, queue_size=10)
    rospy.loginfo("odom_test listening on %s", odom_topic)
    rospy.spin()


if __name__ == "__main__":
    main()
