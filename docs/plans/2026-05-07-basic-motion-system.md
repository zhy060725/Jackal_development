# Basic Motion System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first ROS2 Foxy basic motion system for Jackal, with a custom `MotionCommand` message and a Python node that maps direction and normalized speed to `geometry_msgs/Twist`.

**Architecture:** Create one interface package, `jackal_motion_interfaces`, and one Python package, `jackal_basic_motion`. Keep safety-critical mapping logic in pure Python functions so it can be tested without a local ROS2 runtime; the ROS2 node handles parameters, subscription, timeout stop, and publishing.

**Tech Stack:** ROS2 Foxy, `rclpy`, `geometry_msgs`, custom ROS2 message generation, Python 3, `pytest`.

---

### Task 1: Pure Motion Mapping Contract

**Files:**
- Create: `jackal_basic_motion/jackal_basic_motion/motion_mapper.py`
- Create: `jackal_basic_motion/test/test_motion_mapper.py`

**Step 1: Write the failing test**

Add tests for:
- `forward` maps to positive `linear_x`.
- `backward` maps to negative `linear_x`.
- `left` maps to positive `angular_z`.
- `right` maps to negative `angular_z`.
- `stop` returns zero motion.
- invalid directions return zero motion and `is_valid=False`.
- non-finite speed returns zero motion and `is_valid=False`.
- speed below `0.0` clamps to `0.0`.
- speed above `1.0` clamps to `1.0`.

**Step 2: Run test to verify it fails**

Run:

```bash
pytest jackal_basic_motion/test/test_motion_mapper.py -v
```

Expected: FAIL because `motion_mapper.py` does not exist yet.

**Step 3: Write minimal implementation**

Create:
- `MotionVector`
- `MotionLimits`
- `MotionMappingResult`
- `map_motion_command_to_vector(direction, speed, limits)`

Use normalized speed `[0.0, 1.0]`. Do not import ROS2 in this file.

**Step 4: Run test to verify it passes**

Run:

```bash
pytest jackal_basic_motion/test/test_motion_mapper.py -v
```

Expected: PASS.

### Task 2: ROS2 Interface Package

**Files:**
- Create: `jackal_motion_interfaces/msg/MotionCommand.msg`
- Create: `jackal_motion_interfaces/package.xml`
- Create: `jackal_motion_interfaces/CMakeLists.txt`

**Step 1: Create custom message**

Create `MotionCommand.msg`:

```text
string direction
float32 speed
```

**Step 2: Create interface package metadata**

Add `package.xml` and `CMakeLists.txt` for ROS2 Foxy message generation using `rosidl_default_generators`.

**Step 3: Verify static content**

Run:

```bash
python3 -m py_compile jackal_basic_motion/jackal_basic_motion/motion_mapper.py
```

Expected: PASS. Full message generation requires ROS2 Foxy and `colcon build`.

### Task 3: Python Package and Basic Motion Node

**Files:**
- Create: `jackal_basic_motion/package.xml`
- Create: `jackal_basic_motion/setup.py`
- Create: `jackal_basic_motion/setup.cfg`
- Create: `jackal_basic_motion/resource/jackal_basic_motion`
- Create: `jackal_basic_motion/jackal_basic_motion/__init__.py`
- Create: `jackal_basic_motion/jackal_basic_motion/basic_motion_node.py`
- Create: `jackal_basic_motion/test/test_basic_motion_imports.py`

**Step 1: Write import-level test**

Add a test that imports `jackal_basic_motion.motion_mapper` and validates the package layout without requiring ROS2 runtime.

**Step 2: Run test to verify it fails**

Run:

```bash
pytest jackal_basic_motion/test/test_basic_motion_imports.py -v
```

Expected: FAIL before package files exist.

**Step 3: Create Python package files**

Create ROS2 Python package metadata and node entry point:

```text
basic_motion_node = jackal_basic_motion.basic_motion_node:main
```

**Step 4: Create node implementation**

The node should:
- Name itself `jackal_basic_motion_node`.
- Declare parameters:
  - `motion_command_topic` default `/jackal/motion/command`
  - `cmd_vel_topic` default `/cmd_vel`
  - `max_linear_speed` default `0.5`
  - `max_angular_speed` default `1.0`
  - `command_timeout_sec` default `0.5`
  - `publish_rate_hz` default `20.0`
  - `enable_timeout_stop` default `True`
- Subscribe to `jackal_motion_interfaces.msg.MotionCommand`.
- Publish `geometry_msgs.msg.Twist`.
- Use `map_motion_command_to_vector`.
- Publish stop on invalid command.
- Publish stop when command timeout is exceeded.

**Step 5: Run tests and syntax checks**

Run:

```bash
pytest jackal_basic_motion/test -v
python3 -m py_compile jackal_basic_motion/jackal_basic_motion/motion_mapper.py jackal_basic_motion/jackal_basic_motion/basic_motion_node.py
```

Expected: PASS if dependencies are importable. If ROS2 Python modules are not installed locally, document that node import is not locally verified.

### Task 4: Documentation Updates

**Files:**
- Modify: `PROJECT_LOG.md`
- Modify: `docs/ros2_foxy_jackal_install.md`

**Step 1: Update design status**

Mark these choices as implemented:
- normalized `speed` range `[0.0, 1.0]`
- package names
- `/jackal/motion/command`
- `/cmd_vel`

**Step 2: Update install guide**

Make the guide reflect actual package files and test commands.

**Step 3: Review docs**

Run:

```bash
rg -n "jackal_motion_interfaces|jackal_basic_motion|/jackal/motion/command|MotionCommand" PROJECT_LOG.md docs
```

Expected: all references are consistent.

### Task 5: Final Verification

**Files:**
- All created files.

**Step 1: Run available local verification**

Run:

```bash
pytest jackal_basic_motion/test -v
python3 -m py_compile jackal_basic_motion/jackal_basic_motion/motion_mapper.py jackal_basic_motion/jackal_basic_motion/basic_motion_node.py
```

**Step 2: Report ROS2-only verification gap**

If local machine lacks ROS2 Foxy modules, report that `colcon build`, `ros2 interface show`, and `ros2 run` must be verified on the Jackal host or Foxy workspace.
