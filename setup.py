#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = "1.0.0"

requirements = [
    'attrs==18.2.0',
    'numpy==1.15.4',
    'pandas==0.23.4',
    'pyaml==17.12.1',
    'PyWavelets==1.0.1',
    'PyYAML==5.4',
    'scipy==1.1.0',
    'tqdm==4.28.1',
]

setup(
    name='pmvc',
    version=version,
    description=(
        'A utility that creates pmv videos.'),
    author='indigocalifornia',
    url='https://github.com/indigocalifornia/pmvc',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.7',
    install_requires=requirements,
)
