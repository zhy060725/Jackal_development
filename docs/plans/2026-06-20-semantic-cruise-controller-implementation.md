# Semantic Cruise Controller Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a separate ROS1 cruise controller that keeps moving without a detected green car, avoids model-labelled cones, and pursues a detected green car.

**Architecture:** Reuse the detector adapter and existing semantic planner primitives. Add a derived pure-Python cruise planner and a separate ROS node; load the existing semantic YAML first and a cruise-specific YAML overlay second.

**Tech Stack:** ROS1 `rospy`, `geometry_msgs/Twist`, Python 3, pytest, catkin.

---

### Task 1: Correct Semantic Labels

**Files:**
- Modify: `my_robot_package/src/semantic_motion_controller.py`
- Modify: `my_robot_package/src/my_robot_package/semantic_planner.py`
- Modify: `my_robot_package/config/semantic_motion_controller.yaml`
- Modify: `my_robot_package/test/test_semantic_planner.py`

1. Change default target labels to `green_car`, `truck`, and `vehicle`.
2. Change default obstacle labels to `black_cone` and `red_cone`.
3. Update tests to use the actual model labels.
4. Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test/test_semantic_planner.py -v` and expect all tests to pass.

### Task 2: Add Cruise Planner with Tests

**Files:**
- Create: `my_robot_package/src/my_robot_package/semantic_cruise_planner.py`
- Create: `my_robot_package/test/test_semantic_cruise_planner.py`

1. Write failing tests for clear-path cruise, target pursuit, both cone labels, lateral avoidance, close-obstacle stop, and no-safe-trajectory stop.
2. Run the new test file and verify import/test failures.
3. Implement `CruisePlannerConfig` and `SemanticCruisePlanner` using inherited trajectory simulation and safety helpers.
4. Run the new tests and expect them to pass.

### Task 3: Add ROS Node, Launch, and Configuration

**Files:**
- Create: `my_robot_package/src/semantic_cruise_controller.py`
- Create: `my_robot_package/config/semantic_cruise_controller.yaml`
- Create: `my_robot_package/launch/semantic_cruise_controller.launch`
- Modify: `my_robot_package/CMakeLists.txt`
- Modify: `my_robot_package/test/test_launch_compatibility.py`

1. Write a failing launch compatibility test.
2. Add the separate ROS node using existing detector creation and normalization functions.
3. Add the cruise overlay YAML and launch file that loads base then overlay configuration.
4. Install the new executable through catkin.
5. Run launch compatibility tests and expect them to pass.

### Task 4: Update Operator Documentation

**Files:**
- Modify: `docs/ros1_jackal_motion_install.md`
- Modify: `docs/ros1_jackal_motion_file_guide.md`

1. Correct documented labels.
2. Document the new node, launch command, behavior, and cruise overlay parameters.
3. Preserve the existing `confidence_threshold: 0.02` documentation.

### Task 5: Verify the Complete Change

1. Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test -v`.
2. Run `python3 -m py_compile` for all package Python source files.
3. Run `git diff --check`.
4. Review `git diff` and confirm no camera-module or unrelated behavior changes.
