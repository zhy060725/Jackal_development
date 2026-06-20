# Semantic Wall Controller Design

## Goal

Add an independent ROS1 controller that uses a wall-only depth mask to prevent Jackal from colliding with the blue arena walls while retaining cone avoidance, green-car pursuit, and default cruise behavior.

## Detector Contract

The wall controller uses the updated detector API:

```python
capture_rgb, capture_depth, musk_depth = detector.capture()
capture_result = detector.predict(capture_rgb, capture_depth)
```

`capture_rgb` and `capture_depth` are the original aligned camera frames. `musk_depth` is a two-dimensional depth array aligned with the image. A value greater than zero is the measured depth of a wall pixel. Zero means the pixel is not part of a wall. Non-finite and negative values are invalid. `capture_result` retains the previous grouped semantic-detection interface.

The mask uses raw RealSense sensor units. The controller converts it to metres with `detector.depth_scale` unless a positive override is configured.

## Scope

- Add a new wall-aware controller and planner without changing existing semantic or cruise node behavior.
- Reuse detector lifecycle helpers, semantic detection normalization, cruise trajectory sampling, pursuit scoring, and cone avoidance.
- Do not implement exit detection or interception in this phase.
- Do not modify the detector implementation; the controller targets the agreed detector contract.

## Wall Depth Compression

The raw mask may contain many wall pixels. Before planning:

1. Keep finite depth values within configured minimum and maximum ranges.
2. Subsample image rows and columns with a configurable stride.
3. Divide the image width into angular bins.
4. For each occupied bin, use a low depth percentile instead of a single minimum to reject isolated noise.
5. Convert the bin center and depth to camera-relative lateral and forward coordinates using `x = (u - cx) / fx * z`.

The result is normally 60-120 local wall points rather than tens of thousands of pixels.

## Planning

`SemanticWallPlanner` extends `SemanticCruisePlanner`. Wall points are added to the obstacle set under an internal wall label. Existing candidate simulation and target/cone scoring remain reusable.

Safety priority is:

1. Wall emergency stop.
2. Wall collision rejection and escape turn.
3. Cone collision avoidance.
4. Green-car pursuit.
5. Default cruise.

The effective collision radius is the configured robot radius plus a wall safety margin. A wall inside the emergency distance returns zero velocity. A wall inside the stop corridor but outside the emergency distance returns zero linear velocity and rotates toward the side with greater measured clearance. Otherwise, trajectories intersecting the inflated wall boundary are rejected.

## Failure Behavior

- Detector initialization, capture, prediction, malformed mask, or planning exceptions publish stop.
- An empty valid wall mask is treated as no currently observed wall, provided capture itself succeeded.
- The controller publishes stop on shutdown.
- Exit gaps are intentionally treated as open space in this phase.

## Files

- `my_robot_package/src/semantic_wall_controller.py`
- `my_robot_package/src/my_robot_package/semantic_wall_planner.py`
- `my_robot_package/config/semantic_wall_controller.yaml`
- `my_robot_package/launch/semantic_wall_controller.launch`
- `my_robot_package/test/test_semantic_wall_planner.py`

The launch file loads semantic base configuration, cruise overlay configuration, and wall overlay configuration in that order.
