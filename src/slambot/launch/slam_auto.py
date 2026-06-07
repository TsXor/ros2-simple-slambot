from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription as Include
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import \
    AnyLaunchDescriptionSource as LaunchFile
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkgdir = Path(get_package_share_directory('slambot'))
    frontier_exploration_dir = Path(get_package_share_directory('frontier_exploration_ros2'))
    launch_include_dir = pkgdir / 'launch' / 'include'

    world = LaunchConfiguration('world')
    world_file = LaunchConfiguration('world_file')
    carto_config = LaunchConfiguration('carto_config')
    nav2_config = LaunchConfiguration('nav2_config')
    explorer_config = LaunchConfiguration('explorer_config')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    initial_explorer_desc = Node(
        name='initial_exploration',
        package='slambot',
        executable='initial_exploration',
        output='screen',
        parameters=[{
            'rotation_speed': 1.2,              # rad/s，可调
            'target_rotation': 6.28318530718,   # 2*pi，即 360°
            'cmd_vel_topic': 'cmd_vel',
            'odom_topic': 'odom',
        }]
    )
    full_explorer_desc = Include(
        LaunchFile(str(frontier_exploration_dir / 'launch' / 'frontier_explorer.launch.py')),
        launch_arguments={
            'use_sim_time': 'true',
            'params_file': explorer_config,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='',
            description='Name of a packaged world'
        ),
        DeclareLaunchArgument(
            'world_file',
            default_value='',
            description='Path to Gazebo world file'
        ),
        DeclareLaunchArgument(
            'carto_config',
            default_value=str(pkgdir / 'config' / 'cartographer.lua'),
            description='Path to Cartographer configuration file'
        ),
        DeclareLaunchArgument(
            'nav2_config',
            default_value=str(pkgdir / 'config' / 'nav2_params.yaml'),
            description='Path to Navigation2 configuration file'
        ),
        DeclareLaunchArgument(
            'explorer_config',
            default_value=str(pkgdir / 'config' / 'explorer_params.yaml'),
            description='Path to Frontier Exploration configuration file'
        ),
        DeclareLaunchArgument('x'),
        DeclareLaunchArgument('y'),
        DeclareLaunchArgument('z'),
        DeclareLaunchArgument('roll'),
        DeclareLaunchArgument('pitch'),
        DeclareLaunchArgument('yaw'),

        Include(
            LaunchFile(str(launch_include_dir / 'sim_packaged.py')),
            launch_arguments={
                'world': world,
                'world_file': world_file,
                'x': x,
                'y': y,
                'z': z,
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw,
            }.items()
        ),
        Include(
            LaunchFile(str(launch_include_dir / 'cartographer.py')),
            launch_arguments={
                'resolution': '0.05',
                'publish_period_sec': '1.0',
                'config': carto_config,
            }.items()
        ),
        Include(
            LaunchFile(str(launch_include_dir / 'navigation.py')),
            launch_arguments={
                'use_sim_time': 'true',
                'params_file': nav2_config,
            }.items(),
        ),
        initial_explorer_desc,
        RegisterEventHandler(
            OnProcessExit(
                target_action=initial_explorer_desc,
                on_exit=[full_explorer_desc]
            )
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', str(pkgdir / 'rviz' / 'slam_auto.rviz')],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),
    ])
