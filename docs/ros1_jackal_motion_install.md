# ROS1 Jackal Motion Package Guide

本指南用于把当前仓库中的 ROS1 运动兼容包部署到已经 build 好 `jackal` 和 `jackal_robot` 的 catkin workspace 中。

## 适用范围

- ROS 发行版：ROS1，当前主机历史记录主要对应 Melodic。
- 底盘栈：`jackal` 和 `jackal_robot` 已完成构建。
- 当前包：`my_robot_package`。

## Workspace 布局

建议将本仓库放在 catkin workspace 的 `src/` 下，或至少将 `my_robot_package/` 放入 `src/`：

```text
~/catkin_ws/
  src/
    my_robot_package/
    jackal/
    jackal_robot/
```

## 构建

```bash
cd ~/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

如果使用 `catkin_tools`：

```bash
cd ~/catkin_ws
source /opt/ros/melodic/setup.bash
catkin build
source devel/setup.bash
```

## 启动 Jackal 底盘

历史命令中最常用的底盘入口是：

```bash
roslaunch jackal_base base.launch
```

如果需要远程主机连接实车 ROS master，先设置：

```bash
export ROS_MASTER_URI=http://cpr-jackal-0001:11311
export ROS_IP=<your-host-ip>
```

## 运行兼容运动节点

默认前进，发布到 `/cmd_vel`：

```bash
roslaunch my_robot_package move_to_goal.launch
```

指定方向和速度：

```bash
roslaunch my_robot_package move_to_goal.launch direction:=left speed:=0.5
```

按历史命令兼容：

```bash
roslaunch my_robot_package move_to_goal1.launch
roslaunch my_robot_package move_to_goal2.launch
roslaunch my_robot_package turn_circle.launch
roslaunch my_robot_package odom_test.launch
```

启动 GUI 运动控制：

```bash
roslaunch my_robot_package motion_gui.launch
```

GUI 需要图形桌面环境和 Tkinter。如果主机缺少 Tkinter，需要安装系统包，例如 Ubuntu 上的 `python3-tk`。

启动终端键盘控制：

```bash
rosrun my_robot_package keyboard_control.py
```

键盘控制使用当前终端读取按键，推荐用 `rosrun` 启动。`keyboard_control.launch` 也提供同名参数，但 `roslaunch` 在部分环境下不会把终端输入传给节点。

## 参数

`move_to_goal.launch` 支持：

```text
cmd_vel_topic: /cmd_vel
direction: forward|backward|left|right|stop
speed: normalized [0.0, 1.0]
linear_speed: 0.1
angular_speed: 0.2
duration: 0.0
publish_rate: 20.0
```

`turn_circle.launch` 支持：

```text
cmd_vel_topic: /cmd_vel
linear_speed: 0.0
angular_speed: -0.2
duration: 0.0
publish_rate: 20.0
```

`odom_test.launch` 支持：

```text
odom_topic: /odometry/filtered
```

`motion_gui.launch` 支持：

```text
cmd_vel_topic: /cmd_vel
linear_speed: 0.1
angular_speed: 0.2
publish_rate: 20.0
```

`keyboard_control.py` 支持 ROS private parameters：

```text
cmd_vel_topic: /cmd_vel
linear_speed: 0.1
angular_speed: 0.2
initial_speed: 0.3
speed_step: 0.1
publish_rate: 20.0
```

键位：

```text
Up: forward
Down: backward
Left: left
Right: right
+ or =: increase speed
- or _: decrease speed
Space: stop
q or Esc: quit
```

## 低速验证

启动底盘后，先验证 topic：

```bash
rostopic list
rostopic echo /cmd_vel
rostopic echo /odometry/filtered
```

再低速测试：

```bash
roslaunch my_robot_package move_to_goal.launch direction:=forward speed:=0.3 duration:=2.0
roslaunch my_robot_package move_to_goal.launch direction:=stop speed:=0.0 duration:=1.0
```

测试时确认急停可用，并从低速、短时间开始。
