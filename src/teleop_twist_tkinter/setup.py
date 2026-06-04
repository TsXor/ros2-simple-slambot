from setuptools import setup

package_name = 'teleop_twist_tkinter'

setup(
    name=package_name,
    version='0.0.1',
    packages=[],
    py_modules=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tsxor',
    maintainer_email='zhang050525@outlook.com',
    description='Teleop twist control with Tkinter',
    license='BSD',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'teleop_twist_tkinter = teleop_twist_tkinter:main'
        ],
    },
)
