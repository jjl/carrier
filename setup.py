#!/usr/bin/env python
from setuptools import setup, find_packages

import conveyor


install_requires = [
    "APScheduler",
    "forklift",
    "redis",
    "xmlrpc2",
]

setup(
    name="conveyor",
    version=conveyor.__version__,

    description="Warehouse and PyPI Synchronization",
    long_description=open("README.rst").read(),
    url="https://github.com/crateio/conveyor/",
    license=open("LICENSE").read(),

    author="Donald Stufft",
    author_email="donald.stufft@gmail.com",

    install_requires=install_requires,

    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
)
