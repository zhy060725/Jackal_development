# Semantic Motion Controller Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a ROS1 semantic motion controller that imports the YOLO capture package, reads `CaptureResult.detections`, performs cone avoidance and vehicle pursuit, and publishes `/cmd_vel`.

**Architecture:** Keep ROS, detector integration, and planning separated. `semantic_motion_controller.py` owns ROS node lifecycle and publishing. `yolo_capture_adapter.py` normalizes detector outputs. `semantic_planner.py` is pure Python and testable without ROS or YOLO.

**Tech Stack:** ROS1 `rospy`, `geometry_msgs/Twist`, importable YOLO capture Python package, pure Python unit tests with pytest.

---

### Task 1: Planner Data Model and Tests

**Files:**
- Create: `my_robot_package/src/my_robot_package/semantic_planner.py`
- Create: `my_robot_package/test/test_semantic_planner.py`

**Steps:**
1. Write tests for target-only pursuit.
2. Write tests for close cone hard stop.
3. Write tests for target plus cone avoidance bias.
4. Implement pure Python planner data classes and scoring.
5. Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test/test_semantic_planner.py -v`.

### Task 2: YOLO Capture Adapter

**Files:**
- Create: `my_robot_package/src/my_robot_package/yolo_capture_adapter.py`
- Create: `my_robot_package/test/test_yolo_capture_adapter.py`

**Steps:**
1. Write fake detector result objects matching the YOLO docs.
2. Test flattening `dict[str, list[DetectedObject]]` into normalized detections.
3. Test invalid `(0.0, 0.0, 0.0)` depth filtering.
4. Test dynamic detector import with configurable module/class names.
5. Implement adapter.

### Task 3: ROS Controller Node

**Files:**
- Create: `my_robot_package/src/semantic_motion_controller.py`
- Create: `my_robot_package/launch/semantic_motion_controller.launch`
- Create: `my_robot_package/config/semantic_motion_controller.yaml`
- Modify: `my_robot_package/CMakeLists.txt`

**Steps:**
1. Add launch compatibility test for `semantic_motion_controller.launch`.
2. Implement ROS node lifecycle: initialize detector, capture, plan, publish.
3. Publish stop on startup, exceptions, timeout, and shutdown.
4. Add script to `catkin_install_python`.

### Task 4: Documentation

**Files:**
- Modify: `docs/ros1_jackal_motion_install.md`
- Modify: `docs/ros1_jackal_motion_file_guide.md`

**Steps:**
1. Document YOLO package import assumption.
2. Document semantic controller launch command.
3. Document parameters and safe low-speed test procedure.

### Task 5: Verification

**Commands:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test -v
python3 -m py_compile \
  my_robot_package/src/my_robot_package/motion_mapper.py \
  my_robot_package/src/my_robot_package/keyboard_control_state.py \
  my_robot_package/src/my_robot_package/semantic_planner.py \
  my_robot_package/src/my_robot_package/yolo_capture_adapter.py \
  my_robot_package/src/move_to_goal.py \
  my_robot_package/src/motion_gui.py \
  my_robot_package/src/keyboard_control.py \
  my_robot_package/src/semantic_motion_controller.py \
  my_robot_package/src/turn_circle.py \
  my_robot_package/src/odom_test.py
```

Expected: all tests pass and Python syntax checks pass.
