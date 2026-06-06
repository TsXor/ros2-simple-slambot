cmake_minimum_required(VERSION 3.8)
project(slambot)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(nav2_msgs REQUIRED)

add_executable(initial_exploration src/initial_exploration.cpp)
target_include_directories(initial_exploration PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>
)
target_compile_features(initial_exploration PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17
ament_target_dependencies(initial_exploration
  rclcpp geometry_msgs nav_msgs tf2 tf2_geometry_msgs rclcpp_action nav2_msgs
)

install(TARGETS initial_exploration
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)
install(DIRECTORY model
  DESTINATION share/${PROJECT_NAME}
)
install(DIRECTORY rviz
  DESTINATION share/${PROJECT_NAME}
)
install(DIRECTORY world
  DESTINATION share/${PROJECT_NAME}
)
ament_package()
