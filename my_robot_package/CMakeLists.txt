cmake_minimum_required(VERSION 3.0.2)
project(my_robot_package)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  nav_msgs
  rospy
)

catkin_python_setup()

catkin_package(
  CATKIN_DEPENDS geometry_msgs nav_msgs rospy
)

catkin_install_python(PROGRAMS
  src/keyboard_control.py
  src/move_to_goal.py
  src/motion_gui.py
  src/turn_circle.py
  src/odom_test.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
