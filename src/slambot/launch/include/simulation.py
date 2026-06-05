from pathlib import Path

from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription as Include
from launch.launch_description_sources import \
    AnyLaunchDescriptionSource as LaunchFile
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkgdir = Path(get_package_share_directory('slambot'))
    gazebo_ros_dir = Path(get_package_share_directory('ros_gz_sim'))

    world_file = LaunchConfiguration('world_file')
    xacro_file = LaunchConfiguration('xacro_file')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    return LaunchDescription([
        DeclareLaunchArgument('world_file'),
        DeclareLaunchArgument('xacro_file'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.0'),
        DeclareLaunchArgument('roll', default_value='0.0'),
        DeclareLaunchArgument('pitch', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),

        Include(
            LaunchFile(str(gazebo_ros_dir / 'launch' / 'gz_sim.launch.py')),
            launch_arguments={
                'gz_args': ['-r ', world_file],
                'use_sim_time': 'true',
                'gui': 'true',
                'on_exit_shutdown': 'true'
            }.items()
        ),
        Node(
            name='robot_state_publisher',
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': Command(['xacro ', xacro_file]),
            }]
        ),
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'slambot',
                '-topic', 'robot_description',
                '-x', x,
                '-y', y,
                '-z', z,
                '-R', roll,
                '-P', pitch,
                '-Y', yaw,
                '-allow_renaming', 'true'
            ],
            output='screen'
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                'diff_drive_base_controller',
                '--param-file', pkgdir / 'config' / 'controller.yaml',
            ],
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                '/camera/image@sensor_msgs/msg/Image@gz.msgs.Image',
                '/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
                '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
                '/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
            ],
            output='screen'
        ),
    ])
