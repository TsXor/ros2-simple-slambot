import json
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument, OpaqueFunction
from launch.actions import IncludeLaunchDescription as Include
from launch.actions import SetLaunchConfiguration
from launch.launch_description_sources import \
    AnyLaunchDescriptionSource as LaunchFile
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkgdir = Path(get_package_share_directory('slambot'))
    launch_include_dir = pkgdir / 'launch' / 'include'
    xacro_file = pkgdir / 'model' / 'model.xacro'

    world_file = LaunchConfiguration('world_file')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    def find_packaged_world(context: LaunchContext, *args, **kwargs):
        world = str(context.launch_configurations['world'])
        if not world:
            world_params = ['world_file', 'x', 'y', 'z', 'roll', 'pitch', 'yaw']
            world_specified = all(context.launch_configurations[p] for p in world_params)
            if not world_specified: raise ValueError('world parameters not specified')
            return []
        world_path = pkgdir / 'world' / f'{world}.world'
        config_path = pkgdir / 'world' / f'{world}.json'
        if not world_path.exists():
            raise ValueError(f'specified packaged world {world} does not exist')
        if not config_path.exists():
            raise ValueError(f'world {world} is packaged, but corresponding config file not found')
        world_info = json.loads(config_path.read_text())
        [x, y, z], [roll, pitch, yaw] = world_info['initial_pose']
        return [
            SetLaunchConfiguration('world_file', str(world_path)),
            SetLaunchConfiguration('x', str(x)),
            SetLaunchConfiguration('y', str(y)),
            SetLaunchConfiguration('z', str(z)),
            SetLaunchConfiguration('roll', str(roll)),
            SetLaunchConfiguration('pitch', str(pitch)),
            SetLaunchConfiguration('yaw', str(yaw)),
        ]

    return LaunchDescription([
        DeclareLaunchArgument('world'),
        DeclareLaunchArgument('world_file'),
        DeclareLaunchArgument('x'),
        DeclareLaunchArgument('y'),
        DeclareLaunchArgument('z'),
        DeclareLaunchArgument('roll'),
        DeclareLaunchArgument('pitch'),
        DeclareLaunchArgument('yaw'),

        OpaqueFunction(function=find_packaged_world),
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
    ])
