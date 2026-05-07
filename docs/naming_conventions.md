# Jackal ROS2 项目命名规范

本规范用于约束协作者在本仓库中开发 Jackal 相关模块时的命名方式。目标是让运动控制、目标检测、目标追踪、避障、传感器处理和上层控制模块在 ROS2 图中清晰可读、接口稳定、便于迁移到小车主机验证。

## 总体原则

- 命名应表达模块职责，而不是表达个人习惯或临时实验目的。
- 同一概念在 package、节点、topic、参数、文件和测试中应使用一致词汇。
- 名称应优先使用小写英文、数字和下划线。
- 避免缩写；只有 ROS2、Jackal 或领域内通用缩写可以使用，例如 `cmd_vel`、`odom`、`imu`、`lidar`。
- 不使用拼音、中文、空格、连字符或大小写混合命名 ROS2 资源。
- 临时代码应以 `experimental_` 或 `debug_` 标记，并不得作为正式接口被其他模块依赖。

## 领域词汇

项目中优先使用以下英文词汇：

| 中文概念 | 推荐英文 |
| --- | --- |
| 基本运动 | `basic_motion` |
| 运动控制 | `motion_control` |
| 目标检测 | `object_detection` |
| 目标追踪 | `target_tracking` |
| 避障 | `obstacle_avoidance` |
| 传感器处理 | `sensor_processing` |
| 上层控制 | `upper_control` |
| 安全监控 | `safety_monitor` |
| 速度指令 | `velocity_command` |
| 运动指令 | `motion_command` |
| 检测结果 | `detection_result` |
| 追踪目标 | `tracked_target` |

## ROS2 Package 命名

package 使用小写 snake_case，并以 `jackal_` 作为项目前缀。

推荐格式：

```text
jackal_<domain>
jackal_<domain>_interfaces
```

示例：

```text
jackal_basic_motion
jackal_motion_interfaces
jackal_object_detection
jackal_target_tracking
jackal_obstacle_avoidance
jackal_sensor_processing
```

规则：

- 业务 package 使用 `jackal_<domain>`。
- 自定义 message、service、action package 使用 `jackal_<domain>_interfaces`。
- 不将多个职责合并到一个模糊 package，例如避免 `jackal_utils_all`、`jackal_main`。
- 通用工具只有在被两个以上模块复用时才独立成包，例如 `jackal_common`。

## Python 文件和模块命名

Python 文件使用 snake_case。

推荐格式：

```text
<role>_node.py
<domain>_mapper.py
<domain>_validator.py
<domain>_config.py
```

示例：

```text
basic_motion_node.py
motion_mapper.py
motion_command_validator.py
object_detection_node.py
target_tracker.py
obstacle_avoidance_node.py
```

规则：

- ROS2 可执行节点文件以 `_node.py` 结尾。
- 纯逻辑文件不加 `_node`，例如 `motion_mapper.py`。
- 配置解析文件使用 `_config.py`。
- 数据校验文件使用 `_validator.py`。
- 测试辅助工具使用 `test_helpers.py` 或 `<domain>_test_helpers.py`。

## Python 类、函数和变量命名

Python 命名遵循 PEP 8，并结合 ROS2 语义。

类名使用 PascalCase：

```python
BasicMotionNode
MotionCommandValidator
TargetTracker
ObstacleAvoidanceNode
```

函数和变量使用 snake_case：

```python
map_motion_command_to_twist
validate_motion_command
max_linear_speed
motion_command_topic
```

回调函数应体现输入来源：

```python
motion_command_callback
scan_callback
image_callback
timer_callback
odom_callback
```

规则：

- 节点类以 `Node` 结尾。
- 数据转换函数使用 `map_<input>_to_<output>`。
- 校验函数使用 `validate_<object>`。
- 创建消息的函数使用 `create_<message_name>`。
- 布尔变量使用 `is_`、`has_`、`should_`、`enable_` 开头。

## ROS2 Node 命名

ROS2 node 名称使用 snake_case，表达模块职责。

推荐格式：

```text
jackal_<domain>_node
```

示例：

```text
jackal_basic_motion_node
jackal_object_detection_node
jackal_target_tracking_node
jackal_obstacle_avoidance_node
jackal_safety_monitor_node
```

规则：

- node 名称应稳定，不随实现细节变化。
- 不在 node 名称中加入作者、日期、实验编号。
- 一个 node 只表达一个主要职责。

## ROS2 Topic 命名

topic 使用小写 snake_case，并按功能域分组。

推荐格式：

```text
/jackal/<domain>/<name>
```

示例：

