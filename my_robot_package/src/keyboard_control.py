#!/usr/bin/env python3
from __future__ import print_function

import select
import sys
import termios
import tty

import rospy
from geometry_msgs.msg import Twist

from my_robot_package.keyboard_control_state import KeyboardControlState, apply_key
from my_robot_package.motion_mapper import MotionLimits, map_motion_command


HELP_TEXT = """
Jackal keyboard control

  w            forward
  s            backward
  a            left
  d            right
  + / =        increase speed
  - / _        decrease speed
  Space        stop
  q / Esc      quit
"""


def read_key(timeout_sec):
    ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)
    if not ready:
        return None

    first = sys.stdin.read(1)
    if first == "\x1b":
        ready, _, _ = select.select([sys.stdin], [], [], 0.01)
        if not ready:
            return first
        second = sys.stdin.read(1)
        if second != "[":
            return first + second
        ready, _, _ = select.select([sys.stdin], [], [], 0.01)
        if not ready:
            return first + second
        third = sys.stdin.read(1)
        return first + second + third
    return first


def twist_from_state(state, limits):
    result = map_motion_command(state.direction, state.speed, limits)
    twist = Twist()
    twist.linear.x = result.linear_x
    twist.angular.z = result.angular_z
    return twist


def print_status(state, twist, topic):
    sys.stdout.write(
        "\rtopic={} direction={} speed={:.2f} linear.x={:.3f} angular.z={:.3f}    ".format(
            topic,
            state.direction,
            state.speed,
            twist.linear.x,
            twist.angular.z,
        )
    )
    sys.stdout.flush()


def main():
    rospy.init_node("keyboard_control")

    cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
    max_linear_speed = rospy.get_param("~linear_speed", 0.1)
    max_angular_speed = rospy.get_param("~angular_speed", 0.2)
    initial_speed = rospy.get_param("~initial_speed", 0.3)
    speed_step = rospy.get_param("~speed_step", 0.1)
    publish_rate = float(rospy.get_param("~publish_rate", 20.0))

    publisher = rospy.Publisher(cmd_vel_topic, Twist, queue_size=1)
    limits = MotionLimits(max_linear_speed, max_angular_speed)
    state = KeyboardControlState(speed=0.0, speed_step=speed_step, default_speed=initial_speed)

    old_terminal_settings = termios.tcgetattr(sys.stdin)
    rate_hz = publish_rate if publish_rate > 0.0 else 20.0
    timeout_sec = 1.0 / rate_hz

    print(HELP_TEXT)
    rospy.loginfo("keyboard_control publishing to %s", cmd_vel_topic)

    try:
        tty.setcbreak(sys.stdin.fileno())
        while not rospy.is_shutdown():
            key = read_key(timeout_sec)
            if key in ("q", "Q", "\x1b"):
                break
            if key is not None:
                state = apply_key(state, key)

            twist = twist_from_state(state, limits)
            publisher.publish(twist)
            print_status(state, twist, cmd_vel_topic)
    finally:
        publisher.publish(Twist())
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_terminal_settings)
        sys.stdout.write("\nStopped Jackal keyboard control.\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
