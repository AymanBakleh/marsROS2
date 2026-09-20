cmake_minimum_required(VERSION 3.8)
project(clover_simulation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}
)

install(FILES resource/${PROJECT_NAME}
  DESTINATION share/ament_index/resource_index/packages
)

install(FILES package.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
