from pathlib import Path

from launch import LaunchContext, LaunchDescription
from launch.actions import (DeclareLaunchArgument, OpaqueFunction,
                            SetLaunchConfiguration)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    resolution = LaunchConfiguration('resolution')
    publish_period_sec = LaunchConfiguration('publish_period_sec')
    config_dir = LaunchConfiguration('config_dir')
    config_basename = LaunchConfiguration('config_basename')

    def split_config_path(context: LaunchContext, *args, **kwargs):
        config_path = Path(context.launch_configurations['config'])
        return [
            SetLaunchConfiguration('config_dir', config_path.parent),
            SetLaunchConfiguration('config_basename', config_path.name),
        ]

    return LaunchDescription([
        DeclareLaunchArgument('resolution', default_value='0.05'),
        DeclareLaunchArgument('publish_period_sec', default_value='1.0'),
        DeclareLaunchArgument('config'),
        OpaqueFunction(function=split_config_path),

        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '-configuration_directory', config_dir,
                '-configuration_basename', config_basename,
            ]
        ),
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '-resolution', resolution,
                '-publish_period_sec', publish_period_sec,
            ]
        ),
    ])
