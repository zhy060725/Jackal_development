# ROS1 Jackal Motion File Guide

本文说明当前 ROS1 运动兼容包中每个文件的作用、常用操作方法和修改入口。部署和实车运行步骤见 `docs/ros1_jackal_motion_install.md`。

## 总体结构

```text
my_robot_package/
  CMakeLists.txt
  package.xml
  setup.py
  launch/
    move_to_goal.launch
    move_to_goal1.launch
    move_to_goal2.launch
    motion_gui.launch
    keyboard_control.launch
    turn_circle.launch
    odom_test.launch
  src/
    move_to_goal.py
    motion_gui.py
    keyboard_control.py
    turn_circle.py
    odom_test.py
    my_robot_package/
      __init__.py
      keyboard_control_state.py
      motion_mapper.py
  test/
    test_launch_compatibility.py
    test_motion_mapper.py
```

这个包的目标是保留历史主机上已经使用过的命令入口，同时把底层运动逻辑写成更容易理解和维护的代码。

## Catkin 元数据文件

### `my_robot_package/package.xml`

ROS1 package 描述文件。它声明包名、版本、维护者、许可证和依赖。

当前关键依赖：

- `rospy`: Python ROS1 节点。
- `geometry_msgs`: 发布 `geometry_msgs/Twist` 到 `/cmd_vel`。
- `nav_msgs`: 订阅 `nav_msgs/Odometry`，用于 `odom_test.py`。

新增 ROS message、service 或额外 ROS 包依赖时，先在这里补依赖。

### `my_robot_package/CMakeLists.txt`

catkin 构建入口。它做三件事：

- 查找 `rospy`、`geometry_msgs`、`nav_msgs`。
- 调用 `catkin_python_setup()`，让 `src/my_robot_package/` 下的 Python 模块可以被脚本 import。
- 安装可执行脚本和 launch 文件。

新增可执行脚本时，需要把脚本加入：

```cmake
catkin_install_python(PROGRAMS
  src/move_to_goal.py
  src/motion_gui.py
  src/turn_circle.py
  src/odom_test.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
```

### `my_robot_package/setup.py`

Python 包安装配置。它让 `my_robot_package.motion_mapper` 能在 ROS 节点脚本里被 import。

一般不需要改。只有新增 Python 子包或调整 `src/` 下的包路径时才需要改。

## Launch 文件

所有 launch 文件都位于 `my_robot_package/launch/`。这些文件是用户最常直接运行的入口。

### `move_to_goal.launch`

启动 `src/move_to_goal.py`。这是当前推荐的基础运动入口。

默认行为：

```text
direction: forward
speed: 1.0
linear_speed: 0.1
angular_speed: 0.2
cmd_vel_topic: /cmd_vel
duration: 0.0
publish_rate: 20.0
```

常用命令：

```bash
roslaunch my_robot_package move_to_goal.launch
roslaunch my_robot_package move_to_goal.launch direction:=forward speed:=0.3 duration:=2.0
roslaunch my_robot_package move_to_goal.launch direction:=left speed:=0.5 duration:=1.0
roslaunch my_robot_package move_to_goal.launch direction:=stop speed:=0.0 duration:=1.0
```

`duration:=0.0` 表示持续发布，直到节点被停止。实车第一次测试建议设置短时间，例如 `duration:=2.0`。

### `move_to_goal1.launch` 和 `move_to_goal2.launch`

兼容历史命令：

```bash
roslaunch my_robot_package move_to_goal1.launch
roslaunch my_robot_package move_to_goal2.launch
```

这两个文件直接启动同一个 `move_to_goal.py` 脚本，只是节点名分别是 `move_to_goal1` 和 `move_to_goal2`。保留它们是为了让历史命令继续可用。

如果后续确认不再需要历史入口，可以删除这两个 launch 文件，并同步删除 `test_launch_compatibility.py` 中对应断言。

### `turn_circle.launch`

启动 `src/turn_circle.py`，用于持续原地转向。

默认行为：

```text
linear_speed: 0.0
angular_speed: -0.2
cmd_vel_topic: /cmd_vel
duration: 0.0
publish_rate: 20.0
```

常用命令：

```bash
roslaunch my_robot_package turn_circle.launch duration:=2.0
roslaunch my_robot_package turn_circle.launch angular_speed:=0.2 duration:=2.0
```

`angular_speed` 为正时按 ROS 坐标约定左转，为负时右转。

### `odom_test.launch`

