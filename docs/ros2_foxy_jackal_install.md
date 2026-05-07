# ROS2 Foxy Jackal 安装与迁移指南

本指南用于把本仓库中的 ROS2 代码迁移到 Jackal 小车主机或 ROS2 Foxy 开发主机中进行构建和验证。当前内容覆盖基本运动系统的预期部署方式，后续模块开发时应持续维护。

## 适用范围

- ROS2 发行版：Foxy Fitzroy。
- 推荐系统：Ubuntu 20.04 Focal。
- 目标场景：在 ROS2 workspace 中构建自定义 message package 和 Python 节点 package。
- 当前模块：基本运动系统。

ROS2 Foxy 已进入 EOL 状态。迁移到小车主机前，应确认小车主机已有可用的 Foxy 环境，或由用户明确决定继续使用 Foxy。

参考资料：

- ROS2 Foxy 安装文档：https://docs.ros.org/en/foxy/Installation.html
- ROS2 Foxy 自定义接口教程：https://docs.ros.org/en/foxy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html
- ROS2 Foxy colcon 构建教程：https://docs.ros.org/en/foxy/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html

## 预期仓库结构

当前设计计划在本仓库中维护以下 ROS2 package：

```text
jackal_motion_interfaces/
  msg/
    MotionCommand.msg
  CMakeLists.txt
  package.xml

jackal_basic_motion/
  jackal_basic_motion/
    __init__.py
      basic_motion_node.py
      motion_mapper.py
  package.xml
  setup.py
  setup.cfg
  resource/
  test/
```

`MotionCommand.speed` 当前定义为归一化速度，取值范围为 `[0.0, 1.0]`。节点会根据参数 `max_linear_speed` 和 `max_angular_speed` 映射到实际 `Twist` 速度。

## 小车主机环境要求

在 Jackal 小车主机上确认：

```bash
source /opt/ros/foxy/setup.bash
ros2 --version
python3 --version
colcon --help
```

如果 `colcon` 不可用，需要先安装 ROS2 构建工具。安装方式应以小车主机系统状态和 ROS2 Foxy 官方文档为准。

## Workspace 准备

建议在小车主机上使用独立 workspace，例如：

```bash
mkdir -p ~/jackal_ros2_ws/src
cd ~/jackal_ros2_ws/src
```

将本仓库放入 `src/` 目录下。示例结构：

```text
~/jackal_ros2_ws/
  src/
    Jackal_development/
      agent.md
      PROJECT_LOG.md
      docs/
      jackal_motion_interfaces/
      jackal_basic_motion/
```

## 构建步骤

进入 workspace 根目录：

```bash
cd ~/jackal_ros2_ws
source /opt/ros/foxy/setup.bash
colcon build
source install/setup.bash
```

如果只需要构建基本运动相关包，预期命令为：

```bash
colcon build --packages-select jackal_motion_interfaces jackal_basic_motion
source install/setup.bash
```

如果主机同时安装了 Conda 或其他 Python 环境，应确认构建时使用的是 ROS2 Foxy 对应的系统 Python。可使用干净 PATH 构建：

```bash
PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/ros/foxy/bin bash --noprofile --norc -c 'source /opt/ros/foxy/setup.bash && colcon build --packages-select jackal_motion_interfaces jackal_basic_motion'
```

## 验证自定义 Message

构建并 source workspace 后，使用以下命令确认 message 已生成：

```bash
ros2 interface show jackal_motion_interfaces/msg/MotionCommand
```

预期能看到类似字段：

```text
string direction
float32 speed
```

如果无法显示该接口，优先检查：

- 是否已在 workspace 根目录运行 `colcon build`。
- 是否已执行 `source install/setup.bash`。
- `jackal_motion_interfaces` 是否位于 workspace 的 `src/` 下。
- `package.xml` 和 `CMakeLists.txt` 是否正确声明 `rosidl_default_generators`。

## 运行基本运动节点

构建完成并 source 后，预期可以运行：

```bash
ros2 run jackal_basic_motion basic_motion_node
```

节点默认参数：

```text
motion_command_topic: /jackal/motion/command
cmd_vel_topic: /cmd_vel
max_linear_speed: 0.5
max_angular_speed: 1.0
command_timeout_sec: 0.5
publish_rate_hz: 20.0
enable_timeout_stop: true
```

节点应订阅：

```text
/jackal/motion/command
```

节点应发布：

```text
/cmd_vel
```

实际 topic 名称应以后续代码参数配置为准。

## 发布测试指令

实车测试前应先在仿真或架空轮状态下低速验证。示例：

```bash
ros2 topic pub --once /jackal/motion/command jackal_motion_interfaces/msg/MotionCommand "{direction: stop, speed: 0.0}"
```

低速前进示例：

```bash
ros2 topic pub --once /jackal/motion/command jackal_motion_interfaces/msg/MotionCommand "{direction: forward, speed: 0.1}"
```

测试完成后立即发送停止：

```bash
ros2 topic pub --once /jackal/motion/command jackal_motion_interfaces/msg/MotionCommand "{direction: stop, speed: 0.0}"
```

## 实车测试前安全检查

- 确认急停可用。
- 确认小车周围有足够空旷空间。
- 确认 `speed` 使用低速值开始测试。
- 确认 `/cmd_vel` topic 指向预期 Jackal 底盘控制器。
- 确认节点启动后不会默认发布非零速度。
- 确认发送非法方向、非法速度或停止指令时，小车不会继续运动。
- 确认测试人员可以随时终止节点或发送停止指令。

## 常见问题

### 本地 pytest 出现 launch_testing 插件错误

如果本地 Python/ROS2 pytest 插件版本不兼容，可能在普通单元测试收集阶段出现 `launch_testing` 相关错误。可先禁用 pytest 插件自动加载来运行纯 Python 测试：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest jackal_basic_motion/test -v
```

这只用于本地纯 Python 测试隔离，不替代 ROS2 Foxy workspace 中的构建和运行验证。

### Python 节点无法 import 自定义 message

通常是 workspace 未 source 或 interface package 未成功构建。执行：

```bash
cd ~/jackal_ros2_ws
source install/setup.bash
ros2 interface show jackal_motion_interfaces/msg/MotionCommand
```

### 构建自定义 message 时提示 `No module named 'em'`

这通常表示 `colcon build` 使用了错误的 Python 解释器，例如 Conda Python，而不是 ROS2 Foxy 的系统 Python。先确认：

```bash
which python3
```

若输出指向 Conda 路径，使用上文的干净 PATH 构建方式，或退出 Conda 环境后重新构建。

### 找不到基本运动节点

检查 Python package 是否已构建并 source：

```bash
colcon build --packages-select jackal_basic_motion
source install/setup.bash
ros2 pkg executables jackal_basic_motion
```

### 小车没有运动

先不要提高速度。按顺序检查：

- 基本运动节点是否在运行。
- `/jackal/motion/command` 是否有消息。
- `/cmd_vel` 是否有输出。
- Jackal 底盘控制器实际监听的 topic 是否为 `/cmd_vel`。
- 急停或底盘安全机制是否处于停止状态。

## 后续维护要求

- 新增 package 时，补充构建和运行命令。
- 修改 message 字段时，补充重新构建和验证步骤。
- 修改 topic 或参数名时，更新运行和测试命令。
- 增加目标检测、追踪、避障模块后，补充对应依赖和启动顺序。
