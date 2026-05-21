# ROS1 Jackal Motion Compatibility Design

## Goal

Replace the earlier ROS2 motion prototype with a ROS1 catkin package that keeps the command names seen in the host history working against the newly built Jackal stack.

## Architecture

The package name will be `my_robot_package` because the old host commands repeatedly used `roslaunch my_robot_package ...`. Launch files will publish to `/cmd_vel` by default, matching the observed Jackal control path through `jackal_base` and `jackal_control`.

The implementation keeps ROS-specific code in executable scripts and keeps motion mapping in a pure Python module so it can be tested without a running ROS master. This preserves the known Jackal interface while making the behavior readable.

## Components

- `my_robot_package/src/my_robot_package/motion_mapper.py`: direction and speed mapping to linear/angular velocity values.
- `my_robot_package/src/move_to_goal.py`: command-driven motion node.
- `my_robot_package/src/turn_circle.py`: continuous turn helper compatible with `turn_circle.launch`.
- `my_robot_package/src/odom_test.py`: `/odometry/filtered` observer compatible with `odom_test.launch`.
- `my_robot_package/launch/*.launch`: legacy launch entry points.

## Defaults

- `cmd_vel_topic`: `/cmd_vel`
- `odom_topic`: `/odometry/filtered`
- `linear_speed`: `0.1`
- `angular_speed`: `0.2`
- `direction`: `forward`
- `duration`: `0.0`, meaning run until stopped.

## Compatibility

The following commands remain the main smoke tests:

```bash
roslaunch jackal_base base.launch
roslaunch my_robot_package move_to_goal.launch
roslaunch my_robot_package turn_circle.launch
roslaunch my_robot_package odom_test.launch
```

Manual historical commands still remain valid because this package publishes standard `geometry_msgs/Twist` messages to `/cmd_vel`.
