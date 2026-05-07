import importlib


def test_motion_mapper_imports_without_ros2_runtime():
    module = importlib.import_module("jackal_basic_motion.motion_mapper")

    assert hasattr(module, "map_motion_command_to_vector")


def test_basic_motion_node_module_exists():
    module = importlib.import_module("jackal_basic_motion.basic_motion_node")

    assert hasattr(module, "BasicMotionNode")
