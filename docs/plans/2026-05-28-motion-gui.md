# ROS1 Motion GUI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a ROS1 desktop GUI for dynamically controlling Jackal direction and speed while continuing to publish standard `geometry_msgs/Twist` messages to `/cmd_vel`.

**Architecture:** Add a Tkinter-based ROS node, `motion_gui.py`, plus `motion_gui.launch`. The GUI keeps a current direction and normalized speed, maps them through the existing `motion_mapper.py`, and publishes at a fixed rate.

**Tech Stack:** ROS1 `rospy`, `geometry_msgs/Twist`, Python 3, Tkinter, pytest.

---

### Task 1: Launch Compatibility Test

Add a test asserting `motion_gui.launch` exists and starts `motion_gui.py`.

### Task 2: GUI Node

Create `src/motion_gui.py`, install it via `CMakeLists.txt`, and add `launch/motion_gui.launch`.

### Task 3: Docs and Verification

Update ROS1 usage docs and run pytest plus Python syntax checks.
