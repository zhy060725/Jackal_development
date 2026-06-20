import pathlib
import xml.etree.ElementTree as ET


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _node_types(launch_name):
    tree = ET.parse(str(PACKAGE_ROOT / "launch" / launch_name))
    return [
        node.attrib.get("type")
        for node in tree.getroot().iter("node")
        if node.attrib.get("pkg") == "my_robot_package"
    ]


def test_legacy_launch_files_exist():
    expected_files = [
        "move_to_goal.launch",
        "move_to_goal1.launch",
        "move_to_goal2.launch",
        "motion_gui.launch",
        "keyboard_control.launch",
        "semantic_motion_controller.launch",
        "semantic_cruise_controller.launch",
        "semantic_wall_controller.launch",
        "turn_circle.launch",
        "odom_test.launch",
    ]

    for launch_name in expected_files:
        assert (PACKAGE_ROOT / "launch" / launch_name).exists()


def test_move_to_goal_launches_use_move_to_goal_script():
    for launch_name in ["move_to_goal.launch", "move_to_goal1.launch", "move_to_goal2.launch"]:
        assert "move_to_goal.py" in _node_types(launch_name)


def test_turn_and_odom_launch_files_use_expected_scripts():
    assert "turn_circle.py" in _node_types("turn_circle.launch")
    assert "odom_test.py" in _node_types("odom_test.launch")


def test_motion_gui_launch_file_uses_expected_script():
    assert "motion_gui.py" in _node_types("motion_gui.launch")


def test_keyboard_control_launch_file_uses_expected_script():
    assert "keyboard_control.py" in _node_types("keyboard_control.launch")


def test_semantic_controller_launch_file_uses_expected_script():
    assert "semantic_motion_controller.py" in _node_types("semantic_motion_controller.launch")


def test_semantic_cruise_launch_file_uses_expected_script():
    assert "semantic_cruise_controller.py" in _node_types(
        "semantic_cruise_controller.launch"
    )


def test_semantic_wall_launch_file_uses_expected_script():
    assert "semantic_wall_controller.py" in _node_types(
        "semantic_wall_controller.launch"
    )
