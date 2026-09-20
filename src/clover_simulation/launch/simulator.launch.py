import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    clover_description_share = get_package_share_directory("clover_description")
    clover_description_share_parent = os.path.dirname(clover_description_share)

    # Gazebo resolves model://clover_description/... against resource roots.
    # Add both package share root and package dir to maximize compatibility.
    resource_paths = ":".join([
        clover_description_share_parent,
        clover_description_share,
    ])

    default_world_file = PathJoinSubstitution([
        FindPackageShare("clover_simulation"),
        "worlds",
        "uav_in_forest.sdf",
    ])
    world_file = LaunchConfiguration("world")

    clover_xacro = PathJoinSubstitution([
        FindPackageShare("clover_description"),
        "urdf",
        "clover",
        "clover4_gz_visual.xacro",
    ])

    clover_spawn_description = Command([
        FindExecutable(name="xacro"),
        " ",
        clover_xacro,
    ])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            ])
        ),
        launch_arguments={"gz_args": ["-r ", world_file]}.items(),
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-world",
            "default",
            "-string",
            clover_spawn_description,
            "-name",
            "clover",
            "-allow_renaming",
            "false",
            "-x",
            LaunchConfiguration("spawn_x"),
            "-y",
            LaunchConfiguration("spawn_y"),
            "-z",
            LaunchConfiguration("spawn_z"),
            "-R",
            LaunchConfiguration("spawn_roll"),
            "-P",
            LaunchConfiguration("spawn_pitch"),
            "-Y",
            LaunchConfiguration("spawn_yaw"),
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument("world", default_value=default_world_file),
        DeclareLaunchArgument("spawn_x", default_value="0.0"),
        DeclareLaunchArgument("spawn_y", default_value="0.0"),
        DeclareLaunchArgument("spawn_z", default_value="0.3"),
        DeclareLaunchArgument("spawn_roll", default_value="0.0"),
        DeclareLaunchArgument("spawn_pitch", default_value="0.0"),
        DeclareLaunchArgument("spawn_yaw", default_value="0.0"),
        SetEnvironmentVariable(name="GZ_SIM_RESOURCE_PATH", value=resource_paths),
        SetEnvironmentVariable(name="IGN_GAZEBO_RESOURCE_PATH", value=resource_paths),
        gazebo,
        spawn_entity,
    ])
