from setuptools import setup
setup(
    name='eagletools',
    description='Tools for manipulating PCB files created by EAGLE CAD',
    version='0.1dev',
    author='Andrew Drake',
    author_email='adrake@adrake.org',
    license='Apache-2.0',

    packages=['eagletools'],
    package_data={'eagletools': ['py.typed']},
    install_requires=[
        'click>=6.7',
        'defusedxml>=0.5.0',
        'hwpy@git+ssh://git@github.com/drakedevel/hwpy@master',
        'tabulate>=0.7.7',
    ],
    entry_points={
        'console_scripts': [
            'eagletools = eagletools.cli:cli'
        ],
    },
    zip_safe=False,
)
