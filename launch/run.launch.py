import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import SetParameter


def generate_launch_description():

    share_dir = get_package_share_directory('lio_sam')
    parameter_file = LaunchConfiguration('params_file')
    ekf_params_file = LaunchConfiguration('ekf_params_file')
    rviz_config_file = os.path.join(share_dir, 'config', 'tartan.rviz')

    params_declare = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            share_dir, 'config', 'tartan_params.yaml'),
        description='FPath to the ROS2 parameters file to use.')
    
    ekf_params_declare = DeclareLaunchArgument(
        'ekf_params_file',
        default_value=os.path.join(
            share_dir, 'config', 'ekf_params.yaml'),
        description='EKF params file path.')
    
    map_name_declare = DeclareLaunchArgument(
        'map_name',
        default_value='my_map',
        description='Map name directory.')

    set_use_sim_time = SetParameter(name="use_sim_time", value="True")

    # Based on dev.sh docker script
    MAPS_DIRECTORY = 'maps'

    return LaunchDescription([
        set_use_sim_time,
        params_declare,
        ekf_params_declare,
        map_name_declare,
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments='0.0 0.0 0.0 0.0 0.0 0.0 map odom'.split(' '),
            parameters=[parameter_file],
            output='screen'
            ),
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat',
            parameters=[ekf_params_file],
            output='screen',
            remappings=[
                # Input
                ('gps/fix', '/sensor/gps/nav_sat_fix'),
                ('odometry/filtered', 'odometry/ekf_local'),
                ('imu', '/sensor/imu/front/data'),
                # Output
                ('gps/filtered', 'gps/filtered'),
                ('odometry/gps', 'odometry/gps')
                ]
            ),
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_gps',
            parameters=[ekf_params_file],
            output='screen',
            remappings=[
                ('odometry/filtered', 'odometry/ekf_local')
                ]
            ),
        Node(
            package='lio_sam',
            executable='lio_sam_imuPreintegration',
            name='lio_sam_imuPreintegration',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_imageProjection',
            name='lio_sam_imageProjection',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_featureExtraction',
            name='lio_sam_featureExtraction',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_mapOptimization',
            name='lio_sam_mapOptimization',
            parameters=[parameter_file,
                        {
                            'savePCDDirectory': PathJoinSubstitution([
                                "/", MAPS_DIRECTORY, LaunchConfiguration('map_name'), ""
                            ])
                        }
                        ],
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        )
    ])
