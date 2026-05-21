# PROJECT_LOG

本文件记录 Jackal 开发项目中的设计信息、接口决策和待确认问题。后续每次新增模块、调整接口或改变部署方式时，应同步更新本文件。

## 2026-05-21 ROS1 Jackal 运动兼容包

### 背景

已在新环境中 build 好 `jackal` 和 `jackal_robot` 相关内容。后续开发确定基于 ROS1/catkin，不再继续使用 2026-05-07 的 ROS2 Foxy 原型包。

### 已确认设计

- 当前底层运动兼容包采用 ROS1/catkin。
- ROS package 名称采用历史命令中反复出现的 `my_robot_package`。
- 保留历史 launch 文件名：
  - `move_to_goal.launch`
  - `move_to_goal1.launch`
  - `move_to_goal2.launch`
  - `turn_circle.launch`
  - `odom_test.launch`
- 默认速度输出 topic 采用 `/cmd_vel`，兼容历史命令和 Jackal 底盘控制入口。
- 默认里程计 topic 采用 `/odometry/filtered`。
- 不再维护 `jackal_basic_motion` 和 `jackal_motion_interfaces` ROS2 包。

### 当前模块结构

```text
my_robot_package/
  CMakeLists.txt
  package.xml
  setup.py
  launch/
    move_to_goal.launch
    move_to_goal1.launch
    move_to_goal2.launch
    turn_circle.launch
    odom_test.launch
  src/
    move_to_goal.py
    turn_circle.py
    odom_test.py
    my_robot_package/
      motion_mapper.py
  test/
```

### 当前推荐 ROS1 数据流

```text
my_robot_package node
  -> /cmd_vel
  -> jackal_base / jackal_control
  -> Jackal base controller
```

### 当前推荐运动映射

- `forward`: `linear.x = +speed * linear_speed`
- `backward`: `linear.x = -speed * linear_speed`
- `left`: `angular.z = +speed * angular_speed`
- `right`: `angular.z = -speed * angular_speed`
- `stop`: `linear.x = 0.0`, `angular.z = 0.0`

### 本地验证记录

- 已通过纯 Python 运动映射测试。
- 已通过 launch 文件兼容性测试。
- 已通过 Python 语法检查。
- 尚未在 Jackal 实车主机上完成 `catkin_make` 或 `catkin build` 后的实车运行验证。

## 2026-05-07 基本运动系统设计记录（已废弃）

以下记录保留为历史背景。对应 ROS2 包已删除，不再作为当前开发路线。

### 背景

本阶段开始开发 Jackal 小车的基本运动系统。基本运动系统负责生成底层运动机制，包括前进、后退、左转、右转和停止，并为未来上层网络控制模块提供明确接口。

### 已确认设计

- 基本运动系统采用 ROS2 Foxy。
- 底层运动系统需要能被未来上层网络控制，但上层网络的具体形式暂未确定。
- 上层到基本运动系统的控制指令由参数组构成：
  - `direction`
  - `speed`
- `direction` 支持以下取值：
  - `forward`
  - `backward`
  - `left`
  - `right`
  - `stop`
- `speed` 采用连续数值形式。
- 第一版实现中，`speed` 定义为归一化范围 `[0.0, 1.0]`。
- 控制接口采用 ROS2 自定义 message 方案，而不是 JSON 字符串或拆分 topic。
- 为支持自定义 message，需要新增 ROS2 interface package。
- 第一版 package 名称采用 `jackal_motion_interfaces` 和 `jackal_basic_motion`。
- 第一版项目内部运动命令 topic 采用 `/jackal/motion/command`。
- 第一版默认底盘速度输出 topic 采用 `/cmd_vel`，并通过参数 `cmd_vel_topic` 支持调整。
- 由于自定义 message 需要 ROS2 构建生成 Python 类型，项目必须同步维护安装和迁移指南，保证代码可迁移到 Jackal 小车主机的 ROS2 Foxy workspace 中运行。

### 当前推荐模块结构

```text
jackal_motion_interfaces/
  msg/
    MotionCommand.msg

jackal_basic_motion/
  jackal_basic_motion/
    basic_motion_node.py
    motion_mapper.py
```

### 当前推荐消息接口

```text
string direction
float32 speed
```

### 当前推荐 ROS2 数据流

```text
upper controller or network
  -> /jackal/motion/command
  -> jackal_basic_motion node
  -> /cmd_vel
  -> Jackal base controller
```

### 当前推荐运动映射

- `forward`: `linear.x = +speed * max_linear_speed`
- `backward`: `linear.x = -speed * max_linear_speed`
- `left`: `angular.z = +speed * max_angular_speed`
- `right`: `angular.z = -speed * max_angular_speed`
- `stop`: `linear.x = 0.0`, `angular.z = 0.0`

### 安全策略

- 节点启动后默认不发布非零速度。
- 非法方向应触发停止或拒绝执行。
- 非法速度、非有限速度或超出允许范围的速度必须被处理，不能直接透传到底盘。
- 控制指令超时后应自动停止。
- 最大线速度、最大角速度和超时时间必须通过参数配置，不应硬编码在逻辑深处。

### 待确认问题

- 是否需要在 `MotionCommand.msg` 中加入时间戳、来源标识或命令序号。
- 是否需要单独提供一个测试发布器节点用于实车前低速验证。

### 已实现文件

```text
jackal_motion_interfaces/
  msg/MotionCommand.msg
  CMakeLists.txt
  package.xml

jackal_basic_motion/
  jackal_basic_motion/basic_motion_node.py
  jackal_basic_motion/motion_mapper.py
  package.xml
  setup.py
  setup.cfg
  resource/jackal_basic_motion
  test/
```

### 本地验证记录

- 已通过纯 Python 运动映射测试。
- 已通过节点模块导入测试。
- 已通过 Python 语法检查。
- 已在本机 ROS2 Foxy 环境完成 `colcon build --packages-select jackal_motion_interfaces jackal_basic_motion`。
- 已通过 `ros2 interface show jackal_motion_interfaces/msg/MotionCommand` 验证自定义 message 生成结果。
- 已通过 `ros2 pkg executables jackal_basic_motion` 验证 `basic_motion_node` 可执行入口注册。
- 尚未在 Jackal 实车主机上完成运行和运动验证。

## 文档维护规则

- 接口字段变更时，必须更新本文件和安装指南。
- ROS2 package 名称、topic 名称、参数名称变更时，必须更新本文件和安装指南。
- 小车主机迁移步骤变更时，必须更新安装指南。
- 未经实车验证的行为必须明确标注为未实车验证。

## 2026-05-07 协作者命名规范

### 已新增文档

- `docs/naming_conventions.md`

### 目的

为协作者开发 Jackal 运动控制、目标检测、目标追踪、避障、传感器处理、上层控制等模块提供统一命名规则，减少 package、节点、topic、参数和测试文件命名不一致带来的集成成本。

### 适用范围

- ROS2 package。
- Python 模块、类、函数、变量。
- ROS2 node、topic、service、action、parameter。
- 自定义 message、service、action interface。
- launch、config、test 和文档文件。