启动 `src/odom_test.py`，用于观察 Jackal 的滤波里程计。

默认订阅：

```text
/odometry/filtered
```

常用命令：

```bash
roslaunch my_robot_package odom_test.launch
roslaunch my_robot_package odom_test.launch odom_topic:=/jackal_velocity_controller/odom
```

如果新环境中的里程计 topic 不同，用 `odom_topic:=...` 覆盖。

### `motion_gui.launch`

启动 `src/motion_gui.py`，提供桌面 GUI 控制方向和速度。

默认行为：

```text
cmd_vel_topic: /cmd_vel
linear_speed: 0.1
angular_speed: 0.2
publish_rate: 20.0
```

常用命令：

```bash
roslaunch my_robot_package motion_gui.launch
roslaunch my_robot_package motion_gui.launch linear_speed:=0.2 angular_speed:=0.4
```

GUI 需要图形桌面环境和 Tkinter。如果主机缺少 Tkinter，需要安装 `python3-tk`。

### `keyboard_control.launch`

启动 `src/keyboard_control.py`。这个 launch 文件用于参数配置和包入口完整性，但终端键盘输入更推荐用 `rosrun my_robot_package keyboard_control.py`，因为 `roslaunch` 在部分环境下不会把当前终端 stdin 传给节点。

默认行为：

```text
cmd_vel_topic: /cmd_vel
linear_speed: 0.1
angular_speed: 0.2
initial_speed: 0.3
speed_step: 0.1
publish_rate: 20.0
```

## Python 节点脚本

### `src/move_to_goal.py`

基础运动发布节点。它读取 launch 参数，将 `direction` 和 `speed` 交给 `motion_mapper.py`，再发布 `geometry_msgs/Twist`。

数据流：

```text
launch args
  -> move_to_goal.py
  -> motion_mapper.map_motion_command()
  -> geometry_msgs/Twist
  -> /cmd_vel
```

可改入口：

- 默认 topic：优先改 launch 文件中的 `cmd_vel_topic` 默认值。
- 默认线速度和角速度：优先改 launch 文件中的 `linear_speed`、`angular_speed` 默认值。
- 发布循环和退出停止逻辑：改 `move_to_goal.py`。

安全行为：

- 非法方向会发布零速度。
- 非法速度会发布零速度。
- 节点退出时默认发布一次停止命令。

### `src/turn_circle.py`

原地转向发布节点。它不使用 `direction`，直接读取 `linear_speed` 和 `angular_speed`，持续发布 `Twist`。

适用场景：

- 快速验证 `/cmd_vel` 到底盘的链路。
- 复现历史中的转圈测试。

可改入口：

- 默认转向速度：改 `turn_circle.launch` 的 `angular_speed`。
- 是否带线速度绕圈：设置 `linear_speed` 为非零。

### `src/odom_test.py`

里程计观察节点。它订阅 `nav_msgs/Odometry`，每秒节流打印位置、姿态 z 分量、线速度和角速度。

适用场景：

- 确认 Jackal 底盘启动后有里程计输出。
- 检查运动命令发布后 `/odometry/filtered` 是否变化。

如果需要完整姿态角，后续可以在这里加入 quaternion 到 yaw 的转换。

### `src/motion_gui.py`

桌面运动控制 GUI。它使用 Tkinter 创建方向按钮、速度滑条、停止按钮，并按固定频率发布 `geometry_msgs/Twist` 到 `/cmd_vel`。

数据流：

```text
GUI button/slider
  -> motion_gui.py
  -> motion_mapper.map_motion_command()
  -> geometry_msgs/Twist
  -> /cmd_vel
```

界面行为：

- `Forward`、`Backward`、`Left`、`Right` 设置当前方向。
- `Stop` 设置方向为 `stop`，速度为 `0.0`，并立即发布零速度。
- 速度滑条范围是 `0.0` 到 `1.0`。
- 点击方向按钮且速度为 `0.0` 时，默认把速度提到 `0.3`，避免按钮看似无效。
- 关闭窗口时发布一次停止命令。

可改入口：

- 发布 topic：改 `motion_gui.launch` 的 `cmd_vel_topic`。
- 最大线速度和角速度：改 `linear_speed`、`angular_speed`。
- GUI 布局和按钮行为：改 `motion_gui.py`。

### `src/keyboard_control.py`

终端键盘控制节点。它读取当前终端的按键输入，把方向和速度状态转换为 `Twist` 并持续发布到 `/cmd_vel`。

推荐运行：

```bash
rosrun my_robot_package keyboard_control.py
```

