#!/usr/bin/env python3
from __future__ import print_function

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:  # pragma: no cover - depends on host Python packages.
    tk = None
    ttk = None

import rospy
from geometry_msgs.msg import Twist

from my_robot_package.motion_mapper import MotionLimits, map_motion_command


DIRECTIONS = [
    ("Forward", "forward"),
    ("Backward", "backward"),
    ("Left", "left"),
    ("Right", "right"),
    ("Stop", "stop"),
]


class MotionGui(object):
    def __init__(self):
        if tk is None:
            raise RuntimeError("Tkinter is not available. Install python3-tk on the GUI host.")

        self.cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
        self.publish_rate = float(rospy.get_param("~publish_rate", 20.0))
        self.limits = MotionLimits(
            rospy.get_param("~linear_speed", 0.1),
            rospy.get_param("~angular_speed", 0.2),
        )
        self.publisher = rospy.Publisher(self.cmd_vel_topic, Twist, queue_size=1)

        self.root = tk.Tk()
        self.root.title("Jackal Motion Control")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.direction = tk.StringVar(value="stop")
        self.speed = tk.DoubleVar(value=0.0)
        self.status = tk.StringVar(value="Publishing stop to {}".format(self.cmd_vel_topic))

        self._build_layout()
        self._schedule_publish()

    def _build_layout(self):
        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        title = ttk.Label(main, text="Jackal Motion Control")
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(main, text="Direction").grid(row=1, column=0, sticky="w")
        buttons = ttk.Frame(main)
        buttons.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 10))

        for index, (label, value) in enumerate(DIRECTIONS):
            button = ttk.Button(buttons, text=label, command=lambda selected=value: self.set_direction(selected))
            button.grid(row=index // 3, column=index % 3, padx=3, pady=3, sticky="ew")
            buttons.columnconfigure(index % 3, weight=1)

        ttk.Label(main, text="Normalized speed").grid(row=3, column=0, sticky="w")
        speed_scale = ttk.Scale(main, from_=0.0, to=1.0, orient="horizontal", variable=self.speed)
        speed_scale.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 4))
        main.columnconfigure(1, weight=1)

        self.speed_label = ttk.Label(main, width=6)
        self.speed_label.grid(row=4, column=2, sticky="e")
        self._update_speed_label()

        ttk.Button(main, text="Stop", command=self.stop).grid(row=5, column=0, sticky="ew", pady=(8, 4))
        ttk.Button(main, text="Close", command=self.close).grid(row=5, column=1, columnspan=2, sticky="ew", pady=(8, 4))

        status = ttk.Label(main, textvariable=self.status)
        status.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def set_direction(self, direction):
        self.direction.set(direction)
        if direction != "stop" and self.speed.get() <= 0.0:
            self.speed.set(0.3)
        self._update_speed_label()

    def stop(self):
        self.direction.set("stop")
        self.speed.set(0.0)
        self._publish_stop()
        self._update_speed_label()

    def close(self):
        self._publish_stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    def _schedule_publish(self):
        if rospy.is_shutdown():
            self.close()
            return

        self._publish_current_motion()
        self._update_speed_label()
        interval_ms = int(1000.0 / self.publish_rate) if self.publish_rate > 0.0 else 50
        self.root.after(max(interval_ms, 10), self._schedule_publish)

    def _publish_current_motion(self):
        result = map_motion_command(self.direction.get(), self.speed.get(), self.limits)
        twist = Twist()
        twist.linear.x = result.linear_x
        twist.angular.z = result.angular_z
        self.publisher.publish(twist)

        self.status.set(
            "topic={} direction={} speed={:.2f} linear.x={:.3f} angular.z={:.3f}".format(
                self.cmd_vel_topic,
                self.direction.get(),
                self.speed.get(),
                twist.linear.x,
                twist.angular.z,
            )
        )

    def _publish_stop(self):
        self.publisher.publish(Twist())
        self.status.set("Publishing stop to {}".format(self.cmd_vel_topic))

    def _update_speed_label(self):
        if hasattr(self, "speed_label"):
            self.speed_label.configure(text="{:.2f}".format(self.speed.get()))


def main():
    rospy.init_node("motion_gui")
    gui = MotionGui()
    try:
        gui.run()
    finally:
        gui._publish_stop()


if __name__ == "__main__":
    main()
