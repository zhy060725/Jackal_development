# Semantic Motion Controller Design

## Goal

Build the next motion-control layer for Jackal: a ROS1 node that directly uses the YOLO capture package, reasons about semantic detections, and publishes stable `/cmd_vel` commands for cone avoidance and vehicle pursuit.

## Current Assumptions

- The project remains ROS1/catkin based.
- The Jackal base accepts `geometry_msgs/Twist` on `/cmd_vel`.
- The YOLO package is used as an importable Python API.
- The YOLO package owns model loading and model-path selection. The motion controller does not pass a model path.
- The available detector API follows the documented shape:

```python
from detector import RealSenseYOLODetector

with RealSenseYOLODetector(...) as detector:
    result = detector.capture()
    detections = result.detections
```

- `result.detections` is a `dict[str, list[DetectedObject]]`.
- Each `DetectedObject` provides `label`, `confidence`, `bbox_2d`, `centroid_2d`, and `centroid_3d`.
- `centroid_3d` is `(x, y, z)` in metres.
- `(0.0, 0.0, 0.0)` means invalid depth and must not be used for pursuit or obstacle avoidance.

## Recommended Architecture

```text
YOLO capture package
  -> RealSenseYOLODetector.capture()
  -> CaptureResult.detections
  -> yolo_capture_adapter.py
  -> semantic_planner.py
  -> semantic_motion_controller.py
  -> /cmd_vel
  -> jackal_base
```

The first implementation should not introduce a `/yolo/detections` ROS topic or custom detection message. Keeping YOLO inside the controller is simpler and matches the released package API. If later modules need the same detections, the detector can be split into a separate publisher.

## Algorithm Choice

Use a lightweight semantic variant of Dynamic Window Approach (DWA).

DWA is a mature local-planning method used by ROS Navigation's `dwa_local_planner`: sample candidate velocities, simulate short trajectories, score them, then publish the best velocity command. Full ROS Navigation integration would require costmaps, TF, robot footprint, and goal plumbing. For the first semantic controller, reuse the DWA idea locally with detections from YOLO.

References:

- ROS Index `dwa_local_planner`: https://index.ros.org/p/dwa_local_planner/
- ROS Navigation DWA implementation overview: https://deepwiki.com/ros-planning/navigation/5.2-dwa-local-planner/
- PythonRobotics DWA reference implementation: https://deepwiki.com/AtsushiSakai/PythonRobotics/2.4-dynamic-window-approach

## Planner Behavior

### Target Pursuit

Target labels:

```text
car
truck
vehicle
```

Rules:

- Select the nearest valid target by `centroid_3d.z`.
- Use target lateral offset `centroid_3d.x` to steer.
- Move forward when target distance is greater than `desired_follow_distance`.
- Slow or stop when target distance is below `minimum_target_distance`.
- If target is lost for longer than `target_lost_timeout_sec`, publish stop.

### Cone Avoidance

Obstacle labels:

```text
cone
```

Rules:

- Ignore cone detections with invalid depth.
- Cone closer than `obstacle_stop_distance` in the forward corridor triggers immediate stop.
- Cone inside `obstacle_avoid_distance` adds a strong penalty to candidate trajectories that move toward it.
- Cone left of center should bias the controller right.
- Cone right of center should bias the controller left.

### Candidate Velocity Scoring

Each control tick:

1. Build candidate linear velocities from `0.0` to `max_linear_speed`.
2. Build candidate angular velocities from `-max_angular_speed` to `+max_angular_speed`.
3. Simulate each candidate for `simulation_horizon_sec`.
4. Score each candidate:
   - target approach score
   - target alignment score
   - obstacle clearance score
   - speed smoothness score
   - stop/safety penalty
5. Publish the best candidate as `Twist`.

## Proposed Files

```text
my_robot_package/
  config/
    semantic_motion_controller.yaml
  launch/
    semantic_motion_controller.launch
  src/
    semantic_motion_controller.py
    my_robot_package/
      semantic_planner.py
      yolo_capture_adapter.py
```

## Parameters

```yaml
cmd_vel_topic: /cmd_vel
publish_rate: 10.0

detector_import_path: detector
detector_class_name: RealSenseYOLODetector
detector_kwargs: {}

target_labels: ["car", "truck", "vehicle"]
obstacle_labels: ["cone"]

max_linear_speed: 0.25
max_angular_speed: 0.8
desired_follow_distance: 1.2
minimum_target_distance: 0.6
target_lost_timeout_sec: 0.5

obstacle_avoid_distance: 1.2
obstacle_stop_distance: 0.45
forward_corridor_half_width: 0.35

linear_samples: 5
angular_samples: 9
simulation_horizon_sec: 1.0
simulation_dt_sec: 0.1
```

`detector_kwargs` exists only for optional detector configuration, such as confidence threshold or camera FPS. It must not require a model path unless the YOLO package later changes its contract.

## Safety Handling

- Publish stop before detector startup.
- Publish stop if detector initialization fails.
- Publish stop on capture exception.
- Publish stop on invalid or stale detections.
- Publish stop on node shutdown.
- Clamp all generated velocities.
- Keep the old manual control tools available for recovery and comparison.

## Testing Strategy

The core planner must be testable without ROS, RealSense, or YOLO:

- Unit-test detection normalization in `yolo_capture_adapter.py` using fake detector objects.
- Unit-test pursuit behavior with target-only detection fixtures.
- Unit-test cone avoidance with obstacle-only and target-plus-obstacle fixtures.
- Unit-test hard stop behavior for invalid depth and close cone.
- Keep syntax checks for ROS entry scripts.

Integration testing on the robot:

1. Confirm `/cmd_vel` manual command still works.
2. Run the semantic controller with low speed limits.
3. Place a cone in front and verify stop/avoid behavior.
4. Place a target vehicle label in view and verify pursuit.
5. Test loss of target and detector failure behavior.

## Deferred Work

- ROS detection topic and custom detection messages.
- Full `move_base`/costmap integration.
- Global path planning.
- Multi-target identity tracking.
- Visualization overlays.
