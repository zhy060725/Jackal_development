from setuptools import setup


package_name = "jackal_basic_motion"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Jackal Development Team",
    maintainer_email="user@example.com",
    description="Basic motion node for Jackal direction and speed commands.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "basic_motion_node = jackal_basic_motion.basic_motion_node:main",
        ],
    },
)
