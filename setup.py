#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="slowish",
    version="0.0.1",
    author="Nimbis Services, Inc.",
    author_email="info@nimbisservices.com",
    description="Lightweight implementation of Swift API for testing",
    license="BSD",
    packages=find_packages(exclude=["test_project", ]),
    install_requires=[
        "django<2.0",
    ],
    zip_safe=False,
    include_package_data=True,
    test_suite='test_project.main',
)
