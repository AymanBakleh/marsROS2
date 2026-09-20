"""
mission.launch.py - Launch forest arena simulation and autonomous mission behavior.

Starts:
- Gazebo simulation launch (forest arena world)
- Patrol manager node for autonomous patrol and fire-response diversion
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("tetrix_description")

    gazebo_launch = os.path.join(pkg_share, "launch", "gazebo.launch.py")
    forest_world = os.path.join(pkg_share, "worlds", "forest_arena.sdf")
    patrol_params = os.path.join(pkg_share, "config", "patrol_waypoints.yaml")

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(gazebo_launch),
                launch_arguments={"world": forest_world}.items(),
            ),
            Node(
                package="tetrix_description",
                executable="patrol_manager.py",
                name="patrol_manager",
                output="screen",
                parameters=[patrol_params],
            ),
        ]
    )
