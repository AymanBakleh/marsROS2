from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gui_enabled = LaunchConfiguration("gui")

    forest_world = PathJoinSubstitution([
        FindPackageShare("clover_simulation"),
        "worlds",
        "uav_in_forest.sdf",
    ])

    simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("clover_simulation"),
                "launch",
                "simulator.launch.py",
            ])
        ),
        launch_arguments={
            "world": forest_world,
            "spawn_x": "-5.0",
            "spawn_y": "3.4",
            "spawn_z": "1.0",
        }.items(),
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/world/default/set_pose@ros_gz_interfaces/srv/SetEntityPose",
        ],
    )

    tetrix_xacro = PathJoinSubstitution([
        FindPackageShare("tetrix_description"),
        "urdf",
        "tetrix_robot.urdf.xacro",
    ])

    tetrix_description = ParameterValue(
        Command([
        "xacro ",
        tetrix_xacro,
        " sim_backend:=gz",
        ]),
        value_type=str,
    )

    tetrix_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"robot_description": tetrix_description},
        ],
    )

    tetrix_spawner = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-world",
            "default",
            "-topic",
            "robot_description",
            "-name",
            "tetrix_robot",
            "-allow_renaming",
            "false",
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.05",
            "-Y",
            "0.0",
        ],
    )

    goal_commander = Node(
        package="clover_mission",
        executable="goal_commander",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"world_name": "default"},
            {"entity_name": "clover"},
        ],
    )

    tetrix_goal_commander = Node(
        package="clover_mission",
        executable="tetrix_goal_commander",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    mission_gui = Node(
        package="clover_mission",
        executable="mission_gui",
        output="screen",
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(gui_enabled),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Start simple coordinate GUI for Clover and Tetrix goals.",
        ),
        simulator,
        bridge,
        tetrix_state_publisher,
        tetrix_spawner,
        goal_commander,
        tetrix_goal_commander,
        mission_gui,
    ])
