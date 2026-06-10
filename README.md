# ROS2 Simple SLAMbot

简单的 SLAM 机器人仿真。

## 快速开始

### 1. 克隆仓库

本仓库使用 [Git Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) 管理外部依赖。请使用 `--recursive` 参数克隆，以确保所有子模块被正确拉取：

```bash
git clone --recursive https://github.com/TsXor/ros2-simple-slambot.git
```

> 如果已经克隆了仓库但忘记加 `--recursive`，可以在仓库根目录下运行：
> ```bash
> git submodule update --init --recursive
> ```

### 2. 安装系统依赖

确保已安装 ROS 2 及 `rosdep`。首次使用 `rosdep` 时，需要初始化并更新数据库：

```bash
sudo rosdep init
rosdep update
```

然后，在工作区根目录下运行以下命令，自动安装 `src` 目录下所有包的依赖：

```bash
rosdep install -r --from-paths src --ignore-src --rosdistro $ROS_DISTRO -y
```

> `-r` 表示遇到无法解析的依赖时继续安装其他可解析的依赖。

### 3. 编译工作区

#### 编译所有包（推荐首次使用）

```bash
colcon build --packages-up-to slambot
```

> `--packages-up-to slambot` 会编译 `slambot` 及其所有依赖包。

#### 仅编译 `slambot` 包（后续增量编译）

```bash
colcon build --packages-select slambot
```

## 运行

在运行以下命令或 rqt 等工具前，记得 source 工作区：

```bash
source install/setup.bash
```

### 手动遥控建图（Teleop SLAM）

```bash
# 在 TurtleBot3 World 环境中运行
ros2 launch slambot slam_teleop.py world:=turtlebot3_world
# 在 TurtleBot3 House 环境中运行
ros2 launch slambot slam_teleop.py world:=turtlebot3_house
```

### 自动导航建图（Auto SLAM）

```bash
# 在 TurtleBot3 World 环境中运行
ros2 launch slambot slam_auto.py world:=turtlebot3_world
# 在 TurtleBot3 House 环境中运行
ros2 launch slambot slam_auto.py world:=turtlebot3_house
```

### 已知地图导航（Nav）

```bash
# 在 TurtleBot3 World 环境中运行
ros2 launch slambot nav.py world:=turtlebot3_world
# 在 TurtleBot3 House 环境中运行
ros2 launch slambot nav.py world:=turtlebot3_house
```

## 添加新世界

### 指定任意世界

你可以通过`world_file`参数来指定世界，同时需要指定对应的初始位姿。在运行已知地图导航时，你还需要用`map_file`参数指定相应的地图文件。

```bash
ros2 launch slambot slam_teleop.py world_file:=/path/to/your/world \
    x:=0.0 y:=0.0 z:=0.0 roll:=0.0 pitch:=0.0 yaw:=0.0
```

### 指定打包的世界

如果你打算经常使用某个世界，我建议将它添加到包内，并通过`world`参数使用。

要将一个世界添加到包内，你需要这样做：
1. 将世界文件放到`world`文件夹下，并保证其名称以`.world`结尾。文件名中`.world`后缀之前的部分称为世界名。
2. 在`world`文件夹下编写配置文件`<世界名>.json`。目前，你需要在这个配置文件中指定初始位姿。
3. 将世界文件依赖的模型文件放到`model`文件夹下。该文件夹在启动仿真时会自动添加到 Gazebo 的模型路径。
4. 在完成建图后，将生成的 YAML 与 PGM 文件移动到`map`文件夹下，YAML 文件需重命名为`<世界名>.yaml`。

将世界添加到包内后，就可以通过世界名来简便地使用：

```bash
ros2 launch slambot slam_teleop.py world:=<世界名>
```
