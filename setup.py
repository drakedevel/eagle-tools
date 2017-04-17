from setuptools import find_packages, setup
setup(
    name='eagletools',
    description='Tools for manipulating PCB files created by EAGLE CAD',
    version='0.1dev',
    author='Andrew Drake',
    author_email='adrake@adrake.org',
    license='Apache-2.0',

    packages=find_packages(),
    install_requires=[
        'click>=6.7',
        'defusedxml>=0.5.0',
        'tabulate>=0.7.7',
    ],
    entry_points={
        'console_scripts': [
            'eagletools = eagletools.cli:cli'
        ],
    }
)
