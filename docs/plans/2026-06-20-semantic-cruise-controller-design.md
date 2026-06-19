# Semantic Cruise Controller Design

## Goal

Add a separate ROS1 motion controller that keeps Jackal moving when `green_car` is not detected, avoids `black_cone` and `red_cone` using RealSense depth, and adjusts its trajectory toward the target when one is available.

## Scope

- Keep the existing `semantic_motion_controller.py` behavior unchanged except for correcting its default labels.
- Keep the existing `SemanticPlanner.plan()` pursuit-only behavior unchanged.
- Reuse the current RealSense YOLO detector adapter and normalized `Detection` model.
- Add a separate planner, ROS node, launch file, and overlay configuration for cruise behavior.
- Do not modify the camera module, depth projection, keyboard control, GUI control, or `/cmd_vel` interface.

## Labels

The model's actual labels become the defaults:

```yaml
target_labels: [green_car, truck, vehicle]
obstacle_labels: [black_cone, red_cone]
```

Legacy labels may still be supplied explicitly through ROS parameters, but they are not defaults.

## Architecture

`semantic_cruise_controller.py` owns ROS lifecycle, detector startup, capture, publishing, and fail-safe stopping. It reuses `create_detector()` and `normalize_detections()` from the existing adapter.

`SemanticCruisePlanner` extends the existing planner. It preserves the inherited stop-obstacle check and pursuit candidate scoring. When no target exists, it evaluates target-free candidate trajectories and rewards forward speed, straight heading, and obstacle clearance. Unsafe candidates are rejected using the existing robot-radius clearance rule.

## Behavior

1. Normalize detections with valid RealSense depth.
2. Select configured cone labels as obstacles.
3. Stop if a close cone occupies the forward corridor.
4. If a target exists, use the existing pursuit behavior with cone avoidance.
5. If no target exists, select the best safe cruise trajectory.
6. Stop when no collision-free trajectory exists.
7. Stop on detector initialization or capture failure.

Target loss immediately returns the new node to cruise instead of stopping. The first version intentionally has no target memory, temporal filtering, or additional sensor fusion.

## Configuration

The launch file first loads `semantic_motion_controller.yaml` as reusable base configuration and then loads `semantic_cruise_controller.yaml` as an overlay. The overlay owns the corrected labels and cruise scoring parameters.

Initial real-robot values remain conservative. "High speed" means raising the configured speed only after staged validation; the controller cannot guarantee obstacle safety outside the camera field of view or when a cone is not detected.

## Verification

Unit tests cover clear-path cruising, both cone labels, cone avoidance, emergency stop, target pursuit, and no-safe-trajectory behavior. Launch compatibility, Python compilation, the complete test suite, and whitespace checks must pass.
