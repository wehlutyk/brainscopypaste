from setuptools import setup, find_packages

setup(
    name='brainscopypaste',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        brainscopypaste=brainscopypaste.cli:cli
    ''',
)
