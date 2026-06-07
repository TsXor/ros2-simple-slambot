from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription as Include
from launch.launch_description_sources import \
    AnyLaunchDescriptionSource as LaunchFile
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkgdir = Path(get_package_share_directory('slambot'))
    launch_include_dir = pkgdir / 'launch' / 'include'
    xacro_file = pkgdir / 'model' / 'model.xacro'

    world_file = LaunchConfiguration('world_file')
    carto_config = LaunchConfiguration('carto_config')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world_file',
            default_value=str(pkgdir / 'world' / 'turtlebot3_world.world'),
            description='Path to Gazebo world file'
        ),
        DeclareLaunchArgument(
            'carto_config',
            default_value=str(pkgdir / 'config' / 'cartographer.lua'),
            description='Path to Cartographer configuration file'
        ),
        DeclareLaunchArgument('x', default_value='0.55'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.1'),
        DeclareLaunchArgument('roll', default_value='0.0'),
        DeclareLaunchArgument('pitch', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),

        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', str(pkgdir / 'model')),

        Include(
            LaunchFile(str(launch_include_dir / 'simulation.py')),
            launch_arguments={
                'world_file': world_file,
                'xacro_file': xacro_file,
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
        Node(
            name='teleop',
            package='teleop_twist_tkinter',
            executable='teleop_twist_tkinter',
            output='screen',
            parameters=[{
                'stamped': True,
                'frame_id': 'cmd_vel',
                'speed': 0.5,
                'turn': 1.0,
            }],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', str(pkgdir / 'rviz' / 'slam_teleop.rviz')],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),
    ])
