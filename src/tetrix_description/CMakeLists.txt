cmake_minimum_required(VERSION 3.8)
project(tetrix_description)

find_package(ament_cmake REQUIRED)

# Install all resource directories so launch / rviz / urdf files are available
# at runtime via ament's share path.
install(
  DIRECTORY
    config
    launch
    meshes
    rviz
    worlds
    urdf
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/patrol_manager.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