```text
/jackal/motion/command
/jackal/motion/status
/jackal/detection/objects
/jackal/tracking/target
/jackal/avoidance/status
/jackal/safety/state
```

与 Jackal 底盘或 ROS 生态已有约定兼容的 topic 可以保留原名：

```text
/cmd_vel
/odom
/tf
/tf_static
```

规则：

- 新增项目内部 topic 优先使用 `/jackal/<domain>/<name>`。
- 连接已有 Jackal 底盘控制器时，可通过参数配置外部 topic，例如默认 `cmd_vel_topic:=/cmd_vel`。
- 不在 topic 中加入消息类型名称，例如避免 `/jackal/motion/twist_msg`。
- 状态输出使用 `status` 或 `state`，不要混用。
- 命令输入使用 `command`，不要混用 `cmd`，除非沿用 ROS 约定 `cmd_vel`。

## ROS2 Parameter 命名

参数使用 snake_case。安全、速度、topic 和超时参数必须语义明确。

示例：

```text
motion_command_topic
cmd_vel_topic
max_linear_speed
max_angular_speed
command_timeout_sec
publish_rate_hz
enable_timeout_stop
```

规则：

- 时间参数以 `_sec` 或 `_ms` 结尾。
- 频率参数以 `_hz` 结尾。
- 速度参数应区分 `linear` 和 `angular`。
- topic 参数以 `_topic` 结尾。
- frame 参数以 `_frame` 结尾。
- 布尔参数使用 `enable_`、`use_`、`allow_` 开头。

## ROS2 Interface 命名

自定义 message、service、action 使用 PascalCase 文件名，字段使用 snake_case。

message 示例：

```text
MotionCommand.msg
TrackedTarget.msg
DetectionResult.msg
ObstacleState.msg
SafetyState.msg
```

字段示例：

```text
string direction
float32 speed
float32 confidence
string target_id
```

规则：

- message 名称表达数据含义，而不是发布者名称。
- service 名称表达请求行为，例如 `SetMotionMode.srv`。
- action 名称表达长时任务，例如 `FollowTarget.action`。
- interface package 应以 `_interfaces` 结尾。

## Launch 和 Config 文件命名

launch 文件使用 snake_case，并以 `.launch.py` 结尾。

示例：

```text
basic_motion.launch.py
object_detection.launch.py
target_tracking.launch.py
obstacle_avoidance.launch.py
full_stack.launch.py
```

配置文件使用 snake_case，并以 `.yaml` 结尾。

示例：

```text
basic_motion.yaml
motion_limits.yaml
detection_model.yaml
tracking_params.yaml
obstacle_avoidance.yaml
```

规则：

- 单模块启动文件使用 `<domain>.launch.py`。
- 多模块组合启动文件使用 `<scenario>.launch.py`。
- 安全和速度限制配置应独立命名，避免埋在通用配置中。

## Test 命名

测试文件使用 `test_` 前缀。

示例：

```text
test_motion_mapper.py
test_motion_command_validator.py
test_basic_motion_node.py
test_target_tracker.py
```

测试函数命名应表达行为：

```python
def test_forward_command_maps_to_positive_linear_x():
    ...

def test_invalid_direction_returns_stop_command():
    ...

def test_speed_above_limit_is_clamped():
    ...
```

规则：

- 纯函数逻辑优先写单元测试。
- ROS2 节点行为测试以节点名为核心命名。
- 安全逻辑测试必须清晰表达异常输入和期望停止行为。

## 文档命名

文档文件使用小写 snake_case。

示例：

```text
ros2_foxy_jackal_install.md
naming_conventions.md
basic_motion_design.md
object_detection_design.md
```

规则：

- 设计文档以 `_design.md` 结尾。
- 安装和迁移文档应在文件名中体现目标环境。
- 项目级日志保留根目录 `PROJECT_LOG.md`。

## 禁止命名

禁止使用以下类型命名：

```text
test1.py
new_node.py
main.py
final.py
demo2.py
my_control.py
jackal_new
temp_topic
/data
/result
/control
```

原因：

- 无法表达职责。
- 不利于 ROS2 图调试。
- 容易和其他模块发生接口混淆。
- 后续迁移到小车主机时难以判断依赖关系。

## 基本运动模块命名基准

当前基本运动系统优先采用以下命名：

```text
package: jackal_motion_interfaces
message: MotionCommand.msg

package: jackal_basic_motion
node: jackal_basic_motion_node
command topic: /jackal/motion/command
velocity topic: /cmd_vel
```

若后续代码与本节命名不同，应同步更新 `PROJECT_LOG.md`、安装指南和本规范。