按键：

```text
Up arrow: forward
Down arrow: backward
Left arrow: left
Right arrow: right
+ or =: increase normalized speed by speed_step
- or _: decrease normalized speed by speed_step
Space: stop and zero speed
q or Esc: quit
```

说明：

- 按方向键时，如果当前速度为 `0.0`，节点会自动使用 `initial_speed`。
- 按一次 `+` 或 `-` 会按 `speed_step` 改变归一化速度。
- 速度会被限制在 `[0.0, 1.0]`。
- 退出节点时会发布一次停止命令。

## Python 逻辑模块

### `src/my_robot_package/motion_mapper.py`

纯 Python 运动映射模块，不依赖 ROS。它负责把上层命令转成线速度和角速度数值。

当前支持方向：

```text
forward
backward
left
right
stop
```

映射规则：

```text
forward  -> linear_x = +speed * max_linear_speed
backward -> linear_x = -speed * max_linear_speed
left     -> angular_z = +speed * max_angular_speed
right    -> angular_z = -speed * max_angular_speed
stop     -> linear_x = 0.0, angular_z = 0.0
```

`speed` 是归一化值，范围会被夹到 `[0.0, 1.0]`。非有限值、非数字值和非法方向会返回零速度，并标记 `is_valid=False`。

新增方向时，需要同时修改：

- `VALID_DIRECTIONS`
- `map_motion_command()`
- `test/test_motion_mapper.py`

### `src/my_robot_package/keyboard_control_state.py`

纯 Python 键盘状态模块，不依赖 ROS。它负责把按键映射成当前方向和归一化速度。

当前映射：

```text
Arrow keys -> direction
Space -> stop
+ / = -> speed + speed_step
- / _ -> speed - speed_step
```

新增键位或改变键位行为时，先改这里和 `test/test_keyboard_control.py`，再改 `keyboard_control.py`。

### `src/my_robot_package/__init__.py`

Python 包标记文件。当前没有运行逻辑，一般不需要修改。

## 测试文件

### `test/test_motion_mapper.py`

验证运动映射逻辑。它不需要 ROS master，可以在开发机直接运行。

运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test/test_motion_mapper.py -v
```

覆盖内容：

- 前进、后退、左转、右转。
- 停止。
- 非法方向。
- 非法速度。
- 速度上下限夹取。

### `test/test_launch_compatibility.py`

验证历史 launch 文件存在，并且指向预期脚本。

运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test/test_launch_compatibility.py -v
```

如果删除或重命名历史 launch 文件，需要同步修改这个测试。

## 常用操作

### 本地非 ROS 测试

在仓库根目录运行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest my_robot_package/test -v
python3 -m py_compile my_robot_package/src/my_robot_package/motion_mapper.py my_robot_package/src/my_robot_package/keyboard_control_state.py my_robot_package/src/move_to_goal.py my_robot_package/src/motion_gui.py my_robot_package/src/keyboard_control.py my_robot_package/src/turn_circle.py my_robot_package/src/odom_test.py
```

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 用于避开本机 ROS2 pytest 插件和当前 ROS1 包测试之间的插件冲突。

### Catkin 构建

在 catkin workspace 根目录运行：

```bash
cd ~/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

或：

```bash
cd ~/catkin_ws
source /opt/ros/melodic/setup.bash
catkin build
source devel/setup.bash
```

### 实车低速验证

先启动底盘：

```bash
roslaunch jackal_base base.launch
```

再开另一个终端：

```bash
source ~/catkin_ws/devel/setup.bash
roslaunch my_robot_package move_to_goal.launch direction:=forward speed:=0.3 duration:=2.0
roslaunch my_robot_package move_to_goal.launch direction:=stop speed:=0.0 duration:=1.0
```

GUI 控制：

```bash
roslaunch my_robot_package motion_gui.launch
```

键盘控制：

```bash
rosrun my_robot_package keyboard_control.py
```

同时可观察：

```bash
rostopic echo /cmd_vel
rostopic echo /odometry/filtered
```

## 修改建议

- 要改默认速度，优先改 launch 文件，不要先改 Python 逻辑。
- 要新增运动语义，先改 `motion_mapper.py` 和对应测试，再接入 launch 或节点。
- 要换底盘速度入口，优先用 `cmd_vel_topic:=...` 参数验证，再修改默认值。
- 要换里程计入口，优先用 `odom_topic:=...` 参数验证。
- 实车测试前始终先设置低速和短 `duration`。
