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

        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', str(pkgdir / 'model')),

        Include(
            LaunchFile(str(launch_include_dir / 'simulation.py')),
            launch_arguments={
                'world_file': world_file,
                'xacro_file': xacro_file,
                'x': '0.55',
                'y': '0',
                'z': '0.1',
                'roll': '0',
                'pitch': '0',
                'yaw': '0',
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
