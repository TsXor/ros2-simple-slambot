import json
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription as Include
from launch.actions import OpaqueFunction, SetLaunchConfiguration
from launch.launch_description_sources import \
    AnyLaunchDescriptionSource as LaunchFile
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkgdir = Path(get_package_share_directory('slambot'))
    nav2_bringup_dir = Path(get_package_share_directory('nav2_bringup'))
    launch_include_dir = pkgdir / 'launch' / 'include'

    world = LaunchConfiguration('world')
    world_file = LaunchConfiguration('world_file')
    map_file = LaunchConfiguration('map_file')
    nav2_config = LaunchConfiguration('nav2_config')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    def find_packaged_map(context: LaunchContext, *args, **kwargs):
        world = str(context.launch_configurations['world'])
        if not world:
            if not context.launch_configurations['map_file']:
                raise ValueError('map file not specified')
            return []
        world_path = pkgdir / 'world' / f'{world}.world'
        map_path = pkgdir / 'map' / f'{world}.yaml'
        if not world_path.exists():
            raise ValueError(f'specified packaged world {world} does not exist')
        if not map_path.exists():
            raise ValueError(f'world {world} is packaged, but corresponding map file not found')
        return [
            SetLaunchConfiguration('map_file', str(map_path)),
        ]

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
            'map_file',
            default_value='',
            description='Path to map file'
        ),
        DeclareLaunchArgument(
            'nav2_config',
            default_value=str(pkgdir / 'config' / 'nav2_params.yaml'),
            description='Path to Navigation2 configuration file'
        ),
        DeclareLaunchArgument('x', default_value=''),
        DeclareLaunchArgument('y', default_value=''),
        DeclareLaunchArgument('z', default_value=''),
        DeclareLaunchArgument('roll', default_value=''),
        DeclareLaunchArgument('pitch', default_value=''),
        DeclareLaunchArgument('yaw', default_value=''),

        OpaqueFunction(function=find_packaged_map),

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
            LaunchFile(str(launch_include_dir / 'navigation.py')),
            launch_arguments={
                'use_sim_time': 'true',
                'params_file': nav2_config,
            }.items(),
        ),
        Include(
            LaunchFile(str(nav2_bringup_dir / 'launch' / 'localization_launch.py')),
            launch_arguments={
                'use_sim_time': 'true',
                'params_file': nav2_config,
                'map': map_file,
            }.items(),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', str(pkgdir / 'rviz' / 'nav.rviz')],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),
    ])
