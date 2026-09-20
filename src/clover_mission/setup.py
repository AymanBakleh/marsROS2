from setuptools import setup

package_name = "clover_mission"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/forest_mission.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Clover User",
    maintainer_email="user@example.com",
    description="Goal-based mission control for Clover in Gazebo Harmonic.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "goal_commander = clover_mission.goal_commander:main",
            "tetrix_goal_commander = clover_mission.tetrix_goal_commander:main",
            "mission_gui = clover_mission.mission_gui:main",
        ],
    },
)
