# Semantic Wall Controller Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an independent ROS1 wall-aware cruise controller using a zero-background depth mask while preserving existing semantic pursuit and cone avoidance behavior.

**Architecture:** Compress the wall mask into camera-relative local points, then feed those points into a planner derived from the existing cruise planner. Keep ROS/detector orchestration in a separate node and load existing YAML files before a wall-specific overlay.

**Tech Stack:** ROS1 `rospy`, NumPy, `geometry_msgs/Twist`, pytest, catkin.

---

### Task 1: Define Wall Mask Processing and Planner Behavior

**Files:**
- Create: `my_robot_package/test/test_semantic_wall_planner.py`
- Create: `my_robot_package/src/my_robot_package/semantic_wall_planner.py`

1. Write failing tests showing that zero and invalid depth values are ignored.
2. Write failing tests for angular compression and pixel-to-local-point conversion.
3. Write failing tests for clear cruise, wall avoidance, close-wall escape rotation, emergency stop, and pursuit with wall constraints.
4. Run the test file and verify failure because the module is absent.
5. Implement the minimum wall processor, configuration, and planner required by the tests.
6. Run the test file and expect all tests to pass.

### Task 2: Add the Independent ROS Node

**Files:**
- Create: `my_robot_package/src/semantic_wall_controller.py`
- Create: `my_robot_package/config/semantic_wall_controller.yaml`
- Create: `my_robot_package/launch/semantic_wall_controller.launch`
- Modify: `my_robot_package/CMakeLists.txt`
- Modify: `my_robot_package/test/test_launch_compatibility.py`

1. Add a failing launch compatibility test.
2. Implement the agreed `capture()` and `predict()` sequence.
3. Read camera intrinsics from the started detector and compress `musk_depth` before planning.
4. Add the wall configuration overlay and three-stage configuration launch file.
5. Install the new controller executable through catkin.
6. Run launch and planner tests and expect all tests to pass.

### Task 3: Document and Verify

**Files:**
- Modify: `docs/ros1_jackal_motion_install.md`
- Modify: `docs/ros1_jackal_motion_file_guide.md`

1. Document the detector contract, wall-mask meaning, launch command, parameters, and absence of exit handling.
2. Run the complete pytest suite.
3. Compile every Python source file with `python3 -m py_compile`.
4. Run `git diff --check` and review the complete scope.
