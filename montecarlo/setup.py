import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

setup(
    name='montecarlo',
    version='0.0.2',
    description='Abstract Monte Carlo and statistics',
    author='Laktionov Mikhail',
    author_email = 'miklakt@gmail.com',
    packages=['montecarlo'],
)