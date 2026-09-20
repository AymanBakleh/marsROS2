"""
display.launch.py – Launch the Tetrix omni-wheel robot description in RViz.

Nodes started:
  • robot_state_publisher  – broadcasts the robot URDF and TF tree
  • joint_state_publisher_gui – GUI sliders to move the wheel joints
  • rviz2                   – opens the preconfigured display.rviz view

Usage:
  ros2 launch tetrix_description display.launch.py
  ros2 launch tetrix_description display.launch.py use_gui:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("tetrix_description")

    urdf_file = os.path.join(pkg_share, "urdf", "tetrix_robot.urdf.xacro")
    rviz_config = os.path.join(pkg_share, "rviz", "display.rviz")

    # Expand the xacro file to a robot_description string at launch time.
    robot_description = ParameterValue(
        Command(["xacro ", urdf_file]),
        value_type=str,
    )

    use_gui = LaunchConfiguration("use_gui")

    return LaunchDescription(
        [
            # ------------------------------------------------------------------
            # Launch arguments
            # ------------------------------------------------------------------
            DeclareLaunchArgument(
                "use_gui",
                default_value="true",
                description="Whether to use the joint_state_publisher_gui",
            ),

            # ------------------------------------------------------------------
            # robot_state_publisher
            # ------------------------------------------------------------------
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": False,
                    }
                ],
            ),

            # ------------------------------------------------------------------
            # joint_state_publisher_gui  (interactive sliders)
            # ------------------------------------------------------------------
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                output="screen",
                condition=IfCondition(use_gui),
            ),

            # ------------------------------------------------------------------
            # joint_state_publisher  (headless – publishes zeros)
            # ------------------------------------------------------------------
            Node(
                package="joint_state_publisher",
                executable="joint_state_publisher",
                name="joint_state_publisher",
                output="screen",
                condition=UnlessCondition(use_gui),
            ),

            # ------------------------------------------------------------------
            # RViz2
            # ------------------------------------------------------------------
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", rviz_config],
            ),
        ]
    )
