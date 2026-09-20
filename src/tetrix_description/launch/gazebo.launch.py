"""
gazebo.launch.py – Spawn the Tetrix robot in Gazebo Harmonic (ros_gz_sim).

Nodes / processes started:
    • gz_sim / ign gazebo   – Gazebo simulator server + GUI
    • robot_state_publisher – broadcasts URDF and TF
    • create / spawn_entity – spawns the robot from /robot_description
    • parameter_bridge      – bridges clock, scan, odom, and cmd_vel

Usage:
    ros2 launch tetrix_description gazebo.launch.py
    ros2 launch tetrix_description gazebo.launch.py world:=<path/to/world.sdf>
"""

import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("tetrix_description")

    backend = None
    sim_share = None
    try:
        sim_share = get_package_share_directory("ros_gz_sim")
        backend = "ros_gz_sim"
    except PackageNotFoundError:
        try:
            sim_share = get_package_share_directory("ros_ign_gazebo")
            backend = "ros_ign_gazebo"
        except PackageNotFoundError:
            try:
                sim_share = get_package_share_directory("gazebo_ros")
                backend = "gazebo_ros"
            except PackageNotFoundError as exc:
                raise RuntimeError(
                    "No ROS Gazebo integration package found. Install one of: "
                    "ros-humble-ros-gz-sim + ros-humble-ros-gz-bridge (Harmonic), "
                    "or ros-humble-ros-ign-gazebo + ros-humble-ros-ign-bridge, "
                    "or ros-humble-gazebo-ros-pkgs (Classic)."
                ) from exc

    urdf_file = os.path.join(pkg_share, "urdf", "tetrix_robot.urdf.xacro")
    world_file = os.path.join(pkg_share, "worlds", "forest_arena.sdf")

    if backend == "gazebo_ros":
        sim_backend_arg = "classic"
    elif backend == "ros_gz_sim":
        sim_backend_arg = "gz"
    else:
        sim_backend_arg = "ign"
    robot_description = ParameterValue(
        Command(["xacro ", urdf_file, " sim_backend:=", sim_backend_arg]),
        value_type=str,
    )

    world = LaunchConfiguration("world")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    yaw = LaunchConfiguration("yaw")

    actions = [
            # ------------------------------------------------------------------
            # Launch arguments
            # ------------------------------------------------------------------
            DeclareLaunchArgument(
                "world",
                default_value=world_file,
                description="Path to the Gazebo world file",
            ),
            DeclareLaunchArgument(
                "x", default_value="0.0", description="Initial X position"
            ),
            DeclareLaunchArgument(
                "y", default_value="0.0", description="Initial Y position"
            ),
            DeclareLaunchArgument(
                "z", default_value="0.05", description="Initial Z position"
            ),
            DeclareLaunchArgument(
                "yaw", default_value="0.0", description="Initial yaw orientation"
            ),
    ]

    if backend == "ros_gz_sim":
        actions.extend(
            [
                LogInfo(msg="Using Gazebo Harmonic backend: ros_gz_sim"),
                # Gazebo Harmonic (server + GUI client)
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(sim_share, "launch", "gz_sim.launch.py")
                    ),
                    launch_arguments={"gz_args": ["-r ", world]}.items(),
                ),
            ]
        )
    elif backend == "ros_ign_gazebo":
        actions.extend(
            [
                LogInfo(msg="Using Gazebo Fortress/Garden backend: ros_ign_gazebo"),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(sim_share, "launch", "ign_gazebo.launch.py")
                    ),
                    launch_arguments={"ign_args": ["-r ", world]}.items(),
                ),
            ]
        )
    else:
        actions.extend(
            [
                LogInfo(msg="Using Gazebo Classic backend: gazebo_ros"),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(sim_share, "launch", "gazebo.launch.py")
                    ),
                    launch_arguments={"world": world}.items(),
                ),
            ]
        )

    actions.extend(
        [
            # ------------------------------------------------------------------
            # robot_state_publisher – makes robot_description available on /topic
            # ------------------------------------------------------------------
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )

    if backend == "ros_gz_sim":
        actions.extend(
            [
                # Spawn entity in Gazebo Harmonic from /robot_description
                Node(
                    package="ros_gz_sim",
                    executable="create",
                    name="spawn_tetrix_robot",
                    output="screen",
                    arguments=[
                        "-topic", "robot_description",
                        "-name", "tetrix_robot",
                        "-x", x,
                        "-y", y,
                        "-z", z,
                        "-Y", yaw,
                    ],
                ),
                # Bridge Gazebo simulation clock to ROS 2 /clock
                Node(
                    package="ros_gz_bridge",
                    executable="parameter_bridge",
                    name="gz_bridge",
                    output="screen",
                    arguments=[
                        "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
                        "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
                        "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
                        "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                    ],
                ),
            ]
        )
    elif backend == "ros_ign_gazebo":
        actions.extend(
            [
                Node(
                    package="ros_ign_gazebo",
                    executable="create",
                    name="spawn_tetrix_robot",
                    output="screen",
                    arguments=[
                        "-topic", "robot_description",
                        "-name", "tetrix_robot",
                        "-x", x,
                        "-y", y,
                        "-z", z,
                        "-Y", yaw,
                    ],
                ),
                Node(
                    package="ros_ign_bridge",
                    executable="parameter_bridge",
                    name="ign_bridge",
                    output="screen",
                    arguments=[
                        "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
                        "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
                        "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
                        "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
                    ],
                ),
            ]
        )
    else:
        actions.append(
            # Spawn entity in Gazebo Classic from /robot_description
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                name="spawn_tetrix_robot",
                output="screen",
                arguments=[
                    "-topic", "robot_description",
                    "-entity", "tetrix_robot",
                    "-x", x,
                    "-y", y,
                    "-z", z,
                    "-Y", yaw,
                ],
            )
        )

    return LaunchDescription(actions)
